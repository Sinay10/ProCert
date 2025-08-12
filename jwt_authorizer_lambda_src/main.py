"""
JWT Token Validation Lambda Authorizer

Validates JWT tokens from AWS Cognito for API Gateway authorization.
"""

import json
import jwt
import requests
import os
from typing import Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')

# Cache for JWKS
jwks_cache = {}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer for validating JWT tokens from Cognito.
    
    Returns an IAM policy that allows or denies access to API Gateway resources.
    """
    try:
        # Extract token from Authorization header
        token = extract_token(event)
        if not token:
            logger.error("No token found in request")
            raise Exception('Unauthorized')
        
        # Validate the token
        logger.info(f"Validating token: {token[:50]}...")
        claims = validate_jwt_token(token)
        if not claims:
            logger.error("Token validation failed")
            raise Exception('Unauthorized')
        
        logger.info(f"Token validation successful. Claims: {claims}")
        
        # Extract user information
        user_id = claims.get('sub')
        email = claims.get('email')
        
        if not user_id:
            logger.error("No user ID found in token claims")
            raise Exception('Unauthorized')
        
        # Generate policy
        policy = generate_policy(user_id, 'Allow', event['methodArn'])
        
        # Add user context
        policy['context'] = {
            'user_id': user_id,
            'email': email or '',
            'token_use': claims.get('token_use', ''),
            'client_id': claims.get('client_id', '')
        }
        
        logger.info(f"Authorization successful for user: {user_id}")
        return policy
        
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        # Return deny policy
        return generate_policy('user', 'Deny', event.get('methodArn', '*'))


def extract_token(event: Dict[str, Any]) -> Optional[str]:
    """Extract JWT token from the Authorization header."""
    try:
        # For API Gateway TOKEN authorizer, the token comes in authorizationToken
        auth_token = event.get('authorizationToken', '')
        if auth_token:
            if auth_token.startswith('Bearer '):
                return auth_token[7:]  # Remove 'Bearer ' prefix
            return auth_token
        
        # Fallback: try headers (for REQUEST authorizer)
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization', '') or headers.get('authorization', '')
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        return None
    except Exception as e:
        logger.error(f"Error extracting token: {str(e)}")
        return None


def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token against Cognito User Pool.
    
    Returns the token claims if valid, None otherwise.
    """
    try:
        logger.info(f"Starting token validation for User Pool: {USER_POOL_ID}")
        
        # Get JWKS (JSON Web Key Set) from Cognito
        jwks_url = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
        logger.info(f"JWKS URL: {jwks_url}")
        
        # Use cached JWKS if available
        if jwks_url not in jwks_cache:
            logger.info("Fetching JWKS from Cognito...")
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            jwks_cache[jwks_url] = response.json()
            logger.info("JWKS cached successfully")
        
        jwks = jwks_cache[jwks_url]
        
        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        logger.info(f"Token kid: {kid}")
        
        if not kid:
            logger.error("No 'kid' found in token header")
            return None
        
        # Find the correct key
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                logger.info(f"Found matching key for kid: {kid}")
                break
        
        if not key:
            logger.error(f"No matching key found for kid: {kid}")
            logger.error(f"Available kids: {[k['kid'] for k in jwks['keys']]}")
            return None
        
        # Verify and decode the token
        logger.info("Decoding and verifying token...")
        claims = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}",
            options={"verify_aud": False}  # Cognito access tokens don't have aud claim
        )
        
        logger.info(f"Token decoded successfully. Token use: {claims.get('token_use')}")
        logger.info(f"Client ID in token: {claims.get('client_id')}")
        logger.info(f"Expected Client ID: {USER_POOL_CLIENT_ID}")
        
        # Additional validation
        if claims.get('token_use') not in ['access', 'id']:
            logger.error(f"Invalid token_use: {claims.get('token_use')}")
            return None
        
        # Validate client_id for access tokens (instead of audience)
        if claims.get('token_use') == 'access' and claims.get('client_id') != USER_POOL_CLIENT_ID:
            logger.error(f"Invalid client_id: {claims.get('client_id')}")
            return None
        
        logger.info("Token validation successful")
        return claims
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching JWKS: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None


def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
    """
    Generate IAM policy for API Gateway.
    
    Args:
        principal_id: User identifier
        effect: 'Allow' or 'Deny'
        resource: API Gateway method ARN
    
    Returns:
        IAM policy document
    """
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    return policy
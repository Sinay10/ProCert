"""
JWT Token Validation Middleware for API Gateway.

Provides utilities for validating JWT tokens from AWS Cognito
and extracting user information for authorization.
"""

import json
import os
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp')


def create_policy(effect: str, resource: str, principal_id: str = "user") -> Dict[str, Any]:
    """
    Create an IAM policy for API Gateway authorization.
    
    Args:
        effect: 'Allow' or 'Deny'
        resource: The resource ARN
        principal_id: The principal ID for the policy
        
    Returns:
        IAM policy document
    """
    return {
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


def lambda_authorizer_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer function for API Gateway.
    
    Validates JWT tokens from Authorization header and returns
    IAM policy allowing or denying access.
    """
    try:
        # Extract token from Authorization header
        token = event.get('authorizationToken', '')
        method_arn = event.get('methodArn', '')
        
        if not token.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header format")
            raise Exception('Unauthorized')
        
        access_token = token.replace('Bearer ', '')
        
        # Validate token with Cognito
        try:
            user_info = cognito_client.get_user(AccessToken=access_token)
            user_id = user_info['Username']
            
            # Extract user attributes
            user_attributes = {}
            for attr in user_info.get('UserAttributes', []):
                user_attributes[attr['Name']] = attr['Value']
            
            # Create allow policy
            policy = create_policy('Allow', method_arn, user_id)
            
            # Add user context
            policy['context'] = {
                'user_id': user_id,
                'email': user_attributes.get('email', ''),
                'name': user_attributes.get('name', ''),
                'subscription_tier': user_attributes.get('custom:subscription_tier', 'standard')
            }
            
            return policy
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.warning(f"Token validation failed: {error_code}")
            raise Exception('Unauthorized')
            
    except Exception as e:
        logger.error(f"Authorization error: {str(e)}")
        # Return deny policy
        return create_policy('Deny', method_arn, 'unauthorized')


def validate_user_access(user_id_from_token: str, requested_user_id: str) -> bool:
    """
    Validate that the user can access the requested resource.
    
    Args:
        user_id_from_token: User ID from the JWT token
        requested_user_id: User ID being requested in the API call
        
    Returns:
        True if access is allowed, False otherwise
    """
    # Users can only access their own resources
    return user_id_from_token == requested_user_id


def extract_user_from_event(event: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract user information from API Gateway event context.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary with user information or None if not available
    """
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    
    if not authorizer:
        return None
    
    return {
        'user_id': authorizer.get('user_id', ''),
        'email': authorizer.get('email', ''),
        'name': authorizer.get('name', ''),
        'subscription_tier': authorizer.get('subscription_tier', 'standard')
    }


def require_authentication(func):
    """
    Decorator to require authentication for Lambda functions.
    
    Extracts user information from the event and passes it to the function.
    """
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        user_info = extract_user_from_event(event)
        
        if not user_info or not user_info.get('user_id'):
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Add user info to event
        event['user_info'] = user_info
        
        return func(event, context)
    
    return wrapper


def require_user_authorization(func):
    """
    Decorator to require user authorization for accessing user-specific resources.
    
    Validates that the authenticated user can access the requested user resource.
    """
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        user_info = extract_user_from_event(event)
        path_parameters = event.get('pathParameters', {})
        requested_user_id = path_parameters.get('user_id', '')
        
        if not user_info or not user_info.get('user_id'):
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        if not validate_user_access(user_info['user_id'], requested_user_id):
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Access denied'})
            }
        
        # Add user info to event
        event['user_info'] = user_info
        
        return func(event, context)
    
    return wrapper


class JWTMiddleware:
    """
    JWT middleware class for handling authentication in Lambda functions.
    """
    
    def __init__(self, user_pool_id: str):
        """
        Initialize JWT middleware.
        
        Args:
            user_pool_id: AWS Cognito User Pool ID
        """
        self.user_pool_id = user_pool_id
        self.cognito_client = boto3.client('cognito-idp')
    
    def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT access token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            user_info = self.cognito_client.get_user(AccessToken=access_token)
            
            # Extract user attributes
            user_attributes = {}
            for attr in user_info.get('UserAttributes', []):
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'user_id': user_info['Username'],
                'email': user_attributes.get('email', ''),
                'name': user_attributes.get('name', ''),
                'subscription_tier': user_attributes.get('custom:subscription_tier', 'standard'),
                'email_verified': user_attributes.get('email_verified', 'false') == 'true'
            }
            
        except ClientError as e:
            logger.warning(f"Token validation failed: {e.response['Error']['Code']}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return None
    
    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            authorization_header: Authorization header value
            
        Returns:
            JWT token if valid format, None otherwise
        """
        if not authorization_header or not authorization_header.startswith('Bearer '):
            return None
        
        return authorization_header.replace('Bearer ', '')
    
    def create_error_response(self, status_code: int, message: str) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            status_code: HTTP status code
            message: Error message
            
        Returns:
            API Gateway response
        """
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({'error': message})
        }
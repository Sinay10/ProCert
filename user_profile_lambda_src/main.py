"""
User Profile Management Lambda Function

Handles user profile CRUD operations, authentication validation,
and integration with AWS Cognito for the ProCert Learning Platform.
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cognito_client = boto3.client('cognito-idp')

# Environment variables
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')
USER_POOL_ID = os.environ.get('USER_POOL_ID')

# Initialize DynamoDB table
user_profiles_table = dynamodb.Table(USER_PROFILES_TABLE) if USER_PROFILES_TABLE else None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for user profile management operations.
    
    Supports the following operations:
    - POST /auth/register - Register new user
    - POST /auth/login - User login
    - GET /profile/{user_id} - Get user profile
    - PUT /profile/{user_id} - Update user profile
    - DELETE /profile/{user_id} - Delete user profile
    - POST /auth/forgot-password - Initiate password reset
    - POST /auth/confirm-forgot-password - Confirm password reset
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        body = event.get('body', '{}')
        headers = event.get('headers', {})
        
        # Parse JSON body
        try:
            request_body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON in request body'})
        
        logger.info(f"Processing {http_method} {path}")
        
        # Route the request
        if path.startswith('/auth/register') and http_method == 'POST':
            return handle_register(request_body)
        elif path.startswith('/auth/login') and http_method == 'POST':
            return handle_login(request_body)
        elif path.startswith('/auth/forgot-password') and http_method == 'POST':
            return handle_forgot_password(request_body)
        elif path.startswith('/auth/confirm-forgot-password') and http_method == 'POST':
            return handle_confirm_forgot_password(request_body)
        elif path.startswith('/profile/') and http_method == 'GET':
            user_id = path_parameters.get('user_id')
            return handle_get_profile(user_id, event)
        elif path.startswith('/profile/') and http_method == 'PUT':
            user_id = path_parameters.get('user_id')
            return handle_update_profile(user_id, request_body, event)
        elif path.startswith('/profile/') and http_method == 'DELETE':
            user_id = path_parameters.get('user_id')
            return handle_delete_profile(user_id, event)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def handle_register(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user registration."""
    try:
        # Validate required fields
        required_fields = ['email', 'password', 'given_name', 'family_name']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'{field} is required'})
        
        email = request_body['email'].lower().strip()
        password = request_body['password']
        given_name = request_body['given_name'].strip()
        family_name = request_body['family_name'].strip()
        target_certifications = request_body.get('target_certifications', [])
        
        # Create user in Cognito
        try:
            response = cognito_client.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'given_name', 'Value': given_name},
                    {'Name': 'family_name', 'Value': family_name},
                    {'Name': 'custom:target_certifications', 'Value': ','.join(target_certifications)},
                    {'Name': 'custom:subscription_tier', 'Value': 'free'}
                ],
                TemporaryPassword=password,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            
            user_id = response['User']['Username']
            
            # Set permanent password
            cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=user_id,
                Password=password,
                Permanent=True
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                return create_response(409, {'error': 'User already exists'})
            elif error_code == 'InvalidPasswordException':
                return create_response(400, {'error': 'Password does not meet requirements'})
            else:
                logger.error(f"Cognito error: {str(e)}")
                return create_response(500, {'error': 'Registration failed'})
        
        # Create user profile in DynamoDB
        user_profile = {
            'user_id': user_id,
            'email': email,
            'name': f"{given_name} {family_name}",
            'target_certifications': target_certifications,
            'study_preferences': {
                'daily_goal_minutes': 30,
                'preferred_difficulty': 'intermediate',
                'notification_settings': {
                    'quiz_reminders': True,
                    'study_reminders': True,
                    'achievement_notifications': True,
                    'weekly_progress': True
                },
                'preferred_study_time': 'evening',
                'quiz_length_preference': 10,
                'auto_advance_difficulty': True
            },
            'created_at': datetime.utcnow().isoformat(),
            'last_active': datetime.utcnow().isoformat(),
            'is_active': True,
            'subscription_tier': 'free',
            'timezone': 'UTC',
            'language': 'en',
            'profile_completion': calculate_profile_completion({
                'name': f"{given_name} {family_name}",
                'email': email,
                'target_certifications': target_certifications
            }),
            'metadata': {}
        }
        
        user_profiles_table.put_item(Item=user_profile)
        
        # Remove sensitive data from response
        response_profile = user_profile.copy()
        
        return create_response(201, {
            'message': 'User registered successfully',
            'user_profile': response_profile
        })
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return create_response(500, {'error': 'Registration failed'})


def handle_login(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user login."""
    try:
        # Validate required fields
        if not request_body.get('email') or not request_body.get('password'):
            return create_response(400, {'error': 'Email and password are required'})
        
        email = request_body['email'].lower().strip()
        password = request_body['password']
        
        # Authenticate with Cognito
        try:
            response = cognito_client.admin_initiate_auth(
                UserPoolId=USER_POOL_ID,
                ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            id_token = auth_result['IdToken']
            refresh_token = auth_result['RefreshToken']
            
            # Get user info from token
            user_info = cognito_client.get_user(AccessToken=access_token)
            user_id = user_info['Username']
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
                return create_response(401, {'error': 'Invalid credentials'})
            else:
                logger.error(f"Login error: {str(e)}")
                return create_response(500, {'error': 'Login failed'})
        
        # Update last active in user profile
        try:
            user_profiles_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET last_active = :timestamp',
                ExpressionAttributeValues={':timestamp': datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to update last active: {str(e)}")
        
        return create_response(200, {
            'message': 'Login successful',
            'tokens': {
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token
            },
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return create_response(500, {'error': 'Login failed'})


def handle_forgot_password(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle forgot password request."""
    try:
        if not request_body.get('email'):
            return create_response(400, {'error': 'Email is required'})
        
        email = request_body['email'].lower().strip()
        
        try:
            cognito_client.forgot_password(
                ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
                Username=email
            )
            
            return create_response(200, {
                'message': 'Password reset code sent to email'
            })
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                # Don't reveal if user exists or not
                return create_response(200, {
                    'message': 'Password reset code sent to email'
                })
            else:
                logger.error(f"Forgot password error: {str(e)}")
                return create_response(500, {'error': 'Password reset failed'})
                
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return create_response(500, {'error': 'Password reset failed'})


def handle_confirm_forgot_password(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle password reset confirmation."""
    try:
        required_fields = ['email', 'confirmation_code', 'new_password']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'{field} is required'})
        
        email = request_body['email'].lower().strip()
        confirmation_code = request_body['confirmation_code']
        new_password = request_body['new_password']
        
        try:
            cognito_client.confirm_forgot_password(
                ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            
            return create_response(200, {
                'message': 'Password reset successful'
            })
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                return create_response(400, {'error': 'Invalid confirmation code'})
            elif error_code == 'ExpiredCodeException':
                return create_response(400, {'error': 'Confirmation code expired'})
            elif error_code == 'InvalidPasswordException':
                return create_response(400, {'error': 'Password does not meet requirements'})
            else:
                logger.error(f"Confirm forgot password error: {str(e)}")
                return create_response(500, {'error': 'Password reset failed'})
                
    except Exception as e:
        logger.error(f"Confirm forgot password error: {str(e)}")
        return create_response(500, {'error': 'Password reset failed'})


def handle_get_profile(user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user profile request."""
    try:
        # Extract user info from authorizer context
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        authenticated_user_id = authorizer.get('user_id', '')
        
        # Verify user can access this profile
        if authenticated_user_id != user_id:
            return create_response(403, {'error': 'Access denied'})
        
        # Get user profile from DynamoDB
        try:
            response = user_profiles_table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return create_response(404, {'error': 'User profile not found'})
            
            user_profile = response['Item']
            
            return create_response(200, {
                'user_profile': user_profile
            })
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return create_response(500, {'error': 'Failed to retrieve profile'})
            
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve profile'})


def handle_update_profile(user_id: str, request_body: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update user profile request."""
    try:
        # Extract user info from authorizer context
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        authenticated_user_id = authorizer.get('user_id', '')
        
        # Verify user can access this profile
        if authenticated_user_id != user_id:
            return create_response(403, {'error': 'Access denied'})
        
        # Get current profile
        try:
            response = user_profiles_table.get_item(Key={'user_id': user_id})
            if 'Item' not in response:
                return create_response(404, {'error': 'User profile not found'})
            
            current_profile = response['Item']
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return create_response(500, {'error': 'Failed to retrieve current profile'})
        
        # Update allowed fields
        updatable_fields = [
            'name', 'target_certifications', 'study_preferences', 
            'timezone', 'language', 'metadata'
        ]
        
        update_expression_parts = []
        expression_attribute_values = {}
        
        for field in updatable_fields:
            if field in request_body:
                update_expression_parts.append(f"{field} = :{field}")
                expression_attribute_values[f":{field}"] = request_body[field]
        
        if not update_expression_parts:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update last_active and profile_completion
        update_expression_parts.append("last_active = :last_active")
        expression_attribute_values[":last_active"] = datetime.utcnow().isoformat()
        
        # Calculate new profile completion
        updated_profile = current_profile.copy()
        updated_profile.update(request_body)
        profile_completion = calculate_profile_completion(updated_profile)
        
        update_expression_parts.append("profile_completion = :profile_completion")
        expression_attribute_values[":profile_completion"] = profile_completion
        
        # Perform update
        try:
            user_profiles_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=f"SET {', '.join(update_expression_parts)}",
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            # Get updated profile
            response = user_profiles_table.get_item(Key={'user_id': user_id})
            updated_profile = response['Item']
            
            return create_response(200, {
                'message': 'Profile updated successfully',
                'user_profile': updated_profile
            })
            
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return create_response(500, {'error': 'Failed to update profile'})
            
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return create_response(500, {'error': 'Failed to update profile'})


def handle_delete_profile(user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delete user profile request."""
    try:
        # Extract user info from authorizer context
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        authenticated_user_id = authorizer.get('user_id', '')
        
        # Verify user can access this profile
        if authenticated_user_id != user_id:
            return create_response(403, {'error': 'Access denied'})
        
        # Delete from Cognito
        try:
            cognito_client.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=user_id
            )
        except ClientError as e:
            logger.error(f"Cognito delete error: {str(e)}")
            # Continue with DynamoDB deletion even if Cognito fails
        
        # Delete from DynamoDB
        try:
            user_profiles_table.delete_item(Key={'user_id': user_id})
            
            return create_response(200, {
                'message': 'User profile deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Database delete error: {str(e)}")
            return create_response(500, {'error': 'Failed to delete profile'})
            
    except Exception as e:
        logger.error(f"Delete profile error: {str(e)}")
        return create_response(500, {'error': 'Failed to delete profile'})


def validate_jwt_token(headers: Dict[str, Any], expected_user_id: str = None) -> Dict[str, Any]:
    """
    Validate JWT token from Authorization header.
    
    Args:
        headers: Request headers
        expected_user_id: Expected user ID for authorization check
        
    Returns:
        Dict with 'valid' boolean and 'error' message if invalid
    """
    try:
        auth_header = headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'valid': False, 'error': 'Missing or invalid Authorization header'}
        
        access_token = auth_header.replace('Bearer ', '')
        
        # Validate token with Cognito
        try:
            user_info = cognito_client.get_user(AccessToken=access_token)
            token_user_id = user_info['Username']
            
            # Check if user is authorized to access this resource
            if expected_user_id and token_user_id != expected_user_id:
                return {'valid': False, 'error': 'Unauthorized access'}
            
            return {'valid': True, 'user_id': token_user_id}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                return {'valid': False, 'error': 'Invalid or expired token'}
            else:
                logger.error(f"Token validation error: {str(e)}")
                return {'valid': False, 'error': 'Token validation failed'}
                
    except Exception as e:
        logger.error(f"JWT validation error: {str(e)}")
        return {'valid': False, 'error': 'Token validation failed'}


def calculate_profile_completion(profile: Dict[str, Any]) -> float:
    """Calculate profile completion percentage."""
    completion_factors = {
        'has_name': bool(profile.get('name', '').strip()),
        'has_email': bool(profile.get('email', '').strip()),
        'has_target_certifications': len(profile.get('target_certifications', [])) > 0,
        'has_study_preferences': bool(profile.get('study_preferences', {}).get('daily_goal_minutes', 0) > 0),
        'has_timezone': bool(profile.get('timezone', 'UTC') != 'UTC')
    }
    
    completed_factors = sum(1 for completed in completion_factors.values() if completed)
    return (completed_factors / len(completion_factors)) * 100


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }
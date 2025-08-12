"""
User Profile Management Lambda Function

Handles user registration, profile management, and authentication-related operations
for the ProCert Learning Platform.
"""

import json
import boto3
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from decimal import Decimal

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


def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def convert_decimals_to_numbers(obj):
    """Convert Decimal values back to numbers for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_decimals_to_numbers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_numbers(v) for v in obj]
    elif isinstance(obj, Decimal):
        # Convert Decimal to int if it's a whole number, otherwise to float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


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
            return handle_get_profile(user_id)
        elif path.startswith('/profile/') and http_method == 'PUT':
            user_id = path_parameters.get('user_id')
            return handle_update_profile(user_id, request_body)
        elif path.startswith('/profile/') and http_method == 'DELETE':
            user_id = path_parameters.get('user_id')
            return handle_delete_profile(user_id)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def handle_register(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user registration."""
    try:
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        email = request_body['email'].lower().strip()
        password = request_body['password']
        name = request_body['name'].strip()
        target_certifications = request_body.get('target_certifications', [])
        
        # Create user in Cognito
        try:
            response = cognito_client.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'given_name', 'Value': name.split()[0]},
                    {'Name': 'family_name', 'Value': ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''},
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
            
        except cognito_client.exceptions.UsernameExistsException:
            return create_response(409, {'error': 'User already exists'})
        except Exception as e:
            logger.error(f"Cognito registration error: {str(e)}")
            return create_response(500, {'error': 'Registration failed'})
        
        # Create user profile in DynamoDB
        user_profile = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'target_certifications': target_certifications,
            'study_preferences': {
                'daily_goal_minutes': Decimal('30'),
                'preferred_difficulty': 'intermediate',
                'notification_settings': {
                    'email_reminders': True,
                    'achievement_notifications': True,
                    'study_recommendations': True
                },
                'preferred_study_time': 'evening',
                'quiz_length_preference': Decimal('10')
            },
            'created_at': datetime.utcnow().isoformat(),
            'last_active': datetime.utcnow().isoformat(),
            'is_active': True,
            'subscription_tier': 'free',
            'total_study_time': Decimal('0'),
            'achievements': [],
            'metadata': {}
        }
        
        logger.info(f"Saving user profile to DynamoDB for user_id: {user_id}")
        try:
            user_profiles_table.put_item(Item=convert_floats_to_decimal(user_profile))
            logger.info(f"User profile saved successfully for user_id: {user_id}")
        except Exception as db_error:
            logger.error(f"DynamoDB error: {str(db_error)}")
            logger.error(f"Profile data: {user_profile}")
            raise db_error
        
        # Remove sensitive data from response
        response_profile = user_profile.copy()
        
        return create_response(201, {
            'message': 'User registered successfully',
            'user_id': user_id,
            'profile': response_profile
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
            
            # Update last active in profile
            try:
                user_profiles_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression='SET last_active = :timestamp',
                    ExpressionAttributeValues={':timestamp': datetime.utcnow().isoformat()}
                )
            except Exception as e:
                logger.warning(f"Failed to update last_active: {str(e)}")
            
            return create_response(200, {
                'message': 'Login successful',
                'user_id': user_id,
                'tokens': {
                    'access_token': access_token,
                    'id_token': id_token,
                    'refresh_token': refresh_token
                }
            })
            
        except cognito_client.exceptions.NotAuthorizedException:
            return create_response(401, {'error': 'Invalid credentials'})
        except cognito_client.exceptions.UserNotConfirmedException:
            return create_response(401, {'error': 'User not confirmed'})
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return create_response(500, {'error': 'Login failed'})
            
    except Exception as e:
        logger.error(f"Login handler error: {str(e)}")
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
            
        except cognito_client.exceptions.UserNotFoundException:
            # Don't reveal if user exists or not
            return create_response(200, {
                'message': 'If the email exists, a password reset code has been sent'
            })
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            return create_response(500, {'error': 'Password reset failed'})
            
    except Exception as e:
        logger.error(f"Forgot password handler error: {str(e)}")
        return create_response(500, {'error': 'Password reset failed'})


def handle_confirm_forgot_password(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle password reset confirmation."""
    try:
        required_fields = ['email', 'confirmation_code', 'new_password']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
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
            
        except cognito_client.exceptions.CodeMismatchException:
            return create_response(400, {'error': 'Invalid confirmation code'})
        except cognito_client.exceptions.ExpiredCodeException:
            return create_response(400, {'error': 'Confirmation code expired'})
        except Exception as e:
            logger.error(f"Confirm forgot password error: {str(e)}")
            return create_response(500, {'error': 'Password reset confirmation failed'})
            
    except Exception as e:
        logger.error(f"Confirm forgot password handler error: {str(e)}")
        return create_response(500, {'error': 'Password reset confirmation failed'})


def handle_get_profile(user_id: str) -> Dict[str, Any]:
    """Handle get user profile request."""
    try:
        logger.info(f"Getting profile for user_id: {user_id}")
        
        if not user_id:
            logger.error("No user_id provided")
            return create_response(400, {'error': 'User ID is required'})
        
        # Get profile from DynamoDB
        logger.info(f"Querying DynamoDB table: {USER_PROFILES_TABLE}")
        response = user_profiles_table.get_item(Key={'user_id': user_id})
        logger.info(f"DynamoDB response: {response}")
        
        if 'Item' not in response:
            logger.warning(f"Profile not found for user_id: {user_id}")
            return create_response(404, {'error': 'User profile not found'})
        
        profile = response['Item']
        logger.info(f"Profile retrieved successfully for user_id: {user_id}")
        
        return create_response(200, {'profile': profile})
        
    except Exception as e:
        logger.error(f"Get profile error for user_id {user_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return create_response(500, {'error': 'Failed to retrieve profile'})


def handle_update_profile(user_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update user profile request."""
    try:
        if not user_id:
            return create_response(400, {'error': 'User ID is required'})
        
        # Get current profile
        response = user_profiles_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'User profile not found'})
        
        current_profile = response['Item']
        
        # Update allowed fields
        update_expression_parts = []
        expression_attribute_values = {}
        
        updatable_fields = [
            'name', 'target_certifications', 'study_preferences', 
            'subscription_tier', 'achievements', 'metadata'
        ]
        
        for field in updatable_fields:
            if field in request_body:
                update_expression_parts.append(f"{field} = :{field}")
                expression_attribute_values[f":{field}"] = request_body[field]
        
        if not update_expression_parts:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update last_active
        update_expression_parts.append("last_active = :last_active")
        expression_attribute_values[":last_active"] = datetime.utcnow().isoformat()
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        # Update profile
        user_profiles_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        # Get updated profile
        response = user_profiles_table.get_item(Key={'user_id': user_id})
        updated_profile = response['Item']
        
        return create_response(200, {
            'message': 'Profile updated successfully',
            'profile': updated_profile
        })
        
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return create_response(500, {'error': 'Failed to update profile'})


def handle_delete_profile(user_id: str) -> Dict[str, Any]:
    """Handle delete user profile request."""
    try:
        if not user_id:
            return create_response(400, {'error': 'User ID is required'})
        
        # Delete from Cognito
        try:
            cognito_client.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=user_id
            )
        except cognito_client.exceptions.UserNotFoundException:
            logger.warning(f"User {user_id} not found in Cognito")
        
        # Delete from DynamoDB
        user_profiles_table.delete_item(Key={'user_id': user_id})
        
        return create_response(200, {'message': 'User profile deleted successfully'})
        
    except Exception as e:
        logger.error(f"Delete profile error: {str(e)}")
        return create_response(500, {'error': 'Failed to delete profile'})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized API response."""
    # Convert Decimal objects to JSON-serializable numbers
    serializable_body = convert_decimals_to_numbers(body)
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(serializable_body)
    }
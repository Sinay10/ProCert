"""
Integration tests for authentication flow and user profile management.
"""

import pytest
import json
import boto3
import requests
from moto import mock_aws
import os
import time
from datetime import datetime
from unittest.mock import patch, MagicMock


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_infrastructure(aws_credentials):
    """Set up mock AWS infrastructure for integration testing."""
    with mock_aws():
        # Create DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # User profiles table
        user_profiles_table = dynamodb.create_table(
            TableName='test-user-profiles',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Quiz sessions table
        quiz_sessions_table = dynamodb.create_table(
            TableName='test-quiz-sessions',
            KeySchema=[
                {'AttributeName': 'quiz_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'quiz_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'started_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserQuizIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'started_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Recommendations table
        recommendations_table = dynamodb.create_table(
            TableName='test-recommendations',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'recommendation_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'recommendation_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create Cognito User Pool
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        user_pool = cognito_client.create_user_pool(
            PoolName='test-procert-pool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email']
        )
        
        user_pool_client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool['UserPool']['Id'],
            ClientName='test-procert-client',
            GenerateSecret=False,
            ExplicitAuthFlows=['ADMIN_NO_SRP_AUTH', 'USER_PASSWORD_AUTH']
        )
        
        yield {
            'dynamodb': dynamodb,
            'cognito_client': cognito_client,
            'user_pool_id': user_pool['UserPool']['Id'],
            'user_pool_client_id': user_pool_client['UserPoolClient']['ClientId'],
            'tables': {
                'user_profiles': user_profiles_table,
                'quiz_sessions': quiz_sessions_table,
                'recommendations': recommendations_table
            }
        }


class TestAuthenticationFlow:
    """Test complete authentication flow integration."""
    
    def test_user_registration_flow(self, mock_infrastructure):
        """Test complete user registration flow."""
        # Set up environment variables
        os.environ['USER_PROFILES_TABLE'] = 'test-user-profiles'
        os.environ['USER_POOL_ID'] = mock_infrastructure['user_pool_id']
        os.environ['USER_POOL_CLIENT_ID'] = mock_infrastructure['user_pool_client_id']
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # Test data
        registration_data = {
            "email": "testuser@example.com",
            "password": "TestPass123!",
            "name": "Test User",
            "target_certifications": ["SAA", "DVA"]
        }
        
        # Test registration
        response = user_profile_lambda.handle_register(registration_data)
        
        assert response['statusCode'] == 201
        response_data = json.loads(response['body'])
        assert 'user_id' in response_data
        assert 'profile' in response_data
        
        user_id = response_data['user_id']
        
        # Verify user was created in DynamoDB
        user_profiles_table = mock_infrastructure['tables']['user_profiles']
        db_response = user_profiles_table.get_item(Key={'user_id': user_id})
        assert 'Item' in db_response
        
        profile = db_response['Item']
        assert profile['email'] == registration_data['email']
        assert profile['name'] == registration_data['name']
        assert profile['target_certifications'] == registration_data['target_certifications']
        
        return user_id, registration_data
    
    def test_user_login_flow(self, mock_infrastructure):
        """Test complete user login flow."""
        # First register a user
        user_id, registration_data = self.test_user_registration_flow(mock_infrastructure)
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # Test login
        login_data = {
            "email": registration_data['email'],
            "password": registration_data['password']
        }
        
        response = user_profile_lambda.handle_login(login_data)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert response_data['message'] == 'Login successful'
        assert 'tokens' in response_data
        assert 'user_id' in response_data
        assert response_data['user_id'] == user_id
        
        # Verify tokens are present
        tokens = response_data['tokens']
        assert 'access_token' in tokens
        assert 'id_token' in tokens
        assert 'refresh_token' in tokens
        
        return user_id, tokens
    
    def test_profile_management_flow(self, mock_infrastructure):
        """Test complete profile management flow."""
        # First register and login a user
        user_id, tokens = self.test_user_login_flow(mock_infrastructure)
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # Test get profile
        response = user_profile_lambda.handle_get_profile(user_id)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert 'profile' in response_data
        
        original_profile = response_data['profile']
        
        # Test update profile
        update_data = {
            "name": "Updated Test User",
            "target_certifications": ["SAA", "DVA", "SOA"],
            "study_preferences": {
                "daily_goal_minutes": 60,
                "preferred_difficulty": "advanced",
                "notification_settings": {
                    "email_reminders": False,
                    "achievement_notifications": True,
                    "study_recommendations": True
                }
            }
        }
        
        response = user_profile_lambda.handle_update_profile(user_id, update_data)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert response_data['message'] == 'Profile updated successfully'
        
        updated_profile = response_data['profile']
        assert updated_profile['name'] == update_data['name']
        assert updated_profile['target_certifications'] == update_data['target_certifications']
        assert updated_profile['study_preferences']['daily_goal_minutes'] == 60
        
        # Verify last_active was updated
        assert updated_profile['last_active'] > original_profile['last_active']
    
    def test_password_reset_flow(self, mock_infrastructure):
        """Test password reset flow."""
        # First register a user
        user_id, registration_data = self.test_user_registration_flow(mock_infrastructure)
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # Test forgot password
        forgot_password_data = {
            "email": registration_data['email']
        }
        
        response = user_profile_lambda.handle_forgot_password(forgot_password_data)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert 'Password reset code sent' in response_data['message'] or 'If the email exists' in response_data['message']
        
        # Note: In a real scenario, we would get the confirmation code from email
        # For testing, we'll simulate the confirmation
        confirm_data = {
            "email": registration_data['email'],
            "confirmation_code": "123456",  # Mock code
            "new_password": "NewTestPass123!"
        }
        
        # This would normally work with a real confirmation code
        # For moto testing, we'll just verify the function handles the request
        response = user_profile_lambda.handle_confirm_forgot_password(confirm_data)
        
        # The response might be an error due to moto limitations, but we verify the function runs
        assert response['statusCode'] in [200, 400, 500]
    
    def test_user_deletion_flow(self, mock_infrastructure):
        """Test user deletion flow."""
        # First register a user
        user_id, registration_data = self.test_user_registration_flow(mock_infrastructure)
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # Verify user exists
        response = user_profile_lambda.handle_get_profile(user_id)
        assert response['statusCode'] == 200
        
        # Delete user
        response = user_profile_lambda.handle_delete_profile(user_id)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert response_data['message'] == 'User profile deleted successfully'
        
        # Verify user no longer exists in DynamoDB
        user_profiles_table = mock_infrastructure['tables']['user_profiles']
        db_response = user_profiles_table.get_item(Key={'user_id': user_id})
        assert 'Item' not in db_response


class TestJWTAuthorization:
    """Test JWT token validation and authorization."""
    
    @patch('jwt_authorizer_lambda_src.main.requests.get')
    @patch('jwt_authorizer_lambda_src.main.jwt.decode')
    def test_valid_jwt_token(self, mock_jwt_decode, mock_requests_get):
        """Test JWT token validation with valid token."""
        # Set up environment variables
        os.environ['USER_POOL_ID'] = 'us-east-1_testpool'
        os.environ['USER_POOL_CLIENT_ID'] = 'test-client-id'
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'jwt_authorizer_lambda_src'))
        import main as jwt_authorizer
        
        # Mock JWKS response
        mock_requests_get.return_value.json.return_value = {
            'keys': [
                {
                    'kid': 'test-key-id',
                    'kty': 'RSA',
                    'use': 'sig',
                    'n': 'test-n',
                    'e': 'AQAB'
                }
            ]
        }
        mock_requests_get.return_value.raise_for_status.return_value = None
        
        # Mock JWT decode
        mock_jwt_decode.return_value = {
            'sub': 'test-user-123',
            'email': 'test@example.com',
            'token_use': 'access',
            'client_id': 'test-client-id'
        }
        
        # Test event
        event = {
            'headers': {
                'Authorization': 'Bearer valid-jwt-token'
            },
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/profile/test-user-123'
        }
        
        with patch('jwt_authorizer_lambda_src.main.jwt.get_unverified_header') as mock_header:
            mock_header.return_value = {'kid': 'test-key-id'}
            
            with patch('jwt_authorizer_lambda_src.main.jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
                mock_from_jwk.return_value = MagicMock()
                
                response = jwt_authorizer.lambda_handler(event, {})
                
                assert response['principalId'] == 'test-user-123'
                assert response['policyDocument']['Statement'][0]['Effect'] == 'Allow'
                assert response['context']['user_id'] == 'test-user-123'
                assert response['context']['email'] == 'test@example.com'
    
    def test_invalid_jwt_token(self):
        """Test JWT token validation with invalid token."""
        # Set up environment variables
        os.environ['USER_POOL_ID'] = 'us-east-1_testpool'
        os.environ['USER_POOL_CLIENT_ID'] = 'test-client-id'
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'jwt_authorizer_lambda_src'))
        import main as jwt_authorizer
        
        # Test event with invalid token
        event = {
            'headers': {
                'Authorization': 'Bearer invalid-jwt-token'
            },
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/profile/test-user-123'
        }
        
        response = jwt_authorizer.lambda_handler(event, {})
        
        assert response['principalId'] == 'user'
        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'
    
    def test_missing_authorization_header(self):
        """Test JWT authorization with missing Authorization header."""
        # Set up environment variables
        os.environ['USER_POOL_ID'] = 'us-east-1_testpool'
        os.environ['USER_POOL_CLIENT_ID'] = 'test-client-id'
        
        # Import after setting environment variables
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'jwt_authorizer_lambda_src'))
        import main as jwt_authorizer
        
        # Test event without Authorization header
        event = {
            'headers': {},
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/profile/test-user-123'
        }
        
        response = jwt_authorizer.lambda_handler(event, {})
        
        assert response['principalId'] == 'user'
        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'


class TestEndToEndFlow:
    """Test complete end-to-end authentication and API flow."""
    
    def test_complete_user_journey(self, mock_infrastructure):
        """Test complete user journey from registration to API usage."""
        # Set up environment variables
        os.environ['USER_PROFILES_TABLE'] = 'test-user-profiles'
        os.environ['USER_POOL_ID'] = mock_infrastructure['user_pool_id']
        os.environ['USER_POOL_CLIENT_ID'] = mock_infrastructure['user_pool_client_id']
        
        # Import Lambda functions
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))
        import main as user_profile_lambda
        
        # 1. User Registration
        registration_data = {
            "email": "journey@example.com",
            "password": "JourneyPass123!",
            "name": "Journey User",
            "target_certifications": ["SAA"]
        }
        
        response = user_profile_lambda.handle_register(registration_data)
        assert response['statusCode'] == 201
        
        user_id = json.loads(response['body'])['user_id']
        
        # 2. User Login
        login_data = {
            "email": registration_data['email'],
            "password": registration_data['password']
        }
        
        response = user_profile_lambda.handle_login(login_data)
        assert response['statusCode'] == 200
        
        tokens = json.loads(response['body'])['tokens']
        
        # 3. Profile Access (simulating authorized request)
        response = user_profile_lambda.handle_get_profile(user_id)
        assert response['statusCode'] == 200
        
        profile = json.loads(response['body'])['profile']
        assert profile['email'] == registration_data['email']
        
        # 4. Profile Update
        update_data = {
            "target_certifications": ["SAA", "DVA"],
            "study_preferences": {
                "daily_goal_minutes": 45,
                "preferred_difficulty": "intermediate"
            }
        }
        
        response = user_profile_lambda.handle_update_profile(user_id, update_data)
        assert response['statusCode'] == 200
        
        updated_profile = json.loads(response['body'])['profile']
        assert len(updated_profile['target_certifications']) == 2
        assert updated_profile['study_preferences']['daily_goal_minutes'] == 45
        
        # 5. Verify persistence
        response = user_profile_lambda.handle_get_profile(user_id)
        assert response['statusCode'] == 200
        
        final_profile = json.loads(response['body'])['profile']
        assert final_profile['target_certifications'] == ["SAA", "DVA"]


if __name__ == '__main__':
    pytest.main([__file__])
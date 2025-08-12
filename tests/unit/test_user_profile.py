"""
Unit tests for user profile management functionality.
"""

import pytest
import json
import boto3
from moto import mock_aws
from datetime import datetime
from unittest.mock import patch, MagicMock
import os
import sys

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'user_profile_lambda_src'))

from models import UserProfile, StudyPreferences, validate_certification_code
import main as user_profile_lambda


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    os.environ['USER_PROFILES_TABLE'] = 'test-user-profiles'
    os.environ['USER_POOL_ID'] = 'us-east-1_testpool'
    os.environ['USER_POOL_CLIENT_ID'] = 'test-client-id'
    os.environ['QUIZ_SESSIONS_TABLE'] = 'test-quiz-sessions'
    os.environ['RECOMMENDATIONS_TABLE'] = 'test-recommendations'


@pytest.fixture
def dynamodb_table(aws_credentials, mock_env_vars):
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create user profiles table
        table = dynamodb.create_table(
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
        
        yield table


@pytest.fixture
def cognito_client(aws_credentials):
    """Create a mock Cognito client for testing."""
    with mock_aws():
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        # Create user pool
        user_pool = client.create_user_pool(
            PoolName='test-pool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            }
        )
        
        # Create user pool client
        client.create_user_pool_client(
            UserPoolId=user_pool['UserPool']['Id'],
            ClientName='test-client'
        )
        
        yield client


class TestUserProfileModels:
    """Test user profile data models."""
    
    def test_study_preferences_creation(self):
        """Test StudyPreferences model creation and validation."""
        prefs = StudyPreferences()
        assert prefs.daily_goal_minutes == 30
        assert prefs.preferred_difficulty == "intermediate"
        assert prefs.is_valid()
        
        # Test custom preferences
        custom_prefs = StudyPreferences(
            daily_goal_minutes=60,
            preferred_difficulty="advanced",
            preferred_study_time="morning",
            quiz_length_preference=15
        )
        assert custom_prefs.is_valid()
        assert custom_prefs.daily_goal_minutes == 60
        assert custom_prefs.preferred_difficulty == "advanced"
    
    def test_study_preferences_validation(self):
        """Test StudyPreferences validation."""
        # Invalid daily goal
        prefs = StudyPreferences(daily_goal_minutes=-10)
        assert not prefs.is_valid()
        errors = prefs.validate()
        assert any("daily_goal_minutes" in error for error in errors)
        
        # Invalid difficulty
        prefs = StudyPreferences(preferred_difficulty="expert")
        assert not prefs.is_valid()
        errors = prefs.validate()
        assert any("preferred_difficulty" in error for error in errors)
    
    def test_user_profile_creation(self):
        """Test UserProfile model creation and validation."""
        profile = UserProfile(
            user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        assert profile.is_valid()
        assert profile.user_id == "test-user-123"
        assert profile.email == "test@example.com"
        assert profile.subscription_tier == "free"
        assert profile.is_active is True
    
    def test_user_profile_validation(self):
        """Test UserProfile validation."""
        # Missing required fields
        profile = UserProfile(user_id="", email="", name="")
        assert not profile.is_valid()
        errors = profile.validate()
        assert len(errors) >= 3  # user_id, email, name errors
        
        # Invalid email
        profile = UserProfile(
            user_id="test-user",
            email="invalid-email",
            name="Test User"
        )
        assert not profile.is_valid()
        errors = profile.validate()
        assert any("email" in error for error in errors)
    
    def test_user_profile_certification_management(self):
        """Test certification target management."""
        profile = UserProfile(
            user_id="test-user",
            email="test@example.com",
            name="Test User"
        )
        
        # Add valid certification
        assert profile.add_certification_target("SAA")
        assert "SAA" in profile.target_certifications
        
        # Don't add duplicate
        assert not profile.add_certification_target("SAA")
        assert profile.target_certifications.count("SAA") == 1
        
        # Add another certification
        assert profile.add_certification_target("DVA")
        assert len(profile.target_certifications) == 2
        
        # Remove certification
        assert profile.remove_certification_target("SAA")
        assert "SAA" not in profile.target_certifications
        assert len(profile.target_certifications) == 1
    
    def test_user_profile_serialization(self):
        """Test UserProfile to_dict and from_dict methods."""
        original_profile = UserProfile(
            user_id="test-user",
            email="test@example.com",
            name="Test User",
            target_certifications=["SAA", "DVA"]
        )
        
        # Convert to dict
        profile_dict = original_profile.to_dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "test-user"
        assert profile_dict["email"] == "test@example.com"
        
        # Convert back from dict
        restored_profile = UserProfile.from_dict(profile_dict)
        assert restored_profile.user_id == original_profile.user_id
        assert restored_profile.email == original_profile.email
        assert restored_profile.target_certifications == original_profile.target_certifications


class TestUserProfileLambda:
    """Test user profile Lambda functions."""
    
    @patch('user_profile_lambda_src.main.user_profiles_table')
    @patch('user_profile_lambda_src.main.cognito_client')
    def test_handle_register_success(self, mock_cognito, mock_table, mock_env_vars):
        """Test successful user registration."""
        # Mock Cognito response
        mock_cognito.admin_create_user.return_value = {
            'User': {'Username': 'test-user-123'}
        }
        mock_cognito.admin_set_user_password.return_value = {}
        
        # Mock DynamoDB response
        mock_table.put_item.return_value = {}
        
        request_body = {
            "email": "test@example.com",
            "password": "TestPass123",
            "name": "Test User",
            "target_certifications": ["SAA"]
        }
        
        response = user_profile_lambda.handle_register(request_body)
        
        assert response['statusCode'] == 201
        response_data = json.loads(response['body'])
        assert response_data['message'] == 'User registered successfully'
        assert 'user_id' in response_data
        assert 'profile' in response_data
        
        # Verify Cognito calls
        mock_cognito.admin_create_user.assert_called_once()
        mock_cognito.admin_set_user_password.assert_called_once()
        
        # Verify DynamoDB call
        mock_table.put_item.assert_called_once()
    
    @patch('user_profile_lambda_src.main.cognito_client')
    def test_handle_register_user_exists(self, mock_cognito, mock_env_vars):
        """Test registration when user already exists."""
        from botocore.exceptions import ClientError
        
        # Mock Cognito to raise UsernameExistsException
        mock_cognito.admin_create_user.side_effect = ClientError(
            {'Error': {'Code': 'UsernameExistsException'}},
            'AdminCreateUser'
        )
        
        request_body = {
            "email": "existing@example.com",
            "password": "TestPass123",
            "name": "Existing User"
        }
        
        response = user_profile_lambda.handle_register(request_body)
        
        assert response['statusCode'] == 409
        response_data = json.loads(response['body'])
        assert 'User already exists' in response_data['error']
    
    def test_handle_register_missing_fields(self, mock_env_vars):
        """Test registration with missing required fields."""
        request_body = {
            "email": "test@example.com"
            # Missing password and name
        }
        
        response = user_profile_lambda.handle_register(request_body)
        
        assert response['statusCode'] == 400
        response_data = json.loads(response['body'])
        assert 'Missing required field' in response_data['error']
    
    @patch('user_profile_lambda_src.main.cognito_client')
    def test_handle_login_success(self, mock_cognito, mock_env_vars):
        """Test successful user login."""
        # Mock Cognito response
        mock_cognito.admin_initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'access-token',
                'IdToken': 'id-token',
                'RefreshToken': 'refresh-token'
            }
        }
        mock_cognito.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        request_body = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        
        with patch('user_profile_lambda_src.main.user_profiles_table') as mock_table:
            mock_table.update_item.return_value = {}
            
            response = user_profile_lambda.handle_login(request_body)
            
            assert response['statusCode'] == 200
            response_data = json.loads(response['body'])
            assert response_data['message'] == 'Login successful'
            assert 'tokens' in response_data
            assert 'user_id' in response_data
    
    @patch('user_profile_lambda_src.main.cognito_client')
    def test_handle_login_invalid_credentials(self, mock_cognito, mock_env_vars):
        """Test login with invalid credentials."""
        from botocore.exceptions import ClientError
        
        # Mock Cognito to raise NotAuthorizedException
        mock_cognito.admin_initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException'}},
            'AdminInitiateAuth'
        )
        
        request_body = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        response = user_profile_lambda.handle_login(request_body)
        
        assert response['statusCode'] == 401
        response_data = json.loads(response['body'])
        assert 'Invalid credentials' in response_data['error']
    
    @patch('user_profile_lambda_src.main.user_profiles_table')
    def test_handle_get_profile_success(self, mock_table, mock_env_vars):
        """Test successful profile retrieval."""
        # Mock DynamoDB response
        mock_table.get_item.return_value = {
            'Item': {
                'user_id': 'test-user-123',
                'email': 'test@example.com',
                'name': 'Test User',
                'target_certifications': ['SAA'],
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        response = user_profile_lambda.handle_get_profile('test-user-123')
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert 'profile' in response_data
        assert response_data['profile']['user_id'] == 'test-user-123'
    
    @patch('user_profile_lambda_src.main.user_profiles_table')
    def test_handle_get_profile_not_found(self, mock_table, mock_env_vars):
        """Test profile retrieval when user not found."""
        # Mock DynamoDB response with no item
        mock_table.get_item.return_value = {}
        
        response = user_profile_lambda.handle_get_profile('nonexistent-user')
        
        assert response['statusCode'] == 404
        response_data = json.loads(response['body'])
        assert 'User profile not found' in response_data['error']
    
    @patch('user_profile_lambda_src.main.user_profiles_table')
    def test_handle_update_profile_success(self, mock_table, mock_env_vars):
        """Test successful profile update."""
        # Mock DynamoDB responses
        mock_table.get_item.side_effect = [
            # First call - check if profile exists
            {
                'Item': {
                    'user_id': 'test-user-123',
                    'email': 'test@example.com',
                    'name': 'Test User'
                }
            },
            # Second call - return updated profile
            {
                'Item': {
                    'user_id': 'test-user-123',
                    'email': 'test@example.com',
                    'name': 'Updated User',
                    'target_certifications': ['SAA', 'DVA']
                }
            }
        ]
        mock_table.update_item.return_value = {}
        
        request_body = {
            "name": "Updated User",
            "target_certifications": ["SAA", "DVA"]
        }
        
        response = user_profile_lambda.handle_update_profile('test-user-123', request_body)
        
        assert response['statusCode'] == 200
        response_data = json.loads(response['body'])
        assert response_data['message'] == 'Profile updated successfully'
        assert 'profile' in response_data
    
    def test_create_response(self, mock_env_vars):
        """Test response creation utility."""
        response = user_profile_lambda.create_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['message'] == 'success'


class TestCertificationValidation:
    """Test certification code validation."""
    
    def test_valid_certification_codes(self):
        """Test validation of valid certification codes."""
        valid_codes = ['SAA', 'DVA', 'SOA', 'CCP', 'DOP', 'SAP', 'MLS', 'SCS', 'ANS']
        
        for code in valid_codes:
            assert validate_certification_code(code)
            assert validate_certification_code(code.lower())  # Case insensitive
    
    def test_invalid_certification_codes(self):
        """Test validation of invalid certification codes."""
        invalid_codes = ['INVALID', 'XYZ', '', None, '123']
        
        for code in invalid_codes:
            assert not validate_certification_code(code)
    
    def test_certification_code_edge_cases(self):
        """Test edge cases for certification code validation."""
        # Whitespace handling
        assert validate_certification_code('  SAA  ')
        
        # Mixed case
        assert validate_certification_code('sAa')
        assert validate_certification_code('Dva')


if __name__ == '__main__':
    pytest.main([__file__])
"""
Unit tests for User Profile Management Lambda Function.

Tests user registration, login, profile CRUD operations, and authentication flows.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

# Mock environment variables
os.environ['USER_PROFILES_TABLE'] = 'test-user-profiles-table'
os.environ['USER_POOL_ID'] = 'test-user-pool-id'
os.environ['USER_POOL_CLIENT_ID'] = 'test-user-pool-client-id'

# Import after setting environment variables
from user_profile_lambda_src.main import (
    lambda_handler, handle_register, handle_login, handle_get_profile,
    handle_update_profile, handle_delete_profile, validate_jwt_token,
    calculate_profile_completion, create_response
)


class TestUserProfileLambda:
    """Test cases for user profile Lambda function."""
    
    @pytest.fixture
    def mock_dynamodb_table(self):
        """Mock DynamoDB table."""
        with patch('user_profile_lambda_src.main.user_profiles_table') as mock_table:
            yield mock_table
    
    @pytest.fixture
    def mock_cognito_client(self):
        """Mock Cognito client."""
        with patch('user_profile_lambda_src.main.cognito_client') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile data."""
        return {
            'user_id': 'test-user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'target_certifications': ['SAA', 'DVA'],
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
            'created_at': '2025-01-01T00:00:00',
            'last_active': '2025-01-01T00:00:00',
            'is_active': True,
            'subscription_tier': 'free',
            'timezone': 'UTC',
            'language': 'en',
            'profile_completion': 80.0,
            'metadata': {}
        }
    
    def test_lambda_handler_register_success(self, mock_dynamodb_table, mock_cognito_client):
        """Test successful user registration."""
        # Mock Cognito responses
        mock_cognito_client.admin_create_user.return_value = {
            'User': {'Username': 'test-user-123'}
        }
        mock_cognito_client.admin_set_user_password.return_value = {}
        
        # Mock DynamoDB response
        mock_dynamodb_table.put_item.return_value = {}
        
        event = {
            'httpMethod': 'POST',
            'path': '/auth/register',
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'TestPass123',
                'given_name': 'Test',
                'family_name': 'User',
                'target_certifications': ['SAA']
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'User registered successfully'
        assert 'user_profile' in body
        
        # Verify Cognito calls
        mock_cognito_client.admin_create_user.assert_called_once()
        mock_cognito_client.admin_set_user_password.assert_called_once()
        
        # Verify DynamoDB call
        mock_dynamodb_table.put_item.assert_called_once()
    
    def test_lambda_handler_register_user_exists(self, mock_dynamodb_table, mock_cognito_client):
        """Test registration with existing user."""
        # Mock Cognito error
        mock_cognito_client.admin_create_user.side_effect = ClientError(
            {'Error': {'Code': 'UsernameExistsException'}}, 'AdminCreateUser'
        )
        
        event = {
            'httpMethod': 'POST',
            'path': '/auth/register',
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'TestPass123',
                'given_name': 'Test',
                'family_name': 'User'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert body['error'] == 'User already exists'
    
    def test_lambda_handler_login_success(self, mock_cognito_client):
        """Test successful user login."""
        # Mock Cognito responses
        mock_cognito_client.admin_initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test-access-token',
                'IdToken': 'test-id-token',
                'RefreshToken': 'test-refresh-token'
            }
        }
        mock_cognito_client.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        # Mock DynamoDB update
        with patch('user_profile_lambda_src.main.user_profiles_table') as mock_table:
            mock_table.update_item.return_value = {}
            
            event = {
                'httpMethod': 'POST',
                'path': '/auth/login',
                'body': json.dumps({
                    'email': 'test@example.com',
                    'password': 'TestPass123'
                })
            }
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['message'] == 'Login successful'
            assert 'tokens' in body
            assert body['user_id'] == 'test-user-123'
    
    def test_lambda_handler_login_invalid_credentials(self, mock_cognito_client):
        """Test login with invalid credentials."""
        # Mock Cognito error
        mock_cognito_client.admin_initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException'}}, 'AdminInitiateAuth'
        )
        
        event = {
            'httpMethod': 'POST',
            'path': '/auth/login',
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'WrongPassword'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid credentials'
    
    def test_lambda_handler_get_profile_success(self, mock_dynamodb_table, mock_cognito_client, sample_user_profile):
        """Test successful profile retrieval."""
        # Mock JWT validation
        mock_cognito_client.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        # Mock DynamoDB response
        mock_dynamodb_table.get_item.return_value = {
            'Item': sample_user_profile
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/profile/test-user-123',
            'pathParameters': {'user_id': 'test-user-123'},
            'headers': {'Authorization': 'Bearer test-token'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'user_profile' in body
        assert body['user_profile']['user_id'] == 'test-user-123'
    
    def test_lambda_handler_get_profile_unauthorized(self, mock_cognito_client):
        """Test profile retrieval with invalid token."""
        # Mock JWT validation failure
        mock_cognito_client.get_user.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException'}}, 'GetUser'
        )
        
        event = {
            'httpMethod': 'GET',
            'path': '/profile/test-user-123',
            'pathParameters': {'user_id': 'test-user-123'},
            'headers': {'Authorization': 'Bearer invalid-token'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_lambda_handler_update_profile_success(self, mock_dynamodb_table, mock_cognito_client, sample_user_profile):
        """Test successful profile update."""
        # Mock JWT validation
        mock_cognito_client.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        # Mock DynamoDB responses
        mock_dynamodb_table.get_item.return_value = {
            'Item': sample_user_profile
        }
        mock_dynamodb_table.update_item.return_value = {}
        
        event = {
            'httpMethod': 'PUT',
            'path': '/profile/test-user-123',
            'pathParameters': {'user_id': 'test-user-123'},
            'headers': {'Authorization': 'Bearer test-token'},
            'body': json.dumps({
                'name': 'Updated Name',
                'target_certifications': ['SAA', 'DVA', 'SOA']
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Profile updated successfully'
    
    def test_lambda_handler_delete_profile_success(self, mock_dynamodb_table, mock_cognito_client):
        """Test successful profile deletion."""
        # Mock JWT validation
        mock_cognito_client.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        # Mock Cognito and DynamoDB responses
        mock_cognito_client.admin_delete_user.return_value = {}
        mock_dynamodb_table.delete_item.return_value = {}
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/profile/test-user-123',
            'pathParameters': {'user_id': 'test-user-123'},
            'headers': {'Authorization': 'Bearer test-token'}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'User profile deleted successfully'
    
    def test_validate_jwt_token_success(self, mock_cognito_client):
        """Test successful JWT token validation."""
        mock_cognito_client.get_user.return_value = {
            'Username': 'test-user-123'
        }
        
        headers = {'Authorization': 'Bearer valid-token'}
        result = validate_jwt_token(headers, 'test-user-123')
        
        assert result['valid'] is True
        assert result['user_id'] == 'test-user-123'
    
    def test_validate_jwt_token_invalid(self, mock_cognito_client):
        """Test JWT token validation with invalid token."""
        mock_cognito_client.get_user.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException'}}, 'GetUser'
        )
        
        headers = {'Authorization': 'Bearer invalid-token'}
        result = validate_jwt_token(headers)
        
        assert result['valid'] is False
        assert 'error' in result
    
    def test_validate_jwt_token_unauthorized_user(self, mock_cognito_client):
        """Test JWT token validation with unauthorized user."""
        mock_cognito_client.get_user.return_value = {
            'Username': 'different-user-123'
        }
        
        headers = {'Authorization': 'Bearer valid-token'}
        result = validate_jwt_token(headers, 'test-user-123')
        
        assert result['valid'] is False
        assert result['error'] == 'Unauthorized access'
    
    def test_calculate_profile_completion(self):
        """Test profile completion calculation."""
        # Complete profile
        complete_profile = {
            'name': 'Test User',
            'email': 'test@example.com',
            'target_certifications': ['SAA'],
            'study_preferences': {'daily_goal_minutes': 30},
            'timezone': 'America/New_York'
        }
        
        completion = calculate_profile_completion(complete_profile)
        assert completion == 100.0
        
        # Incomplete profile
        incomplete_profile = {
            'name': 'Test User',
            'email': 'test@example.com',
            'target_certifications': [],
            'study_preferences': {'daily_goal_minutes': 0},
            'timezone': 'UTC'
        }
        
        completion = calculate_profile_completion(incomplete_profile)
        assert completion == 40.0  # 2 out of 5 factors completed
    
    def test_create_response(self):
        """Test response creation utility."""
        response = create_response(200, {'message': 'Success'})
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        assert body['message'] == 'Success'
    
    def test_lambda_handler_invalid_json(self):
        """Test handler with invalid JSON body."""
        event = {
            'httpMethod': 'POST',
            'path': '/auth/register',
            'body': 'invalid-json'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid JSON in request body'
    
    def test_lambda_handler_endpoint_not_found(self):
        """Test handler with non-existent endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/nonexistent',
            'body': '{}'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Endpoint not found'
    
    def test_handle_register_missing_fields(self):
        """Test registration with missing required fields."""
        request_body = {
            'email': 'test@example.com',
            # Missing password, given_name, family_name
        }
        
        response = handle_register(request_body)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'password is required' in body['error']
    
    def test_handle_login_missing_fields(self):
        """Test login with missing required fields."""
        request_body = {
            'email': 'test@example.com'
            # Missing password
        }
        
        response = handle_login(request_body)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Email and password are required'


class TestUserProfileModels:
    """Test cases for user profile data models."""
    
    def test_user_profile_validation(self):
        """Test user profile model validation."""
        from shared.models import UserProfile, StudyPreferences, CertificationType
        
        # Valid profile
        valid_profile = UserProfile(
            user_id='test-123',
            email='test@example.com',
            name='Test User',
            target_certifications=[CertificationType.SAA]
        )
        
        assert valid_profile.is_valid()
        assert len(valid_profile.validate()) == 0
        
        # Invalid profile - missing required fields
        invalid_profile = UserProfile(
            user_id='',  # Empty user_id
            email='invalid-email',  # Invalid email format
            name='',  # Empty name
        )
        
        assert not invalid_profile.is_valid()
        errors = invalid_profile.validate()
        assert len(errors) > 0
        assert any('user_id is required' in error for error in errors)
        assert any('email must be a valid email address' in error for error in errors)
        assert any('name is required' in error for error in errors)
    
    def test_study_preferences_validation(self):
        """Test study preferences model validation."""
        from shared.models import StudyPreferences, DifficultyLevel
        
        # Valid preferences
        valid_prefs = StudyPreferences(
            daily_goal_minutes=60,
            preferred_difficulty=DifficultyLevel.INTERMEDIATE,
            preferred_study_time='morning',
            quiz_length_preference=15
        )
        
        assert valid_prefs.is_valid()
        
        # Invalid preferences
        invalid_prefs = StudyPreferences(
            daily_goal_minutes=500,  # Too high
            preferred_study_time='invalid',  # Invalid time
            quiz_length_preference=100  # Too high
        )
        
        assert not invalid_prefs.is_valid()
        errors = invalid_prefs.validate()
        assert len(errors) > 0
    
    def test_user_profile_serialization(self):
        """Test user profile to_dict and from_dict methods."""
        from shared.models import UserProfile, CertificationType
        
        original_profile = UserProfile(
            user_id='test-123',
            email='test@example.com',
            name='Test User',
            target_certifications=[CertificationType.SAA, CertificationType.DVA]
        )
        
        # Test serialization
        profile_dict = original_profile.to_dict()
        assert profile_dict['user_id'] == 'test-123'
        assert profile_dict['email'] == 'test@example.com'
        assert profile_dict['target_certifications'] == ['SAA', 'DVA']
        
        # Test deserialization
        restored_profile = UserProfile.from_dict(profile_dict)
        assert restored_profile.user_id == original_profile.user_id
        assert restored_profile.email == original_profile.email
        assert restored_profile.target_certifications == original_profile.target_certifications
    
    def test_user_profile_methods(self):
        """Test user profile helper methods."""
        from shared.models import UserProfile, CertificationType
        
        profile = UserProfile(
            user_id='test-123',
            email='test@example.com',
            name='Test User'
        )
        
        # Test add_target_certification
        profile.add_target_certification(CertificationType.SAA)
        assert CertificationType.SAA in profile.target_certifications
        
        # Test duplicate addition (should not add twice)
        profile.add_target_certification(CertificationType.SAA)
        assert profile.target_certifications.count(CertificationType.SAA) == 1
        
        # Test remove_target_certification
        profile.remove_target_certification(CertificationType.SAA)
        assert CertificationType.SAA not in profile.target_certifications
        
        # Test update_last_active
        old_last_active = profile.last_active
        profile.update_last_active()
        assert profile.last_active > old_last_active
        
        # Test update_profile_completion
        initial_completion = profile.profile_completion
        profile.add_target_certification(CertificationType.DVA)
        profile.update_profile_completion()
        assert profile.profile_completion > initial_completion


if __name__ == '__main__':
    pytest.main([__file__])
"""
Integration tests for User Authentication Flow.

Tests the complete authentication workflow including registration,
login, profile management, and JWT token validation.
"""

import pytest
import json
import requests
import time
from typing import Dict, Any, Optional
import os
from unittest.mock import patch


class TestUserAuthenticationFlow:
    """Integration tests for user authentication and profile management."""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Get API base URL from environment or use default."""
        return os.environ.get('API_BASE_URL', 'https://api.example.com')
    
    @pytest.fixture(scope="class")
    def test_user_data(self):
        """Test user data for registration."""
        timestamp = int(time.time())
        return {
            'email': f'test.user.{timestamp}@example.com',
            'password': 'TestPassword123!',
            'given_name': 'Test',
            'family_name': 'User',
            'target_certifications': ['SAA', 'DVA']
        }
    
    @pytest.fixture(scope="class")
    def registered_user(self, api_base_url, test_user_data):
        """Register a test user and return user data with tokens."""
        # Register user
        response = requests.post(
            f"{api_base_url}/auth/register",
            json=test_user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 201:
            pytest.skip(f"User registration failed: {response.text}")
        
        registration_data = response.json()
        
        # Login to get tokens
        login_response = requests.post(
            f"{api_base_url}/auth/login",
            json={
                'email': test_user_data['email'],
                'password': test_user_data['password']
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"User login failed: {login_response.text}")
        
        login_data = login_response.json()
        
        return {
            'user_data': test_user_data,
            'user_profile': registration_data['user_profile'],
            'tokens': login_data['tokens'],
            'user_id': login_data['user_id']
        }
    
    def test_user_registration_success(self, api_base_url):
        """Test successful user registration."""
        timestamp = int(time.time())
        user_data = {
            'email': f'register.test.{timestamp}@example.com',
            'password': 'TestPassword123!',
            'given_name': 'Register',
            'family_name': 'Test',
            'target_certifications': ['CCP']
        }
        
        response = requests.post(
            f"{api_base_url}/auth/register",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data['message'] == 'User registered successfully'
        assert 'user_profile' in data
        
        profile = data['user_profile']
        assert profile['email'] == user_data['email']
        assert profile['name'] == f"{user_data['given_name']} {user_data['family_name']}"
        assert profile['target_certifications'] == user_data['target_certifications']
        assert profile['subscription_tier'] == 'free'
        assert profile['is_active'] is True
    
    def test_user_registration_duplicate_email(self, api_base_url, test_user_data):
        """Test registration with duplicate email."""
        response = requests.post(
            f"{api_base_url}/auth/register",
            json=test_user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data['error'] == 'User already exists'
    
    def test_user_registration_invalid_data(self, api_base_url):
        """Test registration with invalid data."""
        invalid_data = {
            'email': 'invalid-email',  # Invalid email format
            'password': '123',  # Too short password
            'given_name': '',  # Empty name
            'family_name': 'Test'
        }
        
        response = requests.post(
            f"{api_base_url}/auth/register",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_user_login_success(self, api_base_url, registered_user):
        """Test successful user login."""
        user_data = registered_user['user_data']
        
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={
                'email': user_data['email'],
                'password': user_data['password']
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['message'] == 'Login successful'
        assert 'tokens' in data
        assert 'access_token' in data['tokens']
        assert 'id_token' in data['tokens']
        assert 'refresh_token' in data['tokens']
        assert 'user_id' in data
    
    def test_user_login_invalid_credentials(self, api_base_url, registered_user):
        """Test login with invalid credentials."""
        user_data = registered_user['user_data']
        
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={
                'email': user_data['email'],
                'password': 'WrongPassword123!'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data['error'] == 'Invalid credentials'
    
    def test_get_user_profile_success(self, api_base_url, registered_user):
        """Test successful profile retrieval."""
        user_id = registered_user['user_id']
        access_token = registered_user['tokens']['access_token']
        
        response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'user_profile' in data
        profile = data['user_profile']
        assert profile['user_id'] == user_id
        assert profile['email'] == registered_user['user_data']['email']
    
    def test_get_user_profile_unauthorized(self, api_base_url, registered_user):
        """Test profile retrieval without valid token."""
        user_id = registered_user['user_id']
        
        response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
    
    def test_get_user_profile_invalid_token(self, api_base_url, registered_user):
        """Test profile retrieval with invalid token."""
        user_id = registered_user['user_id']
        
        response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': 'Bearer invalid-token',
                'Content-Type': 'application/json'
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
    
    def test_update_user_profile_success(self, api_base_url, registered_user):
        """Test successful profile update."""
        user_id = registered_user['user_id']
        access_token = registered_user['tokens']['access_token']
        
        update_data = {
            'name': 'Updated Test User',
            'target_certifications': ['SAA', 'DVA', 'SOA'],
            'study_preferences': {
                'daily_goal_minutes': 60,
                'preferred_difficulty': 'advanced',
                'preferred_study_time': 'morning',
                'quiz_length_preference': 15
            },
            'timezone': 'America/New_York'
        }
        
        response = requests.put(
            f"{api_base_url}/profile/{user_id}",
            json=update_data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['message'] == 'Profile updated successfully'
        assert 'user_profile' in data
        
        profile = data['user_profile']
        assert profile['name'] == update_data['name']
        assert profile['target_certifications'] == update_data['target_certifications']
        assert profile['timezone'] == update_data['timezone']
        assert profile['study_preferences']['daily_goal_minutes'] == 60
    
    def test_update_user_profile_unauthorized(self, api_base_url, registered_user):
        """Test profile update without authorization."""
        user_id = registered_user['user_id']
        
        update_data = {'name': 'Unauthorized Update'}
        
        response = requests.put(
            f"{api_base_url}/profile/{user_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
    
    def test_forgot_password_flow(self, api_base_url, registered_user):
        """Test forgot password initiation."""
        user_data = registered_user['user_data']
        
        response = requests.post(
            f"{api_base_url}/auth/forgot-password",
            json={'email': user_data['email']},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Password reset code sent to email'
    
    def test_forgot_password_nonexistent_user(self, api_base_url):
        """Test forgot password for nonexistent user."""
        response = requests.post(
            f"{api_base_url}/auth/forgot-password",
            json={'email': 'nonexistent@example.com'},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should return success to not reveal user existence
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Password reset code sent to email'
    
    def test_profile_completion_calculation(self, api_base_url, registered_user):
        """Test profile completion percentage calculation."""
        user_id = registered_user['user_id']
        access_token = registered_user['tokens']['access_token']
        
        # Get initial profile
        response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert response.status_code == 200
        initial_profile = response.json()['user_profile']
        initial_completion = initial_profile['profile_completion']
        
        # Update profile to increase completion
        update_data = {
            'timezone': 'America/Los_Angeles',
            'study_preferences': {
                'daily_goal_minutes': 45,
                'preferred_difficulty': 'intermediate'
            }
        }
        
        response = requests.put(
            f"{api_base_url}/profile/{user_id}",
            json=update_data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert response.status_code == 200
        updated_profile = response.json()['user_profile']
        updated_completion = updated_profile['profile_completion']
        
        # Profile completion should have increased
        assert updated_completion >= initial_completion
        assert 0 <= updated_completion <= 100
    
    def test_delete_user_profile_success(self, api_base_url):
        """Test successful profile deletion."""
        # Create a user specifically for deletion test
        timestamp = int(time.time())
        user_data = {
            'email': f'delete.test.{timestamp}@example.com',
            'password': 'TestPassword123!',
            'given_name': 'Delete',
            'family_name': 'Test'
        }
        
        # Register user
        register_response = requests.post(
            f"{api_base_url}/auth/register",
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert register_response.status_code == 201
        
        # Login to get tokens
        login_response = requests.post(
            f"{api_base_url}/auth/login",
            json={
                'email': user_data['email'],
                'password': user_data['password']
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        user_id = login_data['user_id']
        access_token = login_data['tokens']['access_token']
        
        # Delete profile
        delete_response = requests.delete(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data['message'] == 'User profile deleted successfully'
        
        # Verify profile is deleted by trying to access it
        get_response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        # Should return 401 (token invalid) or 404 (profile not found)
        assert get_response.status_code in [401, 404]
    
    def test_cors_headers(self, api_base_url, registered_user):
        """Test CORS headers are present in responses."""
        user_id = registered_user['user_id']
        access_token = registered_user['tokens']['access_token']
        
        response = requests.get(
            f"{api_base_url}/profile/{user_id}",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        # Check CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
    
    def test_api_error_handling(self, api_base_url):
        """Test API error handling and response format."""
        # Test with invalid JSON
        response = requests.post(
            f"{api_base_url}/auth/register",
            data="invalid-json",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        
        # Test with missing endpoint
        response = requests.get(f"{api_base_url}/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert 'error' in data


class TestUserProfileModelsIntegration:
    """Integration tests for user profile data models."""
    
    def test_user_profile_model_integration(self):
        """Test user profile model integration with real data."""
        from shared.models import UserProfile, StudyPreferences, CertificationType
        
        # Create a complete user profile
        study_prefs = StudyPreferences(
            daily_goal_minutes=45,
            preferred_difficulty=CertificationType.SAA,
            preferred_study_time='morning',
            quiz_length_preference=12
        )
        
        profile = UserProfile(
            user_id='integration-test-123',
            email='integration@example.com',
            name='Integration Test User',
            target_certifications=[CertificationType.SAA, CertificationType.DVA],
            study_preferences=study_prefs,
            timezone='America/New_York',
            subscription_tier='premium'
        )
        
        # Test validation
        assert profile.is_valid()
        
        # Test serialization/deserialization
        profile_dict = profile.to_dict()
        restored_profile = UserProfile.from_dict(profile_dict)
        
        assert restored_profile.user_id == profile.user_id
        assert restored_profile.email == profile.email
        assert restored_profile.target_certifications == profile.target_certifications
        assert restored_profile.study_preferences.daily_goal_minutes == study_prefs.daily_goal_minutes
        
        # Test profile methods
        profile.add_target_certification(CertificationType.SOA)
        assert CertificationType.SOA in profile.target_certifications
        
        profile.update_last_active()
        assert profile.last_active is not None
        
        profile.update_profile_completion()
        assert 0 <= profile.profile_completion <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
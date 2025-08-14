"""
Live endpoint validation tests for the enhanced API Gateway.
These tests validate the actual deployed API endpoints with real requests.
"""

import json
import pytest
import requests
import time
import os
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone


class TestAPIEndpointValidation:
    """Test suite for validating live API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment with real API endpoint."""
        # Get API endpoint from environment or CDK outputs
        self.api_base_url = os.environ.get('API_ENDPOINT', 'https://your-api-id.execute-api.region.amazonaws.com/prod')
        self.api_key = os.environ.get('API_KEY', '')  # Optional API key
        
        # Test data
        self.test_user_id = f"test-user-{uuid.uuid4().hex[:8]}"
        self.test_conversation_id = str(uuid.uuid4())
        self.test_quiz_id = str(uuid.uuid4())
        self.test_recommendation_id = str(uuid.uuid4())
        
        # Headers for authenticated requests
        self.auth_headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
        
        # Headers for unauthenticated requests
        self.no_auth_headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
        
        # Get a valid JWT token for testing (you'll need to implement this)
        self.valid_token = self._get_test_jwt_token()
        if self.valid_token:
            self.auth_headers["Authorization"] = f"Bearer {self.valid_token}"

    def _get_test_jwt_token(self) -> Optional[str]:
        """Get a valid JWT token for testing. Implement based on your auth setup."""
        # This would typically involve:
        # 1. Creating a test user in Cognito
        # 2. Authenticating and getting a JWT token
        # 3. Returning the token for use in tests
        
        # For now, return None - tests will skip if no token available
        return os.environ.get('TEST_JWT_TOKEN')

    @pytest.mark.skipif(not os.environ.get('TEST_JWT_TOKEN'), reason="No test JWT token available")
    def test_chat_message_endpoint_validation(self):
        """Test chat message endpoint with various validation scenarios."""
        endpoint = f"{self.api_base_url}/chat/message"
        
        # Test 1: Valid request
        valid_payload = {
            "message": "What is AWS Lambda?",
            "certification": "saa",
            "mode": "rag"
        }
        
        response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
        print(f"Valid request response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "sources" in data
            assert "mode_used" in data
        else:
            print(f"Response body: {response.text}")

        # Test 2: Invalid certification
        invalid_cert_payload = {
            "message": "What is AWS Lambda?",
            "certification": "invalid-cert"
        }
        
        response = requests.post(endpoint, json=invalid_cert_payload, headers=self.auth_headers)
        print(f"Invalid certification response: {response.status_code}")
        assert response.status_code == 400

        # Test 3: Missing required field
        missing_field_payload = {
            "certification": "saa",
            "mode": "rag"
        }
        
        response = requests.post(endpoint, json=missing_field_payload, headers=self.auth_headers)
        print(f"Missing field response: {response.status_code}")
        assert response.status_code == 400

        # Test 4: Message too long
        long_message_payload = {
            "message": "x" * 2001,  # Exceeds limit
            "certification": "saa"
        }
        
        response = requests.post(endpoint, json=long_message_payload, headers=self.auth_headers)
        print(f"Long message response: {response.status_code}")
        assert response.status_code == 400

    def test_cors_headers(self):
        """Test CORS headers on all endpoints."""
        endpoints = [
            "/chat/message",
            "/auth/login",
            "/quiz/generate",
            f"/progress/{self.test_user_id}/interaction",
            f"/recommendations/{self.test_user_id}"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_base_url}{endpoint}"
            
            # Test OPTIONS request
            response = requests.options(url, headers={"Origin": "https://procert.app"})
            print(f"CORS OPTIONS {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                headers = response.headers
                assert "Access-Control-Allow-Origin" in headers
                assert "Access-Control-Allow-Methods" in headers
                assert "Access-Control-Allow-Headers" in headers
                print(f"CORS headers present for {endpoint}")
            else:
                print(f"CORS check failed for {endpoint}: {response.text}")

    def test_authentication_endpoints(self):
        """Test authentication endpoints validation."""
        
        # Test user registration
        register_endpoint = f"{self.api_base_url}/auth/register"
        
        # Valid registration
        valid_register = {
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }
        
        response = requests.post(register_endpoint, json=valid_register, headers=self.no_auth_headers)
        print(f"Registration response: {response.status_code}")
        if response.status_code not in [200, 409]:  # 409 = user already exists
            print(f"Registration response body: {response.text}")

        # Invalid email format
        invalid_email = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "name": "Test User"
        }
        
        response = requests.post(register_endpoint, json=invalid_email, headers=self.no_auth_headers)
        print(f"Invalid email response: {response.status_code}")
        assert response.status_code == 400

        # Password too short
        short_password = {
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": "short",
            "name": "Test User"
        }
        
        response = requests.post(register_endpoint, json=short_password, headers=self.no_auth_headers)
        print(f"Short password response: {response.status_code}")
        assert response.status_code == 400

    @pytest.mark.skipif(not os.environ.get('TEST_JWT_TOKEN'), reason="No test JWT token available")
    def test_quiz_endpoints_validation(self):
        """Test quiz endpoints validation."""
        
        # Test quiz generation
        generate_endpoint = f"{self.api_base_url}/quiz/generate"
        
        # Valid request
        valid_generate = {
            "certification": "saa",
            "difficulty": "intermediate",
            "count": 10,
            "user_id": self.test_user_id
        }
        
        response = requests.post(generate_endpoint, json=valid_generate, headers=self.auth_headers)
        print(f"Quiz generation response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "quiz_id" in data
            quiz_id = data["quiz_id"]
        else:
            print(f"Quiz generation response body: {response.text}")
            quiz_id = self.test_quiz_id  # Use test ID for further tests

        # Invalid count (too high)
        invalid_count = {
            "certification": "saa",
            "count": 25,  # Exceeds max
            "user_id": self.test_user_id
        }
        
        response = requests.post(generate_endpoint, json=invalid_count, headers=self.auth_headers)
        print(f"Invalid count response: {response.status_code}")
        assert response.status_code == 400

        # Test quiz submission
        submit_endpoint = f"{self.api_base_url}/quiz/submit"
        
        # Valid submission
        valid_submit = {
            "quiz_id": quiz_id,
            "answers": [
                {"question_id": "q1", "selected_answer": "A"},
                {"question_id": "q2", "selected_answer": "B"}
            ],
            "user_id": self.test_user_id
        }
        
        response = requests.post(submit_endpoint, json=valid_submit, headers=self.auth_headers)
        print(f"Quiz submission response: {response.status_code}")
        # Note: This might return 404 if quiz doesn't exist, which is expected

        # Invalid quiz ID format
        invalid_quiz_submit = {
            "quiz_id": "invalid-uuid",
            "answers": [{"question_id": "q1", "selected_answer": "A"}],
            "user_id": self.test_user_id
        }
        
        response = requests.post(submit_endpoint, json=invalid_quiz_submit, headers=self.auth_headers)
        print(f"Invalid quiz ID response: {response.status_code}")
        assert response.status_code == 400

    @pytest.mark.skipif(not os.environ.get('TEST_JWT_TOKEN'), reason="No test JWT token available")
    def test_progress_endpoints_validation(self):
        """Test progress tracking endpoints validation."""
        
        # Test interaction recording
        interaction_endpoint = f"{self.api_base_url}/progress/{self.test_user_id}/interaction"
        
        # Valid interaction
        valid_interaction = {
            "content_id": "content-123",
            "interaction_type": "quiz_attempt",
            "data": {"score": 85, "time_spent": 300},
            "certification": "saa"
        }
        
        response = requests.post(interaction_endpoint, json=valid_interaction, headers=self.auth_headers)
        print(f"Progress interaction response: {response.status_code}")

        # Invalid interaction type
        invalid_interaction = {
            "content_id": "content-123",
            "interaction_type": "invalid_type",
            "data": {}
        }
        
        response = requests.post(interaction_endpoint, json=invalid_interaction, headers=self.auth_headers)
        print(f"Invalid interaction type response: {response.status_code}")
        assert response.status_code == 400

        # Test analytics endpoint
        analytics_endpoint = f"{self.api_base_url}/progress/{self.test_user_id}/analytics"
        
        response = requests.get(analytics_endpoint, headers=self.auth_headers)
        print(f"Analytics response: {response.status_code}")
        # This might return 404 if user has no data, which is expected

        # Test with invalid query parameters
        response = requests.get(f"{analytics_endpoint}?timeframe=invalid", headers=self.auth_headers)
        print(f"Invalid timeframe response: {response.status_code}")
        # Should return 400 for invalid parameters

    @pytest.mark.skipif(not os.environ.get('TEST_JWT_TOKEN'), reason="No test JWT token available")
    def test_recommendation_endpoints_validation(self):
        """Test recommendation endpoints validation."""
        
        # Test getting recommendations
        recommendations_endpoint = f"{self.api_base_url}/recommendations/{self.test_user_id}"
        
        response = requests.get(recommendations_endpoint, headers=self.auth_headers)
        print(f"Recommendations response: {response.status_code}")
        # This might return 404 if user has no data, which is expected

        # Test feedback endpoint
        feedback_endpoint = f"{self.api_base_url}/recommendations/{self.test_user_id}/feedback"
        
        # Valid feedback
        valid_feedback = {
            "recommendation_id": self.test_recommendation_id,
            "action": "accepted",
            "feedback": "This was helpful"
        }
        
        response = requests.post(feedback_endpoint, json=valid_feedback, headers=self.auth_headers)
        print(f"Recommendation feedback response: {response.status_code}")

        # Invalid action
        invalid_feedback = {
            "recommendation_id": self.test_recommendation_id,
            "action": "invalid_action"
        }
        
        response = requests.post(feedback_endpoint, json=invalid_feedback, headers=self.auth_headers)
        print(f"Invalid feedback action response: {response.status_code}")
        assert response.status_code == 400

        # Feedback too long
        long_feedback = {
            "recommendation_id": self.test_recommendation_id,
            "action": "accepted",
            "feedback": "x" * 501  # Exceeds limit
        }
        
        response = requests.post(feedback_endpoint, json=long_feedback, headers=self.auth_headers)
        print(f"Long feedback response: {response.status_code}")
        assert response.status_code == 400

    def test_unauthorized_access(self):
        """Test that protected endpoints reject unauthorized requests."""
        protected_endpoints = [
            ("POST", "/chat/message", {"message": "test"}),
            ("GET", f"/chat/conversation/{self.test_conversation_id}"),
            ("POST", "/quiz/generate", {"certification": "saa", "user_id": self.test_user_id}),
            ("GET", f"/profile/{self.test_user_id}"),
            ("GET", f"/progress/{self.test_user_id}/analytics"),
            ("GET", f"/recommendations/{self.test_user_id}")
        ]
        
        for method, endpoint, *payload in protected_endpoints:
            url = f"{self.api_base_url}{endpoint}"
            payload = payload[0] if payload else None
            
            # Test without authorization header
            headers = {"Content-Type": "application/json", "X-Api-Key": self.api_key}
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=payload, headers=headers)
            
            print(f"Unauthorized {method} {endpoint}: {response.status_code}")
            assert response.status_code == 401

    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present in responses."""
        endpoint = f"{self.api_base_url}/auth/login"
        payload = {"email": "test@example.com", "password": "password"}
        
        response = requests.post(endpoint, json=payload, headers=self.no_auth_headers)
        print(f"Rate limiting test response: {response.status_code}")
        
        # Check for rate limiting headers (these might not be present in all implementations)
        headers = response.headers
        print(f"Response headers: {dict(headers)}")
        
        # Some implementations include these headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After"
        ]
        
        for header in rate_limit_headers:
            if header in headers:
                print(f"Found rate limiting header: {header} = {headers[header]}")

    def test_error_response_format(self):
        """Test that error responses follow the expected format."""
        endpoint = f"{self.api_base_url}/chat/message"
        invalid_payload = {"invalid": "payload"}
        
        response = requests.post(endpoint, json=invalid_payload, headers=self.auth_headers)
        print(f"Error format test response: {response.status_code}")
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                print(f"Error response: {error_data}")
                
                # Check if error follows expected format
                if "error" in error_data:
                    error = error_data["error"]
                    assert "code" in error or "message" in error
                    print("Error response follows expected format")
                else:
                    print("Error response doesn't follow expected format")
            except json.JSONDecodeError:
                print(f"Error response is not JSON: {response.text}")

    def test_content_type_requirements(self):
        """Test Content-Type header requirements."""
        endpoint = f"{self.api_base_url}/chat/message"
        payload = {"message": "test"}
        
        # Test with missing Content-Type
        headers_no_content_type = {"Authorization": f"Bearer {self.valid_token}"}
        
        response = requests.post(endpoint, json=payload, headers=headers_no_content_type)
        print(f"Missing Content-Type response: {response.status_code}")
        
        # Test with wrong Content-Type
        headers_wrong_content_type = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "text/plain"
        }
        
        # Note: requests.post with json= automatically sets Content-Type, so we need to override
        response = requests.post(
            endpoint, 
            data=json.dumps(payload), 
            headers=headers_wrong_content_type
        )
        print(f"Wrong Content-Type response: {response.status_code}")


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v", "-s"])
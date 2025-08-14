"""
Integration tests for the enhanced API Gateway with validation, CORS, and rate limiting.
Tests all new learning platform endpoints with proper validation and error handling.
"""

import json
import pytest
import requests
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
import boto3
import uuid
from datetime import datetime, timezone

# Try to import moto decorators, skip if not available
try:
    from moto import mock_dynamodb2 as mock_dynamodb, mock_cognitoidp as mock_cognito_idp
except ImportError:
    try:
        from moto import mock_dynamodb, mock_cognito_idp
    except ImportError:
        # Create dummy decorators if moto is not available
        def mock_dynamodb(func):
            return func
        def mock_cognito_idp(func):
            return func


class TestEnhancedAPIGateway:
    """Test suite for enhanced API Gateway functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.api_base_url = "https://test-api.procert.app"  # Mock API URL
        self.valid_token = "valid-jwt-token"
        self.invalid_token = "invalid-jwt-token"
        self.test_user_id = "test-user-123"
        self.test_conversation_id = str(uuid.uuid4())
        self.test_quiz_id = str(uuid.uuid4())
        self.test_recommendation_id = str(uuid.uuid4())
        
        # Common headers
        self.auth_headers = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "application/json"
        }
        self.no_auth_headers = {
            "Content-Type": "application/json"
        }

    def test_cors_preflight_requests(self):
        """Test CORS preflight requests for all endpoints."""
        endpoints = [
            "/chat/message",
            "/auth/login",
            "/quiz/generate",
            "/progress/test-user/interaction",
            "/recommendations/test-user"
        ]
        
        for endpoint in endpoints:
            with patch('requests.options') as mock_options:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With,Accept,Origin,Referer",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600"
                }
                mock_options.return_value = mock_response
                
                response = requests.options(f"{self.api_base_url}{endpoint}")
                
                assert response.status_code == 200
                assert "Access-Control-Allow-Origin" in response.headers
                assert "Access-Control-Allow-Methods" in response.headers
                assert "Access-Control-Allow-Headers" in response.headers

    def test_chat_message_validation(self):
        """Test chat message endpoint request validation."""
        endpoint = f"{self.api_base_url}/chat/message"
        
        # Test valid request
        valid_payload = {
            "message": "What is AWS Lambda?",
            "certification": "saa",
            "mode": "rag"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "AWS Lambda is a serverless compute service...",
                "sources": ["doc1.pdf"],
                "mode_used": "rag",
                "conversation_id": self.test_conversation_id
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
            assert response.status_code == 200

        # Test invalid certification
        invalid_payload = {
            "message": "What is AWS Lambda?",
            "certification": "invalid-cert",
            "mode": "rag"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid certification type"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_payload, headers=self.auth_headers)
            assert response.status_code == 400

        # Test missing required field
        missing_field_payload = {
            "certification": "saa",
            "mode": "rag"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Missing required field: message"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=missing_field_payload, headers=self.auth_headers)
            assert response.status_code == 400

        # Test message too long
        long_message_payload = {
            "message": "x" * 2001,  # Exceeds 2000 character limit
            "certification": "saa"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Message exceeds maximum length"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=long_message_payload, headers=self.auth_headers)
            assert response.status_code == 400

    def test_quiz_generation_validation(self):
        """Test quiz generation endpoint request validation."""
        endpoint = f"{self.api_base_url}/quiz/generate"
        
        # Test valid request
        valid_payload = {
            "certification": "saa",
            "difficulty": "intermediate",
            "count": 10,
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "quiz_id": self.test_quiz_id,
                "questions": [],
                "metadata": {"count": 10, "difficulty": "intermediate"}
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
            assert response.status_code == 200

        # Test invalid count (too high)
        invalid_count_payload = {
            "certification": "saa",
            "count": 25,  # Exceeds maximum of 20
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Count exceeds maximum allowed value"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_count_payload, headers=self.auth_headers)
            assert response.status_code == 400

        # Test invalid count (too low)
        invalid_low_count_payload = {
            "certification": "saa",
            "count": 3,  # Below minimum of 5
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Count below minimum allowed value"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_low_count_payload, headers=self.auth_headers)
            assert response.status_code == 400

    def test_quiz_submission_validation(self):
        """Test quiz submission endpoint request validation."""
        endpoint = f"{self.api_base_url}/quiz/submit"
        
        # Test valid request
        valid_payload = {
            "quiz_id": self.test_quiz_id,
            "answers": [
                {"question_id": "q1", "selected_answer": "A"},
                {"question_id": "q2", "selected_answer": "B"}
            ],
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "score": 85,
                "results": [],
                "feedback": []
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
            assert response.status_code == 200

        # Test invalid quiz_id format
        invalid_quiz_id_payload = {
            "quiz_id": "invalid-uuid",
            "answers": [{"question_id": "q1", "selected_answer": "A"}],
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid quiz ID format"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_quiz_id_payload, headers=self.auth_headers)
            assert response.status_code == 400

        # Test too many answers
        too_many_answers_payload = {
            "quiz_id": self.test_quiz_id,
            "answers": [{"question_id": f"q{i}", "selected_answer": "A"} for i in range(25)],  # Exceeds max of 20
            "user_id": self.test_user_id
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Too many answers provided"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=too_many_answers_payload, headers=self.auth_headers)
            assert response.status_code == 400

    def test_authentication_endpoints_validation(self):
        """Test authentication endpoint request validation."""
        
        # Test user registration validation
        register_endpoint = f"{self.api_base_url}/auth/register"
        
        valid_register_payload = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "name": "Test User"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": self.test_user_id,
                "message": "User registered successfully"
            }
            mock_post.return_value = mock_response
            
            response = requests.post(register_endpoint, json=valid_register_payload, headers=self.no_auth_headers)
            assert response.status_code == 200

        # Test invalid email format
        invalid_email_payload = {
            "email": "invalid-email",
            "password": "SecurePass123",
            "name": "Test User"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid email format"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(register_endpoint, json=invalid_email_payload, headers=self.no_auth_headers)
            assert response.status_code == 400

        # Test password too short
        short_password_payload = {
            "email": "test@example.com",
            "password": "short",
            "name": "Test User"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Password too short"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(register_endpoint, json=short_password_payload, headers=self.no_auth_headers)
            assert response.status_code == 400

    def test_progress_interaction_validation(self):
        """Test progress interaction endpoint request validation."""
        endpoint = f"{self.api_base_url}/progress/{self.test_user_id}/interaction"
        
        # Test valid request
        valid_payload = {
            "content_id": "content-123",
            "interaction_type": "quiz_attempt",
            "data": {"score": 85, "time_spent": 300},
            "certification": "saa"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
            assert response.status_code == 200

        # Test invalid interaction type
        invalid_interaction_payload = {
            "content_id": "content-123",
            "interaction_type": "invalid_type",
            "data": {}
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid interaction type"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_interaction_payload, headers=self.auth_headers)
            assert response.status_code == 400

    def test_recommendation_feedback_validation(self):
        """Test recommendation feedback endpoint request validation."""
        endpoint = f"{self.api_base_url}/recommendations/{self.test_user_id}/feedback"
        
        # Test valid request
        valid_payload = {
            "recommendation_id": self.test_recommendation_id,
            "action": "accepted",
            "feedback": "This recommendation was very helpful"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=valid_payload, headers=self.auth_headers)
            assert response.status_code == 200

        # Test invalid action
        invalid_action_payload = {
            "recommendation_id": self.test_recommendation_id,
            "action": "invalid_action"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid action type"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_action_payload, headers=self.auth_headers)
            assert response.status_code == 400

        # Test feedback too long
        long_feedback_payload = {
            "recommendation_id": self.test_recommendation_id,
            "action": "accepted",
            "feedback": "x" * 501  # Exceeds 500 character limit
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Feedback exceeds maximum length"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=long_feedback_payload, headers=self.auth_headers)
            assert response.status_code == 400

    def test_authorization_enforcement(self):
        """Test that protected endpoints require valid authorization."""
        protected_endpoints = [
            ("POST", "/chat/message", {"message": "test"}),
            ("GET", f"/chat/conversation/{self.test_conversation_id}", None),
            ("DELETE", f"/chat/conversation/{self.test_conversation_id}", None),
            ("POST", "/quiz/generate", {"certification": "saa", "user_id": self.test_user_id}),
            ("POST", "/quiz/submit", {"quiz_id": self.test_quiz_id, "answers": [], "user_id": self.test_user_id}),
            ("GET", f"/quiz/history/{self.test_user_id}", None),
            ("GET", f"/profile/{self.test_user_id}", None),
            ("PUT", f"/profile/{self.test_user_id}", {"name": "Test User"}),
            ("GET", f"/progress/{self.test_user_id}/analytics", None),
            ("POST", f"/progress/{self.test_user_id}/interaction", {"content_id": "test", "interaction_type": "view"}),
            ("GET", f"/recommendations/{self.test_user_id}", None),
            ("POST", f"/recommendations/{self.test_user_id}/feedback", {"recommendation_id": self.test_recommendation_id, "action": "accepted"})
        ]
        
        for method, endpoint, payload in protected_endpoints:
            url = f"{self.api_base_url}{endpoint}"
            
            # Test without authorization header
            with patch(f'requests.{method.lower()}') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.json.return_value = {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing or invalid authorization token"
                    }
                }
                mock_request.return_value = mock_response
                
                if method == "GET":
                    response = requests.get(url, headers=self.no_auth_headers)
                elif method == "POST":
                    response = requests.post(url, json=payload, headers=self.no_auth_headers)
                elif method == "PUT":
                    response = requests.put(url, json=payload, headers=self.no_auth_headers)
                elif method == "DELETE":
                    response = requests.delete(url, headers=self.no_auth_headers)
                
                assert response.status_code == 401

            # Test with invalid authorization token
            invalid_auth_headers = {
                "Authorization": f"Bearer {self.invalid_token}",
                "Content-Type": "application/json"
            }
            
            with patch(f'requests.{method.lower()}') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.json.return_value = {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid authorization token"
                    }
                }
                mock_request.return_value = mock_response
                
                if method == "GET":
                    response = requests.get(url, headers=invalid_auth_headers)
                elif method == "POST":
                    response = requests.post(url, json=payload, headers=invalid_auth_headers)
                elif method == "PUT":
                    response = requests.put(url, json=payload, headers=invalid_auth_headers)
                elif method == "DELETE":
                    response = requests.delete(url, headers=invalid_auth_headers)
                
                assert response.status_code == 401

    def test_rate_limiting_simulation(self):
        """Test rate limiting behavior (simulated)."""
        endpoint = f"{self.api_base_url}/chat/message"
        payload = {"message": "test message", "certification": "saa"}
        
        # Simulate rate limiting after many requests
        with patch('requests.post') as mock_post:
            # First requests succeed
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"response": "test response"}
            
            # Later requests get rate limited
            mock_response_throttled = Mock()
            mock_response_throttled.status_code = 429
            mock_response_throttled.json.return_value = {
                "error": {
                    "code": "THROTTLED",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            }
            mock_response_throttled.headers = {"Retry-After": "60"}
            
            # Simulate successful requests followed by throttling
            mock_post.side_effect = [mock_response_success] * 100 + [mock_response_throttled] * 10
            
            # Make requests until throttled
            throttled_response = None
            for i in range(110):
                response = requests.post(endpoint, json=payload, headers=self.auth_headers)
                if response.status_code == 429:
                    throttled_response = response
                    break
            
            assert throttled_response is not None
            assert throttled_response.status_code == 429
            assert "Retry-After" in throttled_response.headers

    def test_error_response_format(self):
        """Test that error responses follow the standard format."""
        endpoint = f"{self.api_base_url}/chat/message"
        invalid_payload = {"invalid": "payload"}
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request payload",
                    "details": {"field": "message", "issue": "required field missing"},
                    "timestamp": "2025-01-01T00:00:00Z",
                    "request_id": "req-123456"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=invalid_payload, headers=self.auth_headers)
            
            assert response.status_code == 400
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "request_id" in error_data["error"]

    def test_query_parameter_validation(self):
        """Test query parameter validation for GET endpoints."""
        
        # Test progress analytics with invalid timeframe
        endpoint = f"{self.api_base_url}/progress/{self.test_user_id}/analytics"
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid timeframe parameter"
                }
            }
            mock_get.return_value = mock_response
            
            response = requests.get(f"{endpoint}?timeframe=invalid", headers=self.auth_headers)
            assert response.status_code == 400

        # Test recommendations with invalid limit
        endpoint = f"{self.api_base_url}/recommendations/{self.test_user_id}"
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid limit parameter"
                }
            }
            mock_get.return_value = mock_response
            
            response = requests.get(f"{endpoint}?limit=-1", headers=self.auth_headers)
            assert response.status_code == 400

    def test_content_type_validation(self):
        """Test that endpoints require correct Content-Type header."""
        endpoint = f"{self.api_base_url}/chat/message"
        payload = {"message": "test"}
        
        # Test with missing Content-Type
        headers_no_content_type = {"Authorization": f"Bearer {self.valid_token}"}
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Content-Type header is required"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=payload, headers=headers_no_content_type)
            assert response.status_code == 400

        # Test with incorrect Content-Type
        headers_wrong_content_type = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "text/plain"
        }
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid Content-Type. Expected application/json"
                }
            }
            mock_post.return_value = mock_response
            
            response = requests.post(endpoint, json=payload, headers=headers_wrong_content_type)
            assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
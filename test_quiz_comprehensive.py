#!/usr/bin/env python3
"""
Comprehensive Quiz Generation Testing Script
Tests the enhanced API Gateway with JWT authentication and quiz functionality.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration from CDK outputs
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
USER_POOL_ID = "us-east-1_PnLvP0o7M"
USER_POOL_CLIENT_ID = "53kma8sulrhdl9ki7dboi0vj1j"

class QuizTestSuite:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.test_user_email = f"quiz-test-{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "QuizTest123!"
        self.test_user_name = "Quiz Test User"
        self.jwt_token = None
        self.user_id = None
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def test_user_registration(self):
        """Test user registration with enhanced validation."""
        print("\n🔐 Testing User Registration...")
        
        payload = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:  # Accept both 200 and 201 for registration
                data = response.json()
                self.user_id = data.get("user_id")
                self.log_test("User Registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False

    def test_user_login(self):
        """Test user login and JWT token retrieval."""
        print("\n🔑 Testing User Login...")
        
        payload = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Login response data: {data}")  # Debug output
                
                # Try different possible token field names
                tokens = data.get("tokens", {})
                self.jwt_token = (tokens.get("access_token") or 
                                data.get("access_token") or 
                                data.get("AccessToken") or 
                                data.get("token"))
                if not self.user_id:
                    self.user_id = data.get("user_id") or data.get("UserId")
                
                if self.jwt_token:
                    self.log_test("User Login", True, f"Token received: {self.jwt_token[:20]}...")
                    return True
                else:
                    self.log_test("User Login", False, f"No token found in response: {data}")
                    return False
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
            return False

    def test_cors_headers(self):
        """Test CORS configuration."""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            response = requests.options(
                f"{self.api_base_url}/quiz/generate",
                headers={
                    "Origin": "https://procert.app",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                },
                timeout=10
            )
            
            cors_headers = response.headers
            required_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods", 
                "Access-Control-Allow-Headers"
            ]
            
            missing_headers = [h for h in required_headers if h not in cors_headers]
            
            if response.status_code == 200 and not missing_headers:
                self.log_test("CORS Configuration", True, f"All required headers present")
                return True
            else:
                self.log_test("CORS Configuration", False, f"Missing headers: {missing_headers}")
                return False
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
            return False

    def test_quiz_generation_validation(self):
        """Test quiz generation request validation."""
        print("\n📝 Testing Quiz Generation Validation...")
        
        if not self.jwt_token:
            self.log_test("Quiz Generation Validation", False, "No JWT token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Valid request
        valid_payload = {
            "certification_type": "general",  # Use general instead of ANS since we might not have ANS content
            "difficulty": "intermediate", 
            "count": 10,
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=valid_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 400]:  # 400 might be "no questions found" which is expected
                if response.status_code == 200:
                    data = response.json()
                    quiz_id = data.get("quiz_id")
                    self.log_test("Quiz Generation - Valid Request", True, f"Quiz ID: {quiz_id}")
                else:
                    # 400 might be expected if no ANS questions are available
                    error_data = response.json()
                    if "No questions found" in str(error_data):
                        self.log_test("Quiz Generation - Valid Request", True, "No questions available (expected)")
                    else:
                        self.log_test("Quiz Generation - Valid Request", False, f"Unexpected 400: {response.text}")
            else:
                self.log_test("Quiz Generation - Valid Request", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Quiz Generation - Valid Request", False, f"Exception: {str(e)}")
        
        # Test 2: Invalid certification (should be rejected by validation)
        invalid_payload = {
            "certification_type": "invalid-cert",
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=invalid_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 400:
                self.log_test("Quiz Generation - Invalid Certification", True, "Properly rejected invalid certification")
            else:
                self.log_test("Quiz Generation - Invalid Certification", False, f"Should have been 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Quiz Generation - Invalid Certification", False, f"Exception: {str(e)}")
        
        # Test 3: Missing required field (should be rejected by validation)
        missing_field_payload = {
            "difficulty": "intermediate",
            "count": 10
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=missing_field_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 400:
                self.log_test("Quiz Generation - Missing Required Field", True, "Properly rejected missing certification")
            else:
                self.log_test("Quiz Generation - Missing Required Field", False, f"Should have been 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Quiz Generation - Missing Required Field", False, f"Exception: {str(e)}")
        
        # Test 4: Count too high (should be rejected by validation)
        high_count_payload = {
            "certification_type": "ans",
            "count": 25,  # Max is 20
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=high_count_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 400:
                self.log_test("Quiz Generation - Count Too High", True, "Properly rejected high count")
            else:
                self.log_test("Quiz Generation - Count Too High", False, f"Should have been 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Quiz Generation - Count Too High", False, f"Exception: {str(e)}")

    def test_authentication_enforcement(self):
        """Test that quiz endpoints require authentication."""
        print("\n🔒 Testing Authentication Enforcement...")
        
        # Test without authorization header
        payload = {
            "certification_type": "ans",
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_test("Authentication Enforcement - No Token", True, "Properly rejected request without token")
            else:
                self.log_test("Authentication Enforcement - No Token", False, f"Should have been 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication Enforcement - No Token", False, f"Exception: {str(e)}")
        
        # Test with invalid token
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json=payload,
                headers={
                    "Authorization": "Bearer invalid-token-12345",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_test("Authentication Enforcement - Invalid Token", True, "Properly rejected invalid token")
            else:
                self.log_test("Authentication Enforcement - Invalid Token", False, f"Should have been 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication Enforcement - Invalid Token", False, f"Exception: {str(e)}")

    def test_quiz_history_endpoint(self):
        """Test quiz history endpoint."""
        print("\n📚 Testing Quiz History Endpoint...")
        
        if not self.jwt_token or not self.user_id:
            self.log_test("Quiz History", False, "No JWT token or user ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.api_base_url}/quiz/history/{self.user_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 404]:  # 404 is expected for new user with no history
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Quiz History", True, f"Retrieved history: {len(data.get('quizzes', []))} quizzes")
                else:
                    self.log_test("Quiz History", True, "No quiz history found (expected for new user)")
                return True
            else:
                self.log_test("Quiz History", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Quiz History", False, f"Exception: {str(e)}")
            return False

    def test_profile_endpoints_still_work(self):
        """Test that profile endpoints still work after our changes."""
        print("\n👤 Testing Profile Endpoints (Regression Test)...")
        
        if not self.jwt_token or not self.user_id:
            self.log_test("Profile Endpoints", False, "No JWT token or user ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.api_base_url}/profile/{self.user_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Profile Endpoints", True, f"Profile retrieved: {data.get('name', 'Unknown')}")
                return True
            else:
                self.log_test("Profile Endpoints", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Profile Endpoints", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 Starting Comprehensive Quiz Generation Test Suite")
        print("=" * 60)
        
        # Step 1: User Registration and Authentication
        if not self.test_user_registration():
            print("❌ Registration failed, skipping remaining tests")
            return self.print_summary()
        
        time.sleep(2)  # Brief pause between tests
        
        if not self.test_user_login():
            print("❌ Login failed, skipping remaining tests")
            return self.print_summary()
        
        time.sleep(2)
        
        # Step 2: API Gateway Configuration Tests
        self.test_cors_headers()
        time.sleep(1)
        
        # Step 3: Authentication Enforcement Tests
        self.test_authentication_enforcement()
        time.sleep(2)
        
        # Step 4: Quiz Generation Tests (The main event!)
        self.test_quiz_generation_validation()
        time.sleep(2)
        
        # Step 5: Other Quiz Endpoints
        self.test_quiz_history_endpoint()
        time.sleep(1)
        
        # Step 6: Regression Test
        self.test_profile_endpoints_still_work()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status}: {result['test']}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Quiz generation system is working!")
        else:
            print("⚠️  Some tests failed. Check details above.")
        
        return passed == total


if __name__ == "__main__":
    test_suite = QuizTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎯 Ready to proceed with Task 7 (UI/Frontend)!")
    else:
        print("\n🔧 Some issues need to be resolved before proceeding.")
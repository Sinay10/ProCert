#!/usr/bin/env python3
"""
Test script for ProCert User Authentication and Profile Management
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "https://6x0amugsec.execute-api.us-east-1.amazonaws.com/prod"

class ProCertAuthTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def test_user_registration(self, email, password, given_name, family_name):
        """Test user registration endpoint"""
        print(f"\n🔐 Testing User Registration for {email}")
        
        payload = {
            "email": email,
            "password": password,
            "given_name": given_name,
            "family_name": family_name,
            "target_certifications": ["SAA", "DVA"]
        }
        
        response = self.session.post(
            f"{self.api_base}/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful!")
            print(f"User Profile Created: {data['user_profile']['name']}")
            print(f"Profile Completion: {data['user_profile']['profile_completion']}%")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
    
    def test_user_login(self, email, password):
        """Test user login endpoint"""
        print(f"\n🔑 Testing User Login for {email}")
        
        payload = {
            "email": email,
            "password": password
        }
        
        response = self.session.post(
            f"{self.api_base}/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            self.access_token = data['tokens']['access_token']
            self.user_id = data['user_id']
            print(f"User ID: {self.user_id}")
            print(f"Access Token: {self.access_token[:50]}...")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def test_get_profile(self):
        """Test get user profile endpoint"""
        print(f"\n👤 Testing Get User Profile")
        
        if not self.access_token or not self.user_id:
            print("❌ No access token or user ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = self.session.get(
            f"{self.api_base}/profile/{self.user_id}",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            profile = data['user_profile']
            print("✅ Profile retrieval successful!")
            print(f"Name: {profile['name']}")
            print(f"Email: {profile['email']}")
            print(f"Target Certifications: {profile['target_certifications']}")
            print(f"Subscription Tier: {profile['subscription_tier']}")
            print(f"Profile Completion: {profile['profile_completion']}%")
            return True
        else:
            print(f"❌ Profile retrieval failed: {response.text}")
            return False
    
    def test_update_profile(self):
        """Test update user profile endpoint"""
        print(f"\n✏️ Testing Update User Profile")
        
        if not self.access_token or not self.user_id:
            print("❌ No access token or user ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": "Updated Test User",
            "target_certifications": ["SAA", "DVA", "SOA"],
            "study_preferences": {
                "daily_goal_minutes": 60,
                "preferred_difficulty": "advanced",
                "preferred_study_time": "morning",
                "quiz_length_preference": 15
            },
            "timezone": "America/New_York",
            "language": "en"
        }
        
        response = self.session.put(
            f"{self.api_base}/profile/{self.user_id}",
            json=payload,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            profile = data['user_profile']
            print("✅ Profile update successful!")
            print(f"Updated Name: {profile['name']}")
            print(f"Updated Certifications: {profile['target_certifications']}")
            print(f"Updated Timezone: {profile['timezone']}")
            print(f"New Profile Completion: {profile['profile_completion']}%")
            return True
        else:
            print(f"❌ Profile update failed: {response.text}")
            return False
    
    def test_chat_endpoint(self):
        """Test chat endpoint (should work without authentication)"""
        print(f"\n💬 Testing Chat Endpoint")
        
        payload = {
            "message": "What is Amazon EC2?",
            "certification": "SAA",
            "user_id": self.user_id or "test-user"
        }
        
        response = self.session.post(
            f"{self.api_base}/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working!")
            print(f"Response: {data.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Chat endpoint failed: {response.text}")
            return False
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoints without token"""
        print(f"\n🚫 Testing Unauthorized Access")
        
        # Try to access profile without token
        response = self.session.get(f"{self.api_base}/profile/test-user-123")
        print(f"Profile access without token - Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
            return True
        else:
            print("❌ Security issue: unauthorized access allowed")
            return False

def main():
    """Run all authentication tests"""
    print("🧪 ProCert Authentication Testing Suite")
    print("=" * 50)
    
    tester = ProCertAuthTester()
    
    # Generate unique test user
    timestamp = int(time.time())
    test_email = f"test.user.{timestamp}@example.com"
    test_password = "TestPassword123!"
    
    results = []
    
    # Test 1: User Registration
    results.append(tester.test_user_registration(
        email=test_email,
        password=test_password,
        given_name="Test",
        family_name="User"
    ))
    
    # Test 2: User Login
    results.append(tester.test_user_login(test_email, test_password))
    
    # Test 3: Get Profile
    results.append(tester.test_get_profile())
    
    # Test 4: Update Profile
    results.append(tester.test_update_profile())
    
    # Test 5: Chat Endpoint
    results.append(tester.test_chat_endpoint())
    
    # Test 6: Unauthorized Access
    results.append(tester.test_unauthorized_access())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "User Registration",
        "User Login", 
        "Get Profile",
        "Update Profile",
        "Chat Endpoint",
        "Unauthorized Access Protection"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
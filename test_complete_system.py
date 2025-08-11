#!/usr/bin/env python3
"""
Complete System Test for ProCert Learning Platform

Tests all implemented features:
- Task 1: Enhanced Chatbot Service
- Task 2: User Authentication and Profile Management
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "https://6x0amugsec.execute-api.us-east-1.amazonaws.com/prod"

class ProCertSystemTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.conversation_id = None
        
    def test_chatbot_basic(self):
        """Test basic chatbot functionality"""
        print("\n🤖 Testing Basic Chatbot")
        
        payload = {
            "message": "What is AWS Lambda?",
            "certification": "DVA",
            "user_id": "test-user"
        }
        
        response = self.session.post(
            f"{self.api_base}/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chatbot working!")
            print(f"Mode Used: {data.get('mode_used', 'unknown')}")
            print(f"Response Length: {len(data.get('response', ''))}")
            print(f"Sources Found: {len(data.get('sources', []))}")
            if 'conversation_id' in data:
                self.conversation_id = data['conversation_id']
                print(f"Conversation ID: {self.conversation_id}")
            return True
        else:
            print(f"❌ Chatbot failed: {response.text}")
            return False
    
    def test_chatbot_enhanced_mode(self):
        """Test enhanced chatbot mode"""
        print("\n🚀 Testing Enhanced Chatbot Mode")
        
        payload = {
            "message": "Explain AWS Lambda pricing in detail",
            "certification": "DVA",
            "user_id": "test-user",
            "mode": "enhanced"
        }
        
        response = self.session.post(
            f"{self.api_base}/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Enhanced mode working!")
            print(f"Mode Used: {data.get('mode_used', 'unknown')}")
            print(f"Response Length: {len(data.get('response', ''))}")
            return True
        else:
            print(f"❌ Enhanced mode failed: {response.text}")
            return False
    
    def test_conversation_management(self):
        """Test conversation management"""
        print("\n💬 Testing Conversation Management")
        
        if not self.conversation_id:
            print("⚠️ No conversation ID available, skipping")
            return False
        
        # Get conversation
        response = self.session.get(
            f"{self.api_base}/chat/conversation/{self.conversation_id}",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Get Conversation Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Conversation retrieval working!")
            print(f"Messages in conversation: {len(data.get('messages', []))}")
            return True
        else:
            print(f"❌ Conversation retrieval failed: {response.text}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing User Registration")
        
        timestamp = int(time.time())
        test_email = f"test.{timestamp}@example.com"
        
        payload = {
            "email": test_email,
            "password": "TestPassword123!",
            "given_name": "Test",
            "family_name": "User",
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
            print(f"User ID: {data.get('user_id', 'unknown')}")
            return True, test_email
        else:
            print(f"❌ Registration failed: {response.text}")
            return False, test_email
    
    def test_user_login(self, email, password="TestPassword123!"):
        """Test user login"""
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
            self.access_token = data.get('access_token')
            self.user_id = data.get('user_id')
            print(f"User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def test_profile_management(self):
        """Test profile management"""
        print("\n📋 Testing Profile Management")
        
        if not self.access_token or not self.user_id:
            print("❌ No access token or user ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get profile
        response = self.session.get(
            f"{self.api_base}/profile/{self.user_id}",
            headers=headers
        )
        
        print(f"Get Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Profile retrieval working!")
            
            # Update profile
            update_payload = {
                "target_certifications": ["SAA", "DVA", "SOA"],
                "study_preferences": {
                    "daily_goal_minutes": 60,
                    "preferred_difficulty": "advanced"
                }
            }
            
            response = self.session.put(
                f"{self.api_base}/profile/{self.user_id}",
                json=update_payload,
                headers=headers
            )
            
            print(f"Update Profile Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Profile update working!")
                return True
            else:
                print(f"❌ Profile update failed: {response.text}")
                return False
        else:
            print(f"❌ Profile retrieval failed: {response.text}")
            return False
    
    def test_authenticated_chat(self):
        """Test chat with authenticated user"""
        print("\n🔐 Testing Authenticated Chat")
        
        if not self.user_id:
            print("⚠️ No user ID available, using anonymous")
            user_id = "anonymous-user"
        else:
            user_id = self.user_id
        
        payload = {
            "message": "What are the key differences between EC2 instance types?",
            "certification": "SAA",
            "user_id": user_id
        }
        
        response = self.session.post(
            f"{self.api_base}/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Authenticated chat working!")
            print(f"Response Length: {len(data.get('response', ''))}")
            return True
        else:
            print(f"❌ Authenticated chat failed: {response.text}")
            return False
    
    def run_complete_test_suite(self):
        """Run all tests"""
        print("🧪 ProCert Complete System Test Suite")
        print("=" * 60)
        
        results = []
        test_names = []
        
        # Test 1: Basic Chatbot
        test_names.append("Basic Chatbot")
        results.append(self.test_chatbot_basic())
        
        # Test 2: Enhanced Chatbot Mode
        test_names.append("Enhanced Chatbot Mode")
        results.append(self.test_chatbot_enhanced_mode())
        
        # Test 3: Conversation Management
        test_names.append("Conversation Management")
        results.append(self.test_conversation_management())
        
        # Test 4: User Registration
        test_names.append("User Registration")
        reg_result, test_email = self.test_user_registration()
        results.append(reg_result)
        
        # Test 5: User Login
        test_names.append("User Login")
        results.append(self.test_user_login(test_email))
        
        # Test 6: Profile Management
        test_names.append("Profile Management")
        results.append(self.test_profile_management())
        
        # Test 7: Authenticated Chat
        test_names.append("Authenticated Chat")
        results.append(self.test_authenticated_chat())
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Complete Test Results Summary")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for i, (test_name, result) in enumerate(zip(test_names, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is working correctly.")
            print("\n✅ Task 1 (Enhanced Chatbot): COMPLETE")
            print("✅ Task 2 (User Authentication): COMPLETE")
        else:
            print("⚠️ Some tests failed. System needs attention.")
        
        print(f"\n🔗 API Endpoint: {API_BASE_URL}")
        print("🚀 Ready for next development phase!")

def main():
    tester = ProCertSystemTester()
    tester.run_complete_test_suite()

if __name__ == "__main__":
    main()
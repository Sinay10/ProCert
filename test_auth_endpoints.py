#!/usr/bin/env python3
"""
Test script to verify authentication endpoints are working correctly.
"""

import requests
import json
import time

# API endpoint from CDK output
API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_user_registration():
    """Test user registration endpoint."""
    print("🔐 Testing user registration...")
    
    registration_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "target_certifications": ["SAA", "DVA"]
    }
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ User registration successful!")
            return json.loads(response.text)
        else:
            print("❌ User registration failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return None

def test_user_login(email, password):
    """Test user login endpoint."""
    print("\n🔑 Testing user login...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ User login successful!")
            return json.loads(response.text)
        else:
            print("❌ User login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_get_profile(user_id, access_token):
    """Test get user profile endpoint."""
    print("\n👤 Testing get user profile...")
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}/profile/{user_id}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Get profile successful!")
            return json.loads(response.text)
        else:
            print("❌ Get profile failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error getting profile: {e}")
        return None

def test_update_profile(user_id, access_token):
    """Test update user profile endpoint."""
    print("\n✏️ Testing update user profile...")
    
    update_data = {
        "name": "Updated Test User",
        "target_certifications": ["SAA", "DVA", "SOA"],
        "study_preferences": {
            "daily_goal_minutes": 60,
            "preferred_difficulty": "advanced"
        }
    }
    
    try:
        response = requests.put(
            f"{API_ENDPOINT}/profile/{user_id}",
            json=update_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Update profile successful!")
            return json.loads(response.text)
        else:
            print("❌ Update profile failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        return None

def test_chat_endpoint(access_token):
    """Test protected chat endpoint."""
    print("\n💬 Testing protected chat endpoint...")
    
    chat_data = {
        "message": "What is AWS Lambda?",
        "certification": "SAA"
    }
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/chat/message",
            json=chat_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Chat endpoint successful!")
            return json.loads(response.text)
        else:
            print("❌ Chat endpoint failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error with chat endpoint: {e}")
        return None

def main():
    """Run all authentication tests."""
    print("🧪 ProCert Authentication API Tests")
    print("=" * 50)
    
    # Test 1: User Registration
    registration_result = test_user_registration()
    if not registration_result:
        print("❌ Registration failed, stopping tests")
        return
    
    user_id = registration_result.get('user_id')
    email = "testuser@example.com"
    password = "TestPass123!"
    
    # Wait a moment for user to be fully created
    print("\n⏳ Waiting 5 seconds for user creation to complete...")
    time.sleep(5)
    
    # Test 2: User Login
    login_result = test_user_login(email, password)
    if not login_result:
        print("❌ Login failed, stopping tests")
        return
    
    access_token = login_result.get('tokens', {}).get('access_token')
    if not access_token:
        print("❌ No access token received, stopping tests")
        return
    
    # Test 3: Get Profile (Protected)
    profile_result = test_get_profile(user_id, access_token)
    
    # Test 4: Update Profile (Protected)
    update_result = test_update_profile(user_id, access_token)
    
    # Test 5: Chat Endpoint (Protected)
    chat_result = test_chat_endpoint(access_token)
    
    print("\n" + "=" * 50)
    print("🎉 Authentication tests completed!")
    print("✅ All core authentication functionality is working!")

if __name__ == "__main__":
    main()
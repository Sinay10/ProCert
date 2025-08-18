#!/usr/bin/env python3
"""
Test Chat API with Authentication
"""

import json
import requests
import time

API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get JWT token."""
    print("👤 Creating test user and getting JWT token...")
    
    test_email = f"chattest-{int(time.time())}@example.com"
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Chat Test User",
            "given_name": "Chat",
            "family_name": "Test"
        }
        
        print(f"Registering user: {test_email}")
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data,
            timeout=30
        )
        
        print(f"Registration status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✅ User registered: {test_email}")
            
            # Login to get JWT token
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            print("Attempting login...")
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                timeout=30
            )
            
            print(f"Login status: {login_response.status_code}")
            if login_response.status_code == 200:
                login_result = login_response.json()
                tokens = login_result.get('tokens', {})
                jwt_token = tokens.get('access_token') or login_result.get('access_token')
                user_id = login_result.get('user_id', login_result.get('sub'))
                
                print(f"✅ JWT token obtained: {'Yes' if jwt_token else 'No'}")
                print(f"✅ User ID: {user_id}")
                
                if jwt_token:
                    return jwt_token, user_id, test_email
                else:
                    print(f"❌ No JWT token found in response")
                    print(f"Response: {json.dumps(login_result, indent=2)}")
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                print(f"Response: {login_response.text}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
    
    return None, None, None

def test_chat_with_token(jwt_token, user_id):
    """Test the chat API with authentication."""
    print(f"\n💬 Testing chat API with user: {user_id}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    # Test message
    payload = {
        "message": "What is AWS Lambda?",
        "mode": "rag",
        "certification": "aws-solutions-architect-associate"
    }
    
    print(f"Sending message: {payload['message']}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/message",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat response received!")
            print(f"Response: {result.get('response', '')[:200]}...")
            print(f"Mode used: {result.get('mode_used')}")
            print(f"Sources found: {len(result.get('sources', []))}")
            print(f"Conversation ID: {result.get('conversation_id')}")
            
            return result.get('conversation_id')
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Chat request failed: {str(e)}")
    
    return None

def test_follow_up_message(jwt_token, conversation_id):
    """Test a follow-up message in the same conversation."""
    print(f"\n🔄 Testing follow-up message in conversation: {conversation_id}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    payload = {
        "message": "Can you give me more details about Lambda pricing?",
        "mode": "enhanced",
        "conversation_id": conversation_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/message",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Follow-up response received!")
            print(f"Response: {result.get('response', '')[:200]}...")
            print(f"Mode used: {result.get('mode_used')}")
        else:
            print(f"❌ Follow-up failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Follow-up request failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Chat API with Authentication\n")
    
    # Step 1: Create user and get token
    jwt_token, user_id, email = create_test_user_and_get_token()
    
    if jwt_token and user_id:
        # Step 2: Test chat
        conversation_id = test_chat_with_token(jwt_token, user_id)
        
        if conversation_id:
            # Step 3: Test follow-up
            test_follow_up_message(jwt_token, conversation_id)
        
        print(f"\n✅ Test completed for user: {email}")
    else:
        print("\n❌ Could not authenticate user, skipping chat tests")
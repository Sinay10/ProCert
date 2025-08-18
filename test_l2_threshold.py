#!/usr/bin/env python3
"""
Test L2 Distance Threshold

Test the current L2 distance approach with proper thresholds.
"""

import json
import requests
import time

API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get JWT token."""
    test_email = f"l2test-{int(time.time())}@example.com"
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "L2 Test User",
            "given_name": "L2",
            "family_name": "Test"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            # Login to get JWT token
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                tokens = login_result.get('tokens', {})
                jwt_token = tokens.get('access_token') or login_result.get('access_token')
                user_id = login_result.get('user_id', login_result.get('sub'))
                
                if jwt_token:
                    return jwt_token, user_id, test_email
                    
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
    
    return None, None, None

def test_l2_threshold(jwt_token):
    """Test the L2 threshold approach."""
    print("🧪 Testing L2 threshold approach...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    # Test with Lambda-related questions that should have good matches
    test_cases = [
        "What is AWS Lambda?",
        "How does serverless computing work?",
        "Tell me about Lambda functions",
        "What are the benefits of serverless architecture?"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {question}")
        
        payload = {
            "message": question,
            "mode": "rag"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat/message",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                mode_used = result.get('mode_used')
                sources = result.get('sources', [])
                context_quality = result.get('context_quality', {})
                
                print(f"      Mode: {mode_used}")
                print(f"      Sources: {len(sources)}")
                print(f"      Context quality: {context_quality}")
                
                if "I don't have enough information" in response_text:
                    print(f"      ❌ Still getting fallback")
                else:
                    print(f"      ✅ RAG working!")
                
                print(f"      Response: {response_text[:150]}...")
                
            else:
                print(f"      ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing L2 Distance Threshold Approach")
    print("=" * 60)
    
    # Create user and get token
    jwt_token, user_id, email = create_test_user_and_get_token()
    
    if jwt_token:
        test_l2_threshold(jwt_token)
        print(f"\n✅ Test completed for user: {email}")
    else:
        print("\n❌ Could not authenticate user")
    
    print("\n" + "=" * 60)
#!/usr/bin/env python3
"""
Test Chat with Existing Certification

Test the chat API with a certification that actually exists in the index.
"""

import json
import requests
import time

API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get JWT token."""
    print("👤 Creating test user and getting JWT token...")
    
    test_email = f"certtest-{int(time.time())}@example.com"
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Cert Test User",
            "given_name": "Cert",
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

def test_chat_with_different_certs(jwt_token, user_id):
    """Test chat with different certifications that exist in the index."""
    print(f"\n💬 Testing chat with different certifications...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    # Test cases with certifications that exist in the index
    test_cases = [
        {
            "message": "What is AWS Lambda?",
            "certification": None,  # No specific certification
            "mode": "rag"
        },
        {
            "message": "Tell me about serverless computing",
            "certification": "aws-solutions-architect-professional",  # SAP exists
            "mode": "rag"
        },
        {
            "message": "What are AWS networking services?",
            "certification": "aws-advanced-networking-specialty",  # ANS exists
            "mode": "rag"
        },
        {
            "message": "How does data engineering work in AWS?",
            "certification": "aws-data-engineer-associate",  # DEA exists
            "mode": "rag"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   🧪 Test {i}: {test_case['message'][:50]}...")
        print(f"      Certification: {test_case['certification'] or 'None'}")
        
        payload = {
            "message": test_case["message"],
            "mode": test_case["mode"]
        }
        
        if test_case["certification"]:
            payload["certification"] = test_case["certification"]
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat/message",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                mode_used = result.get('mode_used')
                sources = result.get('sources', [])
                context_quality = result.get('context_quality', {})
                
                print(f"      Mode used: {mode_used}")
                print(f"      Sources found: {len(sources)}")
                print(f"      Context quality: {context_quality}")
                
                # Check if it's the fallback message
                if "I don't have enough information" in response_text:
                    print(f"      ❌ RAG fallback message")
                else:
                    print(f"      ✅ RAG found content")
                
                print(f"      Response preview: {response_text[:150]}...")
                
            else:
                print(f"      ❌ Request failed: {response.text}")
                
        except Exception as e:
            print(f"      ❌ Request error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Chat with Existing Certifications\n")
    
    # Step 1: Create user and get token
    jwt_token, user_id, email = create_test_user_and_get_token()
    
    if jwt_token and user_id:
        # Step 2: Test chat with different certifications
        test_chat_with_different_certs(jwt_token, user_id)
        
        print(f"\n✅ Test completed for user: {email}")
    else:
        print("\n❌ Could not authenticate user, skipping chat tests")
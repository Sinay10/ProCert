#!/usr/bin/env python3
"""
Test JWT authorizer directly to debug the issue.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_jwt_authorizer():
    """Test JWT authorizer with different endpoints."""
    print("🔍 Testing JWT Authorizer...")
    
    # Get a fresh token
    registration_data = {
        "email": f"jwttest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "JWT Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Getting fresh token...")
    reg_response = requests.post(
        f"{API_ENDPOINT}/auth/register",
        json=registration_data,
        headers={"Content-Type": "application/json"}
    )
    
    if reg_response.status_code != 201:
        print(f"❌ Registration failed: {reg_response.text}")
        return
    
    reg_data = json.loads(reg_response.text)
    user_id = reg_data['user_id']
    
    login_response = requests.post(
        f"{API_ENDPOINT}/auth/login",
        json={
            "email": registration_data['email'],
            "password": registration_data['password']
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = json.loads(login_response.text)
    access_token = login_data['tokens']['access_token']
    print(f"✅ Got token: {access_token[:30]}...")
    
    # Test different protected endpoints
    endpoints = [
        {
            "name": "Profile (working)",
            "method": "GET",
            "url": f"{API_ENDPOINT}/profile/{user_id}",
            "data": None
        },
        {
            "name": "Quiz Generate (problematic)",
            "method": "POST", 
            "url": f"{API_ENDPOINT}/quiz/generate",
            "data": {
                "user_id": user_id,
                "certification_type": "SAA",
                "question_count": 5
            }
        },
        {
            "name": "Chat Message (should work)",
            "method": "POST",
            "url": f"{API_ENDPOINT}/chat/message", 
            "data": {
                "message": "Test message",
                "certification": "SAA"
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"\n2. Testing protected endpoints...")
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint['name']}")
        
        if endpoint['method'] == 'GET':
            response = requests.get(endpoint['url'], headers=headers)
        else:
            response = requests.post(endpoint['url'], json=endpoint['data'], headers=headers)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Success")
        else:
            print(f"   ❌ Failed: {response.text[:200]}...")
            
            # Try to get more details from the error
            if "Invalid key=value pair" in response.text:
                print(f"   🔍 JWT Authorizer issue detected")
            elif "Missing Authentication Token" in response.text:
                print(f"   🔍 No authorizer configured")
            elif "Unauthorized" in response.text:
                print(f"   🔍 Token validation failed")

if __name__ == "__main__":
    test_jwt_authorizer()
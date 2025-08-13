#!/usr/bin/env python3
"""
Test different authorization header formats to understand what works.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_auth_formats():
    """Test different authorization header formats."""
    print("🔍 Testing Different Authorization Header Formats...")
    
    # Get a fresh token
    registration_data = {
        "email": f"formattest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Format Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Getting fresh authentication token...")
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
    print(f"✅ Got fresh token: {access_token[:50]}...")
    
    # Test different endpoints with different auth formats
    test_cases = [
        {
            "name": "Profile endpoint (known working)",
            "url": f"{API_ENDPOINT}/profile/{user_id}",
            "method": "GET",
            "data": None
        },
        {
            "name": "Quiz endpoint (problematic)",
            "url": f"{API_ENDPOINT}/quiz/generate",
            "method": "POST",
            "data": {
                "user_id": user_id,
                "certification_type": "SAA",
                "question_count": 5,
                "difficulty": "mixed"
            }
        }
    ]
    
    auth_formats = [
        {"name": "Bearer + token", "header": f"Bearer {access_token}"},
        {"name": "Just token", "header": access_token},
        {"name": "Token + space", "header": f"{access_token} "},
        {"name": "bearer + token (lowercase)", "header": f"bearer {access_token}"}
    ]
    
    for test_case in test_cases:
        print(f"\n2. Testing {test_case['name']}...")
        
        for auth_format in auth_formats:
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_format["header"]
            }
            
            try:
                if test_case["method"] == "GET":
                    response = requests.get(test_case["url"], headers=headers)
                else:
                    response = requests.post(test_case["url"], json=test_case["data"], headers=headers)
                
                print(f"   {auth_format['name']}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCESS!")
                elif response.status_code == 400 and "No questions found" in response.text:
                    print(f"      ✅ AUTH SUCCESS (no questions in DB)")
                elif response.status_code == 403:
                    print(f"      ❌ Authorization failed")
                elif response.status_code == 401:
                    print(f"      ❌ Unauthorized")
                else:
                    print(f"      ⚠️  Unexpected: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   {auth_format['name']}: ERROR - {e}")

if __name__ == "__main__":
    test_auth_formats()
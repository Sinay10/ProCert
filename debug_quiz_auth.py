#!/usr/bin/env python3
"""
Debug the quiz authentication issue by testing different approaches.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def debug_quiz_auth():
    """Debug the quiz authentication issue."""
    print("🔍 Debugging Quiz Authentication Issue...")
    
    # First, let's get a fresh token
    registration_data = {
        "email": f"debugtest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Debug Test User",
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
    
    # Test 1: Profile endpoint (known working)
    print("\n2. Testing profile endpoint (should work)...")
    profile_response = requests.get(
        f"{API_ENDPOINT}/profile/{user_id}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    print(f"Profile Status: {profile_response.status_code}")
    if profile_response.status_code != 200:
        print(f"Profile Response: {profile_response.text}")
    else:
        print("✅ Profile endpoint working")
    
    # Test 2: Quiz endpoint (problematic)
    print("\n3. Testing quiz endpoint (problematic)...")
    quiz_data = {
        "user_id": user_id,
        "certification_type": "SAA",  # Using SAA which should have content
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    quiz_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    print(f"Quiz Status: {quiz_response.status_code}")
    print(f"Quiz Response: {quiz_response.text}")
    
    # Test 3: Check if quiz endpoint exists at all
    print("\n4. Testing if quiz endpoint is accessible without auth...")
    test_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"No-auth Status: {test_response.status_code}")
    print(f"No-auth Response: {test_response.text}")
    
    # Test 4: Try different header formats
    print("\n5. Testing different authorization header formats...")
    
    # Format 1: Standard Bearer
    headers1 = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Format 2: Just the token
    headers2 = {
        "Content-Type": "application/json",
        "Authorization": access_token
    }
    
    # Format 3: Different case
    headers3 = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}"
    }
    
    for i, headers in enumerate([headers1, headers2, headers3], 1):
        print(f"\n   Format {i}: {list(headers.keys())}")
        test_resp = requests.post(f"{API_ENDPOINT}/quiz/generate", json=quiz_data, headers=headers)
        print(f"   Status: {test_resp.status_code}")
        if test_resp.status_code != 200:
            print(f"   Response: {test_resp.text[:200]}...")

if __name__ == "__main__":
    debug_quiz_auth()
#!/usr/bin/env python3
"""
Debug the event structure to understand what's being passed to the Lambda.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def debug_event_structure():
    """Debug by calling a working endpoint and seeing the response."""
    print("🔍 Debugging Event Structure...")
    
    # Get a fresh token
    registration_data = {
        "email": f"eventdebug{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Event Debug User",
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
    
    # Test the working profile endpoint to see what we get
    print("\n2. Testing profile endpoint (working)...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    profile_response = requests.get(
        f"{API_ENDPOINT}/profile/{user_id}",
        headers=headers
    )
    
    print(f"Profile Status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        print("✅ Profile endpoint working")
        profile_data = json.loads(profile_response.text)
        print(f"Profile response keys: {list(profile_data.keys())}")
    else:
        print(f"Profile Response: {profile_response.text}")
    
    # Now test quiz endpoint with detailed error analysis
    print("\n3. Testing quiz endpoint with detailed analysis...")
    quiz_data = {
        "user_id": user_id,
        "certification_type": "SAA",
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    quiz_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers=headers
    )
    
    print(f"Quiz Status: {quiz_response.status_code}")
    print(f"Quiz Response: {quiz_response.text}")
    
    # Check response headers for clues
    print(f"Quiz Response Headers: {dict(quiz_response.headers)}")
    
    # Try with different user_id to see if that's the issue
    print("\n4. Testing quiz endpoint with different user_id...")
    quiz_data_different = {
        "user_id": "different-user-id",
        "certification_type": "SAA",
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    quiz_response_different = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data_different,
        headers=headers
    )
    
    print(f"Different User Quiz Status: {quiz_response_different.status_code}")
    print(f"Different User Quiz Response: {quiz_response_different.text}")

if __name__ == "__main__":
    debug_event_structure()
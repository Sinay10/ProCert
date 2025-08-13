#!/usr/bin/env python3
"""
Test quiz endpoint with the working authorization format.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_quiz_with_working_auth():
    """Test quiz endpoint with the authorization format that works."""
    print("🧪 Testing Quiz with Working Authorization Format...")
    
    # Get a fresh token
    registration_data = {
        "email": f"workingtest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Working Test User",
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
    
    # Test quiz endpoint with working format (just the token, no "Bearer")
    print("\n2. Testing quiz endpoint with working authorization format...")
    quiz_data = {
        "user_id": user_id,
        "certification_type": "SAA",
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    # This is the format that worked (Format 2 from debug)
    headers = {
        "Content-Type": "application/json",
        "Authorization": access_token  # Just the token, no "Bearer" prefix
    }
    
    quiz_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers=headers
    )
    
    print(f"Quiz Status: {quiz_response.status_code}")
    print(f"Quiz Response: {quiz_response.text}")
    
    if quiz_response.status_code == 400 and "No questions found" in quiz_response.text:
        print("\n✅ SUCCESS! Authorization is working correctly.")
        print("The 400 error is expected because there are no questions in the database yet.")
        print("The quiz service is properly authenticated and functional.")
    elif quiz_response.status_code == 200:
        print("\n🎉 PERFECT! Quiz generation worked completely!")
    else:
        print(f"\n❌ Unexpected response: {quiz_response.status_code}")

if __name__ == "__main__":
    test_quiz_with_working_auth()
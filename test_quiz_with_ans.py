#!/usr/bin/env python3
"""
Test quiz endpoint with ANS certification type since that's what was uploaded.
"""

import requests
import json
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_quiz_with_ans():
    """Test quiz endpoint with ANS certification type."""
    print("🧪 Testing Quiz with ANS Certification Type...")
    
    # Get a fresh token
    registration_data = {
        "email": f"anstest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "ANS Test User",
        "target_certifications": ["ANS"]
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
    
    # Test quiz endpoint with ANS certification type
    print("\n2. Testing quiz endpoint with ANS certification type...")
    quiz_data = {
        "user_id": user_id,
        "certification_type": "ANS",  # Using ANS since that's what was uploaded
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    quiz_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers=headers
    )
    
    print(f"Quiz Status: {quiz_response.status_code}")
    print(f"Quiz Response: {quiz_response.text}")
    
    if quiz_response.status_code == 200:
        print("\n🎉 SUCCESS! Quiz generated with ANS questions!")
        quiz_data = json.loads(quiz_response.text)
        if 'quiz' in quiz_data and 'questions' in quiz_data['quiz']:
            print(f"Generated {len(quiz_data['quiz']['questions'])} questions")
    elif quiz_response.status_code == 400 and "No questions found" in quiz_response.text:
        print("\n❌ Still no questions found for ANS certification type")
        print("This suggests the content ingestion might not have processed the uploaded PDF yet")
    else:
        print(f"\n⚠️ Unexpected response: {quiz_response.status_code}")

if __name__ == "__main__":
    test_quiz_with_ans()
#!/usr/bin/env python3
"""
Test the quiz service with proper authentication.
"""

import requests
import json
import time

# API endpoint from CDK output
API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_quiz_service():
    """Test the quiz service with fresh authentication."""
    print("🎯 Testing Quiz Generation Service...")
    
    # Register a new user for testing
    registration_data = {
        "email": f"quiztest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Quiz Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Registering new user...")
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
    print(f"✅ User registered: {user_id}")
    
    # Login to get fresh token
    print("2. Logging in to get fresh token...")
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
    print("✅ Fresh token obtained")
    
    # Test quiz generation
    print("3. Testing quiz generation...")
    quiz_data = {
        "user_id": user_id,
        "certification_type": "SAA",
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
    
    print(f"Quiz Generation Status Code: {quiz_response.status_code}")
    print(f"Quiz Generation Response: {quiz_response.text}")
    
    if quiz_response.status_code == 200:
        print("✅ Quiz generation successful!")
        
        quiz_result = json.loads(quiz_response.text)
        quiz_id = quiz_result.get('quiz', {}).get('quiz_id')
        
        if quiz_id:
            print(f"   Quiz ID: {quiz_id}")
            
            # Test quiz history
            print("4. Testing quiz history...")
            history_response = requests.get(
                f"{API_ENDPOINT}/quiz/history/{user_id}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            print(f"Quiz History Status Code: {history_response.status_code}")
            print(f"Quiz History Response: {history_response.text}")
            
            if history_response.status_code == 200:
                print("✅ Quiz history retrieval successful!")
            else:
                print("❌ Quiz history retrieval failed!")
        
    else:
        print("❌ Quiz generation failed!")
        
        # Let's also test if the endpoint exists at all
        print("5. Testing if quiz endpoint is accessible...")
        test_response = requests.options(f"{API_ENDPOINT}/quiz/generate")
        print(f"OPTIONS request status: {test_response.status_code}")
        print(f"OPTIONS response headers: {dict(test_response.headers)}")

if __name__ == "__main__":
    test_quiz_service()
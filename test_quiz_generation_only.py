#!/usr/bin/env python3
"""
Test only the quiz generation endpoint to isolate the issue.
"""

import requests
import json
import uuid
import time

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_quiz_generation_only():
    """Test only quiz generation to isolate the issue."""
    
    # Step 1: Get a fresh user and token
    test_email = f"quiz-only-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "QuizOnly123!"
    
    print("🔐 Creating test user...")
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Quiz Only Test User"
        },
        headers={"Content-Type": "application/json"}
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        return
    
    user_data = register_response.json()
    user_id = user_data.get("user_id")
    print(f"✅ User created: {user_id}")
    
    # Step 2: Login
    print("🔑 Getting JWT token...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    login_data = login_response.json()
    jwt_token = login_data.get("tokens", {}).get("access_token")
    print(f"✅ JWT token obtained")
    
    # Step 3: Test quiz generation with different payloads
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    print("📝 Testing quiz generation...")
    
    # Test 1: Minimal payload
    minimal_payload = {
        "certification_type": "general"
    }
    
    print("Test 1: Minimal payload")
    response = requests.post(f"{API_BASE_URL}/quiz/generate", json=minimal_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test 2: Complete payload
    complete_payload = {
        "certification_type": "general",
        "count": 5,
        "difficulty": "intermediate"
    }
    
    print("Test 2: Complete payload")
    response = requests.post(f"{API_BASE_URL}/quiz/generate", json=complete_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test 3: Different certification
    saa_payload = {
        "certification_type": "saa",
        "count": 5
    }
    
    print("Test 3: SAA certification")
    response = requests.post(f"{API_BASE_URL}/quiz/generate", json=saa_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test 4: Check if it's a method issue - try with different HTTP method
    print("Test 4: Testing quiz history (should work)")
    response = requests.get(f"{API_BASE_URL}/quiz/history/{user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_quiz_generation_only()
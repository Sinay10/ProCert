#!/usr/bin/env python3
"""
Debug script to check JWT authorizer context passing.
"""

import requests
import json
import uuid

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_jwt_context():
    """Test JWT context passing by creating a user and checking profile access."""
    
    # Step 1: Register a test user
    test_email = f"debug-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "DebugTest123!"
    
    print("🔐 Registering test user...")
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Debug Test User"
        },
        headers={"Content-Type": "application/json"}
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
        return
    
    user_data = register_response.json()
    user_id = user_data.get("user_id")
    print(f"✅ User registered: {user_id}")
    
    # Step 2: Login to get JWT token
    print("🔑 Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    login_data = login_response.json()
    jwt_token = login_data.get("tokens", {}).get("access_token")
    print(f"✅ JWT token received: {jwt_token[:50]}...")
    
    # Step 3: Test profile access with detailed debugging
    print("👤 Testing profile access...")
    profile_response = requests.get(
        f"{API_BASE_URL}/profile/{user_id}",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    )
    
    print(f"Profile response status: {profile_response.status_code}")
    print(f"Profile response headers: {dict(profile_response.headers)}")
    print(f"Profile response body: {profile_response.text}")
    
    # Step 4: Test quiz generation
    print("📝 Testing quiz generation...")
    quiz_response = requests.post(
        f"{API_BASE_URL}/quiz/generate",
        json={
            "certification_type": "ans",
            "count": 5
        },
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    )
    
    print(f"Quiz response status: {quiz_response.status_code}")
    print(f"Quiz response body: {quiz_response.text}")

if __name__ == "__main__":
    test_jwt_context()
#!/usr/bin/env python3
"""
Simple test to isolate endpoint issues.
"""

import requests
import json
import uuid

API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_endpoints():
    """Test specific endpoints to isolate issues."""
    
    # Step 1: Register and login
    test_email = f"simple-test-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SimpleTest123!"
    
    print("🔐 Registering user...")
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": test_email, "password": test_password, "name": "Simple Test User"},
        headers={"Content-Type": "application/json"}
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        return
    
    user_id = register_response.json().get("user_id")
    print(f"✅ User registered: {user_id}")
    
    print("🔑 Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": test_email, "password": test_password},
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    jwt_token = login_response.json().get("tokens", {}).get("access_token")
    print(f"✅ JWT token received")
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints one by one
    endpoints_to_test = [
        ("GET", f"/profile/{user_id}", "Profile Access"),
        ("POST", "/quiz/generate", "Quiz Generation", {"certification_type": "ans", "count": 5}),
        ("GET", f"/quiz/history/{user_id}", "Quiz History"),
    ]
    
    for method, endpoint, name, *payload in endpoints_to_test:
        print(f"\n📋 Testing {name}: {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                data = payload[0] if payload else {}
                response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS")
            elif response.status_code == 400:
                print(f"   ⚠️  400 - Expected for some cases: {response.text[:100]}")
            elif response.status_code == 403:
                print(f"   ❌ 403 - Authorization issue: {response.text[:100]}")
            elif response.status_code == 404:
                print(f"   ⚠️  404 - Not found (expected for empty data): {response.text[:100]}")
            else:
                print(f"   ❓ {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_endpoints()
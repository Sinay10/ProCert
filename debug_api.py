#!/usr/bin/env python3
"""
Debug script for ProCert API endpoints
"""

import requests
import json

API_BASE_URL = "https://p7t7avgq97.execute-api.us-east-1.amazonaws.com/prod"

def test_endpoint(method, endpoint, payload=None):
    """Test a single endpoint and return detailed response"""
    url = f"{API_BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {url}")
    
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    print("🔧 ProCert API Debug Tool")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("GET", "/")
    
    # Test chat endpoint
    test_endpoint("POST", "/chat/message", {
        "message": "What is AWS?",
        "certification": "SAA",
        "user_id": "debug-user"
    })
    
    # Test registration
    test_endpoint("POST", "/auth/register", {
        "email": "debug@example.com",
        "password": "DebugPass123!",
        "given_name": "Debug",
        "family_name": "User",
        "target_certifications": ["SAA"]
    })

if __name__ == "__main__":
    main()
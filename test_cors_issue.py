#!/usr/bin/env python3

import requests
import json

def test_cors_issue():
    """Test CORS issue by making requests from different origins."""
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    print("🧪 Testing CORS Issue")
    print("=" * 50)
    
    # Test 1: No authentication (should get 401)
    print("\n📋 Test 1: No authentication")
    try:
        url = f"{base_url}/resources/general"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"✅ CORS header present: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ No CORS header in response")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: OPTIONS request (CORS preflight)
    print("\n📋 Test 2: OPTIONS request (CORS preflight)")
    try:
        url = f"{base_url}/resources/general"
        response = requests.options(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"✅ CORS header present: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ No CORS header in response")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: With Origin header (simulating browser request)
    print("\n📋 Test 3: With Origin header")
    try:
        url = f"{base_url}/resources/general"
        headers = {
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"✅ CORS header present: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ No CORS header in response")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cors_issue()
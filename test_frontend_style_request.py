#!/usr/bin/env python3

import requests
import json
import boto3
from botocore.exceptions import ClientError

def get_fresh_token():
    """Get a fresh JWT token from Cognito."""
    try:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        username = "demo.user@procert.test"
        password = "TestUser123!"
        client_id = "53kma8sulrhdl9ki7dboi0vj1j"
        
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        return response['AuthenticationResult']['AccessToken']
        
    except ClientError as e:
        print(f"❌ Failed to get token: {e}")
        return None

def test_frontend_style_requests():
    """Test requests exactly as a frontend application would make them."""
    
    token = get_fresh_token()
    if not token:
        return
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    print("🌐 Testing Frontend-Style Requests")
    print("=" * 60)
    
    # Test 1: Minimal request (like working tests)
    print("\n📋 Test 1: Minimal headers (working style)")
    headers_minimal = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers_minimal, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Browser-like headers
    print("\n📋 Test 2: Browser-like headers")
    headers_browser = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Origin': 'http://localhost:3000',
        'Referer': 'http://localhost:3000/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site'
    }
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers_browser, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Fetch API style (Next.js default)
    print("\n📋 Test 3: Fetch API style (Next.js)")
    headers_fetch = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'http://localhost:3000'
    }
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers_fetch, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Axios style (common React HTTP client)
    print("\n📋 Test 4: Axios style")
    headers_axios = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers_axios, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_cors_preflight():
    """Test CORS preflight request."""
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    print("\n🔄 Testing CORS Preflight")
    print("=" * 60)
    
    # OPTIONS request (preflight)
    headers_preflight = {
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization,content-type',
        'Origin': 'http://localhost:3000'
    }
    
    try:
        response = requests.options(f"{base_url}/resources/general", headers=headers_preflight, timeout=10)
        print(f"Preflight Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        
        if response.status_code == 200 or response.status_code == 204:
            print("✅ CORS preflight successful")
        else:
            print("❌ CORS preflight failed")
            
    except Exception as e:
        print(f"❌ Preflight Error: {e}")

if __name__ == "__main__":
    test_frontend_style_requests()
    test_cors_preflight()
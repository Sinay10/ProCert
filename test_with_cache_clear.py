#!/usr/bin/env python3

import requests
import json
import boto3
import time
from botocore.exceptions import ClientError

def get_test_token():
    """Get a test JWT token from Cognito."""
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

def test_with_cache_clear():
    """Test endpoints with cache clearing between requests."""
    
    print("🔐 Getting authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got authentication token")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🧪 Testing Endpoints with Cache Clear")
    print("=" * 60)
    
    # Test 1: Chat message
    print("\n📋 Testing POST /chat/message")
    try:
        response = requests.post(f"{base_url}/chat/message", 
                               headers=headers, 
                               json={"message": "test", "certification": "general"}, 
                               timeout=10)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Chat endpoint works!")
        else:
            print(f"❌ Chat failed: {response.text}")
    except Exception as e:
        print(f"❌ Chat Error: {e}")
    
    # Wait for cache to clear
    print("\n⏳ Waiting 35 seconds for authorizer cache to clear...")
    time.sleep(35)
    
    # Test 2: Resources after cache clear
    print("\n📋 Testing GET /resources/general (after cache clear)")
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Resources failed: {response.text}")
    except Exception as e:
        print(f"❌ Resources Error: {e}")
    
    # Test 3: Immediate second resources request (should work due to cache)
    print("\n📋 Testing GET /resources/ccp (immediate)")
    try:
        response = requests.get(f"{base_url}/resources/ccp", headers=headers, timeout=10)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Resources failed: {response.text}")
    except Exception as e:
        print(f"❌ Resources Error: {e}")

if __name__ == "__main__":
    test_with_cache_clear()
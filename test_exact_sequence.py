#!/usr/bin/env python3

import requests
import json
import boto3
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

def test_exact_sequence():
    """Test the exact sequence from debug_frontend_auth.py."""
    
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
    
    print("\n🧪 Testing Exact Sequence from debug_frontend_auth.py")
    print("=" * 60)
    
    # Step 1: POST /chat/message (this works in debug_frontend_auth.py)
    print("\n📋 Step 1: Testing POST /chat/message")
    try:
        response = requests.post(f"{base_url}/chat/message", 
                               headers=headers, 
                               json={"message": "test", "certification": "general"}, 
                               timeout=10)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success! Chat works")
        else:
            print(f"❌ Chat failed: {response.text}")
    except Exception as e:
        print(f"❌ Chat Error: {e}")
    
    # Step 2: GET /resources/general (this fails in debug_frontend_auth.py)
    print("\n📋 Step 2: Testing GET /resources/general (immediately after chat)")
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"❌ Resources failed: {response.text}")
            print(f"Response headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ Resources Error: {e}")

if __name__ == "__main__":
    test_exact_sequence()
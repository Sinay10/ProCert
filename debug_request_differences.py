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

def test_request_variations():
    """Test different request variations to identify what causes the 403."""
    
    token = get_fresh_token()
    if not token:
        return
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    endpoint = "/resources/general"
    
    print("🧪 Testing Different Request Variations")
    print("=" * 60)
    
    # Test 1: Minimal headers (like the working test)
    print("\n📋 Test 1: Minimal headers")
    headers1 = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers1, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With Content-Type (like the failing test)
    print("\n📋 Test 2: With Content-Type header")
    headers2 = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers2, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: With additional headers (like the failing test)
    print("\n📋 Test 3: With additional headers")
    headers3 = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers3, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Different timeout values
    print("\n📋 Test 4: Different timeout (15s)")
    headers4 = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers4, timeout=15)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Exact replication of working test
    print("\n📋 Test 5: Exact replication of working test")
    try:
        response = requests.get(f"{base_url}{endpoint}", headers={'Authorization': f'Bearer {token}'}, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_timing_issue():
    """Test if there's a timing issue between requests."""
    
    token = get_fresh_token()
    if not token:
        return
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    print("\n🕐 Testing Timing Issue")
    print("=" * 60)
    
    # First, make a successful chat request
    print("📋 Step 1: Making chat request first")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        chat_response = requests.post(f"{base_url}/chat/message", 
                                    headers=headers, 
                                    json={"message": "test", "certification": "general"}, 
                                    timeout=10)
        print(f"Chat Status: {chat_response.status_code}")
    except Exception as e:
        print(f"Chat Error: {e}")
    
    # Then immediately try resources
    print("📋 Step 2: Immediately trying resources")
    try:
        resources_response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"Resources Status: {resources_response.status_code}")
        if resources_response.status_code != 200:
            print(f"Resources Error: {resources_response.text}")
    except Exception as e:
        print(f"Resources Error: {e}")

if __name__ == "__main__":
    test_request_variations()
    test_timing_issue()
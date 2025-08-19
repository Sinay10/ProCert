#!/usr/bin/env python3

import requests
import json
import boto3
import time
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

def test_sequence_dependency():
    """Test if the issue is related to request sequence."""
    
    print("🔍 Testing Request Sequence Dependency")
    print("=" * 60)
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test 1: Resources first (should work)
    print("\n📋 Test 1: Resources endpoint first")
    token1 = get_fresh_token()
    headers = {'Authorization': f'Bearer {token1}'}
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"Resources Status: {response.status_code}")
    except Exception as e:
        print(f"Resources Error: {e}")
    
    # Test 2: Chat first, then resources (might fail)
    print("\n📋 Test 2: Chat first, then resources")
    token2 = get_fresh_token()
    headers = {
        'Authorization': f'Bearer {token2}',
        'Content-Type': 'application/json'
    }
    
    # First make chat request
    try:
        chat_response = requests.post(f"{base_url}/chat/message", 
                                    headers=headers, 
                                    json={"message": "test", "certification": "general"}, 
                                    timeout=5)  # Short timeout to potentially cause issues
        print(f"Chat Status: {chat_response.status_code}")
    except requests.exceptions.Timeout:
        print("Chat Timeout (expected)")
    except Exception as e:
        print(f"Chat Error: {e}")
    
    # Then try resources with same token
    try:
        resources_response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"Resources Status: {resources_response.status_code}")
        if resources_response.status_code != 200:
            print(f"Resources Error: {resources_response.text}")
    except Exception as e:
        print(f"Resources Error: {e}")
    
    # Test 3: Wait for cache to clear, then try again
    print("\n📋 Test 3: After cache clear (35 seconds)")
    print("Waiting for authorizer cache to clear...")
    time.sleep(35)
    
    try:
        resources_response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        print(f"Resources Status after cache clear: {resources_response.status_code}")
        if resources_response.status_code == 200:
            data = resources_response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
    except Exception as e:
        print(f"Resources Error: {e}")

if __name__ == "__main__":
    test_sequence_dependency()
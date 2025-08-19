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

def test_api_gateway_direct():
    """Test API Gateway directly to see detailed error responses."""
    
    print("🔐 Getting authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got authentication token")
    print(f"Token preview: {token[:50]}...")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test working endpoint first
    print("\n🧪 Testing WORKING endpoint: /chat/message")
    try:
        url = f"{base_url}/chat/message"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {"message": "test", "certification": "general"}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print("✅ Chat endpoint works!")
        else:
            print(f"❌ Chat endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test broken endpoint
    print("\n🧪 Testing BROKEN endpoint: /resources/general")
    try:
        url = f"{base_url}/resources/general"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        # Check if it's an API Gateway error vs Lambda error
        if 'x-amzn-RequestId' in response.headers:
            print("📍 This is an API Gateway response")
        if 'x-amzn-ErrorType' in response.headers:
            print(f"📍 Error Type: {response.headers['x-amzn-ErrorType']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test if the endpoint exists at all
    print("\n🧪 Testing OPTIONS request to /resources/general")
    try:
        url = f"{base_url}/resources/general"
        response = requests.options(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print("✅ Endpoint exists and CORS is configured")
        else:
            print("❌ Endpoint might not exist or CORS issue")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_gateway_direct()
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

def test_single_resource_request():
    """Make a single resource request to see what happens."""
    
    print("🔐 Getting fresh authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got fresh authentication token")
    print(f"Token preview: {token[:50]}...")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Make a single request with detailed headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n📋 Making GET request to /resources/general")
    print(f"🔗 URL: {base_url}/resources/general")
    print(f"📋 Headers: {headers}")
    
    try:
        response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
        
        print(f"\n📊 Response Details:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        # Check specific error indicators
        if 'x-amzn-ErrorType' in response.headers:
            print(f"🚨 Error Type: {response.headers['x-amzn-ErrorType']}")
        
        if 'x-amzn-RequestId' in response.headers:
            print(f"📋 Request ID: {response.headers['x-amzn-RequestId']}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_single_resource_request()
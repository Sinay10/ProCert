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

def test_with_fresh_token():
    """Test endpoints with a completely fresh token to bypass cache."""
    
    print("🔐 Getting fresh authentication token...")
    token = get_fresh_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got fresh authentication token")
    print(f"Token preview: {token[:50]}...")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test endpoints in sequence with the same fresh token
    endpoints = [
        ("/chat/message", "POST", {"message": "test", "certification": "general"}),
        ("/resources/general", "GET", None),
        ("/resources/ccp", "GET", None),
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',  # Try to bypass any caching
        'X-Requested-With': 'XMLHttpRequest'  # Add this header
    }
    
    print("\n🧪 Testing Endpoints with Fresh Token")
    print("=" * 60)
    
    for endpoint, method, data in endpoints:
        print(f"\n📋 Testing {method} {endpoint}")
        
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=15)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=15)
            
            print(f"📊 Status: {response.status_code}")
            print(f"🔗 URL: {url}")
            
            # Print relevant headers
            relevant_headers = ['x-amzn-RequestId', 'x-amzn-ErrorType', 'x-amz-apigw-id']
            for header in relevant_headers:
                if header in response.headers:
                    print(f"📋 {header}: {response.headers[header]}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if endpoint.startswith("/resources/"):
                        print(f"✅ Success! Found {result.get('total', 0)} resources")
                    else:
                        print(f"✅ Success! Response type: {type(result)}")
                except:
                    print(f"✅ Success! Response length: {len(response.text)}")
            elif response.status_code == 401:
                print("🔒 401 - Authentication failed")
                print(f"Response: {response.text}")
            elif response.status_code == 403:
                print("🚫 403 - Access forbidden")
                print(f"Response: {response.text}")
            else:
                print(f"❌ Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Small delay between requests
        time.sleep(1)

def test_authorizer_cache_behavior():
    """Test if the issue is related to authorizer caching."""
    
    print("\n🔄 Testing Authorizer Cache Behavior")
    print("=" * 60)
    
    # Get a fresh token
    token = get_fresh_token()
    if not token:
        return
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test the same endpoint multiple times to see if caching affects it
    for i in range(3):
        print(f"\n🔄 Attempt {i+1}/3 - Testing /resources/general")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f"{base_url}/resources/general", headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)  # Wait between attempts

if __name__ == "__main__":
    test_with_fresh_token()
    test_authorizer_cache_behavior()
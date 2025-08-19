#!/usr/bin/env python3

import requests
import json
import boto3
from botocore.exceptions import ClientError

def get_cognito_tokens():
    """Get both access and ID tokens from Cognito."""
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
        
        auth_result = response['AuthenticationResult']
        return {
            'access_token': auth_result['AccessToken'],
            'id_token': auth_result['IdToken']
        }
        
    except ClientError as e:
        print(f"❌ Failed to get tokens: {e}")
        return None

def test_token_types():
    """Test both access token and ID token to see which works with Cognito authorizer."""
    
    print("🔍 DEBUGGING: Frontend Token Issue")
    print("=" * 60)
    
    tokens = get_cognito_tokens()
    if not tokens:
        return
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    endpoint = "/chat/message"
    data = {"message": "test", "certification": "general"}
    
    # Test 1: Access Token (what frontend is using)
    print("\n📋 Test 1: Using ACCESS TOKEN (frontend current behavior)")
    headers_access = {
        'Authorization': f'Bearer {tokens["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(f"{base_url}{endpoint}", headers=headers_access, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("✅ Access token works!")
    except Exception as e:
        print(f"❌ Access token failed: {e}")
    
    # Test 2: ID Token (what should work)
    print("\n📋 Test 2: Using ID TOKEN (correct for Cognito User Pool)")
    headers_id = {
        'Authorization': f'Bearer {tokens["id_token"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(f"{base_url}{endpoint}", headers=headers_id, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("✅ ID token works!")
    except Exception as e:
        print(f"❌ ID token failed: {e}")
    
    # Test 3: OPTIONS request (CORS preflight)
    print("\n📋 Test 3: OPTIONS request (CORS preflight)")
    headers_options = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'authorization,content-type'
    }
    
    try:
        response = requests.options(f"{base_url}{endpoint}", headers=headers_options, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Check for required CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods', 
            'Access-Control-Allow-Headers'
        ]
        
        for header in cors_headers:
            if header in response.headers:
                print(f"✅ {header}: {response.headers[header]}")
            else:
                print(f"❌ Missing: {header}")
                
    except Exception as e:
        print(f"❌ OPTIONS failed: {e}")

if __name__ == "__main__":
    test_token_types()
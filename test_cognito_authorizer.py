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
            'id_token': auth_result['IdToken'],
            'refresh_token': auth_result.get('RefreshToken')
        }
        
    except ClientError as e:
        print(f"❌ Failed to get tokens: {e}")
        return None

def test_cognito_authorizer():
    """Test the new Cognito User Pool authorizer."""
    
    print("🚀 EMERGENCY TEST: Cognito User Pool Authorizer")
    print("=" * 60)
    
    tokens = get_cognito_tokens()
    if not tokens:
        print("❌ Could not get tokens")
        return
    
    print("✅ Got Cognito tokens")
    print(f"Access Token: {tokens['access_token'][:50]}...")
    print(f"ID Token: {tokens['id_token'][:50]}...")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test endpoints with ID token (required for Cognito User Pool authorizer)
    endpoints_to_test = [
        ("/resources/general", "GET", None),
        ("/resources/ccp", "GET", None),
        ("/quiz/generate", "POST", {"certification_type": "general", "count": 5, "user_id": "test-user"}),
        ("/chat/message", "POST", {"message": "test", "certification": "general"}),
    ]
    
    for endpoint, method, data in endpoints_to_test:
        print(f"\n📋 Testing {method} {endpoint}")
        
        # Use ID token for Cognito User Pool authorizer
        headers = {
            'Authorization': f'Bearer {tokens["id_token"]}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=15)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=15)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if endpoint.startswith("/resources/"):
                        print(f"✅ SUCCESS! Found {result.get('total', 0)} resources")
                    elif endpoint.startswith("/quiz/"):
                        print(f"✅ SUCCESS! Quiz response keys: {list(result.keys())}")
                    elif endpoint.startswith("/chat/"):
                        print(f"✅ SUCCESS! Chat response keys: {list(result.keys())}")
                    else:
                        print(f"✅ SUCCESS! Response: {type(result)}")
                except:
                    print(f"✅ SUCCESS! Response length: {len(response.text)}")
            elif response.status_code == 401:
                print("🔒 401 - Authentication failed")
                print(f"Response: {response.text}")
            elif response.status_code == 403:
                print("🚫 403 - Access forbidden")  
                print(f"Response: {response.text}")
            else:
                print(f"❌ Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("🎯 EMERGENCY TEST COMPLETE")

if __name__ == "__main__":
    test_cognito_authorizer()
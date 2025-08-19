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
        
        # EMERGENCY FIX: Return ID token for Cognito User Pool authorizer
        return response['AuthenticationResult']['IdToken']
        
    except ClientError as e:
        print(f"❌ Failed to get token: {e}")
        return None

def test_all_endpoints():
    """Test all endpoints to see which ones work with authentication."""
    
    print("🔐 Getting authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got authentication token")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    endpoints_to_test = [
        ("/chat/message", "POST", {"message": "test", "certification": "general"}),
        ("/resources/general", "GET", None),
        ("/resources/ccp", "GET", None),
        ("/quiz/generate", "POST", {"certification_type": "general", "count": 5, "user_id": "test-user"}),
        ("/progress/test-user", "GET", None),
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🧪 Testing All Endpoints")
    print("=" * 60)
    
    for endpoint, method, data in endpoints_to_test:
        print(f"\n📋 Testing {method} {endpoint}")
        
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if endpoint.startswith("/resources/"):
                        print(f"✅ Success! Found {result.get('total', 0)} resources")
                    else:
                        print(f"✅ Success! Response keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict response'}")
                except:
                    print(f"✅ Success! Response length: {len(response.text)}")
            elif response.status_code == 401:
                print("🔒 401 - Authentication failed")
            elif response.status_code == 403:
                print("🚫 403 - Access forbidden")
            elif response.status_code == 404:
                print("📭 404 - Not found")
            else:
                print(f"❌ Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_all_endpoints()
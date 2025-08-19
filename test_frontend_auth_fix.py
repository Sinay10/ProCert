#!/usr/bin/env python3

import boto3
import requests
import json
from botocore.exceptions import ClientError

def test_cognito_direct_auth():
    """Test the same authentication flow that the frontend will now use."""
    
    print("🔍 Testing Frontend Authentication Fix")
    print("=" * 60)
    
    try:
        # Same authentication flow as updated NextAuth
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        params = {
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'ClientId': '53kma8sulrhdl9ki7dboi0vj1j',
            'AuthParameters': {
                'USERNAME': 'demo.user@procert.test',
                'PASSWORD': 'TestUser123!'
            }
        }
        
        print("🔄 Authenticating with Cognito (same as frontend will do)...")
        result = client.initiate_auth(**params)
        
        if result['AuthenticationResult']:
            print("✅ Cognito authentication successful")
            
            # Test with ID token (what frontend will now send)
            id_token = result['AuthenticationResult']['IdToken']
            access_token = result['AuthenticationResult']['AccessToken']
            
            print(f"📋 ID Token: {id_token[:50]}...")
            print(f"📋 Access Token: {access_token[:50]}...")
            
            # Test API call with ID token
            base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
            headers = {
                'Authorization': f'Bearer {id_token}',
                'Content-Type': 'application/json'
            }
            
            print("\n🧪 Testing API call with ID token...")
            response = requests.post(f"{base_url}/chat/message", 
                                   headers=headers, 
                                   json={"message": "test", "certification": "general"}, 
                                   timeout=15)
            
            print(f"📊 Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ SUCCESS! Frontend authentication fix works!")
                result = response.json()
                print(f"Response keys: {list(result.keys())}")
            else:
                print(f"❌ Failed: {response.text}")
                
        else:
            print("❌ Cognito authentication failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cognito_direct_auth()
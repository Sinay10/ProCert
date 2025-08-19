#!/usr/bin/env python3

import requests
import json
import sys
import boto3
from botocore.exceptions import ClientError

def get_test_token():
    """Get a test JWT token from Cognito."""
    try:
        # Use the existing test user credentials
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        # These should match your test user credentials
        username = "demo.user@procert.test"
        password = "TestUser123!"
        client_id = "53kma8sulrhdl9ki7dboi0vj1j"  # From CDK output
        
        # Authenticate and get tokens
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
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_resources_with_auth():
    """Test the resources endpoint with proper authentication."""
    
    print("🔐 Getting authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token. Make sure test user exists.")
        return
    
    print("✅ Got authentication token")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test certifications
    certifications = ['general', 'ccp', 'saa']
    
    print("\n🧪 Testing Resources Endpoint with Authentication")
    print("=" * 60)
    
    for cert in certifications:
        print(f"\n📋 Testing certification: {cert.upper()}")
        
        try:
            url = f"{base_url}/resources/{cert}"
            print(f"🔗 URL: {url}")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Found {data.get('total', 0)} resources")
                print(f"📦 Bucket: {data.get('bucket', 'N/A')}")
                if data.get('resources'):
                    print("📁 Sample resources:")
                    for resource in data['resources'][:3]:  # Show first 3
                        size_mb = resource['size'] / (1024 * 1024)
                        print(f"  - {resource['name']} ({size_mb:.2f} MB)")
            elif response.status_code == 404:
                data = response.json()
                print(f"📭 404 - {data.get('error', 'No resources found')}")
            elif response.status_code == 401:
                print("🔒 401 - Authentication failed")
            elif response.status_code == 403:
                print("🚫 403 - Access forbidden")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✨ Test completed!")

if __name__ == "__main__":
    test_resources_with_auth()
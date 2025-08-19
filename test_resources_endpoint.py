#!/usr/bin/env python3

import requests
import json
import sys

def test_resources_endpoint():
    """Test the resources endpoint for different certifications."""
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test certifications
    certifications = ['general', 'ccp', 'saa', 'dva', 'ans']
    
    print("🧪 Testing Resources Endpoint")
    print("=" * 50)
    
    for cert in certifications:
        print(f"\n📋 Testing certification: {cert.upper()}")
        
        try:
            url = f"{base_url}/resources/{cert}"
            print(f"🔗 URL: {url}")
            
            # Test without authentication first (should fail with 403)
            response = requests.get(url, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Found {data.get('total', 0)} resources")
                if data.get('resources'):
                    print("📁 Sample resources:")
                    for resource in data['resources'][:3]:  # Show first 3
                        print(f"  - {resource['name']} ({resource['size']} bytes)")
            elif response.status_code == 403:
                print("🔒 Expected 403 - Authentication required")
            elif response.status_code == 404:
                print("📭 404 - No resources found for this certification")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Test completed!")

if __name__ == "__main__":
    test_resources_endpoint()
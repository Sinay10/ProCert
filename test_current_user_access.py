#!/usr/bin/env python3

import requests
import json

# The user ID from the frontend error
USER_ID = "54c86428-a031-70d7-9559-b8fffd09eb1d"
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_user_access():
    """Test if the current frontend user has access to the recommendation endpoints."""
    print(f"🔍 Testing access for user: {USER_ID}")
    print("=" * 60)
    
    # Test without authentication first
    test_endpoints = [
        {
            'name': 'Get Recommendations (No Auth)',
            'url': f"{API_BASE_URL}/recommendations/{USER_ID}",
            'params': {'certification_type': 'SAA', 'limit': '10'}
        },
        {
            'name': 'Get Study Path (No Auth)',
            'url': f"{API_BASE_URL}/recommendations/{USER_ID}/study-path",
            'params': {'certification_type': 'SAA'}
        }
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"\n🧪 Testing: {endpoint['name']}")
            response = requests.get(
                endpoint['url'],
                params=endpoint.get('params', {}),
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                if 'recommendations' in data:
                    print(f"   Recommendations: {len(data.get('recommendations', []))}")
                elif 'study_path' in data:
                    print(f"   Study phases: {len(data.get('study_path', {}).get('phases', []))}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_user_access()
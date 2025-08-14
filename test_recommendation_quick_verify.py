#!/usr/bin/env python3
"""
Quick verification test for the recommendation engine
Focuses on the newly implemented ML-based recommendation features
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://api.procert.ai"
TEST_USER_ID = "test-user-rec-verify"

def get_auth_token():
    """Get authentication token"""
    auth_url = f"{BASE_URL}/auth"
    auth_data = {"username": "testuser", "password": "testpass123"}
    
    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get('token')
        return None
    except:
        return None

def test_recommendation_endpoints():
    """Test all 5 recommendation endpoints"""
    print("🔍 Testing Recommendation Engine Endpoints")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test each endpoint
    endpoints = [
        {
            "name": "Personalized Recommendations",
            "method": "GET",
            "url": f"{BASE_URL}/recommendations/{TEST_USER_ID}",
            "expected_keys": ["recommendations", "user_id"]
        },
        {
            "name": "Weak Areas Identification",
            "method": "GET", 
            "url": f"{BASE_URL}/recommendations/{TEST_USER_ID}/weak-areas",
            "expected_keys": ["weak_areas", "analysis"]
        },
        {
            "name": "Content Progression",
            "method": "GET",
            "url": f"{BASE_URL}/recommendations/{TEST_USER_ID}/progression", 
            "expected_keys": ["progression", "readiness_scores"]
        },
        {
            "name": "Study Path Generation",
            "method": "POST",
            "url": f"{BASE_URL}/recommendations/{TEST_USER_ID}/study-path",
            "data": {"target_certification": "AWS Solutions Architect"},
            "expected_keys": ["study_path", "estimated_duration"]
        },
        {
            "name": "Feedback Recording",
            "method": "POST", 
            "url": f"{BASE_URL}/recommendations/{TEST_USER_ID}/feedback",
            "data": {
                "content_id": "test-content-feedback",
                "rating": 4,
                "feedback_type": "helpful"
            },
            "expected_keys": ["status", "message"]
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📡 Testing: {endpoint['name']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=headers)
            else:
                response = requests.post(
                    endpoint['url'], 
                    headers=headers, 
                    json=endpoint.get('data', {})
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success")
                
                # Check expected keys
                missing_keys = []
                for key in endpoint['expected_keys']:
                    if key not in data:
                        missing_keys.append(key)
                
                if missing_keys:
                    print(f"   ⚠️  Missing keys: {missing_keys}")
                else:
                    print(f"   ✅ All expected keys present")
                
                # Show some data details
                if 'recommendations' in data:
                    print(f"   📊 Recommendations count: {len(data['recommendations'])}")
                elif 'weak_areas' in data:
                    print(f"   📊 Weak areas count: {len(data['weak_areas'])}")
                elif 'progression' in data:
                    print(f"   📊 Progression items: {len(data['progression'])}")
                elif 'study_path' in data:
                    print(f"   📊 Study path steps: {len(data['study_path'])}")
                
                results.append({"endpoint": endpoint['name'], "status": "PASS"})
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                results.append({"endpoint": endpoint['name'], "status": "FAIL"})
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({"endpoint": endpoint['name'], "status": "ERROR"})
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        print(f"   {status_icon} {result['endpoint']}: {result['status']}")
    
    if passed == total:
        print("\n🎉 All recommendation engine tests passed!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the details above.")

if __name__ == "__main__":
    test_recommendation_endpoints()
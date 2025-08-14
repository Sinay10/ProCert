#!/usr/bin/env python3
"""
Recommendation Engine Test with Authentication

This script tests the recommendation engine through the API Gateway with proper authentication.
"""

import json
import boto3
import time
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get JWT token."""
    print("👤 Creating test user and getting JWT token...")
    
    test_email = f"test-{int(time.time())}@example.com"
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ User registered: {test_email}")
            
            # Login to get JWT token
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                tokens = login_result.get('tokens', {})
                jwt_token = tokens.get('access_token') or login_result.get('access_token')
                user_id = login_result.get('user_id', login_result.get('sub', f'user-{int(time.time())}'))
                
                print(f"   ✅ JWT token obtained: {'Yes' if jwt_token else 'No'}")
                print(f"   ✅ User ID: {user_id}")
                print(f"   📋 Login response: {json.dumps(login_result, indent=2)}")
                
                if jwt_token:
                    return jwt_token, user_id, test_email
                else:
                    print(f"   ❌ No JWT token found in response")
                    return None, None, None
            else:
                print(f"   ❌ Login failed: {login_response.status_code}")
                print(f"   Response: {login_response.text}")
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"   ❌ Authentication failed: {str(e)}")
    
    return None, None, None

def create_test_data_for_user(user_id):
    """Create test data for the authenticated user."""
    print(f"📝 Creating test data for user: {user_id}")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Content metadata
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_items = [
            {
                'content_id': f'auth-test-ec2-{user_id}',
                'certification_type': 'SAA',
                'title': 'EC2 Fundamentals for Auth Test',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': f'auth-test-s3-{user_id}',
                'certification_type': 'SAA',
                'title': 'S3 Advanced for Auth Test',
                'content_type': 'study_guide',
                'category': 'S3',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            }
        ]
        
        for content in content_items:
            content_table.put_item(Item=content)
        
        # User progress with poor EC2 performance and good S3 performance
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        progress_items = [
            # Poor EC2 performance
            {
                'user_id': user_id,
                'content_id_certification': f'auth-test-ec2-{user_id}#SAA',
                'content_id': f'auth-test-ec2-{user_id}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('40.0'),
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            {
                'user_id': user_id,
                'content_id_certification': f'auth-test-ec2-{user_id}#SAA',
                'content_id': f'auth-test-ec2-{user_id}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('50.0'),
                'time_spent': 500,
                'timestamp': datetime.utcnow().isoformat()
            },
            # Good S3 performance
            {
                'user_id': user_id,
                'content_id_certification': f'auth-test-s3-{user_id}#SAA',
                'content_id': f'auth-test-s3-{user_id}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('85.0'),
                'time_spent': 300,
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                'user_id': user_id,
                'content_id_certification': f'auth-test-s3-{user_id}#SAA',
                'content_id': f'auth-test-s3-{user_id}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('90.0'),
                'time_spent': 250,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print(f"   ✅ Created test data with clear performance patterns")
        print(f"      - EC2: 40%, 50% (should be weak area)")
        print(f"      - S3: 85%, 90% (should be strong area)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create test data: {str(e)}")
        return False

def test_authenticated_api_endpoints(jwt_token, user_id):
    """Test API endpoints with authentication."""
    print(f"\n🌐 Testing authenticated API endpoints for user: {user_id}")
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    test_endpoints = [
        {
            'name': 'Get Recommendations',
            'method': 'GET',
            'url': f"{API_BASE_URL}/recommendations/{user_id}",
            'params': {'certification_type': 'SAA', 'limit': '10'}
        },
        {
            'name': 'Get Weak Areas',
            'method': 'GET',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/weak-areas",
            'params': {'certification_type': 'SAA'}
        },
        {
            'name': 'Get Content Progression',
            'method': 'GET',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/content-progression",
            'params': {'certification_type': 'SAA'}
        },
        {
            'name': 'Get Study Path',
            'method': 'GET',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/study-path",
            'params': {'certification_type': 'SAA'}
        },
        {
            'name': 'Record Feedback',
            'method': 'POST',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/feedback",
            'data': {
                'recommendation_id': f'test-rec-{int(time.time())}',
                'action': 'accepted',
                'feedback_data': {'rating': 5, 'comment': 'Very helpful!'}
            }
        }
    ]
    
    results = {}
    
    for endpoint in test_endpoints:
        print(f"\n   🧪 Testing: {endpoint['name']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    params=endpoint.get('params', {}),
                    headers=headers,
                    timeout=30
                )
            else:  # POST
                response = requests.post(
                    endpoint['url'],
                    json=endpoint.get('data', {}),
                    headers=headers,
                    timeout=30
                )
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if endpoint['name'] == 'Get Recommendations':
                    recs = data.get('recommendations', [])
                    print(f"      Recommendations: {len(recs)}")
                    for i, rec in enumerate(recs[:3]):
                        print(f"        {i+1}. {rec.get('type', 'unknown')} - Priority: {rec.get('priority', 'unknown')}")
                        print(f"           Reasoning: {rec.get('reasoning', 'No reasoning')[:60]}...")
                
                elif endpoint['name'] == 'Get Weak Areas':
                    weak_areas = data.get('weak_areas', {})
                    weak_cats = weak_areas.get('weak_categories', [])
                    print(f"      Weak categories: {len(weak_cats)}")
                    for weak_cat in weak_cats:
                        print(f"        - {weak_cat.get('category', 'unknown')}: {weak_cat.get('avg_score', 0):.1f}%")
                    
                    recommendations = weak_areas.get('recommendations', [])
                    if recommendations:
                        print(f"      Recommendations: {len(recommendations)}")
                        for rec in recommendations[:3]:
                            print(f"        - {rec}")
                
                elif endpoint['name'] == 'Get Content Progression':
                    progression = data.get('progression', {})
                    print(f"      Current level: {progression.get('current_level', 'unknown')}")
                    print(f"      Recommended level: {progression.get('recommended_level', 'unknown')}")
                    print(f"      Overall readiness: {progression.get('overall_readiness', 0):.2f}")
                
                elif endpoint['name'] == 'Get Study Path':
                    study_path = data.get('study_path', {})
                    phases = study_path.get('study_phases', [])
                    print(f"      Study phases: {len(phases)}")
                    print(f"      Total hours: {study_path.get('total_estimated_hours', 0)}")
                    for phase in phases:
                        print(f"        Phase {phase.get('phase', '?')}: {phase.get('title', 'Unknown')}")
                
                elif endpoint['name'] == 'Record Feedback':
                    print(f"      Success: {data.get('success', False)}")
                    print(f"      Message: {data.get('message', 'No message')}")
                
                results[endpoint['name']] = True
            else:
                print(f"      Error: {response.text[:200]}...")
                results[endpoint['name']] = False
                
        except Exception as e:
            print(f"      ❌ Request failed: {str(e)}")
            results[endpoint['name']] = False
    
    return results

def cleanup_test_data(user_id):
    """Clean up test data for the user."""
    print(f"\n🧹 Cleaning up test data for user: {user_id}")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Clean up content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        content_ids = [f'auth-test-ec2-{user_id}', f'auth-test-s3-{user_id}']
        
        for content_id in content_ids:
            try:
                content_table.delete_item(Key={
                    'content_id': content_id,
                    'certification_type': 'SAA'
                })
            except Exception:
                pass
        
        # Clean up progress
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        try:
            response = progress_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            for item in response['Items']:
                if 'auth-test' in item.get('content_id', ''):
                    progress_table.delete_item(Key={
                        'user_id': item['user_id'],
                        'content_id_certification': item['content_id_certification']
                    })
        except Exception:
            pass
        
        print(f"   ✅ Cleaned up test data")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {str(e)}")

def main():
    """Run authenticated recommendation engine tests."""
    print("🚀 Authenticated Recommendation Engine Test")
    print("=" * 70)
    
    # Create test user and get JWT token
    jwt_token, user_id, test_email = create_test_user_and_get_token()
    
    if not jwt_token:
        print("❌ Failed to get authentication token, testing without auth...")
        return
    
    try:
        # Create test data
        if not create_test_data_for_user(user_id):
            print("❌ Failed to create test data")
            return
        
        # Wait for data consistency
        print("\n⏳ Waiting for data consistency...")
        time.sleep(5)
        
        # Test authenticated endpoints
        results = test_authenticated_api_endpoints(jwt_token, user_id)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 AUTHENTICATED TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"User: {test_email}")
        print(f"User ID: {user_id}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL AUTHENTICATED TESTS PASSED!")
            print("The Recommendation Engine is fully functional with authentication!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
        
    finally:
        # Cleanup
        if user_id:
            cleanup_test_data(user_id)
    
    print("=" * 70)

if __name__ == "__main__":
    main()
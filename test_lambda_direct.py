#!/usr/bin/env python3
"""
Direct Lambda Test

Test the recommendation Lambda function directly with proper error handling.
"""

import json
import boto3
from decimal import Decimal

def test_lambda_direct():
    """Test the Lambda function directly with detailed error reporting."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
    
    # Create test data first
    print("📝 Creating test data...")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create content metadata
    content_table = dynamodb.Table('procert-content-metadata-353207798766')
    content_table.put_item(Item={
        'content_id': 'test-content-direct',
        'certification_type': 'SAA',
        'title': 'Test Content for Direct Lambda',
        'content_type': 'study_guide',
        'category': 'EC2',
        'difficulty_level': 'beginner',
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-01-01T00:00:00Z',
        'version': '1.0',
        'chunk_count': 1
    })
    
    # Create user progress
    progress_table = dynamodb.Table('procert-user-progress-353207798766')
    test_user_id = 'test-user-direct'
    progress_table.put_item(Item={
        'user_id': test_user_id,
        'content_id_certification': 'test-content-direct#SAA',
        'content_id': 'test-content-direct',
        'certification_type': 'SAA',
        'progress_type': 'answered',
        'score': Decimal('65.0'),
        'time_spent': 300,
        'timestamp': '2025-01-01T00:00:00Z'
    })
    
    print("✅ Test data created")
    
    # Test different endpoints
    test_cases = [
        {
            'name': 'Get Recommendations',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}',
                'queryStringParameters': {
                    'certification_type': 'SAA',
                    'limit': '3'
                }
            }
        },
        {
            'name': 'Get Weak Areas',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}/weak-areas',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            }
        },
        {
            'name': 'Get Content Progression',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}/content-progression',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_case['event'])
            )
            
            # Read the response
            payload = response['Payload'].read()
            result = json.loads(payload)
            
            print(f"   Status Code: {result.get('statusCode', 'Unknown')}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                print(f"   ✅ Success: {test_case['name']}")
                print(f"   Response keys: {list(body.keys())}")
                results[test_case['name']] = True
            else:
                print(f"   ❌ Failed: {test_case['name']}")
                if 'body' in result:
                    error_body = json.loads(result['body'])
                    print(f"   Error: {error_body.get('error', {}).get('message', 'Unknown error')}")
                results[test_case['name']] = False
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results[test_case['name']] = False
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    try:
        content_table.delete_item(Key={
            'content_id': 'test-content-direct',
            'certification_type': 'SAA'
        })
        progress_table.delete_item(Key={
            'user_id': test_user_id,
            'content_id_certification': 'test-content-direct#SAA'
        })
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup failed: {str(e)}")
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    print(f"\nPassed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the Lambda logs for details.")
        return False

if __name__ == "__main__":
    success = test_lambda_direct()
    exit(0 if success else 1)
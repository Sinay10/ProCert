#!/usr/bin/env python3
"""
Detailed Recommendation Engine Test

This script tests the recommendation engine with more comprehensive data
to understand why recommendations aren't being generated.
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
TEST_USER_ID = f"test-user-{int(time.time())}"
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_comprehensive_test_data():
    """Create comprehensive test data with multiple performance scenarios."""
    print("📝 Creating comprehensive test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Content metadata - multiple pieces of content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_items = [
            {
                'content_id': 'test-ec2-1',
                'certification_type': 'SAA',
                'title': 'EC2 Fundamentals',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': 'test-s3-1',
                'certification_type': 'SAA',
                'title': 'S3 Storage Classes',
                'content_type': 'study_guide',
                'category': 'S3',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            },
            {
                'content_id': 'test-vpc-1',
                'certification_type': 'SAA',
                'title': 'VPC Networking',
                'content_type': 'study_guide',
                'category': 'VPC',
                'difficulty_level': 'advanced',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 12
            },
            {
                'content_id': 'test-iam-1',
                'certification_type': 'SAA',
                'title': 'IAM Policies',
                'content_type': 'question',
                'category': 'IAM',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 3
            }
        ]
        
        for content in content_items:
            content_table.put_item(Item=content)
        
        print(f"   ✅ Created {len(content_items)} content items")
        
        # User progress - varied performance to trigger different recommendation types
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        progress_items = [
            # Weak performance in EC2 (should trigger weak area recommendations)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'test-ec2-1#SAA',
                'content_id': 'test-ec2-1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('45.0'),  # Poor score
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'test-ec2-1#SAA',
                'content_id': 'test-ec2-1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('55.0'),  # Another poor score
                'time_spent': 450,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            # Strong performance in S3 (should trigger progression recommendations)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'test-s3-1#SAA',
                'content_id': 'test-s3-1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('85.0'),  # Good score
                'time_spent': 300,
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'test-s3-1#SAA',
                'content_id': 'test-s3-1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('90.0'),  # Excellent score
                'time_spent': 250,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            # Moderate performance in VPC (should trigger review recommendations)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'test-vpc-1#SAA',
                'content_id': 'test-vpc-1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('75.0'),  # Moderate score
                'time_spent': 800,
                'timestamp': (datetime.utcnow() - timedelta(days=4)).isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print(f"   ✅ Created {len(progress_items)} progress records")
        print("   📊 Performance summary:")
        print("      - EC2: 45%, 55% (weak area)")
        print("      - S3: 85%, 90% (strong area)")
        print("      - VPC: 75% (moderate area)")
        print("      - IAM: No attempts (untested area)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create test data: {str(e)}")
        return False

def test_lambda_with_detailed_logging():
    """Test the Lambda function with detailed logging."""
    print("\n🔧 Testing Lambda function with detailed logging...")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
    
    test_cases = [
        {
            'name': 'Get Recommendations',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}',
                'queryStringParameters': {
                    'certification_type': 'SAA',
                    'limit': '10'
                }
            }
        },
        {
            'name': 'Get Weak Areas',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}/weak-areas',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            }
        },
        {
            'name': 'Get Content Progression',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}/content-progression',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            }
        },
        {
            'name': 'Get Study Path',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}/study-path',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   🧪 Testing: {test_case['name']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_case['event'])
            )
            
            result = json.loads(response['Payload'].read())
            status_code = result.get('statusCode', 'unknown')
            
            print(f"      Status: {status_code}")
            
            if status_code == 200:
                body = json.loads(result['body'])
                
                if test_case['name'] == 'Get Recommendations':
                    recs = body.get('recommendations', [])
                    print(f"      Recommendations: {len(recs)}")
                    for i, rec in enumerate(recs[:3]):  # Show first 3
                        print(f"        {i+1}. {rec.get('type', 'unknown')} - Priority: {rec.get('priority', 'unknown')}")
                        print(f"           Reasoning: {rec.get('reasoning', 'No reasoning')}")
                
                elif test_case['name'] == 'Get Weak Areas':
                    weak_cats = body.get('weak_areas', {}).get('weak_categories', [])
                    print(f"      Weak categories: {len(weak_cats)}")
                    for weak_cat in weak_cats:
                        print(f"        - {weak_cat.get('category', 'unknown')}: {weak_cat.get('avg_score', 0):.1f}%")
                
                elif test_case['name'] == 'Get Content Progression':
                    progression = body.get('progression', {})
                    print(f"      Current level: {progression.get('current_level', 'unknown')}")
                    print(f"      Recommended level: {progression.get('recommended_level', 'unknown')}")
                
                elif test_case['name'] == 'Get Study Path':
                    study_path = body.get('study_path', {})
                    phases = study_path.get('study_phases', [])
                    print(f"      Study phases: {len(phases)}")
                    print(f"      Total hours: {study_path.get('total_estimated_hours', 0)}")
            
            else:
                print(f"      Error: {result.get('body', 'No error details')}")
                
        except Exception as e:
            print(f"      ❌ Test failed: {str(e)}")

def test_api_endpoints():
    """Test API endpoints directly."""
    print("\n🌐 Testing API endpoints...")
    
    # Note: These will likely fail due to authentication, but let's see the error responses
    test_endpoints = [
        f"/recommendations/{TEST_USER_ID}?certification_type=SAA&limit=5",
        f"/recommendations/{TEST_USER_ID}/weak-areas?certification_type=SAA",
        f"/recommendations/{TEST_USER_ID}/content-progression?certification_type=SAA"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code != 200:
                print(f"      Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   {endpoint}: Error - {str(e)}")

def cleanup_comprehensive_test_data():
    """Clean up comprehensive test data."""
    print("\n🧹 Cleaning up comprehensive test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Clean up content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        content_ids = ['test-ec2-1', 'test-s3-1', 'test-vpc-1', 'test-iam-1']
        
        for content_id in content_ids:
            try:
                content_table.delete_item(Key={
                    'content_id': content_id,
                    'certification_type': 'SAA'
                })
            except Exception as e:
                print(f"      ⚠️  Failed to delete {content_id}: {str(e)}")
        
        # Clean up progress
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        response = progress_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': TEST_USER_ID}
        )
        
        for item in response['Items']:
            progress_table.delete_item(Key={
                'user_id': item['user_id'],
                'content_id_certification': item['content_id_certification']
            })
        
        print(f"   ✅ Cleaned up test data for user {TEST_USER_ID}")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {str(e)}")
        return False

def main():
    """Run detailed tests."""
    print("🚀 Detailed Recommendation Engine Test")
    print("=" * 60)
    
    # Create comprehensive test data
    if not create_comprehensive_test_data():
        print("❌ Failed to create test data, aborting")
        return
    
    # Wait for data consistency
    print("\n⏳ Waiting for data consistency...")
    time.sleep(5)
    
    # Test Lambda function with detailed logging
    test_lambda_with_detailed_logging()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Cleanup
    cleanup_comprehensive_test_data()
    
    print("\n" + "=" * 60)
    print("📊 DETAILED TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
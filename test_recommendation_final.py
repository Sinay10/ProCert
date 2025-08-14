#!/usr/bin/env python3
"""
Final Comprehensive Recommendation Engine Test

This script creates a proper test with unique progress records and validates
the complete recommendation engine functionality.
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = f"final-test-{int(time.time())}"

def create_proper_test_data():
    """Create proper test data with unique progress records."""
    print("📝 Creating proper test data with unique progress records...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Content metadata - multiple pieces of content in same category
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_items = [
            {
                'content_id': f'final-ec2-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Basics',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': f'final-ec2-2-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Advanced',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            },
            {
                'content_id': f'final-ec2-3-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Expert',
                'content_type': 'question',
                'category': 'EC2',
                'difficulty_level': 'advanced',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 3
            },
            {
                'content_id': f'final-s3-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'S3 Storage',
                'content_type': 'study_guide',
                'category': 'S3',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 6
            },
            {
                'content_id': f'final-vpc-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'VPC Networking',
                'content_type': 'study_guide',
                'category': 'VPC',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 4
            }
        ]
        
        for content in content_items:
            content_table.put_item(Item=content)
        
        print(f"   ✅ Created {len(content_items)} content items")
        
        # User progress - UNIQUE records for each content item
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        progress_items = [
            # EC2 - Multiple content items with poor performance (weak area)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'final-ec2-1-{TEST_USER_ID}#SAA',
                'content_id': f'final-ec2-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('25.0'),
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=5)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'final-ec2-2-{TEST_USER_ID}#SAA',
                'content_id': f'final-ec2-2-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('35.0'),
                'time_spent': 700,
                'timestamp': (datetime.utcnow() - timedelta(days=4)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'final-ec2-3-{TEST_USER_ID}#SAA',
                'content_id': f'final-ec2-3-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('45.0'),
                'time_spent': 500,
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            # S3 - Excellent performance (strong area)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'final-s3-1-{TEST_USER_ID}#SAA',
                'content_id': f'final-s3-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('90.0'),
                'time_spent': 300,
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            # VPC - Moderate performance (review area)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'final-vpc-1-{TEST_USER_ID}#SAA',
                'content_id': f'final-vpc-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('75.0'),
                'time_spent': 400,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print(f"   ✅ Created {len(progress_items)} unique progress records")
        print("   📊 Performance summary:")
        print("      - EC2: 25%, 35%, 45% (3 attempts, avg 35% - WEAK)")
        print("      - S3: 90% (1 attempt - STRONG)")
        print("      - VPC: 75% (1 attempt - MODERATE)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create test data: {str(e)}")
        return False

def test_all_recommendation_endpoints():
    """Test all recommendation endpoints comprehensively."""
    print("\n🧪 Testing all recommendation endpoints...")
    
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
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n   🔧 Testing: {test_case['name']}")
        
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
                    print(f"      ✅ Recommendations: {len(recs)}")
                    
                    # Categorize recommendations
                    weak_recs = [r for r in recs if r.get('priority', 0) >= 7]
                    progression_recs = [r for r in recs if 5 <= r.get('priority', 0) < 7]
                    review_recs = [r for r in recs if r.get('priority', 0) < 5]
                    
                    print(f"         High priority (weak areas): {len(weak_recs)}")
                    print(f"         Medium priority (progression): {len(progression_recs)}")
                    print(f"         Low priority (review): {len(review_recs)}")
                    
                    for i, rec in enumerate(recs[:5]):  # Show first 5
                        print(f"         {i+1}. {rec.get('type', 'unknown')} - Priority: {rec.get('priority', 0)}")
                        print(f"            Reasoning: {rec.get('reasoning', 'No reasoning')[:60]}...")
                
                elif test_case['name'] == 'Get Weak Areas':
                    weak_areas = body.get('weak_areas', {})
                    weak_cats = weak_areas.get('weak_categories', [])
                    print(f"      ✅ Weak categories: {len(weak_cats)}")
                    
                    for weak_cat in weak_cats:
                        print(f"         - {weak_cat.get('category', 'unknown')}: {weak_cat.get('avg_score', 0):.1f}% (severity: {weak_cat.get('severity', 'unknown')})")
                    
                    category_performance = weak_areas.get('category_performance', {})
                    print(f"      📊 Category performance: {len(category_performance)} categories")
                    
                    for category, perf in category_performance.items():
                        if isinstance(perf, dict):
                            avg_score = perf.get('avg_score', 0)
                            attempts = perf.get('attempts', 0)
                            print(f"         - {category}: {avg_score:.1f}% ({attempts} attempts)")
                
                elif test_case['name'] == 'Get Content Progression':
                    progression = body.get('progression', {})
                    print(f"      ✅ Current level: {progression.get('current_level', 'unknown')}")
                    print(f"         Recommended level: {progression.get('recommended_level', 'unknown')}")
                    print(f"         Overall readiness: {progression.get('overall_readiness', 0):.2f}")
                
                elif test_case['name'] == 'Get Study Path':
                    study_path = body.get('study_path', {})
                    phases = study_path.get('study_phases', [])
                    print(f"      ✅ Study phases: {len(phases)}")
                    print(f"         Total hours: {study_path.get('total_estimated_hours', 0)}")
                    
                    for phase in phases[:3]:  # Show first 3 phases
                        print(f"         Phase {phase.get('phase', '?')}: {phase.get('title', 'Unknown')}")
                        print(f"           Estimated time: {phase.get('estimated_time_hours', 0)} hours")
                
                results[test_case['name']] = True
            else:
                print(f"      ❌ Error: {result.get('body', 'No error details')}")
                results[test_case['name']] = False
                
        except Exception as e:
            print(f"      ❌ Test failed: {str(e)}")
            results[test_case['name']] = False
    
    return results

def cleanup_test_data():
    """Clean up all test data."""
    print("\n🧹 Cleaning up test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Clean up content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_ids = [
            f'final-ec2-1-{TEST_USER_ID}',
            f'final-ec2-2-{TEST_USER_ID}',
            f'final-ec2-3-{TEST_USER_ID}',
            f'final-s3-1-{TEST_USER_ID}',
            f'final-vpc-1-{TEST_USER_ID}'
        ]
        
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
                ExpressionAttributeValues={':user_id': TEST_USER_ID}
            )
            
            for item in response['Items']:
                progress_table.delete_item(Key={
                    'user_id': item['user_id'],
                    'content_id_certification': item['content_id_certification']
                })
        except Exception:
            pass
        
        # Clean up recommendations
        recommendations_table = dynamodb.Table(f'procert-recommendations-{ACCOUNT_ID}')
        
        try:
            response = recommendations_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': TEST_USER_ID}
            )
            
            for item in response['Items']:
                recommendations_table.delete_item(Key={
                    'user_id': item['user_id'],
                    'recommendation_id': item['recommendation_id']
                })
        except Exception:
            pass
        
        print(f"   ✅ Cleaned up test data for user {TEST_USER_ID}")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {str(e)}")

def main():
    """Run final comprehensive test."""
    print("🚀 Final Comprehensive Recommendation Engine Test")
    print("=" * 70)
    
    # Create proper test data
    if not create_proper_test_data():
        print("❌ Failed to create test data, aborting")
        return
    
    # Wait for data consistency
    print("\n⏳ Waiting for data consistency...")
    time.sleep(5)
    
    # Test all endpoints
    results = test_all_recommendation_endpoints()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📊 FINAL COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Recommendation Engine is fully functional and ready for production!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
        print("Review the issues above for debugging.")
    
    # Cleanup
    cleanup_test_data()
    
    print("=" * 70)

if __name__ == "__main__":
    main()
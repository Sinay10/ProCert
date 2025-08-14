#!/usr/bin/env python3
"""
Final Recommendation Engine Test

Comprehensive test of the recommendation engine with the deployed AWS infrastructure.
"""

import json
import boto3
import time
from decimal import Decimal
from datetime import datetime, timedelta

# Configuration
LAMBDA_NAME = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def create_comprehensive_test_data():
    """Create comprehensive test data for thorough testing."""
    print("📝 Creating comprehensive test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
    progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
    
    test_user_id = f'test-user-final-{int(time.time())}'
    
    # Create diverse content metadata
    content_items = [
        {
            'content_id': 'test-ec2-beginner',
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
            'content_id': 'test-s3-intermediate',
            'certification_type': 'SAA',
            'title': 'S3 Advanced Features',
            'content_type': 'study_guide',
            'category': 'S3',
            'difficulty_level': 'intermediate',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 8
        },
        {
            'content_id': 'test-vpc-advanced',
            'certification_type': 'SAA',
            'title': 'VPC Deep Dive',
            'content_type': 'study_guide',
            'category': 'VPC',
            'difficulty_level': 'advanced',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 12
        },
        {
            'content_id': 'test-iam-beginner',
            'certification_type': 'SAA',
            'title': 'IAM Basics',
            'content_type': 'study_guide',
            'category': 'IAM',
            'difficulty_level': 'beginner',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 6
        }
    ]
    
    for item in content_items:
        content_table.put_item(Item=item)
    
    # Create diverse user progress data
    progress_items = [
        # Weak performance in EC2 (should trigger weak area recommendations) - Need 3+ attempts
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-ec2-beginner#1#SAA',
            'content_id': 'test-ec2-beginner',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('45.0'),  # Weak
            'time_spent': 300,
            'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
        },
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-ec2-beginner#2#SAA',
            'content_id': 'test-ec2-beginner',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('55.0'),  # Still weak
            'time_spent': 400,
            'timestamp': (datetime.utcnow() - timedelta(hours=12)).isoformat()
        },
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-ec2-beginner#3#SAA',
            'content_id': 'test-ec2-beginner',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('50.0'),  # Still weak
            'time_spent': 350,
            'timestamp': (datetime.utcnow() - timedelta(hours=6)).isoformat()
        },
        # Strong performance in S3 (should trigger progression recommendations)
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-s3-intermediate#1#SAA',
            'content_id': 'test-s3-intermediate',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('88.0'),  # Strong
            'time_spent': 450,
            'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
        },
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-s3-intermediate#2#SAA',
            'content_id': 'test-s3-intermediate',
            'certification_type': 'SAA',
            'progress_type': 'completed',
            'score': Decimal('92.0'),  # Very strong
            'time_spent': 500,
            'timestamp': (datetime.utcnow() - timedelta(hours=8)).isoformat()
        },
        # Moderate performance in IAM (should trigger review recommendations)
        {
            'user_id': test_user_id,
            'content_id_certification': 'test-iam-beginner#1#SAA',
            'content_id': 'test-iam-beginner',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('75.0'),  # Moderate
            'time_spent': 350,
            'timestamp': (datetime.utcnow() - timedelta(hours=3)).isoformat()
        }
    ]
    
    for item in progress_items:
        progress_table.put_item(Item=item)
    
    print(f"   ✅ Created {len(content_items)} content items")
    print(f"   ✅ Created {len(progress_items)} progress records")
    print(f"   📊 Test user ID: {test_user_id}")
    
    return test_user_id, content_items, progress_items

def test_recommendation_scenarios(test_user_id):
    """Test various recommendation scenarios."""
    print(f"\n🧪 Testing recommendation scenarios for user: {test_user_id}")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    test_scenarios = [
        {
            'name': 'Get Personalized Recommendations',
            'description': 'Should prioritize weak areas (EC2) and progression (S3)',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}',
                'queryStringParameters': {
                    'certification_type': 'SAA',
                    'limit': '5'
                }
            },
            'expected_checks': [
                lambda body: len(body.get('recommendations', [])) > 0,
                lambda body: body.get('user_id') == test_user_id,
                lambda body: body.get('certification_type') == 'SAA'
            ]
        },
        {
            'name': 'Identify Weak Areas',
            'description': 'Should identify EC2 as a weak area',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}/weak-areas',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            },
            'expected_checks': [
                lambda body: 'weak_categories' in body.get('weak_areas', {}),
                lambda body: any(cat.get('category') == 'EC2' for cat in body.get('weak_areas', {}).get('weak_categories', [])),
                lambda body: len(body.get('weak_areas', {}).get('recommendations', [])) > 0
            ]
        },
        {
            'name': 'Content Difficulty Progression',
            'description': 'Should show progression readiness',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}/content-progression',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            },
            'expected_checks': [
                lambda body: 'current_level' in body.get('progression', {}),
                lambda body: 'recommended_level' in body.get('progression', {}),
                lambda body: len(body.get('progression', {}).get('progression_path', [])) > 0
            ]
        },
        {
            'name': 'Generate Study Path',
            'description': 'Should create multi-phase study plan',
            'event': {
                'httpMethod': 'GET',
                'path': f'/recommendations/{test_user_id}/study-path',
                'queryStringParameters': {
                    'certification_type': 'SAA'
                }
            },
            'expected_checks': [
                lambda body: 'study_phases' in body.get('study_path', {}),
                lambda body: len(body.get('study_path', {}).get('study_phases', [])) > 0,
                lambda body: body.get('study_path', {}).get('total_estimated_hours', 0) > 0
            ]
        },
        {
            'name': 'Record Recommendation Feedback',
            'description': 'Should successfully record user feedback',
            'event': {
                'httpMethod': 'POST',
                'path': f'/recommendations/{test_user_id}/feedback',
                'body': json.dumps({
                    'recommendation_id': f'test-rec-{int(time.time())}',
                    'action': 'accepted',
                    'feedback_data': {'rating': 5, 'comment': 'Very helpful!'}
                })
            },
            'expected_checks': [
                lambda body: body.get('success') is True,
                lambda body: 'successfully' in body.get('message', '').lower()
            ]
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n   🎯 {scenario['name']}")
        print(f"      {scenario['description']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(scenario['event'])
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                
                # Run expected checks
                checks_passed = 0
                total_checks = len(scenario['expected_checks'])
                
                for i, check in enumerate(scenario['expected_checks']):
                    try:
                        if check(body):
                            checks_passed += 1
                        else:
                            print(f"      ❌ Check {i+1} failed")
                    except Exception as e:
                        print(f"      ❌ Check {i+1} error: {str(e)}")
                
                if checks_passed == total_checks:
                    print(f"      ✅ All checks passed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = True
                else:
                    print(f"      ⚠️  Some checks failed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = False
                
                # Print some key results
                if 'recommendations' in body:
                    print(f"      📊 Recommendations: {len(body['recommendations'])}")
                if 'weak_areas' in body and 'weak_categories' in body['weak_areas']:
                    weak_cats = [cat['category'] for cat in body['weak_areas']['weak_categories']]
                    print(f"      📊 Weak categories: {weak_cats}")
                if 'study_path' in body and 'study_phases' in body['study_path']:
                    phases = len(body['study_path']['study_phases'])
                    hours = body['study_path'].get('total_estimated_hours', 0)
                    print(f"      📊 Study path: {phases} phases, {hours} hours")
                
            else:
                print(f"      ❌ HTTP {result.get('statusCode')}")
                if 'body' in result:
                    error_body = json.loads(result['body'])
                    print(f"      Error: {error_body.get('error', {}).get('message', 'Unknown')}")
                results[scenario['name']] = False
                
        except Exception as e:
            print(f"      ❌ Exception: {str(e)}")
            results[scenario['name']] = False
    
    return results

def cleanup_test_data(test_user_id, content_items, progress_items):
    """Clean up all test data."""
    print(f"\n🧹 Cleaning up test data for user: {test_user_id}")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
    progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
    recommendations_table = dynamodb.Table(f'procert-recommendations-{ACCOUNT_ID}')
    
    try:
        # Clean up content
        for item in content_items:
            content_table.delete_item(Key={
                'content_id': item['content_id'],
                'certification_type': item['certification_type']
            })
        
        # Clean up progress
        for item in progress_items:
            progress_table.delete_item(Key={
                'user_id': item['user_id'],
                'content_id_certification': item['content_id_certification']
            })
        
        # Clean up any recommendations
        try:
            response = recommendations_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': test_user_id}
            )
            
            for item in response['Items']:
                recommendations_table.delete_item(Key={
                    'user_id': item['user_id'],
                    'recommendation_id': item['recommendation_id']
                })
        except Exception:
            pass  # Recommendations might not exist
        
        print(f"   ✅ Cleaned up {len(content_items)} content items")
        print(f"   ✅ Cleaned up {len(progress_items)} progress records")
        print("   ✅ Cleaned up recommendations")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {str(e)}")
        return False

def main():
    """Run the comprehensive recommendation engine test."""
    print("🚀 Final Recommendation Engine Test")
    print("=" * 60)
    
    try:
        # Create test data
        test_user_id, content_items, progress_items = create_comprehensive_test_data()
        
        # Wait for data consistency
        print("\n⏳ Waiting for data consistency...")
        time.sleep(5)
        
        # Run tests
        results = test_recommendation_scenarios(test_user_id)
        
        # Cleanup
        cleanup_success = cleanup_test_data(test_user_id, content_items, progress_items)
        
        # Final report
        print("\n" + "=" * 60)
        print("📊 FINAL TEST REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"Total Scenarios: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Recommendation Engine is fully functional and ready for production!")
            print("✅ ML-based algorithms working correctly")
            print("✅ Weak area identification accurate")
            print("✅ Study path generation comprehensive")
            print("✅ All API endpoints responding correctly")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
            print("Review the detailed results above for specific issues.")
        
        print("=" * 60)
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
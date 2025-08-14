#!/usr/bin/env python3
"""
Quick Recommendation Engine Test

A focused test script to quickly identify and fix issues with the recommendation engine.
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = f"test-user-{int(time.time())}"

def test_lambda_direct():
    """Test the recommendation Lambda function directly."""
    print("🔧 Testing Recommendation Lambda directly...")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Try different possible Lambda function names
    possible_names = [
        f"ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys",  # From deployment output
        f"ProcertInfrastructureStack-ProcertRecommendationLambda",
        f"ProcertRecommendationLambda",
        f"procert-recommendation-lambda"
    ]
    
    for lambda_name in possible_names:
        try:
            print(f"   Trying Lambda function: {lambda_name}")
            
            # Test event
            test_event = {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}',
                'queryStringParameters': {
                    'certification_type': 'SAA',
                    'limit': '3'
                }
            }
            
            response = lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"   ✅ Found Lambda function: {lambda_name}")
            print(f"   📊 Response status: {result.get('statusCode')}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"   📊 Recommendations: {len(body.get('recommendations', []))}")
            else:
                print(f"   ⚠️  Response body: {result.get('body', 'No body')}")
            
            return True, lambda_name, result
            
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"   ❌ Lambda function not found: {lambda_name}")
            continue
        except Exception as e:
            print(f"   ❌ Error testing {lambda_name}: {str(e)}")
            continue
    
    return False, None, None

def check_dynamodb_tables():
    """Check if DynamoDB tables exist and are accessible."""
    print("\n🗄️  Checking DynamoDB tables...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    # Expected table names
    expected_tables = [
        f'procert-user-progress-{ACCOUNT_ID}',
        f'procert-content-metadata-{ACCOUNT_ID}',
        f'procert-recommendations-{ACCOUNT_ID}'
    ]
    
    table_status = {}
    
    for table_name in expected_tables:
        try:
            table = dynamodb.Table(table_name)
            table.load()  # This will raise an exception if table doesn't exist
            print(f"   ✅ {table_name}: EXISTS")
            table_status[table_name] = True
        except Exception as e:
            print(f"   ❌ {table_name}: {str(e)}")
            table_status[table_name] = False
    
    return table_status

def create_minimal_test_data():
    """Create minimal test data for testing."""
    print("\n📝 Creating minimal test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Content metadata
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        content_table.put_item(Item={
            'content_id': 'test-content-1',
            'certification_type': 'SAA',
            'title': 'Test EC2 Content',
            'content_type': 'study_guide',
            'category': 'EC2',
            'difficulty_level': 'beginner',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 1
        })
        print("   ✅ Created test content metadata")
        
        # User progress
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        progress_table.put_item(Item={
            'user_id': TEST_USER_ID,
            'content_id_certification': 'test-content-1#SAA',
            'content_id': 'test-content-1',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('65.0'),
            'time_spent': 300,
            'timestamp': datetime.utcnow().isoformat()
        })
        print("   ✅ Created test user progress")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create test data: {str(e)}")
        return False

def test_recommendation_engine_components():
    """Test individual components of the recommendation engine."""
    print("\n🧪 Testing recommendation engine components...")
    
    try:
        # Import the recommendation engine
        import sys
        sys.path.append('.')
        from shared.recommendation_engine import RecommendationEngine
        
        # Initialize with actual table names
        engine = RecommendationEngine(
            user_progress_table_name=f'procert-user-progress-{ACCOUNT_ID}',
            content_metadata_table_name=f'procert-content-metadata-{ACCOUNT_ID}',
            recommendations_table_name=f'procert-recommendations-{ACCOUNT_ID}',
            region_name=REGION
        )
        
        print("   ✅ Recommendation engine initialized")
        
        # Test weak area identification
        weak_areas = engine.identify_weak_areas(TEST_USER_ID)
        print(f"   ✅ Weak areas analysis: {len(weak_areas.get('weak_categories', []))} weak categories")
        
        # Test content progression
        progression = engine.get_content_difficulty_progression(TEST_USER_ID)
        print(f"   ✅ Content progression: {progression.get('current_level', 'unknown')} level")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Component test failed: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Clean up content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        content_table.delete_item(Key={
            'content_id': 'test-content-1',
            'certification_type': 'SAA'
        })
        
        # Clean up progress
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        progress_table.delete_item(Key={
            'user_id': TEST_USER_ID,
            'content_id_certification': 'test-content-1#SAA'
        })
        
        print("   ✅ Test data cleaned up")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {str(e)}")
        return False

def main():
    """Run quick tests."""
    print("🚀 Quick Recommendation Engine Test")
    print("=" * 50)
    
    results = {}
    
    # Check DynamoDB tables
    results['tables'] = check_dynamodb_tables()
    
    # Create test data
    results['test_data'] = create_minimal_test_data()
    
    # Wait for consistency
    print("\n⏳ Waiting for data consistency...")
    time.sleep(3)
    
    # Test Lambda function
    results['lambda_success'], lambda_name, lambda_result = test_lambda_direct()
    
    # Test components directly
    results['components'] = test_recommendation_engine_components()
    
    # Cleanup
    results['cleanup'] = cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    
    if results['lambda_success']:
        print(f"✅ Lambda function working: {lambda_name}")
        if lambda_result and lambda_result.get('statusCode') == 200:
            print("✅ Lambda returns successful responses")
        else:
            print("⚠️  Lambda has issues - check logs")
    else:
        print("❌ Lambda function not found or not working")
    
    table_count = sum(1 for status in results['tables'].values() if status)
    print(f"📊 DynamoDB tables: {table_count}/3 accessible")
    
    if results['components']:
        print("✅ Recommendation engine components working")
    else:
        print("❌ Recommendation engine components have issues")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
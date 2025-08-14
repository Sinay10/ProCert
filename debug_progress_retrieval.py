#!/usr/bin/env python3
"""
Debug Progress Retrieval

This script specifically debugs why the progress retrieval is only returning 1 item
instead of multiple items for the same user.
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = f"progress-debug-{int(time.time())}"

def debug_progress_retrieval():
    """Debug the progress retrieval mechanism step by step."""
    print("🔍 Debugging progress retrieval mechanism...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Step 1: Create multiple content items in EC2 category
        print("\n📝 Step 1: Creating multiple EC2 content items...")
        
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_items = [
            {
                'content_id': f'debug-ec2-basics-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Basics Debug',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': f'debug-ec2-advanced-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Advanced Debug',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            },
            {
                'content_id': f'debug-ec2-expert-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'EC2 Expert Debug',
                'content_type': 'question',
                'category': 'EC2',
                'difficulty_level': 'advanced',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 3
            }
        ]
        
        for content in content_items:
            content_table.put_item(Item=content)
        
        print(f"   ✅ Created {len(content_items)} EC2 content items")
        
        # Step 2: Create multiple progress records with UNIQUE keys
        print("\n📝 Step 2: Creating multiple progress records with unique keys...")
        
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        progress_items = [
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'debug-ec2-basics-{TEST_USER_ID}#SAA',
                'content_id': f'debug-ec2-basics-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('25.0'),
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'debug-ec2-advanced-{TEST_USER_ID}#SAA',
                'content_id': f'debug-ec2-advanced-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('35.0'),
                'time_spent': 700,
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'debug-ec2-expert-{TEST_USER_ID}#SAA',
                'content_id': f'debug-ec2-expert-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('45.0'),
                'time_spent': 500,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print(f"   ✅ Created {len(progress_items)} progress records")
        print("   📊 Expected performance: EC2 avg = (25 + 35 + 45) / 3 = 35%")
        
        # Step 3: Verify data was stored correctly
        print("\n🔍 Step 3: Verifying data storage...")
        
        # Check content storage
        print("   Content verification:")
        for content in content_items:
            response = content_table.get_item(
                Key={
                    'content_id': content['content_id'],
                    'certification_type': content['certification_type']
                }
            )
            if 'Item' in response:
                print(f"      ✅ {content['content_id']}: {response['Item'].get('category', 'NO CATEGORY')}")
            else:
                print(f"      ❌ {content['content_id']}: NOT FOUND")
        
        # Check progress storage
        print("   Progress verification:")
        for progress in progress_items:
            response = progress_table.get_item(
                Key={
                    'user_id': progress['user_id'],
                    'content_id_certification': progress['content_id_certification']
                }
            )
            if 'Item' in response:
                score = response['Item'].get('score', 'NO SCORE')
                print(f"      ✅ {progress['content_id']}: {score}%")
            else:
                print(f"      ❌ {progress['content_id']}: NOT FOUND")
        
        # Step 4: Test direct DynamoDB query
        print("\n🔍 Step 4: Testing direct DynamoDB query...")
        
        response = progress_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': TEST_USER_ID}
        )
        
        items = response.get('Items', [])
        print(f"   Direct query returned: {len(items)} items")
        
        for item in items:
            content_id = item.get('content_id', 'NO CONTENT_ID')
            score = item.get('score', 'NO SCORE')
            print(f"      - {content_id}: {score}%")
        
        # Step 5: Test ProgressTracker.get_user_progress
        print("\n🔍 Step 5: Testing ProgressTracker.get_user_progress...")
        
        try:
            import sys
            sys.path.append('.')
            from shared.progress_tracker import ProgressTracker
            
            progress_tracker = ProgressTracker(
                user_progress_table_name=f'procert-user-progress-{ACCOUNT_ID}',
                content_metadata_table_name=f'procert-content-metadata-{ACCOUNT_ID}',
                region_name=REGION
            )
            
            user_progress = progress_tracker.get_user_progress(TEST_USER_ID, None)
            print(f"   ProgressTracker returned: {len(user_progress)} items")
            
            for progress in user_progress:
                print(f"      - {progress.content_id}: {progress.score}%")
            
        except Exception as e:
            print(f"   ❌ ProgressTracker test failed: {str(e)}")
        
        # Step 6: Test RecommendationEngine weak area detection
        print("\n🔍 Step 6: Testing RecommendationEngine weak area detection...")
        
        try:
            from recommendation_lambda_src.shared.recommendation_engine import RecommendationEngine
            
            engine = RecommendationEngine(
                user_progress_table_name=f'procert-user-progress-{ACCOUNT_ID}',
                content_metadata_table_name=f'procert-content-metadata-{ACCOUNT_ID}',
                recommendations_table_name=f'procert-recommendations-{ACCOUNT_ID}',
                region_name=REGION
            )
            
            # Test get_user_progress through recommendation engine
            user_progress = engine.progress_tracker.get_user_progress(TEST_USER_ID, None)
            print(f"   RecommendationEngine.progress_tracker returned: {len(user_progress)} items")
            
            for progress in user_progress:
                print(f"      - {progress.content_id}: {progress.score}%")
            
            # Test weak area identification
            weak_areas = engine.identify_weak_areas(TEST_USER_ID, None)
            
            category_performance = weak_areas.get('category_performance', {})
            print(f"   Category performance analysis: {len(category_performance)} categories")
            
            for category, perf in category_performance.items():
                if isinstance(perf, dict):
                    scores = perf.get('scores', [])
                    attempts = perf.get('attempts', 0)
                    avg_score = perf.get('avg_score', 0)
                    print(f"      - {category}: {avg_score:.1f}% ({attempts} attempts)")
                    print(f"        Scores collected: {scores}")
            
            weak_categories = weak_areas.get('weak_categories', [])
            print(f"   Weak categories detected: {len(weak_categories)}")
            
            for weak_cat in weak_categories:
                print(f"      - {weak_cat}")
            
        except Exception as e:
            print(f"   ❌ RecommendationEngine test failed: {str(e)}")
        
        # Step 7: Test Lambda function directly
        print("\n🔍 Step 7: Testing Lambda function directly...")
        
        lambda_client = boto3.client('lambda', region_name=REGION)
        lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
        
        weak_areas_event = {
            'httpMethod': 'GET',
            'path': f'/recommendations/{TEST_USER_ID}/weak-areas',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(weak_areas_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            weak_areas = body.get('weak_areas', {})
            
            category_performance = weak_areas.get('category_performance', {})
            print(f"   Lambda category performance: {len(category_performance)} categories")
            
            for category, perf in category_performance.items():
                if isinstance(perf, dict):
                    avg_score = perf.get('avg_score', 0)
                    attempts = perf.get('attempts', 0)
                    print(f"      - {category}: {avg_score:.1f}% ({attempts} attempts)")
        
        # Cleanup
        print("\n🧹 Cleaning up debug data...")
        
        # Clean up content
        for content in content_items:
            try:
                content_table.delete_item(Key={
                    'content_id': content['content_id'],
                    'certification_type': content['certification_type']
                })
            except Exception:
                pass
        
        # Clean up progress
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
        
        print("   ✅ Cleanup complete")
        
    except Exception as e:
        print(f"   ❌ Debug failed: {str(e)}")

def main():
    """Run progress retrieval debugging."""
    print("🐛 Debugging Progress Retrieval Issue")
    print("=" * 60)
    
    debug_progress_retrieval()
    
    print("\n" + "=" * 60)
    print("🔍 PROGRESS RETRIEVAL DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
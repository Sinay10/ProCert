#!/usr/bin/env python3
"""
Debug Content Metadata Retrieval

This script debugs if content metadata retrieval is working correctly.
"""

import boto3
from datetime import datetime
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = "metadata-debug-user"

def test_content_metadata_retrieval():
    """Test if content metadata retrieval is working."""
    print("🔍 Testing content metadata retrieval...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Create test content
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_item = {
            'content_id': 'metadata-test-content',
            'certification_type': 'SAA',
            'title': 'Metadata Test Content',
            'content_type': 'study_guide',
            'category': 'TestCategory',
            'difficulty_level': 'beginner',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 5
        }
        
        content_table.put_item(Item=content_item)
        print("   ✅ Created test content")
        
        # Test direct retrieval
        print("\n   🧪 Testing direct DynamoDB retrieval...")
        
        # Method 1: Direct get_item (this should work)
        response = content_table.get_item(
            Key={
                'content_id': 'metadata-test-content',
                'certification_type': 'SAA'
            }
        )
        
        if 'Item' in response:
            item = response['Item']
            print(f"      ✅ Direct get_item works: {item.get('category', 'NO CATEGORY')}")
        else:
            print("      ❌ Direct get_item failed")
        
        # Method 2: Scan for content_id (this is what the recommendation engine might be doing)
        print("\n   🧪 Testing scan method...")
        
        response = content_table.scan(
            FilterExpression='content_id = :content_id',
            ExpressionAttributeValues={':content_id': 'metadata-test-content'}
        )
        
        items = response.get('Items', [])
        if items:
            item = items[0]
            print(f"      ✅ Scan method works: {item.get('category', 'NO CATEGORY')}")
        else:
            print("      ❌ Scan method failed")
        
        # Test the recommendation engine's method
        print("\n   🧪 Testing recommendation engine method...")
        
        try:
            import sys
            sys.path.append('recommendation_lambda_src')
            from shared.recommendation_engine import RecommendationEngine
            
            engine = RecommendationEngine(
                user_progress_table_name=f'procert-user-progress-{ACCOUNT_ID}',
                content_metadata_table_name=f'procert-content-metadata-{ACCOUNT_ID}',
                recommendations_table_name=f'procert-recommendations-{ACCOUNT_ID}',
                region_name=REGION
            )
            
            content = engine._get_content_metadata('metadata-test-content')
            
            if content:
                print(f"      ✅ Recommendation engine method works: {content.category}")
            else:
                print("      ❌ Recommendation engine method failed - returns None")
                
        except Exception as e:
            print(f"      ❌ Recommendation engine method error: {str(e)}")
        
        # Create user progress and test the full weak area detection
        print("\n   🧪 Testing full weak area detection with known content...")
        
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        # Create progress records
        progress_items = [
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'metadata-test-content#SAA',
                'content_id': 'metadata-test-content',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('25.0'),
                'time_spent': 600,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'metadata-test-content#SAA',
                'content_id': 'metadata-test-content',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('30.0'),
                'time_spent': 500,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'metadata-test-content#SAA',
                'content_id': 'metadata-test-content',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('35.0'),
                'time_spent': 400,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print("   ✅ Created 3 progress records with scores: 25%, 30%, 35% (avg: 30%)")
        
        # Test weak area detection
        try:
            weak_areas = engine.identify_weak_areas(TEST_USER_ID, None)
            
            category_performance = weak_areas.get('category_performance', {})
            print(f"      Category performance: {len(category_performance)} categories")
            
            for category, perf in category_performance.items():
                if isinstance(perf, dict):
                    scores = perf.get('scores', [])
                    attempts = perf.get('attempts', 0)
                    avg_score = perf.get('avg_score', 0)
                    print(f"        - {category}: {avg_score:.1f}% ({attempts} attempts, {len(scores)} scores)")
                    print(f"          Scores: {scores}")
            
            weak_categories = weak_areas.get('weak_categories', [])
            print(f"      Weak categories: {len(weak_categories)}")
            
            for weak_cat in weak_categories:
                print(f"        - {weak_cat}")
                
        except Exception as e:
            print(f"      ❌ Weak area detection error: {str(e)}")
        
        # Cleanup
        print("\n   🧹 Cleaning up...")
        
        # Clean up content
        try:
            content_table.delete_item(Key={
                'content_id': 'metadata-test-content',
                'certification_type': 'SAA'
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
        print(f"   ❌ Test failed: {str(e)}")

def main():
    """Run content metadata debugging."""
    print("🐛 Debugging Content Metadata Retrieval")
    print("=" * 60)
    
    test_content_metadata_retrieval()
    
    print("\n" + "=" * 60)
    print("🔍 CONTENT METADATA DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
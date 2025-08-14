#!/usr/bin/env python3
"""
Debug Content Metadata Detailed

This script tests the _get_content_metadata method specifically to see
why it's failing for some content items.
"""

import boto3
import time
from datetime import datetime
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = f"metadata-detailed-{int(time.time())}"

def test_content_metadata_retrieval_detailed():
    """Test content metadata retrieval in detail."""
    print("🔍 Testing content metadata retrieval in detail...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Create 3 test content items
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_items = [
            {
                'content_id': f'detailed-test-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'Test Content 1',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': f'detailed-test-2-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'Test Content 2',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            },
            {
                'content_id': f'detailed-test-3-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': 'Test Content 3',
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
        
        print(f"   ✅ Created {len(content_items)} content items")
        
        # Test each content item retrieval individually
        print("\n🔍 Testing individual content metadata retrieval...")
        
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
            
            for i, content in enumerate(content_items, 1):
                content_id = content['content_id']
                print(f"\n   Testing content {i}: {content_id}")
                
                # Test direct scan
                response = content_table.scan(
                    FilterExpression='content_id = :content_id',
                    ExpressionAttributeValues={':content_id': content_id},
                    Limit=1
                )
                
                if response['Items']:
                    print(f"      ✅ Direct scan found: {response['Items'][0].get('category', 'NO CATEGORY')}")
                else:
                    print(f"      ❌ Direct scan failed")
                
                # Test recommendation engine method
                content_metadata = engine._get_content_metadata(content_id)
                
                if content_metadata:
                    print(f"      ✅ RecommendationEngine found: {content_metadata.category}")
                else:
                    print(f"      ❌ RecommendationEngine failed")
        
        except Exception as e:
            print(f"   ❌ RecommendationEngine test failed: {str(e)}")
        
        # Now test the full weak area detection process step by step
        print("\n🔍 Testing full weak area detection process...")
        
        # Create progress records
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        progress_items = [
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'detailed-test-1-{TEST_USER_ID}#SAA',
                'content_id': f'detailed-test-1-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('25.0'),
                'time_spent': 600,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'detailed-test-2-{TEST_USER_ID}#SAA',
                'content_id': f'detailed-test-2-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('35.0'),
                'time_spent': 700,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': f'detailed-test-3-{TEST_USER_ID}#SAA',
                'content_id': f'detailed-test-3-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('45.0'),
                'time_spent': 500,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print(f"   ✅ Created {len(progress_items)} progress records")
        
        # Test the identify_weak_areas method step by step
        try:
            user_progress = engine.progress_tracker.get_user_progress(TEST_USER_ID, None)
            print(f"   📊 Retrieved {len(user_progress)} progress items")
            
            # Manually simulate the weak area detection logic
            print("\n   🔍 Simulating weak area detection logic...")
            
            from collections import defaultdict
            category_performance = defaultdict(lambda: {'scores': [], 'attempts': 0, 'avg_score': 0.0})
            
            for i, progress in enumerate(user_progress, 1):
                print(f"\n      Processing progress item {i}: {progress.content_id}")
                print(f"         Score: {progress.score}")
                
                # Get content metadata
                content = engine._get_content_metadata(progress.content_id)
                
                if content:
                    print(f"         ✅ Content found: {content.category}")
                    
                    # Add to category performance
                    cat_perf = category_performance[content.category]
                    cat_perf['scores'].append(progress.score)
                    cat_perf['attempts'] += 1
                    
                    print(f"         📊 Category {content.category} now has {len(cat_perf['scores'])} scores: {cat_perf['scores']}")
                else:
                    print(f"         ❌ Content NOT found - score will be ignored!")
            
            # Calculate final averages
            print(f"\n   📊 Final category performance:")
            for category, perf in category_performance.items():
                if perf['scores']:
                    avg_score = sum(perf['scores']) / len(perf['scores'])
                    perf['avg_score'] = avg_score
                    print(f"      - {category}: {avg_score:.1f}% ({perf['attempts']} attempts)")
                    print(f"        Scores: {perf['scores']}")
        
        except Exception as e:
            print(f"   ❌ Weak area simulation failed: {str(e)}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        
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
        print(f"   ❌ Test failed: {str(e)}")

def main():
    """Run detailed content metadata debugging."""
    print("🐛 Debugging Content Metadata Retrieval - Detailed")
    print("=" * 70)
    
    test_content_metadata_retrieval_detailed()
    
    print("\n" + "=" * 70)
    print("🔍 DETAILED CONTENT METADATA DEBUG COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
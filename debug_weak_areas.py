#!/usr/bin/env python3
"""
Debug Weak Areas Detection

This script specifically debugs why weak areas aren't being detected.
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = "weak-debug-user"

def test_weak_area_detection_directly():
    """Test weak area detection by calling the Lambda directly with detailed logging."""
    print("🔍 Testing weak area detection directly...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Create very obvious weak area data
        print("   📝 Creating obvious weak area data...")
        
        # Content metadata
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        content_item = {
            'content_id': 'weak-debug-ec2',
            'certification_type': 'SAA',
            'title': 'EC2 Weak Debug Content',
            'content_type': 'study_guide',
            'category': 'EC2',
            'difficulty_level': 'beginner',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 5
        }
        
        content_table.put_item(Item=content_item)
        
        # User progress with MANY attempts and consistently poor performance
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        # Create 5 attempts with very poor scores
        progress_items = []
        for i in range(5):
            progress_items.append({
                'user_id': TEST_USER_ID,
                'content_id_certification': 'weak-debug-ec2#SAA',
                'content_id': 'weak-debug-ec2',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal(str(20.0 + i * 5)),  # 20%, 25%, 30%, 35%, 40%
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=5-i)).isoformat()
            })
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print("   ✅ Created 5 attempts with scores: 20%, 25%, 30%, 35%, 40%")
        print("   📊 Average: 30% (EXTREMELY weak - should definitely be detected)")
        
        # Wait for consistency
        time.sleep(3)
        
        # Test weak areas detection
        lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
        
        weak_areas_event = {
            'httpMethod': 'GET',
            'path': f'/recommendations/{TEST_USER_ID}/weak-areas',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        print("\n   🧪 Testing weak areas detection...")
        
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(weak_areas_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"      Status: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            weak_areas = body.get('weak_areas', {})
            
            print(f"      Response keys: {list(weak_areas.keys())}")
            
            weak_categories = weak_areas.get('weak_categories', [])
            print(f"      Weak categories detected: {len(weak_categories)}")
            
            if weak_categories:
                for weak_cat in weak_categories:
                    print(f"        ✅ {weak_cat.get('category')}: {weak_cat.get('avg_score', 0):.1f}% (severity: {weak_cat.get('severity', 'unknown')})")
            else:
                print("      ❌ NO WEAK CATEGORIES DETECTED!")
                print("      This is definitely a bug - 30% average should be detected")
            
            # Check category performance data
            category_performance = weak_areas.get('category_performance', {})
            print(f"      Category performance data: {len(category_performance)} categories")
            
            for category, perf in category_performance.items():
                if isinstance(perf, dict):
                    avg_score = perf.get('avg_score', 0)
                    attempts = perf.get('attempts', 0)
                    print(f"        - {category}: {avg_score:.1f}% ({attempts} attempts)")
            
            # Check recommendations
            recommendations = weak_areas.get('recommendations', [])
            print(f"      Recommendations: {len(recommendations)}")
            for rec in recommendations[:3]:
                print(f"        - {rec}")
        
        else:
            print(f"      ❌ Error: {result.get('body')}")
        
        # Also test the recommendation generation to see if it picks up weak areas
        print("\n   🧪 Testing recommendation generation...")
        
        rec_event = {
            'httpMethod': 'GET',
            'path': f'/recommendations/{TEST_USER_ID}',
            'queryStringParameters': {
                'certification_type': 'SAA',
                'limit': '10'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(rec_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            recommendations = body.get('recommendations', [])
            
            print(f"      Recommendations generated: {len(recommendations)}")
            
            weak_area_recs = [r for r in recommendations if 'EC2' in r.get('reasoning', '') or r.get('priority', 0) >= 7]
            print(f"      High-priority/EC2 recommendations: {len(weak_area_recs)}")
            
            for rec in recommendations:
                print(f"        - {rec.get('type', 'unknown')} (Priority: {rec.get('priority', 0)})")
                print(f"          Reasoning: {rec.get('reasoning', 'No reasoning')}")
        
        # Cleanup
        print("\n   🧹 Cleaning up...")
        
        # Clean up content
        try:
            content_table.delete_item(Key={
                'content_id': 'weak-debug-ec2',
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
    """Run weak area debugging."""
    print("🐛 Debugging Weak Area Detection")
    print("=" * 50)
    
    test_weak_area_detection_directly()
    
    print("\n" + "=" * 50)
    print("🔍 WEAK AREA DEBUG COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
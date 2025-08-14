#!/usr/bin/env python3
"""
Debug Weak Areas Detection

Debug why the weak areas detection isn't working as expected.
"""

import json
import boto3
import time
from decimal import Decimal
from datetime import datetime, timedelta

LAMBDA_NAME = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def debug_weak_areas():
    """Debug the weak areas detection."""
    print("🔍 Debugging Weak Areas Detection")
    print("=" * 50)
    
    # Create test data with clear weak performance
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
    progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
    
    test_user_id = f'debug-user-{int(time.time())}'
    
    # Create content
    content_table.put_item(Item={
        'content_id': 'debug-ec2-content',
        'certification_type': 'SAA',
        'title': 'EC2 Debug Content',
        'content_type': 'study_guide',
        'category': 'EC2',
        'difficulty_level': 'beginner',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'version': '1.0',
        'chunk_count': 1
    })
    
    # Create multiple weak progress records for EC2
    weak_scores = [45.0, 50.0, 55.0, 48.0, 52.0]  # All below 70%
    
    for i, score in enumerate(weak_scores):
        progress_table.put_item(Item={
            'user_id': test_user_id,
            'content_id_certification': f'debug-ec2-content#{i}#SAA',  # Unique keys
            'content_id': 'debug-ec2-content',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': 300,
            'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat()
        })
    
    print(f"📝 Created test data for user: {test_user_id}")
    print(f"   📊 EC2 scores: {weak_scores} (avg: {sum(weak_scores)/len(weak_scores):.1f}%)")
    
    # Wait for consistency
    time.sleep(3)
    
    # Test weak areas detection
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    event = {
        'httpMethod': 'GET',
        'path': f'/recommendations/{test_user_id}/weak-areas',
        'queryStringParameters': {
            'certification_type': 'SAA'
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            
            print("\n🔍 Weak Areas Response:")
            print(json.dumps(body, indent=2, default=str))
            
            weak_areas = body.get('weak_areas', {})
            weak_categories = weak_areas.get('weak_categories', [])
            category_performance = weak_areas.get('category_performance', {})
            
            print(f"\n📊 Analysis:")
            print(f"   Weak categories found: {len(weak_categories)}")
            print(f"   Category performance data: {len(category_performance)} categories")
            
            if 'EC2' in category_performance:
                ec2_perf = category_performance['EC2']
                print(f"   EC2 performance: {ec2_perf}")
            else:
                print("   ❌ EC2 not found in category performance")
            
            if weak_categories:
                for cat in weak_categories:
                    print(f"   Weak: {cat['category']} - {cat['avg_score']:.1f}% ({cat['attempts']} attempts)")
            else:
                print("   ❌ No weak categories detected")
        
        else:
            print(f"❌ Error: HTTP {result.get('statusCode')}")
            if 'body' in result:
                error_body = json.loads(result['body'])
                print(f"Error: {error_body}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        content_table.delete_item(Key={
            'content_id': 'debug-ec2-content',
            'certification_type': 'SAA'
        })
        
        for i in range(len(weak_scores)):
            progress_table.delete_item(Key={
                'user_id': test_user_id,
                'content_id_certification': f'debug-ec2-content#{i}#SAA'
            })
        
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup failed: {str(e)}")

if __name__ == "__main__":
    debug_weak_areas()
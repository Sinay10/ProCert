#!/usr/bin/env python3
"""
Debug Recommendation Engine Issues

This script helps debug specific issues with the recommendation engine.
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = "debug-user-123"

def debug_recommendation_algorithm():
    """Debug why recommendations aren't being generated."""
    print("🔍 Debugging recommendation algorithm...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Create very clear test data
        print("   📝 Creating clear test data...")
        
        # Content metadata
        content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
        
        # Create content with clear categories
        content_items = [
            {
                'content_id': 'debug-ec2-weak',
                'certification_type': 'SAA',
                'title': 'EC2 Weak Area Content',
                'content_type': 'study_guide',
                'category': 'EC2',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            },
            {
                'content_id': 'debug-s3-strong',
                'certification_type': 'SAA',
                'title': 'S3 Strong Area Content',
                'content_type': 'study_guide',
                'category': 'S3',
                'difficulty_level': 'intermediate',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 8
            },
            {
                'content_id': 'debug-vpc-untested',
                'certification_type': 'SAA',
                'title': 'VPC Untested Content',
                'content_type': 'study_guide',
                'category': 'VPC',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 3
            }
        ]
        
        for content in content_items:
            content_table.put_item(Item=content)
        
        # User progress with very clear patterns
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        # Multiple attempts with consistently poor EC2 performance
        progress_items = [
            # EC2 - Very poor performance (should definitely be weak area)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'debug-ec2-weak#SAA',
                'content_id': 'debug-ec2-weak',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('30.0'),
                'time_spent': 600,
                'timestamp': (datetime.utcnow() - timedelta(days=5)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'debug-ec2-weak#SAA',
                'content_id': 'debug-ec2-weak',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('35.0'),
                'time_spent': 700,
                'timestamp': (datetime.utcnow() - timedelta(days=4)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'debug-ec2-weak#SAA',
                'content_id': 'debug-ec2-weak',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('40.0'),
                'time_spent': 500,
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            # S3 - Excellent performance (should be strong area)
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'debug-s3-strong#SAA',
                'content_id': 'debug-s3-strong',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('95.0'),
                'time_spent': 200,
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                'user_id': TEST_USER_ID,
                'content_id_certification': 'debug-s3-strong#SAA',
                'content_id': 'debug-s3-strong',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('92.0'),
                'time_spent': 180,
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        for progress in progress_items:
            progress_table.put_item(Item=progress)
        
        print("   ✅ Created debug test data:")
        print("      - EC2: 30%, 35%, 40% (3 attempts, avg 35% - VERY weak)")
        print("      - S3: 95%, 92% (2 attempts, avg 93.5% - VERY strong)")
        print("      - VPC: No attempts (untested)")
        
        # Wait for consistency
        time.sleep(3)
        
        # Test the Lambda function
        print("\n   🧪 Testing Lambda with debug data...")
        
        lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
        
        test_event = {
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
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"      Status: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            recommendations = body.get('recommendations', [])
            
            print(f"      Recommendations: {len(recommendations)}")
            
            if recommendations:
                for i, rec in enumerate(recommendations):
                    print(f"        {i+1}. Type: {rec.get('type')}, Priority: {rec.get('priority')}")
                    print(f"           Category: {rec.get('category', 'N/A')}")
                    print(f"           Reasoning: {rec.get('reasoning', 'No reasoning')}")
            else:
                print("      ❌ No recommendations generated!")
                print("      This suggests an issue with the recommendation algorithm")
        else:
            print(f"      ❌ Error: {result.get('body')}")
        
        # Test weak areas specifically
        print("\n   🧪 Testing weak areas detection...")
        
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
            weak_categories = weak_areas.get('weak_categories', [])
            
            print(f"      Weak categories detected: {len(weak_categories)}")
            
            if weak_categories:
                for weak_cat in weak_categories:
                    print(f"        - {weak_cat.get('category')}: {weak_cat.get('avg_score', 0):.1f}%")
            else:
                print("      ❌ No weak areas detected!")
                print("      With EC2 avg 35%, this should definitely be detected as weak")
        
        # Cleanup
        print("\n   🧹 Cleaning up debug data...")
        
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
        
        print("   ✅ Debug data cleaned up")
        
    except Exception as e:
        print(f"   ❌ Debug failed: {str(e)}")

def check_lambda_logs():
    """Check recent Lambda logs for errors."""
    print("\n📋 Checking recent Lambda logs...")
    
    logs_client = boto3.client('logs', region_name=REGION)
    lambda_name = "ProcertInfrastructureStac-ProcertRecommendationLam-R6RNNN1QUHys"
    log_group_name = f"/aws/lambda/{lambda_name}"
    
    try:
        # Get recent log events
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int((datetime.utcnow() - timedelta(minutes=30)).timestamp() * 1000),
            filterPattern="ERROR"
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"   Found {len(events)} error events in last 30 minutes:")
            for event in events[-5:]:  # Show last 5 errors
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"   [{timestamp}] {event['message']}")
        else:
            print("   ✅ No error events found in recent logs")
            
            # Check for any recent events
            response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=int((datetime.utcnow() - timedelta(minutes=10)).timestamp() * 1000)
            )
            
            events = response.get('events', [])
            if events:
                print(f"   📋 Found {len(events)} recent events (last 10 minutes)")
                for event in events[-3:]:  # Show last 3 events
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'][:100] + "..." if len(event['message']) > 100 else event['message']
                    print(f"   [{timestamp}] {message}")
            else:
                print("   ⚠️  No recent events found - Lambda might not be receiving requests")
    
    except Exception as e:
        print(f"   ❌ Failed to check logs: {str(e)}")

def main():
    """Run debugging tests."""
    print("🐛 Debugging Recommendation Engine Issues")
    print("=" * 60)
    
    debug_recommendation_algorithm()
    check_lambda_logs()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
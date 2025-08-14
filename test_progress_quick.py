#!/usr/bin/env python3
"""
Quick test of progress tracking functionality
"""

import json
import boto3
from datetime import datetime

# Configuration
PROGRESS_LAMBDA_NAME = "ProcertInfrastructureStac-ProcertProgressLambda0CE-nZf56rxEfPgv"
REGION = "us-east-1"

def test_progress_tracking():
    """Test progress tracking functionality."""
    print("📊 Testing Progress Tracking")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Test recording progress
    event = {
        'httpMethod': 'POST',
        'path': '/progress/test-user-progress/interaction',
        'body': json.dumps({
            'content_id': 'test-content-progress',
            'interaction_type': 'completed',
            'certification_type': 'SAA',
            'score': 85,
            'time_spent': 1800,
            'metadata': {'test': True}
        })
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=PROGRESS_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Status Code: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print("✅ Progress recording successful")
            print(f"Response: {json.dumps(body, indent=2)}")
        else:
            body = json.loads(result['body'])
            print(f"❌ Failed: {body.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_progress_tracking()
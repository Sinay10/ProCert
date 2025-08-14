#!/usr/bin/env python3
"""
Debug quiz response to see what's actually returned
"""

import json
import boto3

# Configuration
QUIZ_LAMBDA_NAME = "ProcertInfrastructureStac-ProcertQuizLambda8FDECDE-4RIY4fDPbKM4"
REGION = "us-east-1"

def debug_quiz_generation():
    """Debug quiz generation response."""
    print("🔍 Debugging Quiz Generation Response")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    event = {
        'httpMethod': 'POST',
        'path': '/quiz/generate',
        'body': json.dumps({
            'user_id': 'test-user-quiz',
            'certification_type': 'SAA',
            'question_count': 3,
            'difficulty': 'intermediate'
        })
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=QUIZ_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Status Code: {result.get('statusCode')}")
        
        if 'body' in result:
            body = json.loads(result['body'])
            print(f"Response Body: {json.dumps(body, indent=2)}")
        else:
            print(f"Full Result: {json.dumps(result, indent=2)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_quiz_generation()
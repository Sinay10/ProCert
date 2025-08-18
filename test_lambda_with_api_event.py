#!/usr/bin/env python3
"""
Test the quiz Lambda with a simulated API Gateway event structure
"""

import boto3
import json

def test_lambda_with_api_event():
    """Test Lambda with API Gateway event structure."""
    print("🧪 Testing Lambda with API Gateway Event Structure")
    print("=" * 60)
    
    # Create a simulated API Gateway event
    api_event = {
        "httpMethod": "POST",
        "path": "/quiz/generate",
        "pathParameters": None,
        "body": json.dumps({
            "certification_type": "ANS",
            "difficulty": "mixed",
            "count": 5
        }),
        "requestContext": {
            "authorizer": {
                "user_id": "test-user-123"
            }
        }
    }
    
    print("📋 Simulated API Gateway Event:")
    print(json.dumps(api_event, indent=2))
    
    # Invoke the Lambda function directly
    lambda_client = boto3.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName='ProcertInfrastructureStac-ProcertQuizLambda8FDECDE-4RIY4fDPbKM4',
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"\n📤 Lambda Response:")
        print(f"Status Code: {response_payload.get('statusCode')}")
        
        if 'body' in response_payload:
            body = json.loads(response_payload['body'])
            print(f"Response Body: {json.dumps(body, indent=2)}")
        else:
            print(f"Raw Response: {json.dumps(response_payload, indent=2)}")
            
    except Exception as e:
        print(f"❌ Error invoking Lambda: {str(e)}")

if __name__ == "__main__":
    test_lambda_with_api_event()
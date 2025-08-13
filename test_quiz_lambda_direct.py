#!/usr/bin/env python3
"""
Test the quiz Lambda function directly to see if it's working.
"""

import boto3
import json
import time

def test_quiz_lambda_direct():
    """Test quiz Lambda by invoking it directly."""
    print("🧪 Testing Quiz Lambda directly...")
    
    lambda_client = boto3.client('lambda')
    
    # Find the quiz Lambda function
    functions = lambda_client.list_functions()['Functions']
    quiz_function = None
    for func in functions:
        if 'QuizLambda' in func['FunctionName']:
            quiz_function = func['FunctionName']
            break
    
    if not quiz_function:
        print("❌ Quiz Lambda function not found!")
        return
    
    print(f"Found Quiz Lambda function: {quiz_function}")
    
    # Test event (simulating API Gateway event)
    test_event = {
        "httpMethod": "POST",
        "path": "/quiz/generate",
        "pathParameters": {},
        "body": json.dumps({
            "user_id": "test-user-123",
            "certification_type": "SAA",
            "question_count": 5,
            "difficulty": "mixed"
        }),
        "headers": {
            "Content-Type": "application/json"
        },
        "requestContext": {
            "authorizer": {
                "user_id": "test-user-123",
                "email": "test@example.com",
                "token_use": "access",
                "client_id": "test-client"
            }
        }
    }
    
    try:
        print("Invoking Quiz Lambda...")
        response = lambda_client.invoke(
            FunctionName=quiz_function,
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Quiz Lambda Response: {json.dumps(result, indent=2)}")
        
        if response.get('StatusCode') == 200:
            print("✅ Quiz Lambda invocation successful!")
        else:
            print(f"❌ Quiz Lambda invocation failed with status: {response.get('StatusCode')}")
            
    except Exception as e:
        print(f"❌ Error invoking Quiz Lambda: {e}")

if __name__ == "__main__":
    test_quiz_lambda_direct()
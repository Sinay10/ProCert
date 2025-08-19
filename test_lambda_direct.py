#!/usr/bin/env python3

import boto3
import json

def test_lambda_direct():
    """Test the lambda function directly to see if it works."""
    
    # Get the lambda function name from CDK outputs
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Create a test event that simulates API Gateway
    test_event = {
        "httpMethod": "GET",
        "resource": "/resources/{certification}",
        "pathParameters": {
            "certification": "general"
        },
        "headers": {
            "Authorization": "Bearer test-token"
        },
        "body": None
    }
    
    try:
        # Find the chatbot lambda function
        functions = lambda_client.list_functions()
        chatbot_function = None
        
        for func in functions['Functions']:
            if 'ProcertChatbotLambda' in func['FunctionName']:
                chatbot_function = func['FunctionName']
                break
        
        if not chatbot_function:
            print("❌ Could not find chatbot lambda function")
            return
        
        print(f"🔍 Found lambda function: {chatbot_function}")
        print(f"📤 Invoking with test event...")
        
        # Invoke the lambda function
        response = lambda_client.invoke(
            FunctionName=chatbot_function,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        
        print(f"📊 Status Code: {response['StatusCode']}")
        print(f"📄 Response: {json.dumps(payload, indent=2)}")
        
        if 'errorMessage' in payload:
            print(f"❌ Error: {payload['errorMessage']}")
            if 'errorType' in payload:
                print(f"🔍 Error Type: {payload['errorType']}")
            if 'stackTrace' in payload:
                print(f"📚 Stack Trace: {payload['stackTrace']}")
        
    except Exception as e:
        print(f"❌ Error invoking lambda: {e}")

if __name__ == "__main__":
    test_lambda_direct()
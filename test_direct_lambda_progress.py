#!/usr/bin/env python3
"""
Test progress Lambda directly to bypass API Gateway
"""

import boto3
import json
import time
import requests

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get a valid JWT token."""
    timestamp = int(time.time())
    user_email = f"direct_lambda_{timestamp}@example.com"
    
    registration_data = {
        "email": user_email,
        "password": "TestPass123!",
        "name": "Direct Lambda Test User",
        "target_certifications": ["SAA"]
    }
    
    print(f"Creating user: {user_email}")
    reg_response = requests.post(f"{API_ENDPOINT}/auth/register", json=registration_data)
    
    if reg_response.status_code != 201:
        print(f"❌ Registration failed: {reg_response.text}")
        return None, None
    
    user_id = json.loads(reg_response.text)['user_id']
    time.sleep(2)
    
    login_response = requests.post(f"{API_ENDPOINT}/auth/login", json={
        "email": user_email,
        "password": registration_data['password']
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return None, None
    
    access_token = json.loads(login_response.text)['tokens']['access_token']
    print(f"✅ User created: {user_id}")
    
    return user_id, access_token

def test_progress_lambda_directly(user_id, token):
    """Test the progress Lambda function directly."""
    print(f"\n🧪 Testing Progress Lambda Directly")
    print("-" * 40)
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Find progress Lambda function
        functions = lambda_client.list_functions()['Functions']
        progress_function = None
        for func in functions:
            if 'ProgressLambda' in func['FunctionName']:
                progress_function = func['FunctionName']
                break
        
        if not progress_function:
            print("❌ Progress Lambda function not found")
            return
        
        print(f"Found Progress Lambda: {progress_function}")
        
        # Test different endpoints directly
        test_cases = [
            {
                "description": "Analytics Endpoint",
                "event": {
                    "httpMethod": "GET",
                    "path": f"/progress/{user_id}/analytics",
                    "queryStringParameters": {},
                    "headers": {"Authorization": f"Bearer {token}"},
                    "pathParameters": {"user_id": user_id}
                }
            },
            {
                "description": "Dashboard Endpoint", 
                "event": {
                    "httpMethod": "GET",
                    "path": f"/progress/{user_id}/dashboard",
                    "queryStringParameters": {},
                    "headers": {"Authorization": f"Bearer {token}"},
                    "pathParameters": {"user_id": user_id}
                }
            },
            {
                "description": "Achievements Endpoint",
                "event": {
                    "httpMethod": "GET", 
                    "path": f"/progress/{user_id}/achievements",
                    "queryStringParameters": {},
                    "headers": {"Authorization": f"Bearer {token}"},
                    "pathParameters": {"user_id": user_id}
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['description']}")
            
            response = lambda_client.invoke(
                FunctionName=progress_function,
                Payload=json.dumps(test_case['event'])
            )
            
            result = json.loads(response['Payload'].read())
            status_code = result.get('statusCode', 'No status')
            
            print(f"    Status Code: {status_code}")
            
            if status_code == 200:
                print(f"    ✅ SUCCESS - Lambda working directly!")
                body = json.loads(result.get('body', '{}'))
                print(f"    User ID in response: {body.get('user_id', 'Not found')}")
            else:
                print(f"    ❌ Error: {result.get('body', 'No body')}")
                if 'errorMessage' in result:
                    print(f"    Error Message: {result['errorMessage']}")
                    
    except Exception as e:
        print(f"❌ Error testing Lambda directly: {str(e)}")

def compare_api_gateway_vs_direct():
    """Compare API Gateway response vs direct Lambda invocation."""
    print(f"\n🔍 Comparing API Gateway vs Direct Lambda")
    print("-" * 50)
    
    user_id, token = create_test_user_and_get_token()
    
    if not user_id or not token:
        print("❌ Failed to create test user")
        return
    
    # Test via API Gateway
    print("\n1. Testing via API Gateway:")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}/progress/{user_id}/analytics",
            headers=headers,
            timeout=30
        )
        print(f"   API Gateway Status: {response.status_code}")
        print(f"   API Gateway Response: {response.text[:200]}")
    except Exception as e:
        print(f"   API Gateway Error: {str(e)}")
    
    # Test direct Lambda
    print("\n2. Testing direct Lambda:")
    test_progress_lambda_directly(user_id, token)

def main():
    print("🔍 Testing Progress Lambda Directly vs API Gateway")
    print("=" * 60)
    
    compare_api_gateway_vs_direct()
    
    print("\n" + "=" * 60)
    print("🏁 Direct Lambda Test Complete!")

if __name__ == "__main__":
    main()
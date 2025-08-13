#!/usr/bin/env python3
"""
Test JWT authorizer directly with a fresh token.
"""

import boto3
import json
import requests
import time

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_jwt_with_fresh_token():
    """Test JWT authorizer with a fresh token."""
    print("🔐 Testing JWT Authorizer with Fresh Token...")
    
    # Get a fresh token first
    registration_data = {
        "email": f"jwttest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "JWT Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Getting fresh authentication token...")
    reg_response = requests.post(
        f"{API_ENDPOINT}/auth/register",
        json=registration_data,
        headers={"Content-Type": "application/json"}
    )
    
    if reg_response.status_code != 201:
        print(f"❌ Registration failed: {reg_response.text}")
        return
    
    reg_data = json.loads(reg_response.text)
    user_id = reg_data['user_id']
    
    login_response = requests.post(
        f"{API_ENDPOINT}/auth/login",
        json={
            "email": registration_data['email'],
            "password": registration_data['password']
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = json.loads(login_response.text)
    access_token = login_data['tokens']['access_token']
    print(f"✅ Got fresh token: {access_token[:50]}...")
    
    # Now test the JWT authorizer directly with this fresh token
    print("\n2. Testing JWT authorizer directly with fresh token...")
    
    lambda_client = boto3.client('lambda')
    
    # Find the JWT authorizer function
    functions = lambda_client.list_functions()['Functions']
    jwt_function = None
    for func in functions:
        if 'JWTAuthorizer' in func['FunctionName']:
            jwt_function = func['FunctionName']
            break
    
    if not jwt_function:
        print("❌ JWT Authorizer function not found!")
        return
    
    print(f"Found JWT Authorizer function: {jwt_function}")
    
    # Test different authorization token formats
    test_cases = [
        {
            "name": "Bearer + token",
            "token": f"Bearer {access_token}",
            "resource": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/profile/test-user"
        },
        {
            "name": "Just token",
            "token": access_token,
            "resource": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/profile/test-user"
        },
        {
            "name": "Bearer + token (quiz endpoint)",
            "token": f"Bearer {access_token}",
            "resource": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/POST/quiz/generate"
        },
        {
            "name": "Just token (quiz endpoint)",
            "token": access_token,
            "resource": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/POST/quiz/generate"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        
        # Test event (simulating API Gateway authorizer event)
        test_event = {
            "type": "TOKEN",
            "authorizationToken": test_case["token"],
            "methodArn": test_case["resource"]
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=jwt_function,
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"   Response: {json.dumps(result, indent=4)}")
            
            if result.get('policyDocument', {}).get('Statement', [{}])[0].get('Effect') == 'Allow':
                print("   ✅ ALLOW - Authorization successful!")
            else:
                print("   ❌ DENY - Authorization failed!")
                
        except Exception as e:
            print(f"   ❌ Error invoking JWT Authorizer: {e}")

if __name__ == "__main__":
    test_jwt_with_fresh_token()
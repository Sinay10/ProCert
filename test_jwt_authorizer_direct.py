#!/usr/bin/env python3
"""
Test the JWT authorizer directly to see what policy it returns.
"""

import boto3
import json
import requests
import uuid

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_jwt_authorizer_direct():
    """Test JWT authorizer by invoking it directly."""
    
    # Step 1: Get a valid JWT token
    test_email = f"jwt-test-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "JwtTest123!"
    
    print("🔐 Getting JWT token...")
    
    # Register user
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "JWT Test User"
        },
        headers={"Content-Type": "application/json"}
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        return
    
    # Login to get token
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    login_data = login_response.json()
    jwt_token = login_data.get("tokens", {}).get("access_token")
    user_id = login_data.get("user_id")
    
    print(f"✅ Got JWT token: {jwt_token[:50]}...")
    print(f"✅ User ID: {user_id}")
    
    # Step 2: Find the JWT authorizer Lambda function
    lambda_client = boto3.client('lambda')
    
    try:
        functions = lambda_client.list_functions()['Functions']
        jwt_function = None
        
        jwt_function = "ProcertInfrastructureStac-ProcertJWTAuthorizerLamb-9oBz4ud3A3ay"
        
        if not jwt_function:
            print("❌ Could not find JWT authorizer function")
            return
        
        print(f"✅ Found JWT authorizer function: {jwt_function}")
        
        # Step 3: Test JWT authorizer with profile endpoint ARN
        profile_test_event = {
            "type": "TOKEN",
            "authorizationToken": f"Bearer {jwt_token}",
            "methodArn": f"arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/profile/{user_id}"
        }
        
        print("🧪 Testing JWT authorizer with profile endpoint...")
        profile_response = lambda_client.invoke(
            FunctionName=jwt_function,
            Payload=json.dumps(profile_test_event)
        )
        
        profile_result = json.loads(profile_response['Payload'].read())
        print(f"Profile endpoint result: {json.dumps(profile_result, indent=2)}")
        
        # Step 4: Test JWT authorizer with quiz endpoint ARN
        quiz_test_event = {
            "type": "TOKEN",
            "authorizationToken": f"Bearer {jwt_token}",
            "methodArn": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/POST/quiz/generate"
        }
        
        print("🧪 Testing JWT authorizer with quiz endpoint...")
        quiz_response = lambda_client.invoke(
            FunctionName=jwt_function,
            Payload=json.dumps(quiz_test_event)
        )
        
        quiz_result = json.loads(quiz_response['Payload'].read())
        print(f"Quiz endpoint result: {json.dumps(quiz_result, indent=2)}")
        
        # Step 5: Compare the results
        profile_effect = profile_result.get('policyDocument', {}).get('Statement', [{}])[0].get('Effect')
        quiz_effect = quiz_result.get('policyDocument', {}).get('Statement', [{}])[0].get('Effect')
        
        print(f"\n📊 Comparison:")
        print(f"Profile endpoint policy effect: {profile_effect}")
        print(f"Quiz endpoint policy effect: {quiz_effect}")
        
        if profile_effect == quiz_effect:
            print("✅ Both endpoints get the same policy - issue might be elsewhere")
        else:
            print("❌ Different policies returned - this is the issue!")
            
    except Exception as e:
        print(f"❌ Error testing JWT authorizer: {str(e)}")

if __name__ == "__main__":
    test_jwt_authorizer_direct()
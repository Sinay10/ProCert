#!/usr/bin/env python3
"""
Test with a fresh token by registering a new user and immediately testing.
"""

import requests
import json
import time

# API endpoint from CDK output
API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_with_fresh_token():
    """Test with a fresh token."""
    print("🔐 Testing with fresh token...")
    
    # Register a new user
    registration_data = {
        "email": f"testuser{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Fresh Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Registering new user...")
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
    print(f"✅ User registered: {user_id}")
    
    # Wait a moment
    time.sleep(2)
    
    # Login to get fresh token
    print("2. Logging in to get fresh token...")
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
    print("✅ Fresh token obtained")
    
    # Test protected endpoint immediately
    print("3. Testing protected endpoint with fresh token...")
    profile_response = requests.get(
        f"{API_ENDPOINT}/profile/{user_id}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    print(f"Status Code: {profile_response.status_code}")
    print(f"Response: {profile_response.text}")
    
    if profile_response.status_code == 200:
        print("✅ Fresh token test successful!")
    else:
        print("❌ Fresh token test failed!")
        
        # Let's also test the JWT authorizer directly with this fresh token
        print("4. Testing JWT authorizer directly with fresh token...")
        import boto3
        
        lambda_client = boto3.client('lambda')
        functions = lambda_client.list_functions()['Functions']
        jwt_function = None
        for func in functions:
            if 'JWTAuthorizer' in func['FunctionName']:
                jwt_function = func['FunctionName']
                break
        
        if jwt_function:
            test_event = {
                "type": "TOKEN",
                "authorizationToken": f"Bearer {access_token}",
                "methodArn": f"arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/profile/{user_id}"
            }
            
            try:
                response = lambda_client.invoke(
                    FunctionName=jwt_function,
                    Payload=json.dumps(test_event)
                )
                
                result = json.loads(response['Payload'].read())
                print(f"Direct JWT test result: {json.dumps(result, indent=2)}")
                
            except Exception as e:
                print(f"❌ Error testing JWT directly: {e}")

if __name__ == "__main__":
    test_with_fresh_token()
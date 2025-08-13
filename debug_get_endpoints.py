#!/usr/bin/env python3
"""
Debug GET endpoint authorization issues
"""

import requests
import json
import time
import boto3

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user_and_get_token():
    """Create a test user and get a valid JWT token."""
    timestamp = int(time.time())
    user_email = f"debug_get_{timestamp}@example.com"
    
    registration_data = {
        "email": user_email,
        "password": "TestPass123!",
        "name": "Debug GET Test User",
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
    print(f"✅ Token obtained: {access_token[:20]}...")
    
    return user_id, access_token

def test_different_endpoints(user_id, token):
    """Test different endpoints to see which ones work."""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints_to_test = [
        # Known working endpoints
        {"method": "GET", "url": f"{API_ENDPOINT}/profile/{user_id}", "description": "Profile (known working)"},
        
        # Progress endpoints
        {"method": "GET", "url": f"{API_ENDPOINT}/progress/{user_id}/analytics", "description": "Progress Analytics"},
        {"method": "GET", "url": f"{API_ENDPOINT}/progress/{user_id}/dashboard", "description": "Progress Dashboard"},
        {"method": "GET", "url": f"{API_ENDPOINT}/progress/{user_id}/achievements", "description": "Progress Achievements"},
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['description']}")
        print(f"   {endpoint['method']} {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=headers, timeout=30)
            else:
                response = requests.post(endpoint['url'], headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS")
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN - Authorization issue")
            else:
                print(f"   ⚠️  Other error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

def test_jwt_authorizer_for_different_methods(token, user_id):
    """Test JWT authorizer directly for different HTTP methods."""
    print(f"\n🔍 Testing JWT Authorizer for Different Methods")
    print("-" * 50)
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Find JWT authorizer function
        functions = lambda_client.list_functions()['Functions']
        jwt_function = None
        for func in functions:
            if 'JWTAuthorizer' in func['FunctionName']:
                jwt_function = func['FunctionName']
                break
        
        if not jwt_function:
            print("❌ JWT Authorizer function not found")
            return
        
        test_cases = [
            {"method": "GET", "resource": f"/profile/{user_id}", "description": "GET Profile (working)"},
            {"method": "GET", "resource": f"/progress/{user_id}/analytics", "description": "GET Progress Analytics"},
            {"method": "POST", "resource": f"/progress/{user_id}/interaction", "description": "POST Progress Interaction (working)"},
        ]
        
        for test_case in test_cases:
            print(f"\nTesting JWT for: {test_case['description']}")
            
            test_event = {
                "type": "TOKEN",
                "authorizationToken": f"Bearer {token}",
                "methodArn": f"arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/{test_case['method']}{test_case['resource']}"
            }
            
            response = lambda_client.invoke(
                FunctionName=jwt_function,
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'policyDocument' in result:
                effect = result['policyDocument']['Statement'][0]['Effect']
                print(f"   JWT Result: {effect}")
                
                if effect == "Allow":
                    print(f"   ✅ JWT authorizer allows this request")
                else:
                    print(f"   ❌ JWT authorizer denies this request")
                    print(f"   Policy: {json.dumps(result, indent=2)}")
            else:
                print(f"   ❌ Unexpected JWT response: {result}")
                
    except Exception as e:
        print(f"❌ Error testing JWT authorizer: {str(e)}")

def main():
    print("🔍 Debugging GET Endpoint Authorization Issues")
    print("=" * 60)
    
    user_id, token = create_test_user_and_get_token()
    
    if not user_id or not token:
        print("❌ Failed to create test user")
        return
    
    # Test different endpoints
    test_different_endpoints(user_id, token)
    
    # Test JWT authorizer directly
    test_jwt_authorizer_for_different_methods(token, user_id)
    
    print("\n" + "=" * 60)
    print("🏁 Debug Complete!")

if __name__ == "__main__":
    main()
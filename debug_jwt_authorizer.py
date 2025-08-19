#!/usr/bin/env python3

import boto3
import json
import requests
from botocore.exceptions import ClientError

def get_test_token():
    """Get a test JWT token from Cognito."""
    try:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        username = "demo.user@procert.test"
        password = "TestUser123!"
        client_id = "53kma8sulrhdl9ki7dboi0vj1j"
        
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        return response['AuthenticationResult']['AccessToken']
        
    except ClientError as e:
        print(f"❌ Failed to get token: {e}")
        return None

def test_jwt_authorizer_directly():
    """Test the JWT authorizer lambda directly to see what policies it generates."""
    
    print("🔐 Getting authentication token...")
    token = get_test_token()
    
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got authentication token")
    
    # Test different method ARNs to see what policies are generated
    test_arns = [
        "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/POST/chat/message",
        "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/resources/general",
        "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/resources/ccp",
        "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/POST/quiz/generate"
    ]
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    for arn in test_arns:
        print(f"\n🧪 Testing ARN: {arn}")
        
        # Create test event for JWT authorizer
        test_event = {
            "type": "TOKEN",
            "authorizationToken": f"Bearer {token}",
            "methodArn": arn
        }
        
        try:
            # Invoke the JWT authorizer lambda directly
            response = lambda_client.invoke(
                FunctionName='ProcertInfrastructureStac-ProcertJWTAuthorizerLamb-9oBz4ud3A3ay',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'errorMessage' in result:
                print(f"❌ Error: {result['errorMessage']}")
            else:
                print(f"✅ Success!")
                print(f"Principal ID: {result.get('principalId', 'N/A')}")
                
                policy = result.get('policyDocument', {})
                statements = policy.get('Statement', [])
                
                for i, statement in enumerate(statements):
                    effect = statement.get('Effect', 'N/A')
                    resource = statement.get('Resource', 'N/A')
                    print(f"  Statement {i+1}: {effect} - {resource}")
                
                context = result.get('context', {})
                print(f"Context: user_id={context.get('user_id', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error invoking authorizer: {e}")

if __name__ == "__main__":
    test_jwt_authorizer_directly()
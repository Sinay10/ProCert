#!/usr/bin/env python3
"""
Test the JWT authorizer directly by invoking the Lambda function.
"""

import boto3
import json

def test_jwt_authorizer_direct():
    """Test JWT authorizer by invoking it directly."""
    print("🔐 Testing JWT authorizer directly...")
    
    lambda_client = boto3.client('lambda')
    
    # Get the Lambda function name
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
    
    # Test event (simulating API Gateway authorizer event)
    test_event = {
        "type": "TOKEN",
        "authorizationToken": "Bearer eyJraWQiOiJEdjUrV2FNbXlSeFRLa1dcL21OT0tiK0FCOFwvK2cyQ3MxRmJmRThveUNpMzg9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJhNDM4ZTQ3OC05MDcxLTcwYTEtZjI3ZC02MzM1NmQ1ZmEzMDQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9Qbkx2UDBvN00iLCJjbGllbnRfaWQiOiI1M2ttYThzdWxyaGRsOWtpN2Rib2kwdmoxaiIsIm9yaWdpbl9qdGkiOiI4NzAwZGY4Zi1mOWY3LTQyYjItOTViYS03MDc2NDc2NTlmYjAiLCJldmVudF9pZCI6ImM5ZDliZTEyLTA1ZDYtNGEzZC04MDZkLTdjYmU1NTgyNDZmMiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3NTQ5ODU0OTgsImV4cCI6MTc1NDk4OTA5OCwiaWF0IjoxNzU0OTg1NDk4LCJqdGkiOiJiNGUwYzI5Ny1iOTc3LTQzZGYtYTNiNC00ODUwOTUwOGU2N2YiLCJ1c2VybmFtZSI6ImE0MzhlNDc4LTkwNzEtNzBhMS1mMjdkLTYzMzU2ZDVmYTMwNCJ9.dtHe7MfY6L0801DN_ZhGmVAgeZ1lrraJzuoBn6YbFW6xYFYoEsTfDaDpNeLj9bOspHbodn3r4oOTPTUVFhVyS0-J7i9GjGeP39uefry_O7DchqN7_afHU_lGkmqjFti0yjN__y8yu4R5GBy_DJ8V6-eKFJhVZ1VtifMkOA1073xFpR-5A5o953fNZkSgJVWWIfvtRc00iaCfjFtC158VQlXJwQmED-CVEFtuKxvb6oDrGvAv8exj8cjKu5fqGMzCx0ir1UdIazVmRUk4HrNBYBk5m9uM_N91g0s4uDvYKc3zypwy6Y1CiwaIOg-z68OFR-vKCVCmQeOtKd04N2CZWg",
        "methodArn": "arn:aws:execute-api:us-east-1:353207798766:04l6uq5jl4/prod/GET/profile/test-user"
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=jwt_function,
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"JWT Authorizer Response: {json.dumps(result, indent=2)}")
        
        if 'principalId' in result:
            print("✅ JWT Authorizer working!")
        else:
            print("❌ JWT Authorizer failed!")
            
    except Exception as e:
        print(f"❌ Error invoking JWT Authorizer: {e}")

if __name__ == "__main__":
    test_jwt_authorizer_direct()
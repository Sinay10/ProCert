#!/usr/bin/env python3

import boto3
import json

def check_method_authorization():
    """Check the authorization configuration for specific methods."""
    
    client = boto3.client('apigateway', region_name='us-east-1')
    api_id = '04l6uq5jl4'
    
    print("🔍 Checking Method Authorization Configuration")
    print("=" * 60)
    
    # Check POST /chat/message
    print("\n📋 POST /chat/message (Resource ID: 0apj4w)")
    try:
        method = client.get_method(
            restApiId=api_id,
            resourceId='0apj4w',  # message resource
            httpMethod='POST'
        )
        print(f"  ✅ Authorization Type: {method.get('authorizationType', 'N/A')}")
        print(f"  ✅ Authorizer ID: {method.get('authorizerId', 'N/A')}")
        print(f"  ✅ API Key Required: {method.get('apiKeyRequired', 'N/A')}")
        
        # Check integration
        integration = method.get('methodIntegration', {})
        print(f"  ✅ Integration Type: {integration.get('type', 'N/A')}")
        uri = integration.get('uri', 'N/A')
        if 'lambda' in uri:
            function_name = uri.split('/')[-2]
            print(f"  ✅ Lambda Function: {function_name}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check GET /resources/{certification}
    print("\n📋 GET /resources/{certification} (Resource ID: rkdu8m)")
    try:
        method = client.get_method(
            restApiId=api_id,
            resourceId='rkdu8m',  # {certification} resource
            httpMethod='GET'
        )
        print(f"  ✅ Authorization Type: {method.get('authorizationType', 'N/A')}")
        print(f"  ✅ Authorizer ID: {method.get('authorizerId', 'N/A')}")
        print(f"  ✅ API Key Required: {method.get('apiKeyRequired', 'N/A')}")
        
        # Check integration
        integration = method.get('methodIntegration', {})
        print(f"  ✅ Integration Type: {integration.get('type', 'N/A')}")
        uri = integration.get('uri', 'N/A')
        if 'lambda' in uri:
            function_name = uri.split('/')[-2]
            print(f"  ✅ Lambda Function: {function_name}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check authorizer details
    print("\n📋 JWT Authorizer Details")
    try:
        authorizers = client.get_authorizers(restApiId=api_id)
        for auth in authorizers['items']:
            if auth['name'] == 'ProcertJWTAuthorizer':
                print(f"  ✅ Authorizer ID: {auth['id']}")
                print(f"  ✅ Type: {auth['type']}")
                print(f"  ✅ Cache TTL: {auth.get('authorizerResultTtlInSeconds', 'N/A')} seconds")
                print(f"  ✅ Identity Source: {auth.get('identitySource', 'N/A')}")
                print(f"  ✅ Lambda URI: {auth.get('authorizerUri', 'N/A')}")
                break
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    check_method_authorization()
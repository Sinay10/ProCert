#!/usr/bin/env python3
"""
Check the actual API Gateway configuration to understand the difference between working and non-working endpoints.
"""

import boto3
import json

def check_api_gateway_config():
    """Check API Gateway configuration."""
    print("🔍 Checking API Gateway Configuration...")
    
    apigateway = boto3.client('apigateway')
    
    # Find the ProCert API
    apis = apigateway.get_rest_apis()
    procert_api = None
    
    for api in apis['items']:
        if 'ProCert' in api['name']:
            procert_api = api
            break
    
    if not procert_api:
        print("❌ ProCert API not found!")
        return
    
    api_id = procert_api['id']
    print(f"Found ProCert API: {api_id} - {procert_api['name']}")
    
    # Get resources
    resources = apigateway.get_resources(restApiId=api_id)
    
    print(f"\n📋 API Resources:")
    for resource in resources['items']:
        path = resource.get('pathPart', '/')
        resource_id = resource['id']
        parent_id = resource.get('parentId', 'ROOT')
        
        print(f"   Resource: {path} (ID: {resource_id}, Parent: {parent_id})")
        
        # Get methods for this resource
        if 'resourceMethods' in resource:
            for method in resource['resourceMethods']:
                print(f"      Method: {method}")
                
                try:
                    method_details = apigateway.get_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method
                    )
                    
                    # Check if authorizer is configured
                    auth_type = method_details.get('authorizationType', 'NONE')
                    authorizer_id = method_details.get('authorizerId')
                    
                    print(f"         Auth Type: {auth_type}")
                    if authorizer_id:
                        print(f"         Authorizer ID: {authorizer_id}")
                    
                    # Check method integration
                    integration = method_details.get('methodIntegration', {})
                    integration_type = integration.get('type', 'UNKNOWN')
                    uri = integration.get('uri', 'N/A')
                    
                    print(f"         Integration: {integration_type}")
                    if 'lambda' in uri.lower():
                        # Extract Lambda function name from URI
                        lambda_name = uri.split('/')[-2] if '/' in uri else 'Unknown'
                        print(f"         Lambda: {lambda_name}")
                    
                except Exception as e:
                    print(f"         Error getting method details: {e}")
    
    # Get authorizers
    print(f"\n📋 API Authorizers:")
    try:
        authorizers = apigateway.get_authorizers(restApiId=api_id)
        for auth in authorizers['items']:
            auth_id = auth['id']
            auth_name = auth['name']
            auth_type = auth['type']
            print(f"   Authorizer: {auth_name} (ID: {auth_id}, Type: {auth_type})")
            
            if auth_type == 'TOKEN':
                identity_source = auth.get('identitySource', 'N/A')
                print(f"      Identity Source: {identity_source}")
                
    except Exception as e:
        print(f"Error getting authorizers: {e}")

if __name__ == "__main__":
    check_api_gateway_config()
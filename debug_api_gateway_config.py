#!/usr/bin/env python3

import boto3
import json

def check_api_gateway_config():
    """Check the API Gateway configuration for authorization differences."""
    
    client = boto3.client('apigateway', region_name='us-east-1')
    api_id = '04l6uq5jl4'
    
    print("🔍 Checking API Gateway Configuration")
    print("=" * 60)
    
    # Get all resources
    resources = client.get_resources(restApiId=api_id)
    
    # Find the resources we care about
    chat_message_resource = None
    resources_cert_resource = None
    
    # First, let's see all resources
    print("📋 All API Gateway Resources:")
    for resource in resources['items']:
        path = resource.get('pathPart', '')
        resource_id = resource['id']
        parent_id = resource.get('parentId', '')
        print(f"  {resource_id}: {path} (parent: {parent_id})")
    
    # Now find specific resources
    for resource in resources['items']:
        path = resource.get('pathPart', '')
        
        if path == "message":
            chat_message_resource = resource
            print(f"📋 Found message resource: {resource['id']}")
        elif path == "{certification}" or (resource.get('parentId') == 'i93a1y'):  # i93a1y is resources
            resources_cert_resource = resource
            print(f"📋 Found certification resource: {resource['id']} - {path}")
    
    if not chat_message_resource or not resources_cert_resource:
        print("❌ Could not find required resources")
        return
    
    # Check method configurations
    print(f"\n🔍 Checking POST /chat/message (Resource ID: {chat_message_resource['id']})")
    try:
        chat_method = client.get_method(
            restApiId=api_id,
            resourceId=chat_message_resource['id'],
            httpMethod='POST'
        )
        print(f"  Authorization Type: {chat_method.get('authorizationType', 'N/A')}")
        print(f"  Authorizer ID: {chat_method.get('authorizerId', 'N/A')}")
        print(f"  API Key Required: {chat_method.get('apiKeyRequired', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error getting method: {e}")
    
    # Hardcode the resource ID we found
    resources_cert_resource_id = 'rkdu8m'
    print(f"\n🔍 Checking GET /resources/{{certification}} (Resource ID: {resources_cert_resource_id})")
    try:
        resources_method = client.get_method(
            restApiId=api_id,
            resourceId=resources_cert_resource_id,
            httpMethod='GET'
        )
        print(f"  Authorization Type: {resources_method.get('authorizationType', 'N/A')}")
        print(f"  Authorizer ID: {resources_method.get('authorizerId', 'N/A')}")
        print(f"  API Key Required: {resources_method.get('apiKeyRequired', 'N/A')}")
        
        # Check integration details
        integration = resources_method.get('methodIntegration', {})
        print(f"  Integration Type: {integration.get('type', 'N/A')}")
        print(f"  Integration URI: {integration.get('uri', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Error getting method: {e}")
    
    # Check authorizer configuration
    print(f"\n🔍 Checking Authorizer Configuration")
    try:
        authorizers = client.get_authorizers(restApiId=api_id)
        for auth in authorizers['items']:
            print(f"  Authorizer ID: {auth['id']}")
            print(f"  Name: {auth['name']}")
            print(f"  Type: {auth['type']}")
            print(f"  Cache TTL: {auth.get('authorizerResultTtlInSeconds', 'N/A')} seconds")
            print(f"  Identity Source: {auth.get('identitySource', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error getting authorizers: {e}")

def check_deployment_stage():
    """Check the deployment stage configuration."""
    
    client = boto3.client('apigateway', region_name='us-east-1')
    api_id = '04l6uq5jl4'
    
    print(f"\n🔍 Checking Deployment Stage")
    try:
        stage = client.get_stage(restApiId=api_id, stageName='prod')
        print(f"  Stage Name: {stage['stageName']}")
        print(f"  Deployment ID: {stage['deploymentId']}")
        print(f"  Cache Cluster Enabled: {stage.get('cacheClusterEnabled', False)}")
        
        # Check method settings
        method_settings = stage.get('methodSettings', {})
        for path, settings in method_settings.items():
            print(f"  Method {path}:")
            print(f"    Caching Enabled: {settings.get('cachingEnabled', False)}")
            print(f"    Cache TTL: {settings.get('cacheTtlInSeconds', 'N/A')}")
            
    except Exception as e:
        print(f"  ❌ Error getting stage: {e}")

if __name__ == "__main__":
    check_api_gateway_config()
    check_deployment_stage()
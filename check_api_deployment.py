#!/usr/bin/env python3
"""
Check API Gateway deployment status.
"""

import boto3
import json
from datetime import datetime

def check_api_deployment():
    """Check API Gateway deployment status."""
    print("🚀 Checking API Gateway Deployment Status...")
    
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
    
    # Get deployments
    try:
        deployments = apigateway.get_deployments(restApiId=api_id)
        
        print(f"\n📋 API Deployments:")
        for deployment in deployments['items']:
            deployment_id = deployment['id']
            created_date = deployment.get('createdDate', 'Unknown')
            description = deployment.get('description', 'No description')
            
            print(f"   Deployment: {deployment_id}")
            print(f"      Created: {created_date}")
            print(f"      Description: {description}")
            
        # Get stages
        stages = apigateway.get_stages(restApiId=api_id)
        
        print(f"\n📋 API Stages:")
        for stage in stages['item']:
            stage_name = stage['stageName']
            deployment_id = stage.get('deploymentId', 'Unknown')
            last_updated = stage.get('lastUpdatedDate', 'Unknown')
            
            print(f"   Stage: {stage_name}")
            print(f"      Deployment ID: {deployment_id}")
            print(f"      Last Updated: {last_updated}")
            
            # Check if this stage has any method settings
            method_settings = stage.get('methodSettings', {})
            if method_settings:
                print(f"      Method Settings: {len(method_settings)} configured")
                
    except Exception as e:
        print(f"❌ Error checking deployments: {e}")
    
    # Try to get the specific method configuration for quiz/generate
    try:
        print(f"\n🔍 Checking specific method configuration...")
        
        # Get the quiz resource
        resources = apigateway.get_resources(restApiId=api_id)
        quiz_resource_id = None
        generate_resource_id = None
        
        for resource in resources['items']:
            if resource.get('pathPart') == 'quiz':
                quiz_resource_id = resource['id']
            elif resource.get('pathPart') == 'generate':
                generate_resource_id = resource['id']
        
        if generate_resource_id:
            print(f"Found generate resource ID: {generate_resource_id}")
            
            # Get the POST method for /quiz/generate
            method = apigateway.get_method(
                restApiId=api_id,
                resourceId=generate_resource_id,
                httpMethod='POST'
            )
            
            print(f"Method configuration:")
            print(f"   Auth Type: {method.get('authorizationType')}")
            print(f"   Authorizer ID: {method.get('authorizerId')}")
            
            # Check integration
            integration = method.get('methodIntegration', {})
            print(f"   Integration Type: {integration.get('type')}")
            print(f"   Integration URI: {integration.get('uri')}")
            
        else:
            print("❌ Generate resource not found!")
            
    except Exception as e:
        print(f"❌ Error checking method configuration: {e}")

if __name__ == "__main__":
    check_api_deployment()
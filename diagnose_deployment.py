#!/usr/bin/env python3
"""
Deployment Diagnostic Script for ProCert Infrastructure

Checks for potential issues that could cause CDK deployment failures.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    print("🔐 Checking AWS Credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ User/Role: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials issue: {str(e)}")
        return False

def check_existing_resources():
    """Check for existing resources that might conflict"""
    print("\n🔍 Checking for Existing Resources...")
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    # Check DynamoDB tables
    dynamodb = boto3.client('dynamodb')
    try:
        tables = dynamodb.list_tables()['TableNames']
        procert_tables = [t for t in tables if 'procert' in t.lower()]
        if procert_tables:
            print(f"⚠️  Found existing DynamoDB tables:")
            for table in procert_tables:
                print(f"   - {table}")
        else:
            print("✅ No conflicting DynamoDB tables found")
    except Exception as e:
        print(f"❌ Error checking DynamoDB: {str(e)}")
    
    # Check S3 buckets
    s3 = boto3.client('s3')
    try:
        buckets = s3.list_buckets()['Buckets']
        procert_buckets = [b['Name'] for b in buckets if 'procert' in b['Name'].lower()]
        if procert_buckets:
            print(f"⚠️  Found existing S3 buckets:")
            for bucket in procert_buckets:
                print(f"   - {bucket}")
        else:
            print("✅ No conflicting S3 buckets found")
    except Exception as e:
        print(f"❌ Error checking S3: {str(e)}")
    
    # Check Cognito User Pools
    cognito = boto3.client('cognito-idp')
    try:
        pools = cognito.list_user_pools(MaxResults=50)['UserPools']
        procert_pools = [p for p in pools if 'procert' in p['Name'].lower()]
        if procert_pools:
            print(f"⚠️  Found existing Cognito User Pools:")
            for pool in procert_pools:
                print(f"   - {pool['Name']} ({pool['Id']})")
        else:
            print("✅ No conflicting Cognito User Pools found")
    except Exception as e:
        print(f"❌ Error checking Cognito: {str(e)}")
    
    # Check OpenSearch Serverless collections
    try:
        opensearch = boto3.client('opensearchserverless')
        collections = opensearch.list_collections()['collectionSummaries']
        procert_collections = [c for c in collections if 'procert' in c['name'].lower()]
        if procert_collections:
            print(f"⚠️  Found existing OpenSearch collections:")
            for collection in procert_collections:
                print(f"   - {collection['name']} ({collection['status']})")
        else:
            print("✅ No conflicting OpenSearch collections found")
    except Exception as e:
        print(f"❌ Error checking OpenSearch: {str(e)}")

def check_cloudformation_stacks():
    """Check for existing CloudFormation stacks"""
    print("\n📚 Checking CloudFormation Stacks...")
    
    cf = boto3.client('cloudformation')
    try:
        stacks = cf.list_stacks(
            StackStatusFilter=[
                'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE',
                'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE',
                'DELETE_IN_PROGRESS', 'DELETE_FAILED',
                'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS',
                'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_ROLLBACK_COMPLETE'
            ]
        )['StackSummaries']
        
        procert_stacks = [s for s in stacks if 'procert' in s['StackName'].lower()]
        
        if procert_stacks:
            print(f"Found {len(procert_stacks)} ProCert-related stacks:")
            for stack in procert_stacks:
                print(f"   - {stack['StackName']}: {stack['StackStatus']}")
                if stack['StackStatus'] in ['ROLLBACK_COMPLETE', 'CREATE_FAILED', 'DELETE_FAILED']:
                    print(f"     ⚠️  Stack in failed state - needs cleanup")
        else:
            print("✅ No existing ProCert CloudFormation stacks found")
            
    except Exception as e:
        print(f"❌ Error checking CloudFormation: {str(e)}")

def check_iam_permissions():
    """Check basic IAM permissions needed for deployment"""
    print("\n🔑 Checking IAM Permissions...")
    
    # Test basic permissions
    permissions_to_test = [
        ('s3', 'list_buckets', {}),
        ('dynamodb', 'list_tables', {}),
        ('lambda', 'list_functions', {}),
        ('cognito-idp', 'list_user_pools', {'MaxResults': 1}),
        ('apigateway', 'get_rest_apis', {}),
    ]
    
    for service, operation, params in permissions_to_test:
        try:
            client = boto3.client(service)
            getattr(client, operation)(**params)
            print(f"✅ {service}:{operation}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print(f"❌ {service}:{operation} - Access Denied")
            else:
                print(f"⚠️  {service}:{operation} - {e.response['Error']['Code']}")
        except Exception as e:
            print(f"❌ {service}:{operation} - {str(e)}")

def check_cdk_environment():
    """Check CDK environment and configuration"""
    print("\n🏗️  Checking CDK Environment...")
    
    import subprocess
    import os
    
    # Check if CDK is installed
    try:
        result = subprocess.run(['cdk', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ CDK Version: {result.stdout.strip()}")
        else:
            print("❌ CDK not installed or not in PATH")
    except FileNotFoundError:
        print("❌ CDK not found - please install AWS CDK")
    
    # Check if we're in a CDK project
    if os.path.exists('cdk.json'):
        print("✅ CDK project configuration found")
    else:
        print("❌ No cdk.json found - not in a CDK project directory")
    
    # Check if Python virtual environment is active
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Python virtual environment is active")
    else:
        print("⚠️  No Python virtual environment detected")

def generate_cleanup_commands():
    """Generate cleanup commands for any conflicting resources"""
    print("\n🧹 Cleanup Commands (if needed):")
    print("# Delete any failed CloudFormation stacks:")
    print("aws cloudformation delete-stack --stack-name ProcertInfrastructureStack")
    print("")
    print("# Delete conflicting DynamoDB tables (if any):")
    print("aws dynamodb delete-table --table-name procert-content-metadata-v2-ACCOUNT_ID")
    print("aws dynamodb delete-table --table-name procert-user-profiles-ACCOUNT_ID")
    print("aws dynamodb delete-table --table-name procert-conversations-ACCOUNT_ID")
    print("aws dynamodb delete-table --table-name procert-quiz-sessions-ACCOUNT_ID")
    print("aws dynamodb delete-table --table-name procert-user-progress-ACCOUNT_ID")
    print("")
    print("# Wait for resources to be fully deleted before redeploying")

def main():
    print("🔧 ProCert Infrastructure Deployment Diagnostics")
    print("=" * 60)
    
    if not check_aws_credentials():
        return
    
    check_existing_resources()
    check_cloudformation_stacks()
    check_iam_permissions()
    check_cdk_environment()
    
    print("\n" + "=" * 60)
    print("📋 Deployment Recommendations:")
    print("1. Clean up any failed/conflicting resources shown above")
    print("2. Ensure you have sufficient IAM permissions")
    print("3. Make sure CDK is properly installed and configured")
    print("4. Run 'cdk bootstrap' if this is your first CDK deployment in this region")
    print("5. Use 'cdk deploy --verbose' for detailed deployment logs")
    
    generate_cleanup_commands()

if __name__ == "__main__":
    import sys
    main()
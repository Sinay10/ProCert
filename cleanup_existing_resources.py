#!/usr/bin/env python3
"""
Cleanup script to remove existing AWS resources before deployment.
This script removes resources that might conflict with the CloudFormation stack.
"""

import boto3
import sys
from botocore.exceptions import ClientError

def cleanup_dynamodb_tables():
    """Remove existing DynamoDB tables."""
    dynamodb = boto3.client('dynamodb')
    
    tables_to_delete = [
        'procert-conversations-353207798766',
        'procert-content-metadata-353207798766', 
        'procert-user-progress-353207798766'
    ]
    
    for table_name in tables_to_delete:
        try:
            print(f"Deleting DynamoDB table: {table_name}")
            dynamodb.delete_table(TableName=table_name)
            print(f"✅ Initiated deletion of table: {table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"ℹ️  Table {table_name} does not exist")
            else:
                print(f"❌ Error deleting table {table_name}: {e}")

def cleanup_s3_buckets():
    """Remove existing S3 buckets."""
    s3 = boto3.client('s3')
    
    buckets_to_delete = [
        'procert-materials-mla-353207798766',
        'procert-materials-soa-353207798766',
        'procert-materials-scs-353207798766',
        'procert-materials-mls-353207798766',
        'procert-materials-dva-353207798766',
        'procert-materials-sap-353207798766',
        'procert-materials-general-353207798766',
        'procert-materials-dea-353207798766',
        'procert-materials-aip-353207798766',
        'procert-materials-ans-353207798766',
        'procert-materials-dop-353207798766',
        'procert-materials-ccp-353207798766',
        'procert-materials-saa-353207798766'
    ]
    
    for bucket_name in buckets_to_delete:
        try:
            print(f"Checking S3 bucket: {bucket_name}")
            
            # First, delete all objects in the bucket
            try:
                response = s3.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in response:
                    objects = [{'Key': obj['Key']} for obj in response['Contents']]
                    if objects:
                        print(f"  Deleting {len(objects)} objects from {bucket_name}")
                        s3.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects}
                        )
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchBucket':
                    print(f"  Error listing objects in {bucket_name}: {e}")
            
            # Then delete the bucket
            s3.delete_bucket(Bucket=bucket_name)
            print(f"✅ Deleted S3 bucket: {bucket_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"ℹ️  Bucket {bucket_name} does not exist")
            else:
                print(f"❌ Error deleting bucket {bucket_name}: {e}")

def cleanup_cloudformation_stack():
    """Remove existing CloudFormation stack if it exists."""
    cf = boto3.client('cloudformation')
    stack_name = 'ProcertInfrastructureStack'
    
    try:
        print(f"Checking CloudFormation stack: {stack_name}")
        cf.describe_stacks(StackName=stack_name)
        
        print(f"Deleting CloudFormation stack: {stack_name}")
        cf.delete_stack(StackName=stack_name)
        print(f"✅ Initiated deletion of stack: {stack_name}")
        print("⏳ Stack deletion may take several minutes...")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print(f"ℹ️  Stack {stack_name} does not exist")
        else:
            print(f"❌ Error deleting stack {stack_name}: {e}")

def main():
    """Main cleanup function."""
    print("🧹 Starting cleanup of existing AWS resources...")
    print("=" * 50)
    
    try:
        # Cleanup in order: CloudFormation stack first, then individual resources
        cleanup_cloudformation_stack()
        print("\n" + "=" * 50)
        
        cleanup_dynamodb_tables()
        print("\n" + "=" * 50)
        
        cleanup_s3_buckets()
        print("\n" + "=" * 50)
        
        print("✅ Cleanup completed!")
        print("\nNote: Some resources may take time to fully delete.")
        print("Wait a few minutes before redeploying the stack.")
        
    except Exception as e:
        print(f"❌ Unexpected error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
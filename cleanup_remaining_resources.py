#!/usr/bin/env python3
"""Clean up ALL remaining AWS resources - comprehensive cleanup"""

import boto3
import time

def cleanup_all_dynamodb_tables():
    """Delete ALL DynamoDB tables with procert in the name"""
    print("🗄️ Cleaning up ALL DynamoDB tables...")
    dynamodb = boto3.client('dynamodb')
    
    try:
        # List all tables
        response = dynamodb.list_tables()
        all_tables = response['TableNames']
        
        # Find all tables with 'procert' in the name
        procert_tables = [table for table in all_tables if 'procert' in table.lower()]
        
        if not procert_tables:
            print("⚠️ No ProCert tables found")
            return
            
        print(f"Found {len(procert_tables)} ProCert tables to delete:")
        for table in procert_tables:
            print(f"  - {table}")
        
        # Delete each table
        for table_name in procert_tables:
            try:
                dynamodb.delete_table(TableName=table_name)
                print(f"✅ Deleted table: {table_name}")
                time.sleep(2)  # Small delay between deletions
            except Exception as e:
                if "ResourceNotFoundException" in str(e):
                    print(f"⚠️ Table already deleted: {table_name}")
                else:
                    print(f"❌ Error deleting {table_name}: {str(e)}")
                    
    except Exception as e:
        print(f"❌ Error listing tables: {str(e)}")

def cleanup_all_s3_buckets():
    """Delete ALL S3 buckets with procert in the name"""
    print("\n📦 Cleaning up ALL S3 buckets...")
    s3 = boto3.client('s3')
    
    try:
        # List all buckets
        response = s3.list_buckets()
        all_buckets = [bucket['Name'] for bucket in response['Buckets']]
        
        # Find all buckets with 'procert' in the name
        procert_buckets = [bucket for bucket in all_buckets if 'procert' in bucket.lower()]
        
        if not procert_buckets:
            print("⚠️ No ProCert buckets found")
            return
            
        print(f"Found {len(procert_buckets)} ProCert buckets to delete:")
        for bucket in procert_buckets:
            print(f"  - {bucket}")
        
        # Delete each bucket and its contents
        for bucket_name in procert_buckets:
            try:
                # Delete all objects first
                try:
                    response = s3.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in response:
                        objects = [{'Key': obj['Key']} for obj in response['Contents']]
                        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                        print(f"  Deleted {len(objects)} objects from {bucket_name}")
                except Exception as e:
                    print(f"  No objects to delete in {bucket_name}")
                
                # Delete the bucket
                s3.delete_bucket(Bucket=bucket_name)
                print(f"✅ Deleted bucket: {bucket_name}")
                time.sleep(1)  # Small delay between deletions
                
            except Exception as e:
                if "NoSuchBucket" in str(e):
                    print(f"⚠️ Bucket already deleted: {bucket_name}")
                else:
                    print(f"❌ Error deleting {bucket_name}: {str(e)}")
                    
    except Exception as e:
        print(f"❌ Error listing buckets: {str(e)}")

def cleanup_cloudformation_stacks():
    """Delete any remaining CloudFormation stacks"""
    print("\n☁️ Cleaning up CloudFormation stacks...")
    cf = boto3.client('cloudformation')
    
    try:
        # List all stacks
        response = cf.list_stacks(StackStatusFilter=[
            'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'CREATE_FAILED', 
            'UPDATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED'
        ])
        
        all_stacks = response['StackSummaries']
        procert_stacks = [stack for stack in all_stacks if 'procert' in stack['StackName'].lower()]
        
        if not procert_stacks:
            print("⚠️ No ProCert stacks found")
            return
            
        print(f"Found {len(procert_stacks)} ProCert stacks:")
        for stack in procert_stacks:
            print(f"  - {stack['StackName']} ({stack['StackStatus']})")
            
        # Delete each stack
        for stack in procert_stacks:
            try:
                cf.delete_stack(StackName=stack['StackName'])
                print(f"✅ Initiated deletion of stack: {stack['StackName']}")
            except Exception as e:
                print(f"❌ Error deleting stack {stack['StackName']}: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error listing stacks: {str(e)}")

def main():
    print("🧹 COMPREHENSIVE ProCert Resource Cleanup")
    print("=" * 60)
    
    cleanup_all_dynamodb_tables()
    cleanup_all_s3_buckets()
    cleanup_cloudformation_stacks()
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive cleanup completed!")
    print("⏳ Waiting 60 seconds for all resources to fully delete...")
    time.sleep(60)
    print("🚀 Environment should now be completely clean!")

if __name__ == "__main__":
    main()
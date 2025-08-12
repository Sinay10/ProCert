#!/usr/bin/env python3
"""Clean up remaining AWS resources after CDK destroy"""

import boto3
import time

def cleanup_dynamodb_tables():
    """Delete remaining DynamoDB tables"""
    print("🗄️ Cleaning up DynamoDB tables...")
    dynamodb = boto3.client('dynamodb')
    account_id = "353207798766"
    
    tables_to_delete = [
        f"procert-content-metadata-v2-{account_id}",
        f"procert-conversations-{account_id}",
        f"procert-quiz-sessions-{account_id}",
        f"procert-user-profiles-{account_id}",
        f"procert-user-progress-{account_id}"
    ]
    
    for table_name in tables_to_delete:
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"✅ Deleted table: {table_name}")
        except Exception as e:
            if "ResourceNotFoundException" in str(e):
                print(f"⚠️ Table already deleted: {table_name}")
            else:
                print(f"❌ Error deleting {table_name}: {str(e)}")

def cleanup_s3_buckets():
    """Delete S3 buckets and their contents"""
    print("\n📦 Cleaning up S3 buckets...")
    s3 = boto3.client('s3')
    account_id = "353207798766"
    
    bucket_prefixes = [
        "procert-materials-aip",
        "procert-materials-ans", 
        "procert-materials-ccp",
        "procert-materials-dea",
        "procert-materials-dop",
        "procert-materials-dva",
        "procert-materials-general",
        "procert-materials-mla",
        "procert-materials-mls",
        "procert-materials-saa",
        "procert-materials-sap",
        "procert-materials-scs",
        "procert-materials-soa"
    ]
    
    for prefix in bucket_prefixes:
        bucket_name = f"{prefix}-{account_id}"
        try:
            # Delete all objects first
            response = s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                print(f"  Deleted {len(objects)} objects from {bucket_name}")
            
            # Delete the bucket
            s3.delete_bucket(Bucket=bucket_name)
            print(f"✅ Deleted bucket: {bucket_name}")
        except Exception as e:
            if "NoSuchBucket" in str(e):
                print(f"⚠️ Bucket already deleted: {bucket_name}")
            else:
                print(f"❌ Error deleting {bucket_name}: {str(e)}")

def cleanup_cognito_user_pools():
    """Delete Cognito User Pools"""
    print("\n👤 Cleaning up Cognito User Pools...")
    cognito = boto3.client('cognito-idp')
    
    try:
        pools = cognito.list_user_pools(MaxResults=50)['UserPools']
        procert_pools = [p for p in pools if 'procert' in p['Name'].lower()]
        
        for pool in procert_pools:
            try:
                cognito.delete_user_pool(UserPoolId=pool['Id'])
                print(f"✅ Deleted User Pool: {pool['Name']} ({pool['Id']})")
            except Exception as e:
                print(f"❌ Error deleting User Pool {pool['Name']}: {str(e)}")
    except Exception as e:
        print(f"❌ Error listing User Pools: {str(e)}")

def cleanup_opensearch_collections():
    """Delete OpenSearch Serverless collections and security policies"""
    print("\n🔍 Cleaning up OpenSearch collections...")
    
    try:
        opensearch = boto3.client('opensearchserverless')
        collections = opensearch.list_collections()['collectionSummaries']
        procert_collections = [c for c in collections if 'procert' in c['name'].lower()]
        
        for collection in procert_collections:
            try:
                opensearch.delete_collection(id=collection['id'])
                print(f"✅ Deleted OpenSearch collection: {collection['name']}")
            except Exception as e:
                print(f"❌ Error deleting collection {collection['name']}: {str(e)}")
    except Exception as e:
        print(f"❌ Error with OpenSearch cleanup: {str(e)}")
    
    # Clean up OpenSearch security policies
    print("🔒 Cleaning up OpenSearch security policies...")
    try:
        opensearch = boto3.client('opensearchserverless')
        
        # Delete access policies
        try:
            access_policies = opensearch.list_access_policies(type='data')
            for policy in access_policies.get('accessPolicySummaries', []):
                if 'procert' in policy['name'].lower():
                    opensearch.delete_access_policy(type='data', name=policy['name'])
                    print(f"✅ Deleted access policy: {policy['name']}")
        except Exception as e:
            print(f"⚠️ Error cleaning access policies: {e}")
        
        # Delete encryption policies
        try:
            encryption_policies = opensearch.list_security_policies(type='encryption')
            for policy in encryption_policies.get('securityPolicySummaries', []):
                if 'procert' in policy['name'].lower():
                    opensearch.delete_security_policy(type='encryption', name=policy['name'])
                    print(f"✅ Deleted encryption policy: {policy['name']}")
        except Exception as e:
            print(f"⚠️ Error cleaning encryption policies: {e}")
        
        # Delete network policies
        try:
            network_policies = opensearch.list_security_policies(type='network')
            for policy in network_policies.get('securityPolicySummaries', []):
                if 'procert' in policy['name'].lower():
                    opensearch.delete_security_policy(type='network', name=policy['name'])
                    print(f"✅ Deleted network policy: {policy['name']}")
        except Exception as e:
            print(f"⚠️ Error cleaning network policies: {e}")
                
    except Exception as e:
        print(f"⚠️ Error cleaning up OpenSearch security policies: {e}")

def main():
    print("🧹 ProCert Resource Cleanup")
    print("=" * 50)
    
    cleanup_dynamodb_tables()
    cleanup_s3_buckets()
    cleanup_cognito_user_pools()
    cleanup_opensearch_collections()
    
    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("⏳ Waiting 30 seconds for resources to fully delete...")
    time.sleep(30)
    print("🚀 Ready for fresh deployment!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Ingestion Trigger

This script tests if the ingestion Lambda is working by simulating an S3 event
or checking if existing files have been processed.
"""

import boto3
import json
import time
from datetime import datetime

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def check_existing_s3_files():
    """Check what files exist in S3 buckets."""
    print("🔍 Checking existing S3 files...")
    
    s3_client = boto3.client('s3', region_name=REGION)
    
    # Check the SAA bucket
    bucket_name = f"procert-materials-saa-{ACCOUNT_ID}"
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            print(f"   📁 Files in {bucket_name}:")
            for obj in response['Contents']:
                key = obj['Key']
                size = obj['Size']
                modified = obj['LastModified']
                print(f"      - {key} ({size} bytes, modified: {modified})")
            return response['Contents']
        else:
            print(f"   📁 No files found in {bucket_name}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error checking S3 bucket: {str(e)}")
        return []

def check_opensearch_for_content():
    """Check if any content has been ingested into OpenSearch."""
    print("\n🔍 Checking OpenSearch for ingested content...")
    
    try:
        # Get OpenSearch client
        from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
        
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_outputs = outputs.get("ProcertInfrastructureStack", {})
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        
        if not opensearch_endpoint:
            print("   ❌ OpenSearch endpoint not found")
            return False
        
        host = opensearch_endpoint.replace("https://", "")
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, REGION, 'aoss')
        
        opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_timeout=30
        )
        
        # Check if index exists
        index_name = 'procert-content'
        
        if opensearch_client.indices.exists(index=index_name):
            print(f"   ✅ Index '{index_name}' exists")
            
            # Get document count
            stats = opensearch_client.indices.stats(index=index_name)
            doc_count = stats['indices'][index_name]['total']['docs']['count']
            print(f"   📊 Document count: {doc_count}")
            
            if doc_count > 0:
                # Get a sample document
                response = opensearch_client.search(
                    index=index_name,
                    body={
                        "size": 1,
                        "query": {"match_all": {}}
                    }
                )
                
                if response['hits']['hits']:
                    sample_doc = response['hits']['hits'][0]['_source']
                    print(f"   📄 Sample document:")
                    print(f"      - Content ID: {sample_doc.get('content_id', 'unknown')}")
                    print(f"      - Certification: {sample_doc.get('certification_type', 'unknown')}")
                    print(f"      - Text length: {len(sample_doc.get('text', ''))}")
                    print(f"      - Source file: {sample_doc.get('source_file', 'unknown')}")
                
                return True
            else:
                print("   ❌ Index exists but has no documents")
                return False
        else:
            print(f"   ❌ Index '{index_name}' does not exist")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking OpenSearch: {str(e)}")
        return False

def trigger_ingestion_manually():
    """Manually trigger the ingestion Lambda for existing files."""
    print("\n🚀 Manually triggering ingestion Lambda...")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Get the Lambda function name from CDK outputs or construct it
    function_name = f"ProcertInfrastructureStack-IngestionLambda"  # Adjust if needed
    
    # Check existing S3 files
    s3_files = check_existing_s3_files()
    
    if not s3_files:
        print("   ❌ No S3 files to process")
        return False
    
    # Create a mock S3 event for the first file
    first_file = s3_files[0]
    bucket_name = f"procert-materials-saa-{ACCOUNT_ID}"
    
    mock_event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": REGION,
                "eventTime": datetime.utcnow().isoformat() + "Z",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "test-config",
                    "bucket": {
                        "name": bucket_name,
                        "arn": f"arn:aws:s3:::{bucket_name}"
                    },
                    "object": {
                        "key": first_file['Key'],
                        "size": first_file['Size']
                    }
                }
            }
        ]
    }
    
    try:
        # Use the actual function name from the list
        actual_function_name = "ProcertInfrastructureStac-ProcertIngestionLambdaV2-78e2ta6zPl3w"
        print(f"   📤 Invoking Lambda: {actual_function_name}")
        print(f"   📄 Processing file: {first_file['Key']}")
        
        response = lambda_client.invoke(
            FunctionName=actual_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(mock_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print(f"   ✅ Lambda invocation successful")
            print(f"   📋 Response: {payload}")
            return True
        else:
            print(f"   ❌ Lambda invocation failed: {response['StatusCode']}")
            print(f"   📋 Response: {payload}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error invoking Lambda: {str(e)}")
        
        # Try alternative function names
        alternative_names = [
            f"procert-infrastructure-{ACCOUNT_ID}-IngestionLambda",
            "IngestionLambda",
            f"ProcertInfrastructureStack-IngestionLambda{ACCOUNT_ID}"
        ]
        
        for alt_name in alternative_names:
            try:
                print(f"   🔄 Trying alternative name: {alt_name}")
                response = lambda_client.invoke(
                    FunctionName=alt_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(mock_event)
                )
                
                if response['StatusCode'] == 200:
                    payload = json.loads(response['Payload'].read())
                    print(f"   ✅ Lambda invocation successful with {alt_name}")
                    print(f"   📋 Response: {payload}")
                    return True
                    
            except Exception as alt_e:
                print(f"   ❌ {alt_name} also failed: {str(alt_e)}")
                continue
        
        return False

def list_lambda_functions():
    """List all Lambda functions to find the ingestion function."""
    print("\n🔍 Listing Lambda functions to find ingestion function...")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        response = lambda_client.list_functions()
        
        ingestion_functions = []
        for func in response['Functions']:
            func_name = func['FunctionName']
            if 'ingestion' in func_name.lower() or 'procert' in func_name.lower():
                ingestion_functions.append(func)
                print(f"   📋 Found: {func_name}")
                print(f"      - Runtime: {func['Runtime']}")
                print(f"      - Last Modified: {func['LastModified']}")
                print(f"      - Description: {func.get('Description', 'No description')}")
        
        return ingestion_functions
        
    except Exception as e:
        print(f"   ❌ Error listing Lambda functions: {str(e)}")
        return []

def main():
    """Run ingestion trigger test."""
    print("🚀 Testing Ingestion Trigger")
    print("=" * 60)
    
    # Step 1: Check existing S3 files
    s3_files = check_existing_s3_files()
    
    # Step 2: Check if content is already in OpenSearch
    has_content = check_opensearch_for_content()
    
    if has_content:
        print("\n✅ Content already exists in OpenSearch - ingestion has worked!")
    else:
        print("\n❌ No content in OpenSearch - ingestion may not have run")
        
        # Step 3: List Lambda functions
        lambda_functions = list_lambda_functions()
        
        if lambda_functions:
            # Step 4: Try to trigger ingestion manually
            success = trigger_ingestion_manually()
            
            if success:
                print("\n✅ Manual ingestion trigger successful!")
                print("   Wait a few minutes and check OpenSearch again")
            else:
                print("\n❌ Manual ingestion trigger failed")
        else:
            print("\n❌ No ingestion Lambda functions found")
    
    print("\n" + "=" * 60)
    print("🔍 INGESTION TRIGGER TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
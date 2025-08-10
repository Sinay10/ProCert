#!/usr/bin/env python3
"""
Script to check the status of document processing in ProCert.
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_lambda_logs(function_name: str, hours_back: int = 1) -> List[Dict]:
    """Get recent Lambda function logs."""
    try:
        logs_client = boto3.client('logs')
        
        # Get log group name
        log_group_name = f"/aws/lambda/{function_name}"
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get log events
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000)
        )
        
        return response.get('events', [])
    except Exception as e:
        print(f"Error getting Lambda logs: {e}")
        return []

def check_dynamodb_content() -> List[Dict]:
    """Check DynamoDB for processed content."""
    try:
        dynamodb = boto3.resource('dynamodb')
        
        # Get table name from CloudFormation outputs
        cf_client = boto3.client('cloudformation')
        stack_response = cf_client.describe_stacks(StackName='ProcertInfrastructureStack')
        
        content_table_name = None
        for output in stack_response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'ContentMetadataTableName':
                content_table_name = output['OutputValue']
                break
        
        if not content_table_name:
            print("Could not find ContentMetadataTable name")
            return []
        
        table = dynamodb.Table(content_table_name)
        response = table.scan(Limit=10)  # Get recent items
        
        return response.get('Items', [])
    except Exception as e:
        print(f"Error checking DynamoDB: {e}")
        return []

def check_opensearch_content() -> Dict:
    """Check OpenSearch for indexed content."""
    try:
        # Get OpenSearch endpoint from CloudFormation
        cf_client = boto3.client('cloudformation')
        stack_response = cf_client.describe_stacks(StackName='ProcertInfrastructureStack')
        
        opensearch_endpoint = None
        for output in stack_response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'OpenSearchCollectionEndpoint':
                opensearch_endpoint = output['OutputValue']
                break
        
        if opensearch_endpoint:
            print(f"OpenSearch endpoint: {opensearch_endpoint}")
            print("Note: Direct OpenSearch queries require additional setup")
            return {'endpoint': opensearch_endpoint, 'status': 'available'}
        else:
            return {'status': 'not_found'}
    except Exception as e:
        print(f"Error checking OpenSearch: {e}")
        return {'status': 'error', 'error': str(e)}

def check_s3_uploads() -> List[Dict]:
    """Check recent S3 uploads to ProCert buckets."""
    try:
        s3_client = boto3.client('s3')
        
        # List all ProCert buckets
        response = s3_client.list_buckets()
        procert_buckets = [b['Name'] for b in response['Buckets'] if 'procert-materials' in b['Name']]
        
        recent_uploads = []
        for bucket in procert_buckets:
            try:
                objects = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=10)
                for obj in objects.get('Contents', []):
                    recent_uploads.append({
                        'bucket': bucket,
                        'key': obj['Key'],
                        'last_modified': obj['LastModified'],
                        'size': obj['Size']
                    })
            except Exception as e:
                print(f"Error checking bucket {bucket}: {e}")
        
        # Sort by last modified
        recent_uploads.sort(key=lambda x: x['last_modified'], reverse=True)
        return recent_uploads[:10]  # Return 10 most recent
        
    except Exception as e:
        print(f"Error checking S3 uploads: {e}")
        return []

def main():
    """Main function to check processing status."""
    print("🔍 ProCert Document Processing Status Check")
    print("=" * 60)
    
    # 1. Check recent S3 uploads
    print("\n📁 Recent S3 Uploads:")
    print("-" * 30)
    uploads = check_s3_uploads()
    if uploads:
        for upload in uploads:
            cert_type = 'unknown'
            for cert in ['ccp', 'dva', 'saa', 'soa', 'general', 'aip', 'mla', 'dea', 'dop', 'sap', 'mls', 'scs', 'ans']:
                if cert in upload['bucket']:
                    cert_type = cert.upper()
                    break
            
            print(f"  📄 {upload['key']}")
            print(f"      Bucket: {cert_type} ({upload['bucket']})")
            print(f"      Uploaded: {upload['last_modified']}")
            print(f"      Size: {upload['size']:,} bytes")
            print()
    else:
        print("  No recent uploads found")
    
    # 2. Check Lambda logs
    print("\n📋 Recent Lambda Processing Logs:")
    print("-" * 35)
    
    # Try to find the ingestion Lambda function name
    lambda_client = boto3.client('lambda')
    functions = lambda_client.list_functions()
    ingestion_function = None
    
    for func in functions['Functions']:
        if 'ProcertIngestionLambda' in func['FunctionName']:
            ingestion_function = func['FunctionName']
            break
    
    if ingestion_function:
        print(f"Checking logs for: {ingestion_function}")
        logs = get_lambda_logs(ingestion_function, hours_back=2)
        
        # Filter for relevant log messages
        processing_logs = []
        for log in logs:
            message = log.get('message', '')
            if any(keyword in message for keyword in ['Processing new file', 'Certification detected', 'Successfully indexed', 'Error processing']):
                processing_logs.append(log)
        
        if processing_logs:
            for log in processing_logs[-10:]:  # Show last 10 relevant logs
                timestamp = datetime.fromtimestamp(log['timestamp'] / 1000)
                print(f"  [{timestamp.strftime('%H:%M:%S')}] {log['message']}")
        else:
            print("  No recent processing logs found")
    else:
        print("  Could not find ingestion Lambda function")
    
    # 3. Check DynamoDB content
    print("\n🗄️  DynamoDB Content Metadata:")
    print("-" * 30)
    content_items = check_dynamodb_content()
    if content_items:
        for item in content_items[-5:]:  # Show last 5 items
            print(f"  📄 {item.get('title', 'Unknown')}")
            print(f"      ID: {item.get('content_id', 'N/A')}")
            print(f"      Certification: {item.get('certification_type', 'N/A')}")
            print(f"      Type: {item.get('content_type', 'N/A')}")
            print(f"      Created: {item.get('created_at', 'N/A')}")
            if 'detection_details' in item:
                details = item['detection_details']
                print(f"      Detection: S3={details.get('cert_from_s3', 'N/A')}, Content={details.get('cert_from_content', 'N/A')}")
            print()
    else:
        print("  No content metadata found")
    
    # 4. Check OpenSearch status
    print("\n🔍 OpenSearch Status:")
    print("-" * 20)
    opensearch_status = check_opensearch_content()
    if opensearch_status.get('status') == 'available':
        print(f"  ✅ OpenSearch available at: {opensearch_status['endpoint']}")
        print("  💡 Use the API endpoint to query indexed content")
    else:
        print(f"  ❌ OpenSearch status: {opensearch_status.get('status', 'unknown')}")
    
    # 5. Show API endpoint for testing
    print("\n🌐 API Testing:")
    print("-" * 15)
    try:
        cf_client = boto3.client('cloudformation')
        stack_response = cf_client.describe_stacks(StackName='ProcertInfrastructureStack')
        
        api_endpoint = None
        for output in stack_response['Stacks'][0]['Outputs']:
            if 'ApiEndpoint' in output['OutputKey']:
                api_endpoint = output['OutputValue']
                break
        
        if api_endpoint:
            print(f"  🔗 API Endpoint: {api_endpoint}")
            print(f"  📝 Test query: curl -X POST {api_endpoint}query -H 'Content-Type: application/json' -d '{{\"query\": \"cloud practitioner\"}}'")
        else:
            print("  ❌ Could not find API endpoint")
    except Exception as e:
        print(f"  ❌ Error getting API endpoint: {e}")

if __name__ == "__main__":
    main()
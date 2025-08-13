#!/usr/bin/env python3
"""
Test ingestion Lambda with synchronous invocation to see any errors.
"""

import boto3
import json

def test_ingestion_sync():
    """Test ingestion Lambda synchronously."""
    print("🧪 Testing Ingestion Lambda Synchronously...")
    
    lambda_client = boto3.client('lambda')
    
    # Find the ingestion Lambda function
    functions = lambda_client.list_functions()['Functions']
    ingestion_function = None
    
    for func in functions:
        if 'IngestionLambda' in func['FunctionName']:
            ingestion_function = func['FunctionName']
            break
    
    if not ingestion_function:
        print("❌ Ingestion Lambda function not found!")
        return
    
    print(f"Found Ingestion Lambda: {ingestion_function}")
    
    # Get the ANS bucket name
    s3_client = boto3.client('s3')
    buckets = s3_client.list_buckets()
    ans_bucket = None
    
    for bucket in buckets['Buckets']:
        bucket_name = bucket['Name']
        if 'ans' in bucket_name.lower() and 'procert' in bucket_name.lower():
            ans_bucket = bucket_name
            break
    
    if not ans_bucket:
        print("❌ ANS bucket not found!")
        return
    
    print(f"Found ANS bucket: {ans_bucket}")
    
    # Test with one of the sample questions files
    test_file = "AWS-Certified-Advanced-Networking-Specialty_Sample-Questions.pdf"
    
    # Create S3 event
    s3_event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {
                        "name": ans_bucket
                    },
                    "object": {
                        "key": test_file
                    }
                }
            }
        ]
    }
    
    print(f"\n🔄 Testing ingestion with {test_file}...")
    
    try:
        # Invoke the ingestion Lambda synchronously
        response = lambda_client.invoke(
            FunctionName=ingestion_function,
            Payload=json.dumps(s3_event),
            InvocationType='RequestResponse'  # Synchronous invocation
        )
        
        print(f"Status Code: {response['StatusCode']}")
        
        # Read the response payload
        payload = response['Payload'].read()
        if payload:
            try:
                result = json.loads(payload)
                print(f"Response: {json.dumps(result, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw Response: {payload.decode()}")
        
        # Check for function errors
        if 'FunctionError' in response:
            print(f"❌ Function Error: {response['FunctionError']}")
        
        # Check logs payload for errors
        if 'LogResult' in response:
            import base64
            log_data = base64.b64decode(response['LogResult']).decode()
            print(f"\n📋 Execution Logs:")
            print(log_data)
            
    except Exception as e:
        print(f"❌ Error invoking ingestion Lambda: {e}")

if __name__ == "__main__":
    test_ingestion_sync()
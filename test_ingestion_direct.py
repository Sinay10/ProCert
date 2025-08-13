#!/usr/bin/env python3
"""
Test ingestion Lambda directly with synchronous invocation to see errors.
"""

import boto3
import json

def test_ingestion_direct():
    """Test ingestion Lambda directly."""
    print("🧪 Testing Ingestion Lambda Directly...")
    
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
    
    # Get one of the sample questions PDFs
    objects = s3_client.list_objects_v2(Bucket=ans_bucket)
    sample_pdf = None
    
    for obj in objects['Contents']:
        if 'Sample-Questions' in obj['Key'] and obj['Key'].endswith('.pdf'):
            sample_pdf = obj
            break
    
    if not sample_pdf:
        print("❌ No sample questions PDF found!")
        return
    
    pdf_key = sample_pdf['Key']
    print(f"Testing with: {pdf_key}")
    
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
                        "key": pdf_key,
                        "size": sample_pdf['Size']
                    }
                }
            }
        ]
    }
    
    try:
        print(f"\n🔄 Invoking ingestion Lambda synchronously...")
        
        # Invoke synchronously to see the response
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
                
                if response['StatusCode'] == 200:
                    print("✅ Ingestion Lambda executed successfully!")
                else:
                    print(f"❌ Ingestion Lambda failed with status: {response['StatusCode']}")
                    
            except json.JSONDecodeError:
                print(f"Raw response: {payload.decode()}")
        else:
            print("No response payload")
            
        # Check for function errors
        if 'FunctionError' in response:
            print(f"🔴 Function Error: {response['FunctionError']}")
            
    except Exception as e:
        print(f"❌ Error invoking ingestion Lambda: {e}")

if __name__ == "__main__":
    test_ingestion_direct()
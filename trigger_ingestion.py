#!/usr/bin/env python3
"""
Manually trigger the ingestion Lambda to process the uploaded ANS PDFs.
"""

import boto3
import json

def trigger_ingestion():
    """Manually trigger ingestion Lambda for ANS PDFs."""
    print("🚀 Manually Triggering Ingestion Lambda...")
    
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
    
    # List PDF files in the bucket
    objects = s3_client.list_objects_v2(Bucket=ans_bucket)
    
    if 'Contents' not in objects:
        print("❌ No objects found in ANS bucket!")
        return
    
    pdf_files = [obj for obj in objects['Contents'] if obj['Key'].lower().endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf in pdf_files:
        print(f"   {pdf['Key']}")
    
    # Trigger ingestion for each PDF file
    for pdf in pdf_files:
        pdf_key = pdf['Key']
        print(f"\n🔄 Processing {pdf_key}...")
        
        # Create S3 event to simulate the trigger
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
                            "size": pdf['Size']
                        }
                    }
                }
            ]
        }
        
        try:
            # Invoke the ingestion Lambda
            response = lambda_client.invoke(
                FunctionName=ingestion_function,
                Payload=json.dumps(s3_event),
                InvocationType='Event'  # Async invocation
            )
            
            if response['StatusCode'] == 202:
                print(f"   ✅ Successfully triggered ingestion for {pdf_key}")
            else:
                print(f"   ❌ Failed to trigger ingestion for {pdf_key}: {response['StatusCode']}")
                
        except Exception as e:
            print(f"   ❌ Error triggering ingestion for {pdf_key}: {e}")
    
    print(f"\n⏳ Ingestion triggered for {len(pdf_files)} files.")
    print("Wait a few minutes for processing to complete, then test the quiz endpoint again.")

if __name__ == "__main__":
    trigger_ingestion()
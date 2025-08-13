#!/usr/bin/env python3
"""
Retry ingestion with a single file after waiting for throttling to clear.
"""

import boto3
import json
import time

def retry_ingestion_single():
    """Retry ingestion with a single file."""
    print("⏳ Waiting for Bedrock throttling to clear...")
    print("Waiting 30 seconds before retrying...")
    time.sleep(30)
    
    print("🧪 Retrying Ingestion Lambda with Single File...")
    
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
    
    # Try with the smallest PDF first
    objects = s3_client.list_objects_v2(Bucket=ans_bucket)
    smallest_pdf = None
    smallest_size = float('inf')
    
    for obj in objects['Contents']:
        if obj['Key'].endswith('.pdf') and obj['Size'] < smallest_size:
            smallest_pdf = obj
            smallest_size = obj['Size']
    
    if not smallest_pdf:
        print("❌ No PDF found!")
        return
    
    pdf_key = smallest_pdf['Key']
    pdf_size = smallest_pdf['Size']
    print(f"Testing with smallest PDF: {pdf_key} ({pdf_size} bytes)")
    
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
                        "size": pdf_size
                    }
                }
            }
        ]
    }
    
    try:
        print(f"\n🔄 Invoking ingestion Lambda...")
        
        # Invoke synchronously
        response = lambda_client.invoke(
            FunctionName=ingestion_function,
            Payload=json.dumps(s3_event),
            InvocationType='RequestResponse'
        )
        
        print(f"Status Code: {response['StatusCode']}")
        
        # Read the response payload
        payload = response['Payload'].read()
        
        if payload:
            try:
                result = json.loads(payload)
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if result.get('statusCode') == 200:
                    print("✅ Ingestion successful!")
                    
                    # Check if content was added to metadata table
                    print("\n📊 Checking metadata table...")
                    time.sleep(2)  # Wait a moment for DynamoDB consistency
                    
                    dynamodb = boto3.resource('dynamodb')
                    tables = list(dynamodb.tables.all())
                    content_table = None
                    
                    for table in tables:
                        if 'content-metadata' in table.name.lower():
                            content_table = table
                            break
                    
                    if content_table:
                        response = content_table.scan()
                        items = response['Items']
                        
                        if items:
                            ans_items = [item for item in items if item.get('certification_type') == 'ANS']
                            print(f"✅ Found {len(ans_items)} ANS content items!")
                            
                            for item in ans_items:
                                title = item.get('title', 'N/A')
                                question_count = item.get('question_count', 0)
                                print(f"   {title}: {question_count} questions")
                        else:
                            print("❌ Still no content in metadata table")
                    
                elif 'ThrottlingException' in str(result):
                    print("❌ Still getting throttling error from Bedrock")
                    print("You may need to wait longer or contact AWS support about Bedrock limits")
                else:
                    print(f"❌ Ingestion failed: {result}")
                    
            except json.JSONDecodeError:
                print(f"Raw response: {payload.decode()}")
        
    except Exception as e:
        print(f"❌ Error invoking ingestion Lambda: {e}")

if __name__ == "__main__":
    retry_ingestion_single()
#!/usr/bin/env python3
"""
Process ANS PDFs with rate limiting to avoid Bedrock throttling.
"""

import boto3
import json
import time

def process_ans_with_rate_limiting():
    """Process ANS PDFs one at a time with delays."""
    print("🐌 Processing ANS PDFs with Rate Limiting...")
    
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
    
    # Get the ANS bucket and files
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
    
    # Get PDF files, prioritize sample questions (smaller files)
    objects = s3_client.list_objects_v2(Bucket=ans_bucket)
    pdf_files = [obj for obj in objects['Contents'] if obj['Key'].endswith('.pdf')]
    
    # Sort by size (smallest first) and prioritize sample questions
    pdf_files.sort(key=lambda x: (0 if 'Sample-Questions' in x['Key'] else 1, x['Size']))
    
    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf in pdf_files:
        print(f"   {pdf['Key']} ({pdf['Size']} bytes)")
    
    # Process files one at a time with long delays
    for i, pdf in enumerate(pdf_files):
        pdf_key = pdf['Key']
        print(f"\n🔄 Processing file {i+1}/{len(pdf_files)}: {pdf_key}")
        
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
                            "size": pdf['Size']
                        }
                    }
                }
            ]
        }
        
        try:
            # Invoke the Lambda
            response = lambda_client.invoke(
                FunctionName=ingestion_function,
                Payload=json.dumps(s3_event),
                InvocationType='RequestResponse'
            )
            
            print(f"Status Code: {response['StatusCode']}")
            
            # Read response
            payload = response['Payload'].read()
            if payload:
                try:
                    result = json.loads(payload)
                    if result.get('statusCode') == 200:
                        print(f"✅ Successfully processed {pdf_key}")
                        
                        # Check if content was added
                        time.sleep(2)
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
                            ans_items = [item for item in items if item.get('certification_type') == 'ANS']
                            
                            if ans_items:
                                total_questions = sum(item.get('question_count', 0) for item in ans_items)
                                print(f"   📊 Total ANS questions so far: {total_questions}")
                                
                                # If we have questions, test the quiz endpoint
                                if total_questions > 0:
                                    print(f"   🧪 Testing quiz endpoint...")
                                    # We can break here and test, or continue processing
                                    break
                    else:
                        print(f"❌ Failed to process {pdf_key}: {result}")
                        if 'ThrottlingException' in str(result):
                            print("   Still hitting throttling, waiting longer...")
                            time.sleep(120)  # Wait 2 minutes
                        
                except json.JSONDecodeError:
                    print(f"Raw response: {payload.decode()}")
                    
        except Exception as e:
            print(f"❌ Error processing {pdf_key}: {e}")
        
        # Wait between files to avoid throttling
        if i < len(pdf_files) - 1:  # Don't wait after the last file
            wait_time = 60  # Wait 1 minute between files
            print(f"   ⏳ Waiting {wait_time} seconds before next file...")
            time.sleep(wait_time)
    
    print(f"\n📊 Final check of content metadata...")
    # Final check
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
        ans_items = [item for item in items if item.get('certification_type') == 'ANS']
        
        if ans_items:
            total_questions = sum(item.get('question_count', 0) for item in ans_items)
            print(f"✅ Successfully processed ANS content!")
            print(f"Total ANS questions available: {total_questions}")
            
            for item in ans_items:
                title = item.get('title', 'N/A')
                question_count = item.get('question_count', 0)
                source_file = item.get('source_file', 'N/A')
                print(f"   {title}: {question_count} questions (from {source_file})")
        else:
            print("❌ No ANS content was successfully processed")

if __name__ == "__main__":
    process_ans_with_rate_limiting()
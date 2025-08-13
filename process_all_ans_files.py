#!/usr/bin/env python3
"""
Process all ANS files synchronously and then test the quiz endpoint.
"""

import boto3
import json
import time

def process_all_ans_files():
    """Process all ANS files and test quiz endpoint."""
    print("🚀 Processing All ANS Files...")
    
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
    
    # Get all PDF files
    objects = s3_client.list_objects_v2(Bucket=ans_bucket)
    pdf_files = [obj['Key'] for obj in objects['Contents'] if obj['Key'].lower().endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf in pdf_files:
        print(f"   {pdf}")
    
    total_questions = 0
    
    # Process each file
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing {pdf_file}...")
        
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
                            "key": pdf_file
                        }
                    }
                }
            ]
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=ingestion_function,
                Payload=json.dumps(s3_event),
                InvocationType='RequestResponse'
            )
            
            if response['StatusCode'] == 200:
                payload = response['Payload'].read()
                result = json.loads(payload)
                
                if 'body' in result:
                    body = json.loads(result['body'])
                    questions_extracted = body.get('questions_extracted', 0)
                    chunks_processed = body.get('chunks_processed', 0)
                    certification_detected = body.get('certification_detected', 'Unknown')
                    
                    print(f"   ✅ Success: {questions_extracted} questions, {chunks_processed} chunks")
                    print(f"   Certification detected: {certification_detected}")
                    total_questions += questions_extracted
                else:
                    print(f"   ✅ Processed successfully")
            else:
                print(f"   ❌ Failed with status: {response['StatusCode']}")
                
        except Exception as e:
            print(f"   ❌ Error processing {pdf_file}: {e}")
        
        # Small delay between files
        time.sleep(2)
    
    print(f"\n📊 Processing Summary:")
    print(f"   Total files processed: {len(pdf_files)}")
    print(f"   Total questions extracted: {total_questions}")
    
    # Wait a moment for data to propagate
    print(f"\n⏳ Waiting for data to propagate...")
    time.sleep(5)
    
    # Now test the quiz endpoint
    print(f"\n🧪 Testing Quiz Endpoint with ANS...")
    
    import requests
    
    API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    # Get a fresh token
    registration_data = {
        "email": f"ansquiztest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "ANS Quiz Test User",
        "target_certifications": ["ANS"]
    }
    
    reg_response = requests.post(
        f"{API_ENDPOINT}/auth/register",
        json=registration_data,
        headers={"Content-Type": "application/json"}
    )
    
    if reg_response.status_code != 201:
        print(f"❌ Registration failed: {reg_response.text}")
        return
    
    reg_data = json.loads(reg_response.text)
    user_id = reg_data['user_id']
    
    login_response = requests.post(
        f"{API_ENDPOINT}/auth/login",
        json={
            "email": registration_data['email'],
            "password": registration_data['password']
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = json.loads(login_response.text)
    access_token = login_data['tokens']['access_token']
    
    # Test quiz generation
    quiz_data = {
        "user_id": user_id,
        "certification_type": "ANS",
        "question_count": 5,
        "difficulty": "mixed"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    quiz_response = requests.post(
        f"{API_ENDPOINT}/quiz/generate",
        json=quiz_data,
        headers=headers
    )
    
    print(f"Quiz Status: {quiz_response.status_code}")
    print(f"Quiz Response: {quiz_response.text}")
    
    if quiz_response.status_code == 200:
        print("\n🎉 SUCCESS! Quiz generated with ANS questions!")
        quiz_result = json.loads(quiz_response.text)
        if 'quiz' in quiz_result and 'questions' in quiz_result['quiz']:
            questions = quiz_result['quiz']['questions']
            print(f"Generated {len(questions)} questions:")
            for i, q in enumerate(questions, 1):
                print(f"   {i}. {q.get('question_text', 'N/A')[:100]}...")
    else:
        print(f"\n❌ Quiz generation failed")

if __name__ == "__main__":
    process_all_ans_files()
#!/usr/bin/env python3
"""
Test just the question extraction part without embeddings to avoid Bedrock throttling.
"""

import boto3
import json
import io
from pypdf import PdfReader
import re
from typing import List, Dict, Any

def extract_questions_and_answers(text: str, certification_type: str) -> List[Dict[str, Any]]:
    """
    Extract questions and answers from content with certification context.
    Enhanced to handle AWS sample questions format.
    """
    questions = []
    
    # AWS Sample Questions Format Pattern
    aws_pattern = r'(\d+)\)\s*(.+?)(?=\s*A\))\s*A\)\s*(.+?)(?=\s*B\))\s*B\)\s*(.+?)(?=\s*C\))\s*C\)\s*(.+?)(?=\s*D\))\s*D\)\s*(.+?)(?=\s*(?:\d+\)|Answer:|Domain:|$))'
    
    print(f"Extracting questions using AWS format pattern...")
    matches = re.finditer(aws_pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            question_number = match.group(1).strip()
            question_text = match.group(2).strip()
            option_a = match.group(3).strip()
            option_b = match.group(4).strip()
            option_c = match.group(5).strip()
            option_d = match.group(6).strip()
            
            # Clean up question text
            question_lines = question_text.split('\n')
            clean_question = ""
            for line in question_lines:
                line = line.strip()
                if line:
                    clean_question += line + " "
            
            clean_question = clean_question.strip()
            
            # Ensure question ends with a question mark or add context
            if not clean_question.endswith('?'):
                question_indicators = ['Which', 'What', 'How', 'Where', 'When', 'Why']
                last_sentence = clean_question.split('.')[-1].strip()
                if any(indicator in last_sentence for indicator in question_indicators):
                    clean_question = last_sentence + "?"
                else:
                    clean_question += " Which solution will meet these requirements?"
            
            # Clean up options
            options = []
            for opt in [option_a, option_b, option_c, option_d]:
                clean_opt = ' '.join(opt.split())
                if clean_opt:
                    options.append(clean_opt)
            
            if len(options) >= 4 and len(clean_question) > 20:
                question_data = {
                    'question_text': clean_question,
                    'answer_options': options,
                    'certification_type': certification_type,
                    'question_type': 'multiple_choice',
                    'extracted_by': 'aws_format_enhanced',
                    'question_number': question_number
                }
                questions.append(question_data)
                print(f"Extracted Q{question_number}: {clean_question[:100]}...")
                
        except (IndexError, AttributeError) as e:
            print(f"Error processing question match: {e}")
            continue
    
    print(f"Extracted {len(questions)} questions for {certification_type}")
    return questions

def test_question_extraction_only():
    """Test question extraction without embeddings."""
    print("🧪 Testing Question Extraction Only (No Embeddings)...")
    
    s3_client = boto3.client('s3')
    
    # Get the ANS bucket
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
    
    # Download and process the sample questions PDF
    sample_file = "AWS-Certified-Advanced-Networking-Specialty_Sample-Questions.pdf"
    
    try:
        print(f"Downloading {sample_file}...")
        response = s3_client.get_object(Bucket=ans_bucket, Key=sample_file)
        pdf_content = response['Body'].read()
        
        # Parse the PDF
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        print(f"PDF has {len(pdf_reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            full_text += page_text + "\n"
        
        print(f"Total text length: {len(full_text)} characters")
        
        # Extract questions
        questions = extract_questions_and_answers(full_text, "ANS")
        
        if questions:
            print(f"\n✅ Successfully extracted {len(questions)} questions!")
            
            # Show first few questions
            for i, q in enumerate(questions[:3], 1):
                print(f"\n📋 Question {i}:")
                print(f"   Number: {q['question_number']}")
                print(f"   Text: {q['question_text'][:200]}...")
                print(f"   Options: {len(q['answer_options'])}")
                for j, option in enumerate(q['answer_options']):
                    print(f"      {chr(65+j)}) {option[:100]}...")
            
            # Now try to save to DynamoDB without embeddings
            print(f"\n💾 Attempting to save questions to DynamoDB...")
            
            dynamodb = boto3.resource('dynamodb')
            tables = list(dynamodb.tables.all())
            content_table = None
            
            for table in tables:
                if 'content-metadata' in table.name.lower():
                    content_table = table
                    break
            
            if content_table:
                # Create content metadata entry
                from datetime import datetime
                import uuid
                
                content_id = f"content-{sample_file.replace('.pdf', '')}-{hash(sample_file) % 1000000}"
                
                content_metadata = {
                    'content_id': content_id,
                    'certification_type': 'ANS',
                    'title': 'AWS Advanced Networking Specialty Sample Questions',
                    'content_type': 'practice_exam',
                    'category': 'Sample Questions',
                    'difficulty_level': 'advanced',
                    'source_file': sample_file,
                    'source_bucket': ans_bucket,
                    'question_count': len(questions),
                    'chunk_count': 0,  # No chunks since we're skipping embeddings
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'version': '1.0',
                    'tags': ['ans', 'networking', 'specialty', 'sample', 'questions']
                }
                
                try:
                    content_table.put_item(Item=content_metadata)
                    print(f"✅ Saved content metadata to DynamoDB!")
                    print(f"   Content ID: {content_id}")
                    print(f"   Questions: {len(questions)}")
                    
                    # Now test the quiz endpoint
                    print(f"\n🧪 Testing quiz endpoint with ANS...")
                    
                    import requests
                    import time
                    
                    API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
                    
                    # Get a fresh token
                    registration_data = {
                        "email": f"anstest{int(time.time())}@example.com",
                        "password": "TestPass123!",
                        "name": "ANS Test User",
                        "target_certifications": ["ANS"]
                    }
                    
                    reg_response = requests.post(
                        f"{API_ENDPOINT}/auth/register",
                        json=registration_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if reg_response.status_code == 201:
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
                        
                        if login_response.status_code == 200:
                            login_data = json.loads(login_response.text)
                            access_token = login_data['tokens']['access_token']
                            
                            # Test quiz generation
                            quiz_data = {
                                "user_id": user_id,
                                "certification_type": "ANS",
                                "question_count": 3,
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
                            else:
                                print(f"\n❌ Quiz generation failed")
                        else:
                            print(f"❌ Login failed: {login_response.text}")
                    else:
                        print(f"❌ Registration failed: {reg_response.text}")
                    
                except Exception as e:
                    print(f"❌ Error saving to DynamoDB: {e}")
            else:
                print("❌ Content metadata table not found!")
        else:
            print("❌ No questions extracted!")
            
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")

if __name__ == "__main__":
    test_question_extraction_only()
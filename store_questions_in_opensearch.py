#!/usr/bin/env python3
"""
Store extracted ANS questions directly in OpenSearch without embeddings.
"""

import boto3
import json
import io
from pypdf import PdfReader
import re
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def extract_questions_and_answers(text: str, certification_type: str) -> List[Dict[str, Any]]:
    """Extract questions from AWS sample format."""
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
                if line and not line.startswith('©') and 'aws.amazon.com' not in line and 'P a g e' not in line:
                    clean_question += line + " "
            
            clean_question = clean_question.strip()
            
            # Find the actual question part
            if 'Which solution will meet these requirements?' in clean_question:
                parts = clean_question.split('Which solution will meet these requirements?')
                if len(parts) > 1:
                    clean_question = parts[0].strip() + " Which solution will meet these requirements?"
            elif not clean_question.endswith('?'):
                clean_question += " Which solution will meet these requirements?"
            
            # Clean up options
            options = []
            for opt in [option_a, option_b, option_c, option_d]:
                clean_opt = ' '.join(opt.split())
                # Remove page headers and footers
                if clean_opt and not clean_opt.startswith('©') and 'aws.amazon.com' not in clean_opt and 'P a g e' not in clean_opt:
                    options.append(clean_opt)
            
            if len(options) >= 4 and len(clean_question) > 50:
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

def store_questions_in_opensearch():
    """Store questions directly in OpenSearch."""
    print("📊 Storing ANS Questions in OpenSearch...")
    
    # Set up OpenSearch client
    opensearch_endpoint = "https://ik9o77ze3heg82r8yau7.us-east-1.aoss.amazonaws.com"
    host = opensearch_endpoint.replace("https://", "")
    
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')
    
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_timeout=30
    )
    
    # Get and process the PDF
    s3_client = boto3.client('s3')
    ans_bucket = "procert-materials-ans-353207798766"
    sample_file = "AWS-Certified-Advanced-Networking-Specialty_Sample-Questions.pdf"
    
    try:
        print(f"Downloading {sample_file}...")
        response = s3_client.get_object(Bucket=ans_bucket, Key=sample_file)
        pdf_content = response['Body'].read()
        
        # Parse PDF
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        full_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            full_text += page_text + "\n"
        
        # Extract questions
        questions = extract_questions_and_answers(full_text, "ANS")
        
        if not questions:
            print("❌ No questions extracted!")
            return
        
        print(f"✅ Extracted {len(questions)} questions")
        
        # Store each question as a separate document in OpenSearch
        index_name = "procert-vector-collection"
        
        for i, question in enumerate(questions):
            try:
                # Create document for OpenSearch
                doc = {
                    "content_id": f"ans-question-{question['question_number']}-{i}",
                    "text": question['question_text'],
                    "content_type": "question",  # This is what the quiz service looks for
                    "certification_type": "ANS",
                    "category": "sample_questions",
                    "difficulty": "advanced",
                    "metadata": {
                        "question_text": question['question_text'],
                        "answer_options": question['answer_options'],
                        "question_type": question['question_type'],
                        "question_number": question['question_number'],
                        "source_file": sample_file
                    }
                }
                
                # Index the document (let OpenSearch auto-generate ID)
                response = opensearch_client.index(
                    index=index_name,
                    body=doc
                )
                
                print(f"✅ Stored question {question['question_number']} in OpenSearch")
                
            except Exception as e:
                print(f"❌ Error storing question {i}: {e}")
        
        print(f"\n📊 Storage Summary:")
        print(f"   Questions processed: {len(questions)}")
        
        # Verify storage by searching
        print(f"\n🔍 Verifying storage...")
        
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"content_type": "question"}},
                        {"term": {"certification_type": "ANS"}}
                    ]
                }
            },
            "size": 20
        }
        
        search_response = opensearch_client.search(
            index=index_name,
            body=search_query
        )
        
        total_hits = search_response['hits']['total']['value']
        print(f"✅ Found {total_hits} ANS questions in OpenSearch")
        
        if total_hits > 0:
            print(f"\n🧪 Testing quiz endpoint...")
            
            import requests
            import time
            
            API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
            
            # Get a fresh token
            registration_data = {
                "email": f"ansopensearch{int(time.time())}@example.com",
                "password": "TestPass123!",
                "name": "ANS OpenSearch Test User",
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
                        quiz_result = json.loads(quiz_response.text)
                        if 'quiz' in quiz_result and 'questions' in quiz_result['quiz']:
                            questions_generated = quiz_result['quiz']['questions']
                            print(f"Generated {len(questions_generated)} questions:")
                            for i, q in enumerate(questions_generated, 1):
                                print(f"   {i}. {q.get('question_text', 'N/A')[:100]}...")
                    else:
                        print(f"\n❌ Quiz generation failed")
                else:
                    print(f"❌ Login failed: {login_response.text}")
            else:
                print(f"❌ Registration failed: {reg_response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    store_questions_in_opensearch()
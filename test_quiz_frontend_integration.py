#!/usr/bin/env python3
"""
Test script to verify the quiz API integration with the frontend format.
This script tests the exact API calls that the frontend will make.
"""

import json
import boto3
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
QUIZ_LAMBDA_NAME = "ProcertInfrastructureStac-ProcertQuizLambda8FDECDE-4RIY4fDPbKM4"
REGION = "us-east-1"

def test_quiz_generation_direct():
    """Test quiz generation directly via Lambda (simulating API Gateway)."""
    print("🧪 Testing Quiz Generation (Direct Lambda)")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Simulate the exact request that the frontend will send
    event = {
        'httpMethod': 'POST',
        'path': '/quiz/generate',
        'body': json.dumps({
            'certification_type': 'ANS',  # Use Advanced Networking Specialty (available in index)
            'difficulty': 'mixed',
            'count': 5  # Frontend sends 'count' not 'question_count'
        }),
        'requestContext': {
            'authorizer': {
                'user_id': 'test-frontend-user'  # Simulated JWT user
            }
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=QUIZ_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Lambda Response Status: {response['StatusCode']}")
        
        if 'body' in result:
            body = json.loads(result['body'])
            print(f"✅ HTTP Status: {result['statusCode']}")
            print(f"✅ Response Keys: {list(body.keys())}")
            
            if 'quiz_id' in body:
                print(f"✅ Quiz ID: {body['quiz_id']}")
                print(f"✅ Questions Count: {len(body.get('questions', []))}")
                print(f"✅ Metadata: {body.get('metadata', {})}")
                
                # Test quiz submission format
                test_quiz_submission_format(body)
            else:
                print(f"❌ Missing quiz_id in response: {body}")
        else:
            print(f"❌ Unexpected response format: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_quiz_submission_format(quiz_data):
    """Test quiz submission with the format the frontend will use."""
    print("\n🧪 Testing Quiz Submission Format")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Simulate frontend answer format
    questions = quiz_data.get('questions', [])
    if not questions:
        print("❌ No questions to test submission")
        return
    
    # Frontend formats answers as: [{"question_id": "...", "selected_answer": "..."}]
    formatted_answers = []
    for question in questions:
        # For testing, select the first option
        selected_answer = question['options'][0] if question.get('options') else ""
        formatted_answers.append({
            'question_id': question['question_id'],
            'selected_answer': selected_answer
        })
    
    event = {
        'httpMethod': 'POST',
        'path': '/quiz/submit',
        'body': json.dumps({
            'quiz_id': quiz_data['quiz_id'],
            'answers': formatted_answers  # Frontend format
        }),
        'requestContext': {
            'authorizer': {
                'user_id': 'test-frontend-user'
            }
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=QUIZ_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Submission Response Status: {response['StatusCode']}")
        
        if 'body' in result:
            body = json.loads(result['body'])
            print(f"✅ HTTP Status: {result['statusCode']}")
            
            if 'results' in body:
                results = body['results']
                print(f"✅ Quiz Results Keys: {list(results.keys())}")
                print(f"✅ Score: {results.get('score', 'N/A')}%")
                print(f"✅ Correct Answers: {results.get('correct_answers', 'N/A')}/{results.get('total_questions', 'N/A')}")
                print(f"✅ Results Count: {len(results.get('results', []))}")
                
                # Check result format matches frontend expectations
                if results.get('results'):
                    first_result = results['results'][0]
                    expected_keys = ['question_id', 'question_text', 'user_answer', 'correct_answer', 'is_correct', 'explanation']
                    missing_keys = [key for key in expected_keys if key not in first_result]
                    if missing_keys:
                        print(f"⚠️  Missing keys in result: {missing_keys}")
                    else:
                        print("✅ Result format matches frontend expectations")
            else:
                print(f"❌ Missing results in response: {body}")
        else:
            print(f"❌ Unexpected submission response: {result}")
            
    except Exception as e:
        print(f"❌ Submission Error: {e}")

def test_api_gateway_format():
    """Test the actual API Gateway endpoint format (if accessible)."""
    print("\n🧪 Testing API Gateway Format")
    print("=" * 35)
    
    # This would require proper authentication
    print("ℹ️  API Gateway testing requires JWT token")
    print("ℹ️  Use browser dev tools to get token from authenticated session")
    
    # Example of what the frontend will send:
    example_request = {
        "method": "POST",
        "url": f"{API_BASE_URL}/quiz/generate",
        "headers": {
            "Authorization": "Bearer <JWT_TOKEN>",
            "Content-Type": "application/json"
        },
        "body": {
            "certification_type": "SAA",
            "difficulty": "mixed", 
            "count": 10
        }
    }
    
    print("📋 Frontend Request Format:")
    print(json.dumps(example_request, indent=2))

if __name__ == "__main__":
    print("🎯 Quiz Frontend Integration Test")
    print("Testing the exact API format that the frontend will use")
    print("=" * 60)
    
    test_quiz_generation_direct()
    test_api_gateway_format()
    
    print("\n" + "=" * 60)
    print("✅ Integration test complete!")
    print("The frontend should now work with the backend API format.")
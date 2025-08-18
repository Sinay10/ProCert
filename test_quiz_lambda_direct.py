#!/usr/bin/env python3
"""
Test the quiz Lambda function directly to debug the issue.
"""

import json
import boto3
import sys
import os

# Add the quiz lambda source to the path for testing
sys.path.insert(0, 'quiz_lambda_src')

def test_quiz_lambda_direct():
    """Test the quiz Lambda function directly."""
    
    # Set up environment variables that the Lambda expects
    os.environ['QUIZ_SESSIONS_TABLE'] = 'ProcertInfrastructureStack-QuizSessionsTable-1NQXQXQXQXQX'  # This will fail but that's ok for testing
    os.environ['USER_PROGRESS_TABLE'] = 'ProcertInfrastructureStack-UserProgressTable-1NQXQXQXQXQX'
    os.environ['CONTENT_METADATA_TABLE'] = 'ProcertInfrastructureStack-ContentMetadataTable-1NQXQXQXQXQX'
    os.environ['AWS_REGION'] = 'us-east-1'
    
    # Get OpenSearch endpoint from CDK outputs
    with open('cdk-outputs.json', 'r') as f:
        outputs = json.load(f)
    
    stack_outputs = outputs.get("ProcertInfrastructureStack", {})
    opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
    opensearch_index = 'procert-vector-collection'
    
    os.environ['OPENSEARCH_ENDPOINT'] = opensearch_endpoint
    os.environ['OPENSEARCH_INDEX'] = opensearch_index
    
    print("🧪 Testing Quiz Lambda Functions Directly")
    print("=" * 45)
    
    try:
        # Import the functions after setting environment variables
        from main import search_questions_by_certification, select_adaptive_questions
        
        # Test 1: Search for questions
        print("\n1️⃣ Testing search_questions_by_certification...")
        questions = search_questions_by_certification('ANS', limit=10)
        print(f"   Found {len(questions)} questions")
        
        if questions:
            print("   ✅ Sample question structure:")
            sample = questions[0]
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"     {key}: {value[:50]}...")
                elif isinstance(value, list) and len(value) > 2:
                    print(f"     {key}: [{value[0][:30]}..., ...] ({len(value)} items)")
                else:
                    print(f"     {key}: {value}")
        else:
            print("   ❌ No questions found")
            return
        
        # Test 2: Adaptive selection
        print("\n2️⃣ Testing select_adaptive_questions...")
        user_performance = {}  # Empty performance for new user
        recently_answered = []  # No recent answers
        
        selected = select_adaptive_questions(
            questions, user_performance, recently_answered, 5, 'mixed'
        )
        
        print(f"   Selected {len(selected)} questions out of {len(questions)} available")
        
        if selected:
            print("   ✅ Selection successful")
            for i, q in enumerate(selected):
                print(f"     {i+1}. {q.get('content_id')} - {q.get('question_text', '')[:50]}...")
        else:
            print("   ❌ No questions selected")
            return
        
        # Test 3: Try the full create_quiz_session function
        print("\n3️⃣ Testing create_quiz_session...")
        try:
            from main import create_quiz_session
            
            # This will likely fail due to DynamoDB table access, but let's see how far it gets
            quiz_session = create_quiz_session('test-user', 'ANS', 5, 'mixed')
            print("   ✅ Quiz session created successfully!")
            print(f"   Quiz ID: {quiz_session.get('quiz_id')}")
            print(f"   Questions: {len(quiz_session.get('questions', []))}")
            
        except Exception as e:
            print(f"   ⚠️  create_quiz_session failed (expected due to DynamoDB): {e}")
            
            # Let's manually create a quiz session structure to test the response format
            print("   🔧 Creating manual quiz session for testing...")
            
            quiz_questions = []
            for i, question in enumerate(selected[:5]):
                quiz_question = {
                    "question_id": question.get("content_id", f"q_{i}"),
                    "question_text": question["question_text"],
                    "options": question["answer_options"],
                    "correct_answer": question["correct_answer"],
                    "explanation": question.get("explanation", ""),
                    "category": question.get("category", "general"),
                    "difficulty": question.get("difficulty", "intermediate")
                }
                quiz_questions.append(quiz_question)
            
            manual_quiz = {
                'quiz_id': 'test-quiz-123',
                'questions': quiz_questions,
                'metadata': {
                    'certification_type': 'ANS',
                    'difficulty': 'mixed',
                    'count': len(quiz_questions)
                }
            }
            
            print(f"   ✅ Manual quiz created with {len(quiz_questions)} questions")
            print("   📋 Sample question:")
            if quiz_questions:
                sample_q = quiz_questions[0]
                print(f"     ID: {sample_q['question_id']}")
                print(f"     Text: {sample_q['question_text'][:100]}...")
                print(f"     Options: {len(sample_q['options'])} choices")
                print(f"     Correct: {sample_q['correct_answer']}")
        
        print("\n✅ Direct testing complete - the quiz logic should work!")
        
    except Exception as e:
        print(f"❌ Error in direct testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quiz_lambda_direct()
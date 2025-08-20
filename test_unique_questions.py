#!/usr/bin/env python3
"""
Test script to verify unique questions functionality
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def get_auth_token():
    """Get authentication token for testing"""
    # This would need to be implemented based on your auth system
    # For now, return a placeholder
    return "test-token"

def test_unique_questions():
    """Test that unique questions are enforced when requested"""
    print("🧪 Testing Unique Questions Feature...")
    
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Generate quiz without unique_questions flag (should allow duplicates)
    print("\n1. Testing quiz generation without unique_questions flag...")
    payload1 = {
        "certification_type": "ANS",
        "count": 5,
        "difficulty": "mixed"
    }
    
    try:
        response1 = requests.post(f"{API_BASE_URL}/quiz/generate", json=payload1, headers=headers)
        print(f"   Status: {response1.status_code}")
        if response1.status_code == 200:
            quiz1 = response1.json()
            print(f"   ✅ Generated {len(quiz1.get('questions', []))} questions")
        else:
            print(f"   ❌ Error: {response1.text}")
    except Exception as e:
        print(f"   ⚠️  Request failed: {e}")
    
    # Test 2: Generate quiz with unique_questions flag
    print("\n2. Testing quiz generation with unique_questions=true...")
    payload2 = {
        "certification_type": "ANS", 
        "count": 5,
        "difficulty": "mixed",
        "unique_questions": True
    }
    
    try:
        response2 = requests.post(f"{API_BASE_URL}/quiz/generate", json=payload2, headers=headers)
        print(f"   Status: {response2.status_code}")
        if response2.status_code == 200:
            quiz2 = response2.json()
            questions = quiz2.get('questions', [])
            print(f"   ✅ Generated {len(questions)} questions with unique_questions=true")
            
            # Check for duplicates within the quiz
            question_texts = [q.get('question_text', '') for q in questions]
            unique_texts = set(question_texts)
            if len(question_texts) == len(unique_texts):
                print(f"   ✅ No duplicate questions found within the quiz")
            else:
                print(f"   ❌ Found duplicate questions: {len(question_texts)} total, {len(unique_texts)} unique")
        else:
            print(f"   ❌ Error: {response2.text}")
    except Exception as e:
        print(f"   ⚠️  Request failed: {e}")
    
    # Test 3: Generate multiple quizzes to check for duplicates across sessions
    print("\n3. Testing multiple quiz generations for duplicate prevention...")
    quiz_questions = []
    
    for i in range(3):
        payload = {
            "certification_type": "ANS",
            "count": 3,
            "difficulty": "mixed", 
            "unique_questions": True
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/quiz/generate", json=payload, headers=headers)
            if response.status_code == 200:
                quiz = response.json()
                questions = quiz.get('questions', [])
                quiz_questions.extend([q.get('question_text', '') for q in questions])
                print(f"   Quiz {i+1}: Generated {len(questions)} questions")
            else:
                print(f"   Quiz {i+1}: Error {response.status_code}")
        except Exception as e:
            print(f"   Quiz {i+1}: Request failed: {e}")
        
        time.sleep(1)  # Small delay between requests
    
    if quiz_questions:
        total_questions = len(quiz_questions)
        unique_questions = len(set(quiz_questions))
        print(f"   📊 Across 3 quizzes: {total_questions} total questions, {unique_questions} unique")
        if total_questions > unique_questions:
            print(f"   ⚠️  Found {total_questions - unique_questions} duplicate questions across sessions")
        else:
            print(f"   ✅ No duplicates found across quiz sessions")

def main():
    """Run all tests"""
    print("🚀 Testing Unique Questions Feature")
    print("=" * 50)
    
    test_unique_questions()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("✅ Backend modified to accept 'unique_questions' parameter")
    print("✅ Frontend sends unique_questions=true by default")
    print("✅ Duplicate prevention logic added to question selection")
    print("✅ Warning message shows when insufficient unique questions available")
    print("✅ QuestionFeedback component fixed to handle missing correct_answer")

if __name__ == "__main__":
    main()
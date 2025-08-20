#!/usr/bin/env python3
"""
Test script to verify immediate feedback functionality
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_immediate_feedback():
    """Test that quiz questions now include correct answers for immediate feedback"""
    print("🧪 Testing Immediate Feedback Feature...")
    
    # This would need proper authentication in a real test
    headers = {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }
    
    payload = {
        "certification_type": "ANS",
        "count": 3,
        "difficulty": "mixed",
        "unique_questions": True
    }
    
    try:
        print("\n1. Generating quiz to check if correct answers are included...")
        response = requests.post(f"{API_BASE_URL}/quiz/generate", json=payload, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get('questions', [])
            
            print(f"   ✅ Quiz generated with {len(questions)} questions")
            
            # Check if correct answers are included
            has_correct_answers = True
            for i, question in enumerate(questions):
                correct_answer = question.get('correct_answer')
                if not correct_answer:
                    has_correct_answers = False
                    print(f"   ❌ Question {i+1} missing correct_answer")
                else:
                    print(f"   ✅ Question {i+1} has correct_answer: {correct_answer}")
            
            if has_correct_answers:
                print(f"\n   🎉 SUCCESS: All questions include correct answers!")
                print(f"   📚 This enables immediate learning feedback")
            else:
                print(f"\n   ❌ ISSUE: Some questions missing correct answers")
                
        else:
            print(f"   ❌ Quiz generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ⚠️  Request failed: {e}")

def main():
    """Run the test"""
    print("🚀 Testing Immediate Feedback Feature")
    print("=" * 50)
    
    test_immediate_feedback()
    
    print("\n" + "=" * 50)
    print("📋 Changes Made:")
    print("✅ Backend: Modified quiz generation to include correct answers")
    print("✅ Frontend: Updated QuestionFeedback to show immediate right/wrong")
    print("✅ Learning Focus: Prioritized education over anti-cheating")
    print("✅ User Experience: Immediate feedback helps learning")
    
    print("\n🎯 Benefits:")
    print("• Users get instant feedback on their answers")
    print("• Wrong answers show explanations immediately")
    print("• Better learning experience with immediate reinforcement")
    print("• Maintains the comprehensive final results screen")

if __name__ == "__main__":
    main()
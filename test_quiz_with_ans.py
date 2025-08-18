#!/usr/bin/env python3
"""
Test quiz generation specifically with ANS certification (which has questions)
"""

import requests
import json
import uuid

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user():
    """Create a test user and get JWT token."""
    email = f"ans-quiz-test-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    # Register user
    register_response = requests.post(f"{API_BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": "ANS Quiz Test"
    })
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.text}")
        return None
    
    print(f"✅ User registered successfully")
    
    # Login to get token
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return None
    
    token = login_response.json()["tokens"]["access_token"]
    user_id = login_response.json()["user_id"]
    
    print(f"✅ Created test user: {user_id}")
    return token

def test_ans_quiz_generation():
    """Test quiz generation with ANS certification."""
    print("🧪 Testing ANS Quiz Generation")
    print("=" * 40)
    
    # Get JWT token
    token = create_test_user()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test ANS quiz generation
    quiz_payload = {
        "certification_type": "ANS",
        "difficulty": "mixed",
        "count": 5
    }
    
    print(f"📝 Generating ANS quiz with payload: {quiz_payload}")
    
    response = requests.post(
        f"{API_BASE_URL}/quiz/generate",
        headers=headers,
        json=quiz_payload,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        quiz_data = response.json()
        print("✅ Quiz generated successfully!")
        print(f"   Quiz ID: {quiz_data.get('quiz_id')}")
        print(f"   Questions: {len(quiz_data.get('questions', []))}")
        
        # Show first question
        questions = quiz_data.get('questions', [])
        if questions:
            first_q = questions[0]
            print(f"   First question preview: {first_q.get('question_text', '')[:100]}...")
            print(f"   Answer options: {len(first_q.get('answer_options', []))}")
    else:
        print(f"❌ Quiz generation failed: {response.text}")

if __name__ == "__main__":
    test_ans_quiz_generation()
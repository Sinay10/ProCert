#!/usr/bin/env python3
"""
Comprehensive test script for all ProCert Learning Platform features
Tests: Recommendation Engine, Progress Tracking, Chatbot, Quiz Generation
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://api.procert.ai"
TEST_USER_ID = "test-user-comprehensive"

def get_auth_token():
    """Get authentication token"""
    auth_url = f"{BASE_URL}/auth"
    auth_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_recommendation_engine(token):
    """Test all recommendation engine endpoints"""
    print("\n🔍 Testing Recommendation Engine...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Get personalized recommendations
    print("  Testing personalized recommendations...")
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/{TEST_USER_ID}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Got {len(data.get('recommendations', []))} recommendations")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Get weak areas
    print("  Testing weak area identification...")
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/{TEST_USER_ID}/weak-areas",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Identified {len(data.get('weak_areas', []))} weak areas")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 3: Get content progression
    print("  Testing content progression...")
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/{TEST_USER_ID}/progression",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Got progression for {len(data.get('progression', []))} topics")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 4: Generate study path
    print("  Testing study path generation...")
    try:
        response = requests.post(
            f"{BASE_URL}/recommendations/{TEST_USER_ID}/study-path",
            headers=headers,
            json={"target_certification": "AWS Solutions Architect"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Generated study path with {len(data.get('study_path', []))} steps")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 5: Record feedback
    print("  Testing feedback recording...")
    try:
        response = requests.post(
            f"{BASE_URL}/recommendations/{TEST_USER_ID}/feedback",
            headers=headers,
            json={
                "content_id": "test-content-123",
                "rating": 5,
                "feedback_type": "helpful"
            }
        )
        if response.status_code == 200:
            print(f"    ✅ Feedback recorded successfully")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_progress_tracking(token):
    """Test progress tracking functionality"""
    print("\n📊 Testing Progress Tracking...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Record progress
    print("  Testing progress recording...")
    try:
        response = requests.post(
            f"{BASE_URL}/progress",
            headers=headers,
            json={
                "user_id": TEST_USER_ID,
                "content_id": "test-content-progress",
                "content_type": "lesson",
                "score": 85,
                "time_spent": 1800,
                "completed": True
            }
        )
        if response.status_code == 200:
            print(f"    ✅ Progress recorded successfully")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Get user progress
    print("  Testing progress retrieval...")
    try:
        response = requests.get(
            f"{BASE_URL}/progress/{TEST_USER_ID}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Retrieved progress for {len(data.get('progress', []))} items")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 3: Get certification readiness
    print("  Testing certification readiness...")
    try:
        response = requests.get(
            f"{BASE_URL}/progress/{TEST_USER_ID}/readiness/AWS Solutions Architect",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            readiness = data.get('readiness_score', 0)
            print(f"    ✅ Certification readiness: {readiness}%")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_chatbot(token):
    """Test chatbot functionality"""
    print("\n🤖 Testing Chatbot...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test chatbot query
    print("  Testing chatbot query...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json={
                "message": "What is AWS Lambda?",
                "user_id": TEST_USER_ID,
                "context": "AWS certification study"
            }
        )
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            print(f"    ✅ Chatbot responded with {len(response_text)} characters")
            print(f"    Response preview: {response_text[:100]}...")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_quiz_generation(token):
    """Test quiz generation functionality"""
    print("\n📝 Testing Quiz Generation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test quiz generation
    print("  Testing quiz generation...")
    try:
        response = requests.post(
            f"{BASE_URL}/quiz/generate",
            headers=headers,
            json={
                "topic": "AWS Lambda",
                "difficulty": "intermediate",
                "num_questions": 5,
                "question_types": ["multiple_choice", "true_false"]
            }
        )
        if response.status_code == 200:
            data = response.json()
            questions = data.get('questions', [])
            print(f"    ✅ Generated {len(questions)} quiz questions")
            
            # Show first question as example
            if questions:
                first_q = questions[0]
                print(f"    Example question: {first_q.get('question', '')[:80]}...")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test quiz submission
    print("  Testing quiz submission...")
    try:
        response = requests.post(
            f"{BASE_URL}/quiz/submit",
            headers=headers,
            json={
                "user_id": TEST_USER_ID,
                "quiz_id": "test-quiz-123",
                "answers": [
                    {"question_id": "q1", "answer": "A"},
                    {"question_id": "q2", "answer": "True"},
                    {"question_id": "q3", "answer": "B"}
                ]
            }
        )
        if response.status_code == 200:
            data = response.json()
            score = data.get('score', 0)
            print(f"    ✅ Quiz submitted, score: {score}%")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_content_search(token):
    """Test content search functionality"""
    print("\n🔍 Testing Content Search...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test content search
    print("  Testing content search...")
    try:
        response = requests.get(
            f"{BASE_URL}/search",
            headers=headers,
            params={
                "query": "AWS Lambda functions",
                "content_type": "lesson",
                "limit": 10
            }
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"    ✅ Found {len(results)} search results")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def main():
    """Run comprehensive feature tests"""
    print("🚀 Starting Comprehensive ProCert Feature Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Run all tests
    test_recommendation_engine(token)
    test_progress_tracking(token)
    test_chatbot(token)
    test_quiz_generation(token)
    test_content_search(token)
    
    print("\n" + "=" * 60)
    print("🏁 Comprehensive testing completed!")
    print("Check the results above for any failed tests.")

if __name__ == "__main__":
    main()
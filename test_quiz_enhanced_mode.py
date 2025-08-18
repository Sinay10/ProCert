#!/usr/bin/env python3
"""
Test the enhanced quiz generation mode with multiple certification types
"""

import requests
import json
import uuid

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_test_user():
    """Create a test user and get JWT token."""
    email = f"enhanced-quiz-test-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    # Register user
    register_response = requests.post(f"{API_BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": "Enhanced Quiz Test"
    })
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.text}")
        return None
    
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

def test_quiz_generation(certification_type, count=3):
    """Test quiz generation for a specific certification type."""
    print(f"\n🧪 Testing {certification_type} Quiz Generation")
    print("=" * 50)
    
    # Get JWT token
    token = create_test_user()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test quiz generation
    quiz_payload = {
        "certification_type": certification_type,
        "difficulty": "mixed",
        "count": count
    }
    
    print(f"📝 Generating {certification_type} quiz with {count} questions...")
    
    response = requests.post(
        f"{API_BASE_URL}/quiz/generate",
        headers=headers,
        json=quiz_payload,
        timeout=60  # Increased timeout for Bedrock generation
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        quiz_data = response.json()
        print("✅ Quiz generated successfully!")
        print(f"   Quiz ID: {quiz_data.get('quiz_id')}")
        print(f"   Questions: {len(quiz_data.get('questions', []))}")
        
        # Show first question details
        questions = quiz_data.get('questions', [])
        if questions:
            first_q = questions[0]
            print(f"   First question preview: {first_q.get('question_text', '')[:100]}...")
            print(f"   Answer options: {len(first_q.get('options', []))}")
            print(f"   Category: {first_q.get('category', 'N/A')}")
            print(f"   Difficulty: {first_q.get('difficulty', 'N/A')}")
        
        return True
    else:
        print(f"❌ Quiz generation failed: {response.text}")
        return False

def main():
    """Test enhanced quiz generation for multiple certification types."""
    print("🚀 Testing Enhanced Quiz Generation Mode")
    print("=" * 60)
    
    # Test different certification types
    certification_types = ['ANS', 'SAA', 'DVA', 'CCP', 'SOA']
    
    results = {}
    for cert_type in certification_types:
        results[cert_type] = test_quiz_generation(cert_type, count=3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ENHANCED MODE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for cert_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {cert_type} Quiz Generation")
    
    print(f"\nOverall: {passed}/{total} certification types working ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Enhanced mode is working perfectly for all certification types!")
    else:
        print("⚠️  Some certification types need attention.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test quiz endpoint directly without authorization to see what happens.
"""

import requests
import json

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_quiz_endpoint_direct():
    """Test quiz endpoint without authorization."""
    print("🔍 Testing Quiz Endpoint Directly (No Auth)")
    print("=" * 50)
    
    # Test without any authorization
    quiz_data = {
        "user_id": "test-user",
        "certification_type": "SAA",
        "question_count": 5
    }
    
    print("Testing /quiz/generate without authorization...")
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/quiz/generate",
            json=quiz_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            if "Missing Authentication Token" in response.text:
                print("❌ Endpoint doesn't exist or isn't deployed")
            elif "Unauthorized" in response.text or "User is not authorized" in response.text:
                print("✅ Endpoint exists, authorizer is working")
            else:
                print("🤔 Unknown 403 error")
        elif response.status_code == 401:
            print("✅ Endpoint exists, needs authorization")
        else:
            print(f"🤔 Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quiz_endpoint_direct()
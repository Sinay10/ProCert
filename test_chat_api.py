#!/usr/bin/env python3

import requests
import json

# Test the chat API endpoint
api_base = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def test_chat_endpoint():
    """Test the chat message endpoint"""
    url = f"{api_base}/chat/message"
    
    payload = {
        "message": "What is AWS?",
        "mode": "rag"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Testing endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.text:
            try:
                response_json = response.json()
                print(f"Response: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
        else:
            print("No response body")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_options_request():
    """Test CORS preflight request"""
    url = f"{api_base}/chat/message"
    
    headers = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    print(f"\nTesting CORS preflight: {url}")
    
    try:
        response = requests.options(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
    except requests.exceptions.RequestException as e:
        print(f"CORS request failed: {e}")

if __name__ == "__main__":
    test_options_request()
    test_chat_endpoint()
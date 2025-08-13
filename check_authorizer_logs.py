#!/usr/bin/env python3
"""
Check JWT authorizer CloudWatch logs to see what's happening during quiz endpoint calls.
"""

import boto3
import json
import time
import requests
from datetime import datetime, timedelta

API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def check_authorizer_logs():
    """Check JWT authorizer logs while making a request."""
    print("📋 Checking JWT Authorizer CloudWatch Logs...")
    
    # Find the JWT authorizer Lambda function
    lambda_client = boto3.client('lambda')
    functions = lambda_client.list_functions()['Functions']
    
    jwt_function = None
    for func in functions:
        if 'JWTAuthorizer' in func['FunctionName']:
            jwt_function = func['FunctionName']
            break
    
    if not jwt_function:
        print("❌ JWT Authorizer function not found!")
        return
    
    print(f"Found JWT Authorizer function: {jwt_function}")
    
    # Get a fresh token first
    registration_data = {
        "email": f"logtest{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Log Test User",
        "target_certifications": ["SAA"]
    }
    
    print("1. Getting fresh authentication token...")
    reg_response = requests.post(
        f"{API_ENDPOINT}/auth/register",
        json=registration_data,
        headers={"Content-Type": "application/json"}
    )
    
    if reg_response.status_code != 201:
        print(f"❌ Registration failed: {reg_response.text}")
        return
    
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
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = json.loads(login_response.text)
    access_token = login_data['tokens']['access_token']
    print(f"✅ Got fresh token: {access_token[:50]}...")
    
    # Set up CloudWatch logs client
    logs_client = boto3.client('logs')
    log_group_name = f"/aws/lambda/{jwt_function}"
    
    # Get the current time for log filtering
    start_time = datetime.utcnow()
    
    print(f"\n2. Making request to quiz endpoint at {start_time}...")
    
    # Make the request that should trigger the authorizer
    quiz_data = {
        "user_id": user_id,
        "certification_type": "SAA",
        "question_count": 5,
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
    
    # Wait a moment for logs to appear
    print("\n3. Waiting for logs to appear...")
    time.sleep(5)
    
    # Check logs from the time we made the request
    end_time = datetime.utcnow()
    
    try:
        # List recent log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        if not streams_response['logStreams']:
            print("❌ No recent log streams found")
            return
        
        print(f"Found {len(streams_response['logStreams'])} recent log streams")
        
        # Get events from the most recent streams
        for stream in streams_response['logStreams'][:2]:
            stream_name = stream['logStreamName']
            print(f"\n📋 Checking stream: {stream_name}")
            
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                events = events_response['events']
                if events:
                    print(f"Found {len(events)} log events:")
                    for event in events:
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message'].strip()
                        print(f"   {timestamp}: {message}")
                else:
                    print("   No events in this time range")
                    
            except Exception as e:
                print(f"   Error reading stream {stream_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error accessing CloudWatch logs: {e}")

if __name__ == "__main__":
    check_authorizer_logs()
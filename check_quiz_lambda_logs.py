#!/usr/bin/env python3
"""
Check CloudWatch logs for the quiz Lambda to see if it's being invoked.
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def check_quiz_lambda_logs():
    """Check CloudWatch logs for quiz Lambda invocations."""
    print("📋 Checking Quiz Lambda CloudWatch Logs...")
    
    # Find the quiz Lambda function
    lambda_client = boto3.client('lambda')
    functions = lambda_client.list_functions()['Functions']
    
    quiz_function = None
    for func in functions:
        if 'QuizLambda' in func['FunctionName']:
            quiz_function = func['FunctionName']
            break
    
    if not quiz_function:
        print("❌ Quiz Lambda function not found!")
        return
    
    print(f"Found Quiz Lambda function: {quiz_function}")
    
    # Get CloudWatch logs
    logs_client = boto3.client('logs')
    log_group_name = f"/aws/lambda/{quiz_function}"
    
    try:
        # Get log streams from the last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        print(f"Checking logs from {start_time} to {end_time}")
        
        # List log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            print("❌ No recent log streams found")
            return
        
        print(f"Found {len(streams_response['logStreams'])} recent log streams")
        
        # Get events from the most recent streams
        for stream in streams_response['logStreams'][:2]:  # Check top 2 streams
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
                    for event in events[-10:]:  # Show last 10 events
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message'].strip()
                        print(f"   {timestamp}: {message}")
                else:
                    print("   No events in this time range")
                    
            except Exception as e:
                print(f"   Error reading stream {stream_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error accessing CloudWatch logs: {e}")
        print("This might be due to permissions or the log group not existing yet")

if __name__ == "__main__":
    check_quiz_lambda_logs()
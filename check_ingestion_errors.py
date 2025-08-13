#!/usr/bin/env python3
"""
Check ingestion Lambda for errors and detailed logs.
"""

import boto3
import json
from datetime import datetime, timedelta

def check_ingestion_errors():
    """Check ingestion Lambda for errors."""
    print("🔍 Checking Ingestion Lambda for Errors...")
    
    lambda_client = boto3.client('lambda')
    
    # Find the ingestion Lambda function
    functions = lambda_client.list_functions()['Functions']
    ingestion_function = None
    
    for func in functions:
        if 'IngestionLambda' in func['FunctionName']:
            ingestion_function = func['FunctionName']
            break
    
    if not ingestion_function:
        print("❌ Ingestion Lambda function not found!")
        return
    
    print(f"Found Ingestion Lambda: {ingestion_function}")
    
    # Check CloudWatch logs for any activity in the last hour
    logs_client = boto3.client('logs')
    log_group_name = f"/aws/lambda/{ingestion_function}"
    
    try:
        # Get log streams from the last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        print(f"Checking logs from {start_time} to {end_time}")
        
        # List all log streams (not just recent ones)
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=10
        )
        
        if not streams_response['logStreams']:
            print("❌ No log streams found at all!")
            print("This suggests the ingestion Lambda has never been invoked.")
            return
        
        print(f"Found {len(streams_response['logStreams'])} log streams")
        
        # Check each stream for any events
        found_events = False
        for i, stream in enumerate(streams_response['logStreams']):
            stream_name = stream['logStreamName']
            last_event_time = stream.get('lastEventTime')
            
            if last_event_time:
                last_event_dt = datetime.fromtimestamp(last_event_time / 1000)
                print(f"\n📋 Stream {i+1}: {stream_name}")
                print(f"   Last event: {last_event_dt}")
                
                try:
                    # Get all events from this stream (not time-filtered)
                    events_response = logs_client.get_log_events(
                        logGroupName=log_group_name,
                        logStreamName=stream_name
                    )
                    
                    events = events_response['events']
                    if events:
                        found_events = True
                        print(f"   Found {len(events)} events:")
                        
                        # Show recent events
                        for event in events[-10:]:  # Last 10 events
                            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                            message = event['message'].strip()
                            
                            # Highlight errors
                            if any(keyword in message.lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                                print(f"   🔴 {timestamp}: {message}")
                            else:
                                print(f"   📝 {timestamp}: {message}")
                    else:
                        print("   No events in this stream")
                        
                except Exception as e:
                    print(f"   Error reading stream: {e}")
        
        if not found_events:
            print("\n❌ No events found in any log streams!")
            print("The ingestion Lambda may not have been triggered properly.")
            
    except Exception as e:
        print(f"❌ Error accessing CloudWatch logs: {e}")
    
    # Also check if the Lambda function itself has any configuration issues
    print(f"\n🔧 Checking Lambda Function Configuration...")
    
    try:
        func_config = lambda_client.get_function(FunctionName=ingestion_function)
        
        config = func_config['Configuration']
        print(f"Runtime: {config.get('Runtime')}")
        print(f"Handler: {config.get('Handler')}")
        print(f"Timeout: {config.get('Timeout')} seconds")
        print(f"Memory: {config.get('MemorySize')} MB")
        print(f"Last Modified: {config.get('LastModified')}")
        
        # Check environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        print(f"Environment Variables: {len(env_vars)} configured")
        for key, value in env_vars.items():
            if 'TABLE' in key or 'ENDPOINT' in key:
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error checking Lambda configuration: {e}")

if __name__ == "__main__":
    check_ingestion_errors()
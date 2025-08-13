#!/usr/bin/env python3
"""
Monitor the ingestion progress by checking logs and content metadata.
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def monitor_ingestion_progress():
    """Monitor ingestion progress."""
    print("📊 Monitoring Ingestion Progress...")
    
    # Check ingestion Lambda logs
    lambda_client = boto3.client('lambda')
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
    
    # Check CloudWatch logs for recent activity
    logs_client = boto3.client('logs')
    log_group_name = f"/aws/lambda/{ingestion_function}"
    
    try:
        # Get log streams from the last 10 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        print(f"Checking logs from {start_time} to {end_time}")
        
        # List recent log streams
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
        all_events = []
        for stream in streams_response['logStreams'][:3]:
            stream_name = stream['logStreamName']
            
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                events = events_response['events']
                all_events.extend(events)
                
            except Exception as e:
                print(f"   Error reading stream {stream_name}: {e}")
        
        if all_events:
            # Sort events by timestamp
            all_events.sort(key=lambda x: x['timestamp'])
            
            print(f"\n📋 Recent ingestion activity ({len(all_events)} log entries):")
            for event in all_events[-20:]:  # Show last 20 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"   {timestamp}: {message}")
        else:
            print("   No recent events found")
            
    except Exception as e:
        print(f"❌ Error accessing ingestion Lambda logs: {e}")
    
    # Check content metadata table
    print(f"\n📊 Checking Content Metadata Table...")
    
    dynamodb = boto3.resource('dynamodb')
    tables = list(dynamodb.tables.all())
    content_table = None
    
    for table in tables:
        if 'content-metadata' in table.name.lower():
            content_table = table
            break
    
    if content_table:
        try:
            response = content_table.scan()
            items = response['Items']
            
            if items:
                ans_items = [item for item in items if item.get('certification_type') == 'ANS']
                print(f"Found {len(ans_items)} ANS content items in metadata table")
                
                if ans_items:
                    total_questions = sum(item.get('question_count', 0) for item in ans_items)
                    print(f"Total ANS questions: {total_questions}")
                    
                    for item in ans_items:
                        title = item.get('title', 'N/A')
                        question_count = item.get('question_count', 0)
                        source_file = item.get('source_file', 'N/A')
                        print(f"   {title}: {question_count} questions (from {source_file})")
                else:
                    print("No ANS content found yet")
            else:
                print("No content found in metadata table yet")
                
        except Exception as e:
            print(f"❌ Error checking content metadata: {e}")

if __name__ == "__main__":
    monitor_ingestion_progress()
#!/usr/bin/env python3
"""
Check S3 buckets for uploaded content and ingestion Lambda logs.
"""

import boto3
import json
from datetime import datetime, timedelta

def check_s3_content():
    """Check S3 buckets for uploaded content."""
    print("📁 Checking S3 Buckets for Uploaded Content...")
    
    s3_client = boto3.client('s3')
    
    # List all buckets to find the ANS bucket
    buckets = s3_client.list_buckets()
    ans_bucket = None
    
    for bucket in buckets['Buckets']:
        bucket_name = bucket['Name']
        if 'ans' in bucket_name.lower() and 'procert' in bucket_name.lower():
            ans_bucket = bucket_name
            break
    
    if not ans_bucket:
        print("❌ ANS bucket not found!")
        print("Available buckets:")
        for bucket in buckets['Buckets']:
            if 'procert' in bucket['Name'].lower():
                print(f"   {bucket['Name']}")
        return
    
    print(f"Found ANS bucket: {ans_bucket}")
    
    # List objects in the ANS bucket
    try:
        objects = s3_client.list_objects_v2(Bucket=ans_bucket)
        
        if 'Contents' in objects:
            print(f"\n📋 Objects in ANS bucket ({len(objects['Contents'])} items):")
            for obj in objects['Contents']:
                key = obj['Key']
                size = obj['Size']
                modified = obj['LastModified']
                print(f"   {key} ({size} bytes, modified: {modified})")
        else:
            print("\n❌ No objects found in ANS bucket!")
            
    except Exception as e:
        print(f"❌ Error listing objects in ANS bucket: {e}")
    
    # Check ingestion Lambda logs
    print(f"\n📋 Checking Ingestion Lambda Logs...")
    
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
    
    # Check CloudWatch logs for recent ingestion activity
    logs_client = boto3.client('logs')
    log_group_name = f"/aws/lambda/{ingestion_function}"
    
    try:
        # Get log streams from the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        print(f"Checking logs from {start_time} to {end_time}")
        
        # List recent log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            print("❌ No recent log streams found for ingestion Lambda")
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
                    for event in events[-10:]:  # Show last 10 events
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message'].strip()
                        print(f"   {timestamp}: {message}")
                else:
                    print("   No events in this time range")
                    
            except Exception as e:
                print(f"   Error reading stream {stream_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error accessing ingestion Lambda logs: {e}")

if __name__ == "__main__":
    check_s3_content()
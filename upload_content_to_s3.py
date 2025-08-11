#!/usr/bin/env python3
"""
Script to upload sample content to ProCert S3 bucket
"""

import boto3
import json
import os
from pathlib import Path

# Configuration
BUCKET_NAME = "procert-materials-aip-353207798766"
CONTENT_DIR = "sample_content"

def upload_file_to_s3(file_path, s3_key, bucket_name):
    """Upload a file to S3 bucket"""
    try:
        s3_client = boto3.client('s3')
        
        with open(file_path, 'rb') as file:
            s3_client.upload_fileobj(file, bucket_name, s3_key)
        
        print(f"✅ Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
        return True
    except Exception as e:
        print(f"❌ Failed to upload {file_path}: {str(e)}")
        return False

def validate_json_file(file_path):
    """Validate that a JSON file is properly formatted"""
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {str(e)}")
        return False

def main():
    """Upload all sample content to S3"""
    print("📤 ProCert Content Upload Tool")
    print("=" * 50)
    
    # Check if AWS credentials are configured
    try:
        boto3.client('sts').get_caller_identity()
        print("✅ AWS credentials configured")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {str(e)}")
        print("Please run 'aws configure' or set AWS environment variables")
        return
    
    # Check if bucket exists
    try:
        s3_client = boto3.client('s3')
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ S3 bucket '{BUCKET_NAME}' exists")
    except Exception as e:
        print(f"❌ Cannot access S3 bucket '{BUCKET_NAME}': {str(e)}")
        return
    
    # Upload content files
    content_files = [
        {
            "local_path": "sample_content/saa-ec2-questions.json",
            "s3_key": "questions/saa/ec2-questions.json"
        },
        {
            "local_path": "sample_content/saa-s3-questions.json", 
            "s3_key": "questions/saa/s3-questions.json"
        },
        {
            "local_path": "sample_content/dva-lambda-questions.json",
            "s3_key": "questions/dva/lambda-questions.json"
        }
    ]
    
    successful_uploads = 0
    total_files = len(content_files)
    
    for file_info in content_files:
        local_path = file_info["local_path"]
        s3_key = file_info["s3_key"]
        
        # Check if file exists
        if not os.path.exists(local_path):
            print(f"❌ File not found: {local_path}")
            continue
        
        # Validate JSON format
        if not validate_json_file(local_path):
            continue
        
        # Upload to S3
        if upload_file_to_s3(local_path, s3_key, BUCKET_NAME):
            successful_uploads += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Upload Summary: {successful_uploads}/{total_files} files uploaded successfully")
    
    if successful_uploads == total_files:
        print("🎉 All content uploaded successfully!")
    else:
        print("⚠️ Some uploads failed. Please check the errors above.")
    
    # List uploaded content
    print(f"\n📋 Content now available in s3://{BUCKET_NAME}/:")
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="questions/")
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("  No content found in questions/ prefix")
    except Exception as e:
        print(f"❌ Error listing bucket contents: {str(e)}")

if __name__ == "__main__":
    main()
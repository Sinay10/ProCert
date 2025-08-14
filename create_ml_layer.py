#!/usr/bin/env python3
"""
Create ML Lambda Layer

This script creates a Lambda layer with NumPy and scikit-learn for the recommendation engine.
"""

import os
import subprocess
import zipfile
import boto3
from pathlib import Path

def create_ml_layer():
    """Create the ML dependencies layer."""
    print("🔧 Creating ML Lambda Layer...")
    
    layer_dir = Path("lambda-layers/ml-layer")
    python_dir = layer_dir / "python"
    
    # Install dependencies
    print("   📦 Installing ML dependencies...")
    subprocess.run([
        "pip", "install", 
        "--target", str(python_dir),
        "--platform", "manylinux2014_x86_64",
        "--only-binary=:all:",
        "-r", str(layer_dir / "requirements.txt")
    ], check=True)
    
    # Create zip file
    zip_path = "ml-layer.zip"
    print(f"   📁 Creating zip file: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(python_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, layer_dir)
                zipf.write(file_path, arcname)
    
    # Get zip size
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
    print(f"   📊 Layer size: {zip_size:.1f} MB")
    
    if zip_size > 50:
        print("   ⚠️  Warning: Layer is quite large, this might affect cold start times")
    
    # Upload to S3 first, then create layer
    print("   ☁️  Uploading layer to S3...")
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = f"procert-lambda-layers-353207798766"
    s3_key = "ml-layer.zip"
    
    # Create bucket if it doesn't exist
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"   📦 Created S3 bucket: {bucket_name}")
    
    # Upload zip to S3
    s3_client.upload_file(zip_path, bucket_name, s3_key)
    print(f"   ✅ Uploaded to S3: s3://{bucket_name}/{s3_key}")
    
    # Create layer from S3
    print("   ☁️  Creating Lambda layer from S3...")
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.publish_layer_version(
        LayerName='procert-ml-dependencies',
        Description='NumPy and scikit-learn for ProCert recommendation engine',
        Content={
            'S3Bucket': bucket_name,
            'S3Key': s3_key
        },
        CompatibleRuntimes=['python3.11'],
        CompatibleArchitectures=['x86_64']
    )
    
    layer_arn = response['LayerVersionArn']
    print(f"   ✅ Layer created: {layer_arn}")
    
    # Clean up
    os.remove(zip_path)
    
    return layer_arn

if __name__ == "__main__":
    try:
        layer_arn = create_ml_layer()
        print(f"\n🎉 ML Layer created successfully!")
        print(f"Layer ARN: {layer_arn}")
        print("\nAdd this layer to your Lambda function in the CDK stack:")
        print(f"layers=[lambda_.LayerVersion.from_layer_version_arn(self, 'MLLayer', '{layer_arn}')]")
    except Exception as e:
        print(f"\n❌ Failed to create ML layer: {str(e)}")
        exit(1)
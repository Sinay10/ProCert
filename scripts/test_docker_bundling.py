#!/usr/bin/env python3
"""
Test script to verify Docker bundling works for Lambda functions.
This ensures that the production deployment will work correctly.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    return result

def check_docker():
    """Check if Docker is available and running."""
    print("Checking Docker availability...")
    result = run_command("docker info", check=False)
    if result.returncode != 0:
        print("❌ Docker is not available or not running")
        print("Please start Docker and try again")
        return False
    print("✅ Docker is available and running")
    return True

def test_lambda_bundling(lambda_dir, test_name):
    """Test Docker bundling for a specific Lambda function."""
    print(f"\n🧪 Testing {test_name} bundling...")
    
    if not os.path.exists(lambda_dir):
        print(f"❌ Lambda directory {lambda_dir} not found")
        return False
    
    if not os.path.exists(f"{lambda_dir}/requirements.txt"):
        print(f"❌ requirements.txt not found in {lambda_dir}")
        return False
    
    # Create a temporary directory for bundling test
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "bundled")
        os.makedirs(output_dir)
        
        # Simulate CDK bundling command (using --entrypoint to override default)
        bundling_cmd = f"""
        docker run --rm \
            --entrypoint bash \
            -v {os.path.abspath(lambda_dir)}:/asset-input:ro \
            -v {output_dir}:/asset-output \
            public.ecr.aws/lambda/python:3.11 \
            -c "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r /asset-input/requirements.txt -t /asset-output && cp -au /asset-input/. /asset-output"
        """
        
        result = run_command(bundling_cmd, check=False)
        if result.returncode != 0:
            print(f"❌ {test_name} bundling failed")
            print(f"Error: {result.stderr}")
            return False
        
        # Check if bundling produced expected files
        if not os.path.exists(f"{output_dir}/main.py"):
            print(f"❌ {test_name} bundling didn't produce main.py")
            return False
        
        # Check if dependencies were installed
        bundled_files = os.listdir(output_dir)
        if len(bundled_files) < 5:  # Should have main.py + dependencies
            print(f"❌ {test_name} bundling seems incomplete (only {len(bundled_files)} files)")
            return False
        
        print(f"✅ {test_name} bundling successful ({len(bundled_files)} files bundled)")
        return True

def test_cdk_synth_with_docker():
    """Test CDK synth with Docker bundling enabled."""
    print("\n🧪 Testing CDK synth with Docker bundling...")
    
    # Temporarily remove CI environment variables to enable Docker bundling
    env = os.environ.copy()
    env.pop('CI', None)
    env.pop('GITLAB_CI', None)
    
    # Run CDK synth
    result = subprocess.run(
        ["cdk", "synth", "--all"],
        env=env,
        capture_output=True,
        text=True,
        cwd="."
    )
    
    if result.returncode != 0:
        print("❌ CDK synth with Docker bundling failed")
        print(f"Error: {result.stderr}")
        return False
    
    print("✅ CDK synth with Docker bundling successful")
    return True

def main():
    """Main test function."""
    print("🐳 Testing Docker bundling for Lambda functions")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("procert_infrastructure"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check Docker availability
    if not check_docker():
        sys.exit(1)
    
    success = True
    
    # Test individual Lambda function bundling
    lambda_dirs = [
        ("lambda_src", "Ingestion Lambda"),
        ("chatbot_lambda_src", "Chatbot Lambda"),
        ("index_setup_lambda_src", "Index Setup Lambda")
    ]
    
    for lambda_dir, test_name in lambda_dirs:
        if not test_lambda_bundling(lambda_dir, test_name):
            success = False
    
    # Test full CDK synth with Docker bundling
    if not test_cdk_synth_with_docker():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All Docker bundling tests passed!")
        print("Your Lambda functions should deploy correctly in production.")
    else:
        print("❌ Some Docker bundling tests failed!")
        print("Please fix the issues before deploying to production.")
        sys.exit(1)

if __name__ == "__main__":
    main()
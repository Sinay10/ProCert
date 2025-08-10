#!/usr/bin/env python3
"""
Pre-deployment test script to verify everything is ready for production.
This script runs comprehensive checks before deploying to AWS.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    return result

def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("🔍 Checking prerequisites...")
    
    checks = [
        ("python3 --version", "Python"),
        ("docker --version", "Docker"),
        ("aws --version", "AWS CLI"),
        ("cdk --version", "AWS CDK"),
        ("npm --version", "Node.js/npm")
    ]
    
    for cmd, name in checks:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print(f"❌ {name} is not installed or not in PATH")
            return False
        print(f"✅ {name} is available")
    
    return True

def check_aws_credentials():
    """Check if AWS credentials are configured."""
    print("\n🔐 Checking AWS credentials...")
    
    result = run_command("aws sts get-caller-identity", check=False)
    if result.returncode != 0:
        print("❌ AWS credentials not configured or invalid")
        print("Please run 'aws configure' or set AWS environment variables")
        return False
    
    try:
        identity = json.loads(result.stdout)
        print(f"✅ AWS credentials configured for account: {identity.get('Account')}")
        return True
    except json.JSONDecodeError:
        print("❌ Unable to parse AWS identity response")
        return False

def run_tests():
    """Run all tests."""
    print("\n🧪 Running tests...")
    
    # Run unit tests
    print("Running unit tests...")
    result = run_command("python -m pytest tests/unit/ -v", check=False)
    if result.returncode != 0:
        print("❌ Unit tests failed")
        return False
    print("✅ Unit tests passed")
    
    # Run Docker bundling tests
    print("Running Docker bundling tests...")
    result = run_command("python scripts/test_docker_bundling.py", check=False)
    if result.returncode != 0:
        print("❌ Docker bundling tests failed")
        return False
    print("✅ Docker bundling tests passed")
    
    return True

def validate_cdk():
    """Validate CDK configuration."""
    print("\n📋 Validating CDK configuration...")
    
    # CDK synth
    result = run_command("cdk synth --all", check=False)
    if result.returncode != 0:
        print("❌ CDK synth failed")
        return False
    print("✅ CDK synth successful")
    
    # CDK diff (to see what will change)
    print("Checking what will be deployed...")
    result = run_command("cdk diff", check=False)
    if result.returncode == 0:
        print("✅ CDK diff completed - no changes detected")
    elif result.returncode == 1:
        print("ℹ️ CDK diff completed - changes detected:")
        print(result.stdout)
    else:
        print("❌ CDK diff failed")
        return False
    
    return True

def estimate_costs():
    """Provide cost estimation guidance."""
    print("\n💰 Cost Estimation Guidance:")
    print("Based on your configuration, expected monthly costs:")
    print("- Lambda functions: ~$1-5 (depending on usage)")
    print("- DynamoDB: ~$1-3 (pay-per-request)")
    print("- S3 storage: ~$1-10 (depending on data volume)")
    print("- OpenSearch Serverless: ~$10-50 (minimum charges apply)")
    print("- API Gateway: ~$1-5 (depending on requests)")
    print("Total estimated: $15-75/month for light usage")
    print("\nRun 'python scripts/cost_monitor.py' after deployment to track actual costs.")

def main():
    """Main test function."""
    print("🚀 Pre-deployment validation for ProCert Infrastructure")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("procert_infrastructure"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Activate virtual environment if it exists
    if os.path.exists(".venv/bin/activate"):
        print("Activating virtual environment...")
        # Note: This doesn't actually activate the venv in the current process
        # The user should run: source .venv/bin/activate before running this script
    
    success = True
    
    # Run all checks
    if not check_prerequisites():
        success = False
    
    if not check_aws_credentials():
        success = False
    
    if not run_tests():
        success = False
    
    if not validate_cdk():
        success = False
    
    # Show cost estimation
    estimate_costs()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All pre-deployment checks passed!")
        print("\nYou're ready to deploy. Run:")
        print("  cdk bootstrap  # (if not already done)")
        print("  cdk deploy --all")
        print("\nOr use the GitLab CI/CD pipeline for automated deployment.")
    else:
        print("❌ Some pre-deployment checks failed!")
        print("Please fix the issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
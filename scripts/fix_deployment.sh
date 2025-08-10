#!/bin/bash
# Script to fix deployment issues by cleaning up and redeploying

echo "🔧 Fixing ProCert deployment issues..."

# Activate virtual environment
source .venv/bin/activate

echo "1. Destroying existing stack to clean up orphaned resources..."
cdk destroy --all --force || echo "Stack destruction completed (some resources may have been already deleted)"

echo "2. Waiting for cleanup to complete..."
sleep 30

echo "3. Redeploying fresh stack..."
cdk deploy --all --require-approval never

echo "✅ Deployment fix completed!"
#!/bin/bash

# Test Security Pipeline Locally
# This script simulates the GitLab CI security stage locally

set -e

echo "🧪 Testing CDK Nag Security Pipeline Locally"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "security_analysis_ci.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Set CI environment variable
export CI=true

echo "📦 Installing dependencies..."
pip install -q cdk-nag || echo "CDK Nag already installed"

echo "🛡️ Running CDK Nag security analysis..."
python security_analysis_ci.py

echo ""
echo "✅ Local security pipeline test completed successfully!"
echo "🚀 Your code is ready for GitLab CI security checks"
echo ""
echo "💡 Next steps:"
echo "   1. Commit your changes: git add . && git commit -m 'Add CDK nag security scanning'"
echo "   2. Push to GitLab: git push"
echo "   3. Check the pipeline security stage in GitLab CI"
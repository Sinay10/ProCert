#!/bin/bash

# Personal GitLab Setup for ProCert Project
# Simple setup script for personal learning projects

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Personal GitLab Setup for ProCert${NC}"
echo "====================================="

# Get user input
echo ""
echo "Which GitLab instance are you using?"
echo "1) gitlab.com (public)"
echo "2) gitlab.aws.dev (AWS internal)"
echo "3) Custom GitLab instance"
read -p "Enter choice (1-3): " GITLAB_CHOICE

case $GITLAB_CHOICE in
    1)
        GITLAB_URL="https://gitlab.com"
        ;;
    2)
        GITLAB_URL="https://gitlab.aws.dev"
        ;;
    3)
        read -p "Enter your GitLab URL (e.g., https://gitlab.company.com): " GITLAB_URL
        ;;
    *)
        echo "Invalid choice, defaulting to gitlab.com"
        GITLAB_URL="https://gitlab.com"
        ;;
esac

read -p "Enter your GitLab username: " GITLAB_USERNAME
read -p "Enter your project name (default: procert-infrastructure): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-procert-infrastructure}

GITLAB_PROJECT="${GITLAB_USERNAME}/${PROJECT_NAME}"

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "GitLab URL: $GITLAB_URL"
echo "Project: $GITLAB_PROJECT"
echo ""

# Commit current changes
echo -e "${GREEN}📝 Committing current changes...${NC}"
git add .
if git diff --staged --quiet; then
    echo "No changes to commit"
else
    git commit -m "feat: add GitLab CI/CD setup for personal project

- Add simplified GitLab CI/CD pipeline
- Add StorageManager implementation with tests
- Add cost monitoring for personal AWS account
- Update documentation for personal project setup"
    echo "✅ Changes committed"
fi

# Add GitLab remote
echo -e "${GREEN}🔗 Adding GitLab remote...${NC}"
GITLAB_REMOTE_URL="${GITLAB_URL}/${GITLAB_PROJECT}.git"

if git remote get-url gitlab >/dev/null 2>&1; then
    echo "GitLab remote already exists, updating URL..."
    git remote set-url gitlab "$GITLAB_REMOTE_URL"
else
    git remote add gitlab "$GITLAB_REMOTE_URL"
    echo "✅ GitLab remote added: $GITLAB_REMOTE_URL"
fi

# Push to GitLab
echo -e "${GREEN}📤 Pushing to GitLab...${NC}"
echo "Make sure you've created the repository on your GitLab instance first!"
echo "Repository URL: ${GITLAB_URL}/${GITLAB_PROJECT}"
echo ""
read -p "Press Enter when you've created the GitLab repository..."

git push gitlab main

echo -e "${GREEN}✅ Repository pushed to GitLab!${NC}"

# Setup instructions
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "=============="
echo ""
echo "1. Go to your GitLab project: ${GITLAB_URL}/${GITLAB_PROJECT}"
echo ""
echo "2. Set up CI/CD Variables (Settings → CI/CD → Variables):"
echo "   - AWS_ACCESS_KEY_ID (Protected, Masked)"
echo "   - AWS_SECRET_ACCESS_KEY (Protected, Masked)"
echo "   - AWS_ACCOUNT_ID (Protected)"
echo ""
echo "3. Create an IAM user for GitLab CI/CD:"
echo "   aws iam create-user --user-name gitlab-ci-procert"
echo "   aws iam create-access-key --user-name gitlab-ci-procert"
echo "   aws iam attach-user-policy --user-name gitlab-ci-procert --policy-arn arn:aws:iam::aws:policy/PowerUserAccess"
echo ""
echo "4. Test the pipeline by making a small change and pushing to main"
echo ""
echo "5. Monitor costs with: python scripts/cost_monitor.py"
echo ""
echo -e "${GREEN}🎉 Setup complete! Happy coding!${NC}"
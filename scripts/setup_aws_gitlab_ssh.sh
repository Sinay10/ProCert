#!/bin/bash

# AWS GitLab SSH Setup Script for Mac
# This script sets up SSH authentication for gitlab.aws.dev

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 AWS GitLab SSH Setup for Mac${NC}"
echo "=================================="

# Step 1: Check if ECDSA key exists
echo -e "${YELLOW}Step 1: Checking for ECDSA SSH key...${NC}"
if [ ! -f ~/.ssh/id_ecdsa ]; then
    echo "ECDSA key not found. Generating new ECDSA key..."
    ssh-keygen -t ecdsa -f ~/.ssh/id_ecdsa -N ""
    echo -e "${GREEN}✅ ECDSA key generated${NC}"
else
    echo -e "${GREEN}✅ ECDSA key already exists${NC}"
fi

# Step 2: Add GitLab SSH config
echo -e "${YELLOW}Step 2: Adding GitLab SSH configuration...${NC}"

# Check if GitLab config already exists
if grep -q "Host ssh.gitlab.aws.dev" ~/.ssh/config 2>/dev/null; then
    echo "GitLab SSH config already exists"
else
    echo "Adding GitLab SSH configuration..."
    cat >> ~/.ssh/config << 'EOF'

# AWS GitLab Configuration
Host ssh.gitlab.aws.dev
  User git
  IdentityFile ~/.ssh/id_ecdsa
  CertificateFile ~/.ssh/id_ecdsa-cert.pub
  IdentitiesOnly yes
  ProxyCommand none
  ProxyJump none
EOF
    echo -e "${GREEN}✅ GitLab SSH config added${NC}"
fi

# Step 3: Sign key with Midway
echo -e "${YELLOW}Step 3: Signing key with Midway...${NC}"
echo "Running: mwinit -f -k ~/.ssh/id_ecdsa.pub"

if command -v mwinit &> /dev/null; then
    if mwinit -f -k ~/.ssh/id_ecdsa.pub; then
        echo -e "${GREEN}✅ Key signed with Midway successfully${NC}"
    else
        echo -e "${RED}❌ Midway signing failed${NC}"
        echo "Please ensure you have access to Midway and try again"
        exit 1
    fi
else
    echo -e "${RED}❌ mwinit command not found${NC}"
    echo "Please install Midway tools first"
    exit 1
fi

# Step 4: Test connection
echo -e "${YELLOW}Step 4: Testing GitLab connection...${NC}"
echo "Running: ssh -T ssh.gitlab.aws.dev"

if ssh -T ssh.gitlab.aws.dev 2>&1 | grep -q "Welcome to GitLab"; then
    echo -e "${GREEN}✅ GitLab connection successful!${NC}"
    echo -e "${GREEN}You can now use Git with gitlab.aws.dev${NC}"
else
    echo -e "${RED}❌ GitLab connection failed${NC}"
    echo ""
    echo "Debugging information:"
    echo "======================"
    echo "1. Check if certificate exists:"
    ls -la ~/.ssh/id_ecdsa-cert.pub 2>/dev/null || echo "Certificate file not found"
    echo ""
    echo "2. Verbose SSH test:"
    ssh -vvv -T ssh.gitlab.aws.dev 2>&1 | head -20
    echo ""
    echo "Please check the #aws-gitlab-users Slack channel for help"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 AWS GitLab SSH setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Your GitLab repository: https://gitlab.aws.dev/ymarouaz/ProCert"
echo "2. Clone with: git clone ssh://ssh.gitlab.aws.dev/ymarouaz/ProCert.git"
echo "3. Or add remote: git remote add gitlab ssh://ssh.gitlab.aws.dev/ymarouaz/ProCert.git"
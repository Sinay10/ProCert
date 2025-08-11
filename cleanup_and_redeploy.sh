#!/bin/bash

echo "🧹 ProCert Infrastructure Cleanup and Redeploy Script"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="ProcertInfrastructureStack"
TABLE_NAME="procert-content-metadata-v2-353207798766"

echo -e "${YELLOW}Step 1: Checking current stack status...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].StackStatus' --output text 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Current stack status: $STACK_STATUS${NC}"
    
    if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
        echo -e "${YELLOW}Step 2: Deleting failed CloudFormation stack...${NC}"
        aws cloudformation delete-stack --stack-name $STACK_NAME
        
        echo "Waiting for stack deletion to complete..."
        aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Stack deleted successfully${NC}"
        else
            echo -e "${RED}❌ Failed to delete stack${NC}"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}✅ No existing stack found${NC}"
fi

echo -e "${YELLOW}Step 3: Checking for existing DynamoDB table...${NC}"
TABLE_EXISTS=$(aws dynamodb describe-table --table-name $TABLE_NAME 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Found existing table: $TABLE_NAME${NC}"
    echo -e "${YELLOW}Deleting existing table...${NC}"
    
    aws dynamodb delete-table --table-name $TABLE_NAME
    
    echo "Waiting for table deletion to complete..."
    aws dynamodb wait table-not-exists --table-name $TABLE_NAME
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Table deleted successfully${NC}"
    else
        echo -e "${RED}❌ Failed to delete table${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ No existing table found${NC}"
fi

echo -e "${YELLOW}Step 4: Ready for redeployment${NC}"
echo "======================================================"
echo -e "${GREEN}✅ Cleanup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Navigate to your CDK project directory"
echo "2. Run: cdk deploy ProcertInfrastructureStack"
echo "3. Wait for deployment to complete"
echo "4. Run the authentication tests again"
echo ""
echo -e "${YELLOW}Would you like me to attempt the CDK deployment? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}Step 5: Attempting CDK deployment...${NC}"
    
    # Try to find CDK project directory
    if [ -f "cdk.json" ]; then
        echo "Found CDK project in current directory"
        cdk deploy ProcertInfrastructureStack
    elif [ -f "../cdk.json" ]; then
        echo "Found CDK project in parent directory"
        cd ..
        cdk deploy ProcertInfrastructureStack
    else
        echo -e "${RED}❌ Could not find CDK project (cdk.json)${NC}"
        echo "Please navigate to your CDK project directory and run:"
        echo "cdk deploy ProcertInfrastructureStack"
    fi
else
    echo -e "${YELLOW}Skipping CDK deployment. Please run manually when ready.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Script completed!${NC}"
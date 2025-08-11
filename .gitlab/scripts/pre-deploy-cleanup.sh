#!/bin/bash
set -e

echo "🧹 Pre-deployment cleanup script"
echo "=================================="

# Function to delete DynamoDB tables
cleanup_dynamodb() {
    echo "🗄️ Cleaning DynamoDB tables..."
    
    TABLES=(
        "procert-content-metadata-v2-353207798766"
        "procert-conversations-353207798766"
        "procert-quiz-sessions-353207798766"
        "procert-user-profiles-353207798766"
        "procert-user-progress-353207798766"
    )
    
    for table in "${TABLES[@]}"; do
        if aws dynamodb describe-table --table-name "$table" >/dev/null 2>&1; then
            echo "Deleting table: $table"
            aws dynamodb delete-table --table-name "$table"
        else
            echo "Table not found: $table"
        fi
    done
}

# Function to delete S3 buckets
cleanup_s3() {
    echo "📦 Cleaning S3 buckets..."
    
    BUCKET_SUFFIXES=(
        "aip" "ans" "ccp" "dea" "dop" "dva" 
        "general" "mla" "mls" "saa" "sap" "scs" "soa"
    )
    
    for suffix in "${BUCKET_SUFFIXES[@]}"; do
        bucket="procert-materials-${suffix}-353207798766"
        
        if aws s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
            echo "Cleaning bucket: $bucket"
            
            # Delete all object versions
            aws s3api list-object-versions --bucket "$bucket" --query 'Versions[].{Key:Key,VersionId:VersionId}' --output json | \
            jq -r '.[]? | "--key \(.Key) --version-id \(.VersionId)"' | \
            while read -r args; do
                if [ -n "$args" ]; then
                    aws s3api delete-object --bucket "$bucket" $args
                fi
            done
            
            # Delete all delete markers
            aws s3api list-object-versions --bucket "$bucket" --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output json | \
            jq -r '.[]? | "--key \(.Key) --version-id \(.VersionId)"' | \
            while read -r args; do
                if [ -n "$args" ]; then
                    aws s3api delete-object --bucket "$bucket" $args
                fi
            done
            
            # Delete bucket
            aws s3api delete-bucket --bucket "$bucket"
            echo "Deleted bucket: $bucket"
        else
            echo "Bucket not found: $bucket"
        fi
    done
}

# Function to delete Cognito User Pools
cleanup_cognito() {
    echo "👤 Cleaning Cognito User Pools..."
    
    aws cognito-idp list-user-pools --max-results 50 --query 'UserPools[?contains(Name, `procert`)].Id' --output text | \
    while read -r pool_id; do
        if [ -n "$pool_id" ]; then
            echo "Deleting User Pool: $pool_id"
            aws cognito-idp delete-user-pool --user-pool-id "$pool_id"
        fi
    done
}

# Function to delete OpenSearch Serverless policies
cleanup_opensearch_policies() {
    echo "🔍 Cleaning OpenSearch Serverless policies..."
    
    # Delete access policies
    aws opensearchserverless list-access-policies --type data --query 'accessPolicySummaries[?contains(name, `procert`)].name' --output text | \
    while read -r policy_name; do
        if [ -n "$policy_name" ]; then
            echo "Deleting access policy: $policy_name"
            aws opensearchserverless delete-access-policy --name "$policy_name" --type data || true
        fi
    done
    
    # Delete security policies (encryption)
    aws opensearchserverless list-security-policies --type encryption --query 'securityPolicySummaries[?contains(name, `procert`)].name' --output text | \
    while read -r policy_name; do
        if [ -n "$policy_name" ]; then
            echo "Deleting encryption policy: $policy_name"
            aws opensearchserverless delete-security-policy --name "$policy_name" --type encryption || true
        fi
    done
    
    # Delete security policies (network)
    aws opensearchserverless list-security-policies --type network --query 'securityPolicySummaries[?contains(name, `procert`)].name' --output text | \
    while read -r policy_name; do
        if [ -n "$policy_name" ]; then
            echo "Deleting network policy: $policy_name"
            aws opensearchserverless delete-security-policy --name "$policy_name" --type network || true
        fi
    done
    
    # Delete collections
    aws opensearchserverless list-collections --query 'collectionSummaries[?contains(name, `procert`)].name' --output text | \
    while read -r collection_name; do
        if [ -n "$collection_name" ]; then
            echo "Deleting collection: $collection_name"
            aws opensearchserverless delete-collection --name "$collection_name" || true
        fi
    done
}

# Function to delete failed CloudFormation stacks
cleanup_cloudformation() {
    echo "☁️ Cleaning failed CloudFormation stacks..."
    
    if aws cloudformation describe-stacks --stack-name ProcertInfrastructureStack >/dev/null 2>&1; then
        STACK_STATUS=$(aws cloudformation describe-stacks --stack-name ProcertInfrastructureStack --query 'Stacks[0].StackStatus' --output text)
        
        if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" || "$STACK_STATUS" == "CREATE_FAILED" ]]; then
            echo "Deleting failed stack: ProcertInfrastructureStack"
            aws cloudformation delete-stack --stack-name ProcertInfrastructureStack
            
            echo "Waiting for stack deletion..."
            aws cloudformation wait stack-delete-complete --stack-name ProcertInfrastructureStack
        fi
    fi
}

# Main cleanup sequence
main() {
    echo "Starting cleanup sequence..."
    
    cleanup_cloudformation
    cleanup_dynamodb
    cleanup_s3
    cleanup_cognito
    cleanup_opensearch_policies
    
    echo "⏳ Waiting 30 seconds for resources to fully delete..."
    sleep 30
    
    echo "✅ Cleanup completed successfully!"
}

# Run main function
main
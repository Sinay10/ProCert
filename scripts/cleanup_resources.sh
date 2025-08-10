#!/bin/bash
# Script to manually clean up orphaned AWS resources

echo "🗑️ Cleaning up orphaned ProCert resources..."

# Delete S3 buckets (need to empty them first)
echo "1. Deleting S3 buckets..."
aws s3 rm s3://procert-materials-353207798766 --recursive || echo "Bucket already empty or doesn't exist"
aws s3 rb s3://procert-materials-353207798766 || echo "Bucket already deleted"

aws s3 rm s3://procert-materials-dva-353207798766 --recursive || echo "Bucket already empty or doesn't exist"
aws s3 rb s3://procert-materials-dva-353207798766 || echo "Bucket already deleted"

aws s3 rm s3://procert-materials-general-353207798766 --recursive || echo "Bucket already empty or doesn't exist"
aws s3 rb s3://procert-materials-general-353207798766 || echo "Bucket already deleted"

aws s3 rm s3://procert-materials-saa-353207798766 --recursive || echo "Bucket already empty or doesn't exist"
aws s3 rb s3://procert-materials-saa-353207798766 || echo "Bucket already deleted"

aws s3 rm s3://procert-materials-soa-353207798766 --recursive || echo "Bucket already empty or doesn't exist"
aws s3 rb s3://procert-materials-soa-353207798766 || echo "Bucket already deleted"

# Delete DynamoDB tables
echo "2. Deleting DynamoDB tables..."
aws dynamodb delete-table --table-name procert-content-metadata-353207798766 || echo "Table already deleted"
aws dynamodb delete-table --table-name procert-user-progress-353207798766 || echo "Table already deleted"

echo "3. Waiting for DynamoDB tables to be deleted..."
aws dynamodb wait table-not-exists --table-name procert-content-metadata-353207798766 || echo "Table deletion complete"
aws dynamodb wait table-not-exists --table-name procert-user-progress-353207798766 || echo "Table deletion complete"

echo "✅ Cleanup completed! You can now run 'cdk deploy --all'"
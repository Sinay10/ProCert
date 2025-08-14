# Security Fixes Applied

## Overview
This document outlines the security improvements made to address IAM permission issues and hardcoded resource dependencies.

## Issues Fixed

### 1. Overly Permissive IAM Roles ✅ FIXED

**Problem**: Lambda functions had wildcard permissions like `aoss:*` and `aoss:APIAccessAll`

**Solution**: Implemented principle of least privilege with specific permissions:

#### OpenSearch Permissions by Lambda Function:
- **Ingestion Lambda**: `ReadDocument`, `WriteDocument`, `CreateIndex`, `DescribeIndex`
- **Chatbot Lambda**: `ReadDocument`, `DescribeIndex` (read-only)
- **Quiz Lambda**: `ReadDocument`, `DescribeIndex` (read-only)  
- **Index Setup Lambda**: `CreateIndex`, `DescribeIndex`, `UpdateIndex`

#### OpenSearch Access Policy:
- **Collection**: `DescribeCollectionItems`, `CreateCollectionItems`
- **Index**: `ReadDocument`, `WriteDocument`, `CreateIndex`, `DescribeIndex`, `UpdateIndex`

### 2. Hardcoded Lambda Layer ARN ✅ FIXED

**Problem**: Lambda layer ARN was hardcoded to specific account/region:
```
arn:aws:lambda:us-east-1:353207798766:layer:procert-ml-dependencies:1
```

**Solution**: Made layer ARN configurable and account/region aware:

#### Configuration Options:
1. **CDK Context** (recommended): Set `ml_layer_arn` in `cdk.context.json`
2. **Auto-detection**: Defaults to current account/region if not specified
3. **Command line**: `cdk deploy -c ml_layer_arn=arn:aws:lambda:REGION:ACCOUNT:layer:NAME:VERSION`

#### Current Configuration:
The layer ARN is now set in `cdk.context.json` and can be easily changed for different environments.

## Security Benefits

### Reduced Attack Surface
- Eliminated wildcard permissions (`aoss:*`)
- Each Lambda function has only the minimum required permissions
- VPC endpoint policy also uses specific permissions

### Improved Portability
- Stack can now be deployed in any AWS account/region
- No hardcoded account IDs in infrastructure code
- Environment-specific configuration through CDK context

### Better Compliance
- Follows AWS security best practices
- Implements principle of least privilege
- Easier to audit and review permissions

## Deployment Impact

**⚠️ REQUIRES CDK DEPLOYMENT**

These changes modify IAM policies and Lambda configurations, requiring:
```bash
cdk deploy --all
```

**Rollback Plan**: 
- Git revert if issues arise
- Previous permissions were more permissive, so rollback is safe

## Validation

After deployment, verify:
1. Lambda functions can still access OpenSearch (check CloudWatch logs)
2. Ingestion pipeline works (upload a PDF to S3)
3. Chatbot queries work (test API endpoints)
4. No permission errors in Lambda logs

## Future Recommendations

1. **Regular Permission Audits**: Review IAM policies quarterly
2. **Least Privilege Reviews**: Ensure new Lambda functions follow same pattern
3. **Environment-Specific Layers**: Consider separate ML layers per environment
4. **Automated Security Scanning**: Integrate tools like AWS Config Rules
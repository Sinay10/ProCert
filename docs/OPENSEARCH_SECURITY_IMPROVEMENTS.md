# OpenSearch Serverless Security Improvements

## Security Issue Addressed

**Problem**: The OpenSearch Serverless collection was configured with `AllowFromPublic: true`, exposing the vector database endpoint to the public internet. This created an unnecessary attack surface despite having data access policies in place.

**Risk Level**: High - Public exposure of database endpoints is a significant security vulnerability.

## Solution Implemented

### 1. VPC-Based Private Access

- **Created dedicated VPC** (`procert-vpc-{account}`) with:
  - Private subnets for Lambda functions
  - Public subnets for NAT Gateway
  - Single NAT Gateway for cost optimization
  - 2 Availability Zones for high availability

### 2. VPC Endpoint for OpenSearch Serverless

- **Interface VPC Endpoint** for `com.amazonaws.{region}.aoss`
- Deployed in private subnets only
- Secured with dedicated security group
- Proper IAM policy allowing only necessary OpenSearch actions

### 3. Network Policy Updates

**Before**:
```json
{
  "Rules": [...],
  "AllowFromPublic": true
}
```

**After**:
```json
{
  "Rules": [...],
  "AllowFromPublic": false,
  "SourceVPCEs": ["vpce-xxxxxxxxx"]
}
```

### 4. Lambda Functions Updated

The following Lambda functions now run in the VPC with private subnet access:

- **Ingestion Lambda** - Processes documents and stores vectors
- **Chatbot Lambda** - Queries vectors for RAG responses  
- **Index Setup Lambda** - Creates OpenSearch indices

**VPC Configuration Applied**:
- Private subnets with egress (for internet access via NAT)
- Dedicated security group allowing outbound HTTPS
- Proper timeout and memory allocation

## Security Benefits

1. **Zero Public Exposure** - OpenSearch endpoint no longer accessible from internet
2. **Network Isolation** - All traffic flows through private AWS network
3. **Controlled Access** - Only VPC-deployed Lambda functions can access the collection
4. **Defense in Depth** - Multiple layers: VPC, Security Groups, IAM policies, and Data Access policies
5. **Audit Trail** - All access flows through VPC Flow Logs and CloudTrail

## Cost Considerations

- **VPC Endpoint**: ~$7.20/month per endpoint
- **NAT Gateway**: ~$32.40/month + data processing charges
- **Lambda VPC**: Slight cold start increase (~100-200ms)

**Total Additional Cost**: ~$40-50/month for significantly improved security posture.

## Deployment Impact

### Breaking Changes
- Lambda functions will have slightly longer cold starts due to VPC networking
- Any external tools trying to access OpenSearch directly will need VPC access

### Zero Downtime Deployment
- VPC resources created first
- Lambda functions updated to use VPC
- Network policy updated last
- No service interruption expected

## Monitoring and Troubleshooting

### Key Metrics to Monitor
- Lambda function duration (watch for VPC cold starts)
- VPC Endpoint network utilization
- OpenSearch connection errors

### Common Issues
1. **Lambda Timeout**: Increase timeout if VPC cold starts cause issues
2. **DNS Resolution**: Ensure Lambda can resolve VPC endpoint DNS
3. **Security Group Rules**: Verify outbound HTTPS (443) is allowed

## Compliance Benefits

This change helps meet several compliance requirements:
- **AWS Well-Architected Security Pillar**: Defense in depth
- **SOC 2**: Network security controls
- **ISO 27001**: Access control and network security
- **PCI DSS**: Network segmentation (if applicable)

## Next Steps

1. Deploy the updated infrastructure
2. Test all Lambda functions work correctly
3. Monitor performance metrics for 1-2 weeks
4. Consider additional VPC endpoints for other AWS services if needed
5. Review and update security documentation

## Rollback Plan

If issues arise:
1. Update network policy to temporarily allow public access
2. Remove VPC configuration from Lambda functions
3. Investigate and fix VPC networking issues
4. Re-apply VPC configuration

The rollback can be done quickly without data loss since only network configuration changes.
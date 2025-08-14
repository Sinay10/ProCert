# OpenSearch Security Deployment Checklist

## Pre-Deployment Verification

- [ ] **Backup Current State**
  - [ ] Export current OpenSearch data access policies
  - [ ] Document current Lambda function configurations
  - [ ] Take note of current API response times for baseline

- [ ] **Code Review**
  - [ ] Verify VPC configuration in `procert_infrastructure_stack.py`
  - [ ] Confirm all OpenSearch-accessing Lambdas are updated with VPC config
  - [ ] Check security group rules allow outbound HTTPS (443)

- [ ] **Cost Approval**
  - [ ] Confirm budget approval for ~$40-50/month additional costs
  - [ ] VPC Endpoint: ~$7.20/month
  - [ ] NAT Gateway: ~$32.40/month + data processing

## Deployment Steps

### Phase 1: Infrastructure Updates
- [ ] **Deploy VPC Resources**
  ```bash
  cdk deploy --require-approval never
  ```
  - [ ] Verify VPC created successfully
  - [ ] Confirm VPC Endpoint is available
  - [ ] Check security groups are properly configured

### Phase 2: Lambda Function Updates  
- [ ] **Update Lambda Functions**
  - [ ] Ingestion Lambda moved to VPC
  - [ ] Chatbot Lambda moved to VPC
  - [ ] Index Setup Lambda moved to VPC
  - [ ] All functions have proper subnet and security group assignments

### Phase 3: Network Policy Update
- [ ] **Secure OpenSearch Access**
  - [ ] Network policy updated to `AllowFromPublic: false`
  - [ ] VPC Endpoint ID correctly referenced in policy
  - [ ] OpenSearch collection still accessible via VPC

## Post-Deployment Testing

### Functional Testing
- [ ] **Document Ingestion Test**
  - [ ] Upload a test PDF to S3 bucket
  - [ ] Verify ingestion Lambda processes successfully
  - [ ] Check OpenSearch index contains new document

- [ ] **Chatbot Functionality Test**
  - [ ] Send test query via API Gateway
  - [ ] Verify response includes relevant context
  - [ ] Check response times are acceptable

- [ ] **Index Setup Test**
  - [ ] Trigger index setup Lambda manually
  - [ ] Verify OpenSearch indices are created properly

### Performance Testing
- [ ] **Lambda Performance**
  - [ ] Monitor Lambda duration metrics
  - [ ] Check for increased cold start times
  - [ ] Verify no timeout errors

- [ ] **API Response Times**
  - [ ] Test API endpoints response times
  - [ ] Compare with pre-deployment baseline
  - [ ] Ensure acceptable user experience

### Security Validation
- [ ] **Public Access Blocked**
  - [ ] Attempt to access OpenSearch endpoint from internet (should fail)
  - [ ] Verify network policy shows `AllowFromPublic: false`
  - [ ] Confirm only VPC endpoint access works

- [ ] **VPC Flow Logs**
  - [ ] Enable VPC Flow Logs if not already enabled
  - [ ] Verify traffic flows through VPC endpoint
  - [ ] Check no unexpected external traffic

## Monitoring Setup

### CloudWatch Alarms
- [ ] **Lambda Function Errors**
  - [ ] Set up alarms for Lambda function failures
  - [ ] Monitor timeout errors specifically

- [ ] **VPC Endpoint Health**
  - [ ] Monitor VPC endpoint availability
  - [ ] Set up alerts for connection failures

- [ ] **API Gateway Metrics**
  - [ ] Monitor API response times
  - [ ] Set up alerts for increased latency

### Dashboard Creation
- [ ] **Security Dashboard**
  - [ ] VPC Flow Logs visualization
  - [ ] Lambda function performance metrics
  - [ ] OpenSearch access patterns

## Rollback Procedures

### Emergency Rollback (if critical issues)
- [ ] **Immediate Access Restoration**
  ```bash
  # Update network policy to allow public access temporarily
  aws opensearchserverless update-security-policy \
    --name procert-network-policy \
    --type network \
    --policy '{"Rules":[...],"AllowFromPublic":true}'
  ```

### Full Rollback (if needed)
- [ ] **Remove VPC Configuration**
  - [ ] Update Lambda functions to remove VPC settings
  - [ ] Deploy changes
  - [ ] Verify functionality restored

- [ ] **Clean Up Resources**
  - [ ] Delete VPC Endpoint (saves costs)
  - [ ] Consider keeping VPC for future use

## Success Criteria

- [ ] **Functionality**: All features work as before deployment
- [ ] **Performance**: API response times within 20% of baseline
- [ ] **Security**: OpenSearch not accessible from public internet
- [ ] **Monitoring**: All alarms and dashboards operational
- [ ] **Documentation**: Updated architecture diagrams and runbooks

## Sign-off

- [ ] **Technical Lead**: _________________ Date: _______
- [ ] **Security Team**: _________________ Date: _______
- [ ] **Operations Team**: _________________ Date: _______

## Notes

_Use this section to document any issues encountered, deviations from plan, or lessons learned during deployment._

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Rollback Deadline**: _______________ (if no issues, consider deployment successful)
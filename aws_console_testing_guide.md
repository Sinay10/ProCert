# AWS Console Testing Guide for ProCert Learning Platform

## 🎯 Objective
Test the ProCert learning platform components directly through the AWS Console to verify functionality and troubleshoot the 403 API Gateway errors.

## 📋 Pre-Testing Checklist

### 1. AWS Console Access
- [ ] Log into AWS Console
- [ ] Verify you're in the correct region (likely us-east-1)
- [ ] Confirm you have appropriate permissions

### 2. Resource Verification
- [ ] API Gateway exists and is deployed
- [ ] Lambda functions are deployed
- [ ] Cognito User Pool is configured
- [ ] DynamoDB tables exist
- [ ] S3 bucket is accessible

## 🔧 Step-by-Step Testing

### Phase 1: API Gateway Investigation

#### 1.1 Check API Gateway Deployment
1. **Navigate to API Gateway Console**
2. **Find ProCert API** (likely named `procert-api` or similar)
3. **Check Deployment Status**:
   - Go to "Stages" → "prod"
   - Verify deployment exists and is recent
   - Note the Invoke URL
4. **Check Resources**:
   - Verify these resources exist:
     - `/auth/register` (POST)
     - `/auth/login` (POST)
     - `/profile/{user_id}` (GET, PUT)
     - `/chat/message` (POST)

#### 1.2 Check CORS Configuration
1. **For each resource**, verify CORS is enabled:
   - Select resource → Actions → Enable CORS
   - Ensure these headers are allowed:
     - `Content-Type`
     - `Authorization`
     - `X-Amz-Date`
     - `X-Api-Key`
     - `X-Amz-Security-Token`

#### 1.3 Check Resource Policies
1. **Go to Resource Policy** (left sidebar)
2. **Verify no restrictive policies** are blocking requests
3. **If policy exists**, ensure it allows your IP/requests

#### 1.4 Test API Gateway Directly
1. **In API Gateway Console**, select a resource
2. **Click "TEST"**
3. **Test the `/chat/message` endpoint**:
   ```json
   {
     "message": "What is AWS?",
     "certification": "SAA",
     "user_id": "test-user"
   }
   ```
4. **Check response** - should not be 403

### Phase 2: Lambda Function Testing

#### 2.1 Test Chat Handler Function
1. **Navigate to Lambda Console**
2. **Find `procert-chat-handler`**
3. **Create test event**:
   ```json
   {
     "body": "{\"message\":\"What is Amazon EC2?\",\"certification\":\"SAA\",\"user_id\":\"test-user\"}",
     "headers": {
       "Content-Type": "application/json"
     },
     "httpMethod": "POST",
     "path": "/chat/message"
   }
   ```
4. **Execute test** and verify response
5. **Check CloudWatch logs** for any errors

#### 2.2 Test Authentication Functions
1. **Test `procert-auth-register`**:
   ```json
   {
     "body": "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\",\"given_name\":\"Test\",\"family_name\":\"User\",\"target_certifications\":[\"SAA\"]}",
     "headers": {
       "Content-Type": "application/json"
     },
     "httpMethod": "POST",
     "path": "/auth/register"
   }
   ```

2. **Test `procert-auth-login`**:
   ```json
   {
     "body": "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}",
     "headers": {
       "Content-Type": "application/json"
     },
     "httpMethod": "POST",
     "path": "/auth/login"
   }
   ```

### Phase 3: Cognito User Pool Testing

#### 3.1 Manual User Creation
1. **Navigate to Cognito Console**
2. **Find ProCert User Pool**
3. **Create test users manually**:
   - Username: `test1@example.com`
   - Password: `TestPass123!`
   - Email: `test1@example.com`
   - Given name: `Test`
   - Family name: `User`

#### 3.2 Test User Pool Client
1. **Check App Client settings**
2. **Verify these are enabled**:
   - ALLOW_USER_PASSWORD_AUTH
   - ALLOW_REFRESH_TOKEN_AUTH
   - ALLOW_USER_SRP_AUTH

### Phase 4: DynamoDB Testing

#### 4.1 Verify Tables Exist
1. **Navigate to DynamoDB Console**
2. **Check these tables exist**:
   - `procert-user-profiles`
   - `procert-conversations`
   - `procert-content` (if exists)

#### 4.2 Test Table Access
1. **Select `procert-user-profiles` table**
2. **Go to "Explore table items"**
3. **Try to create a test item**:
   ```json
   {
     "user_id": "test-user-123",
     "email": "test@example.com",
     "name": "Test User",
     "target_certifications": ["SAA"],
     "created_at": "2025-01-08T12:00:00Z",
     "is_active": true
   }
   ```

### Phase 5: S3 Content Testing

#### 5.1 Upload Sample Content
1. **Navigate to S3 Console**
2. **Find `procert-content-bucket`**
3. **Create folder structure**:
   ```
   questions/
   ├── saa/
   └── dva/
   ```
4. **Upload the sample question files** we created

#### 5.2 Test Content Access
1. **Verify files are uploaded correctly**
2. **Check file permissions** (should be private)
3. **Test download** to ensure content is accessible

## 🚨 Common Issues and Solutions

### API Gateway 403 Errors

#### Issue 1: Missing Deployment
**Solution**: Redeploy API to "prod" stage
1. Go to API Gateway → Resources
2. Actions → Deploy API
3. Select "prod" stage
4. Add deployment description
5. Deploy

#### Issue 2: CORS Issues
**Solution**: Enable CORS properly
1. Select each resource
2. Actions → Enable CORS
3. Set proper headers
4. Deploy API again

#### Issue 3: Resource Policy Blocking
**Solution**: Check and modify resource policy
1. Go to Resource Policy
2. Remove restrictive policies
3. Or add your IP to allowed sources

#### Issue 4: Lambda Permission Issues
**Solution**: Check Lambda execution role
1. Go to Lambda function
2. Check execution role permissions
3. Ensure it has necessary DynamoDB, S3, Cognito permissions

### Lambda Function Errors

#### Issue 1: Missing Environment Variables
**Solution**: Set required environment variables
- `USER_POOL_ID`
- `CLIENT_ID`
- `CONTENT_BUCKET`
- `REGION`

#### Issue 2: Timeout Issues
**Solution**: Increase timeout and memory
- Set timeout to 30 seconds
- Increase memory to 512MB or higher

## 📊 Testing Checklist

### API Gateway
- [ ] API exists and is deployed to "prod"
- [ ] All resources are configured
- [ ] CORS is properly enabled
- [ ] No restrictive resource policies
- [ ] Test endpoints return 200, not 403

### Lambda Functions
- [ ] All functions exist and are deployed
- [ ] Environment variables are set
- [ ] Execution roles have proper permissions
- [ ] Test invocations work
- [ ] CloudWatch logs show no errors

### Cognito
- [ ] User Pool exists
- [ ] App Client is configured
- [ ] Can create users manually
- [ ] Authentication flows work

### DynamoDB
- [ ] All required tables exist
- [ ] Can read/write to tables
- [ ] Proper indexes are configured

### S3
- [ ] Content bucket exists
- [ ] Can upload/download files
- [ ] Proper folder structure

## 🎯 Success Criteria

✅ **All tests pass when**:
1. API Gateway returns 200 responses (not 403)
2. Lambda functions execute without errors
3. Users can be created in Cognito
4. DynamoDB operations work
5. S3 content is accessible

## 📞 Next Steps After Console Testing

1. **If issues found**: Fix them in AWS Console
2. **If all working**: Re-run API tests
3. **Upload sample content**: Use the upload script
4. **Run comprehensive tests**: Execute full test suite
5. **Document findings**: Update test results

---

**💡 Pro Tip**: Start with Lambda function testing first, as API Gateway issues often stem from Lambda function problems.
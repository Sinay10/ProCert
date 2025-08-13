# ProCert Authentication Troubleshooting Guide

This document provides a comprehensive guide to diagnosing and fixing authentication issues in the ProCert Learning Platform, based on real issues encountered and resolved.

## 🚨 Common Authentication Issues & Solutions

### Issue 1: Quiz Endpoints Return 403 "User is not authorized" While Profile Endpoints Work

**Symptoms:**
- Profile endpoints (GET /profile/{user_id}) work fine with JWT tokens
- Quiz endpoints (POST /quiz/generate) return 403 with same token
- JWT authorizer appears to be working for some endpoints but not others

**What We Initially Thought:**
- JWT authorizer configuration issue
- Different authorization setup between endpoints
- Token format problems (Bearer vs raw token)

**What We Tested:**
1. **JWT Authorizer Direct Testing**: Invoked JWT authorizer Lambda directly
   ```bash
   # Test event structure
   {
     "type": "TOKEN",
     "authorizationToken": "Bearer {token}",
     "methodArn": "arn:aws:execute-api:region:account:api/stage/METHOD/resource"
   }
   ```
   **Result**: ✅ JWT authorizer worked perfectly for both profile and quiz endpoints

2. **API Gateway Configuration Comparison**: Checked if endpoints had different auth setup
   ```bash
   # Both endpoints showed identical configuration:
   # Auth Type: CUSTOM
   # Authorizer ID: e3ypgu (same authorizer)
   # Integration: AWS_PROXY
   ```
   **Result**: ✅ Configuration was identical

3. **Token Format Testing**: Tested different authorization header formats
   ```bash
   # Format 1: "Authorization: Bearer {token}"
   # Format 2: "Authorization: {token}"
   # Format 3: "authorization: Bearer {token}" (lowercase)
   ```
   **Result**: ✅ Profile worked with all formats, quiz failed with all formats

4. **Lambda Permissions Check**: Verified API Gateway can invoke Lambda functions
   ```bash
   # Both Lambdas had identical permissions:
   # Principal: apigateway.amazonaws.com
   # Action: lambda:InvokeFunction
   ```
   **Result**: ✅ Permissions were correct

5. **Direct Lambda Invocation**: Tested Lambda functions directly
   ```bash
   # Both profile and quiz Lambdas worked when invoked directly
   ```
   **Result**: ✅ Lambda functions were operational

**Actual Root Cause:**
- **Temporary API Gateway caching/deployment issue**
- All configuration was correct, but API Gateway had stale cache
- Issue resolved through deployment cycle and cache refresh

**Solution:**
1. Redeploy the CDK stack: `cdk deploy --require-approval never`
2. Wait for deployment to complete
3. Test endpoints again
4. If still failing, check CloudWatch logs for both JWT authorizer and target Lambda

**Prevention:**
- Always check deployment timestamps when authentication suddenly stops working
- Verify recent deployments didn't introduce configuration drift
- Use CloudWatch logs to confirm requests are reaching the intended Lambda functions

---

### Issue 2: JWT Authorizer Returns "Deny" Policy

**Symptoms:**
- JWT authorizer Lambda returns policy with `"Effect": "Deny"`
- All protected endpoints return 403 errors
- Token appears valid but authorization fails

**Diagnostic Steps:**

1. **Check Token Validity:**
   ```bash
   # Get fresh token from login endpoint
   curl -X POST https://api-endpoint/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
   ```

2. **Test JWT Authorizer Directly:**
   ```python
   # Use this test event structure
   test_event = {
       "type": "TOKEN",
       "authorizationToken": "Bearer {fresh_token}",
       "methodArn": "arn:aws:execute-api:region:account:api/stage/METHOD/resource"
   }
   ```

3. **Check JWT Authorizer Logs:**
   ```bash
   # Look for these log patterns in CloudWatch:
   # "Token validation successful"
   # "Invalid token" or "Token has expired"
   # "No matching key found for kid"
   ```

**Common Causes & Solutions:**

| Cause | Symptoms | Solution |
|-------|----------|----------|
| **Expired Token** | "Token has expired" in logs | Get fresh token from login |
| **Invalid Token Format** | "Invalid token" in logs | Check Authorization header format |
| **Wrong User Pool** | "Invalid client_id" in logs | Verify USER_POOL_CLIENT_ID env var |
| **JWKS Issues** | "No matching key found" | Check USER_POOL_ID and region |
| **Network Issues** | "Error fetching JWKS" | Check Lambda VPC/internet access |

---

### Issue 3: Authorization Header Format Problems

**Symptoms:**
- Some endpoints work, others don't with same token
- Inconsistent authentication behavior

**Token Format Testing Matrix:**

| Format | Profile Endpoint | Quiz Endpoint | Status |
|--------|------------------|---------------|---------|
| `Bearer {token}` | ✅ Works | ✅ Works | ✅ Recommended |
| `{token}` (raw) | ✅ Works | ✅ Works | ✅ Also works |
| `bearer {token}` (lowercase) | ❌ Fails | ❌ Fails | ❌ Case sensitive |

**JWT Authorizer Token Extraction Logic:**
```python
# The authorizer handles both formats:
if auth_token.startswith('Bearer '):
    return auth_token[7:]  # Remove 'Bearer ' prefix
return auth_token  # Return as-is
```

**Best Practice:**
- Always use `Authorization: Bearer {token}` format
- Ensure "Bearer" is capitalized
- Include space after "Bearer"

---

### Issue 4: Questions Not Found After Authentication Success

**Symptoms:**
- Authentication works (200 response)
- Quiz generation returns 400 "No questions found for certification type"
- Content exists in S3 but not accessible

**Diagnostic Flow:**

1. **Check Content Metadata Table:**
   ```python
   # Scan DynamoDB content metadata table
   response = content_table.scan()
   items = response['Items']
   ans_items = [item for item in items if item.get('certification_type') == 'ANS']
   ```

2. **Check OpenSearch Content:**
   ```python
   # Search OpenSearch for questions
   query = {
       "query": {
           "bool": {
               "must": [
                   {"term": {"content_type": "question"}},
                   {"term": {"certification_type": "ANS"}}
               ]
           }
       }
   }
   ```

3. **Verify Question Format:**
   - Quiz service expects questions in OpenSearch with `content_type: "question"`
   - Question data should be in `metadata` field, not raw text
   - Each question needs: `question_text`, `answer_options`, `certification_type`

**Common Issues & Solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| **No content in metadata table** | Ingestion Lambda not triggered | Manually trigger ingestion or check S3 event configuration |
| **Content in metadata but not OpenSearch** | Bedrock throttling during ingestion | Store questions directly in OpenSearch without embeddings |
| **Questions in OpenSearch but quiz can't find them** | Wrong content_type or missing metadata | Update quiz service to read from metadata field |
| **Bedrock throttling errors** | Too many embedding requests | Implement rate limiting or skip embeddings for quiz functionality |

---

## 🔧 Diagnostic Tools & Commands

### Quick Authentication Test
```bash
# 1. Get fresh token
curl -X POST https://your-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'

# 2. Test protected endpoint
curl -X GET https://your-api/profile/user-id \
  -H "Authorization: Bearer {token}"

# 3. Test quiz endpoint
curl -X POST https://your-api/quiz/generate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-id", "certification_type": "ANS", "question_count": 5}'
```

### JWT Authorizer Direct Test
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Find JWT authorizer function
functions = lambda_client.list_functions()['Functions']
jwt_function = next(f['FunctionName'] for f in functions if 'JWTAuthorizer' in f['FunctionName'])

# Test event
test_event = {
    "type": "TOKEN",
    "authorizationToken": "Bearer your-token-here",
    "methodArn": "arn:aws:execute-api:us-east-1:account:api/prod/POST/quiz/generate"
}

# Invoke
response = lambda_client.invoke(
    FunctionName=jwt_function,
    Payload=json.dumps(test_event)
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
```

### Content Verification Script
```python
import boto3

# Check DynamoDB content
dynamodb = boto3.resource('dynamodb')
content_table = dynamodb.Table('your-content-metadata-table')
response = content_table.scan()

print(f"Total content items: {len(response['Items'])}")
for item in response['Items']:
    if item.get('certification_type') == 'ANS':
        print(f"ANS Content: {item.get('title')} - {item.get('question_count', 0)} questions")
```

---

## 🚨 Emergency Troubleshooting Checklist

When authentication suddenly stops working:

### ✅ **Step 1: Verify Basic Setup**
- [ ] Recent deployments completed successfully
- [ ] Environment variables are set correctly
- [ ] User Pool and Client IDs match configuration

### ✅ **Step 2: Test Token Validity**
- [ ] Get fresh token from login endpoint
- [ ] Token format is `Bearer {token}`
- [ ] Token hasn't expired (check timestamp)

### ✅ **Step 3: Check JWT Authorizer**
- [ ] JWT authorizer Lambda exists and is deployable
- [ ] CloudWatch logs show successful token validation
- [ ] JWKS retrieval is working (no network issues)

### ✅ **Step 4: Verify API Gateway Configuration**
- [ ] All protected endpoints have same authorizer ID
- [ ] Integration type is AWS_PROXY
- [ ] Recent deployments didn't change configuration

### ✅ **Step 5: Test Lambda Functions Directly**
- [ ] Target Lambda functions work when invoked directly
- [ ] Lambda permissions allow API Gateway invocation
- [ ] No timeout or memory issues in Lambda execution

### ✅ **Step 6: Check Content Availability (for quiz issues)**
- [ ] Content exists in DynamoDB metadata table
- [ ] Questions are properly stored in OpenSearch
- [ ] Question format matches what quiz service expects

---

## 📋 Known Working Configuration

### JWT Authorizer Environment Variables
```bash
USER_POOL_ID=us-east-1_YourPoolId
USER_POOL_CLIENT_ID=your-client-id
AWS_REGION=us-east-1
```

### API Gateway Authorizer Configuration
```yaml
Type: TOKEN
Identity Source: method.request.header.Authorization
Results Cache TTL: 5 minutes
```

### Working Token Formats
```bash
# ✅ Recommended
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

# ✅ Also works
Authorization: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

# ❌ Don't use
authorization: bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Quiz Service Requirements
```json
{
  "content_type": "question",
  "certification_type": "ANS",
  "metadata": {
    "question_text": "Your question here?",
    "answer_options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "question_type": "multiple_choice"
  }
}
```

---

## 🎯 Prevention Best Practices

1. **Always test authentication after deployments**
2. **Use consistent token formats across all requests**
3. **Monitor CloudWatch logs for authentication patterns**
4. **Keep backup of working configuration**
5. **Document any configuration changes**
6. **Test with fresh tokens when debugging**
7. **Verify content ingestion before testing quiz functionality**

---

**Remember**: Most authentication issues are temporary deployment/caching problems, not fundamental configuration issues. When in doubt, redeploy and test with fresh tokens! 🚀
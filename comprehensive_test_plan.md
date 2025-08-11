# ProCert Learning Platform - Comprehensive Testing Plan

## Current Status
- ✅ Task 1: Enhanced Chatbot Service - Implemented
- ✅ Task 2: User Authentication and Profile Management - Implemented
- ❌ API Gateway endpoints returning 403 Forbidden - **NEEDS INVESTIGATION**

## Testing Strategy

### Phase 1: Infrastructure Verification (AWS Console)

#### 1.1 API Gateway Check
**Action Required:** Access AWS Console → API Gateway
- Verify the API Gateway deployment exists
- Check if the API is deployed to the "prod" stage
- Verify CORS configuration
- Check resource policies and authorizers

#### 1.2 Lambda Functions Check
**Action Required:** Access AWS Console → Lambda
- Verify these functions exist and are deployed:
  - `procert-chat-handler`
  - `procert-auth-register`
  - `procert-auth-login`
  - `procert-profile-get`
  - `procert-profile-update`
- Check function logs in CloudWatch for any errors

#### 1.3 Cognito User Pool Check
**Action Required:** Access AWS Console → Cognito
- Verify User Pool exists
- Check User Pool configuration
- Verify App Client settings
- Test user creation manually

#### 1.4 DynamoDB Tables Check
**Action Required:** Access AWS Console → DynamoDB
- Verify these tables exist:
  - `procert-user-profiles`
  - `procert-conversations`
  - `procert-content` (existing)
- Check table schemas and indexes

### Phase 2: Manual Testing (Console-Based)

#### 2.1 Create Test Users via Cognito Console
1. Go to Cognito User Pool
2. Create test users manually:
   - `test1@example.com` / `TestPass123!`
   - `test2@example.com` / `TestPass123!`
   - `admin@example.com` / `AdminPass123!`

#### 2.2 Test S3 Content Upload
1. Access S3 bucket: `procert-content-bucket`
2. Upload test content files:
   - Quiz questions JSON
   - Study materials
   - Reference documents

### Phase 3: API Testing (Once Infrastructure is Fixed)

#### 3.1 Authentication Flow Testing
```bash
# Test user registration
curl -X POST "https://API_URL/prod/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "TestPass123!",
    "given_name": "New",
    "family_name": "User",
    "target_certifications": ["SAA"]
  }'

# Test user login
curl -X POST "https://API_URL/prod/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "TestPass123!"
  }'
```

#### 3.2 Chatbot Testing
```bash
# Test basic chat
curl -X POST "https://API_URL/prod/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Amazon EC2?",
    "certification": "SAA",
    "user_id": "test-user"
  }'

# Test enhanced mode
curl -X POST "https://API_URL/prod/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain AWS Lambda pricing",
    "certification": "SAA",
    "user_id": "test-user",
    "mode": "enhanced"
  }'
```

#### 3.3 Profile Management Testing
```bash
# Get user profile (requires auth token)
curl -X GET "https://API_URL/prod/profile/USER_ID" \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Update user profile
curl -X PUT "https://API_URL/prod/profile/USER_ID" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "target_certifications": ["SAA", "DVA"],
    "study_preferences": {
      "daily_goal_minutes": 60,
      "preferred_difficulty": "advanced"
    }
  }'
```

### Phase 4: Content Upload and Management

#### 4.1 S3 Content Structure
```
procert-content-bucket/
├── questions/
│   ├── saa/
│   │   ├── ec2-questions.json
│   │   ├── s3-questions.json
│   │   └── iam-questions.json
│   └── dva/
│       ├── lambda-questions.json
│       └── dynamodb-questions.json
├── study-materials/
│   ├── saa/
│   │   ├── ec2-guide.md
│   │   └── s3-best-practices.md
│   └── dva/
│       └── lambda-patterns.md
└── references/
    ├── aws-whitepapers/
    └── certification-guides/
```

#### 4.2 Sample Question Format
```json
{
  "questions": [
    {
      "id": "saa-ec2-001",
      "question": "Which EC2 instance type is best for compute-intensive applications?",
      "options": [
        "t3.micro",
        "c5.large",
        "r5.large",
        "i3.large"
      ],
      "correct_answer": 1,
      "explanation": "C5 instances are optimized for compute-intensive applications...",
      "difficulty": "intermediate",
      "topics": ["EC2", "Instance Types"],
      "certification": "SAA"
    }
  ]
}
```

### Phase 5: Integration Testing

#### 5.1 End-to-End User Journey
1. User registration
2. Profile setup
3. Chat interaction
4. Content retrieval
5. Progress tracking

#### 5.2 Performance Testing
- API response times
- Concurrent user handling
- Database query performance

## Immediate Action Items

### 🚨 Priority 1: Fix API Gateway Issues
1. **Check API Gateway Deployment**
   - Verify deployment to "prod" stage
   - Check resource policies
   - Verify CORS settings

2. **Check Lambda Function Permissions**
   - Verify API Gateway can invoke Lambda functions
   - Check IAM roles and policies

3. **Review CloudWatch Logs**
   - Check for deployment errors
   - Look for permission issues

### 📋 Priority 2: Manual Console Testing
1. **Create test users in Cognito**
2. **Upload sample content to S3**
3. **Test Lambda functions directly**

### 🧪 Priority 3: Automated Testing
1. **Fix and run authentication tests**
2. **Create chatbot integration tests**
3. **Build end-to-end test suite**

## Next Steps

1. **Investigate 403 Forbidden errors** - Check AWS Console
2. **Manual testing via AWS Console** - Create users, test functions
3. **Content upload** - Add sample questions and materials
4. **Fix API issues** - Redeploy if necessary
5. **Run comprehensive test suite** - Validate all functionality

Would you like me to guide you through any specific part of this testing plan?
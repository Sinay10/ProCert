# 🚀 ProCert Learning Platform - Demo Guide

Welcome to the ProCert Learning Platform demo! This guide will walk you through the key features we've implemented for AWS certification learning.

## 📋 What We've Built

### ✅ **Task 1: Content Ingestion & RAG System**
- Multi-certification S3 buckets (SAA, DVA, SOA, CCP, etc.)
- Automated PDF processing and chunking
- Vector embeddings with Amazon Titan
- OpenSearch Serverless for semantic search
- Intelligent chatbot with RAG capabilities

### ✅ **Task 2: User Authentication & Profile Management**
- AWS Cognito user authentication
- JWT-based API authorization
- User profile management
- Study preferences and certification tracking
- Secure API endpoints

---

## 🚀 **Quick Working Demo** (Ready to Run!)

### **Current System Status:**
- ✅ **Content Loaded**: AWS Advanced Networking Specialty (ANS) sample questions
- ✅ **Authentication**: Fully functional user registration and login
- ✅ **Vector Search**: 29 networking-related chunks indexed and searchable
- ✅ **Rate Limiting Optimized**: Improved retry logic with 25s Lambda timeout
- ✅ **All Demo Queries Working**: When spaced 30+ seconds apart

### **Working Demo Commands:**

#### **1. Test Content Queries (ANS Content Available)**
**⚠️ IMPORTANT**: Space queries 30+ seconds apart to avoid Bedrock rate limiting

```bash
# ✅ WORKING: Query about CloudFront and NLB (partial content available)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I configure CloudFront with Network Load Balancer?"}'
# Expected: Partial answer with offer for enhanced mode

# Wait 30 seconds, then:
# ✅ WORKING: Query about Route 53 Resolver (comprehensive content available)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Route 53 Resolver?"}'
# Expected: Comprehensive answer about Route 53 Resolver from ANS materials

# Wait 30 seconds, then:
# ✅ WORKING: Query without available content (shows fallback behavior)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AWS Lambda and how does it work?"}'
# Expected: "I don't have enough information... Would you like enhanced mode?"
```

#### **2. Test Authentication Flow**
```bash
# ✅ WORKING: Step 1 - Register (use unique email each time)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo-unique-123@example.com", "password": "DemoPass123!", "name": "Demo User", "target_certifications": ["ANS", "SAA"]}'
# Expected: User registration success with user_id and profile

# ✅ WORKING: Step 2 - Login
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo-unique-123@example.com", "password": "DemoPass123!"}'
# Expected: Login success with JWT tokens (access_token, id_token, refresh_token)

# ✅ WORKING: Step 3 - Access Protected Profile (replace with your tokens)
curl -X GET "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/profile/YOUR_USER_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
# Expected: User profile with study preferences and certifications
```

**Working Example (from our test):**
```bash
# Registration Response:
{"message": "User registered successfully", "user_id": "b4c87458-4041-70ff-2e05-9dd9b0619a82", ...}

# Login Response:
{"message": "Login successful", "tokens": {"access_token": "eyJraWQ...", ...}}

# Profile Response:
{"profile": {"email": "demo-test-123@example.com", "target_certifications": ["ANS", "SAA"], ...}}
```

---

## 🎯 Demo Scenarios

### **Scenario 1: Content Ingestion & RAG System**

#### 1.1 Upload Study Materials
```bash
# Upload a PDF to the SAA certification bucket
aws s3 cp your-saa-study-guide.pdf s3://procert-materials-saa-353207798766/

# Upload to DVA certification bucket
aws s3 cp your-dva-practice-exam.pdf s3://procert-materials-dva-353207798766/
```

**Expected Result**: 
- Lambda function automatically processes the PDF
- Content is chunked and embedded
- Vector data stored in OpenSearch
- Metadata saved to DynamoDB

#### 1.2 Query the RAG System
```bash
# Ask a general networking question (we have ANS content loaded)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I configure Amazon CloudFront with Network Load Balancer?"}'
```

**Expected Response**:
```json
{
  "answer": "Based on the AWS Advanced Networking Specialty materials, to configure Amazon CloudFront with a Network Load Balancer (NLB), you should create a CloudFront distribution with the NLB endpoint as the origin..."
}
```

#### 1.3 Certification-Specific Queries
```bash
# Ask ANS-specific question (we have ANS content loaded)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are Route 53 Resolver outbound endpoint configurations?",
    "certification": "ANS"
  }'
```

**Expected Result**: Response focused on ANS-specific networking content and configurations.

#### 1.4 Content Without Context
```bash
# Ask about something not in our knowledge base
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AWS Lambda and how does it work?"}'
```

**Expected Response**:
```json
{
  "answer": "I don't have enough information in the study materials to answer that question. Would you like me to use enhanced mode for broader AWS knowledge?"
}
```

---

### **Scenario 2: User Authentication System**

#### 2.1 User Registration
```bash
# Register a new user (use a unique email each time)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo-'$(date +%s)'@example.com",
    "password": "DemoPass123!",
    "name": "Demo User",
    "target_certifications": ["ANS", "SAA"]
  }'
```

**Note**: Use a unique email for each registration attempt, or the system will return "User already exists".

**Expected Response**:
```json
{
  "message": "User registered successfully",
  "user_id": "abc123-def456-ghi789",
  "profile": {
    "user_id": "abc123-def456-ghi789",
    "email": "demo@example.com",
    "name": "Demo User",
    "target_certifications": ["SAA", "DVA"],
    "study_preferences": {
      "daily_goal_minutes": 30,
      "preferred_difficulty": "intermediate",
      "preferred_study_time": "evening"
    },
    "subscription_tier": "free",
    "total_study_time": 0
  }
}
```

#### 2.2 User Login
```bash
# Login to get JWT tokens (use the email from registration)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "YOUR_REGISTERED_EMAIL_HERE",
    "password": "DemoPass123!"
  }'
```

**Tip**: Replace `YOUR_REGISTERED_EMAIL_HERE` with the email you used in registration.

**Expected Response**:
```json
{
  "message": "Login successful",
  "user_id": "abc123-def456-ghi789",
  "tokens": {
    "access_token": "eyJraWQiOiJ...",
    "id_token": "eyJraWQiOiJ...",
    "refresh_token": "eyJjdHkiOiJ..."
  }
}
```

#### 2.3 Access Protected Profile
```bash
# Get user profile (requires JWT token)
curl -X GET "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/profile/abc123-def456-ghi789" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Expected Response**:
```json
{
  "profile": {
    "user_id": "abc123-def456-ghi789",
    "email": "demo@example.com",
    "name": "Demo User",
    "target_certifications": ["SAA", "DVA"],
    "study_preferences": {
      "daily_goal_minutes": 30,
      "preferred_difficulty": "intermediate"
    },
    "total_study_time": 0,
    "achievements": []
  }
}
```

#### 2.4 Update User Profile
```bash
# Update study preferences
curl -X PUT "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/profile/abc123-def456-ghi789" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "study_preferences": {
      "daily_goal_minutes": 60,
      "preferred_difficulty": "advanced",
      "preferred_study_time": "morning"
    },
    "target_certifications": ["SAA", "DVA", "SOA"]
  }'
```

**Expected Response**:
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "study_preferences": {
      "daily_goal_minutes": 60,
      "preferred_difficulty": "advanced",
      "preferred_study_time": "morning"
    },
    "target_certifications": ["SAA", "DVA", "SOA"]
  }
}
```

---

### **Scenario 3: Integrated User Experience**

#### 3.1 Authenticated Chat Queries
```bash
# Chat with personalized context (requires JWT)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/chat/message" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "message": "What should I study next for my SAA certification?",
    "certification": "SAA"
  }'
```

**Expected Result**: Personalized response based on user's study preferences and target certifications.

#### 3.2 Password Reset Flow
```bash
# Initiate password reset
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com"}'

# Confirm password reset (after receiving code via email)
curl -X POST "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/auth/confirm-forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "confirmation_code": "123456",
    "new_password": "NewDemoPass123!"
  }'
```

---

## 🏗️ Architecture Highlights

### **Infrastructure Components**
- **13 S3 Buckets**: One for each AWS certification type
- **6 DynamoDB Tables**: Content metadata, user profiles, conversations, etc.
- **4 Lambda Functions**: Ingestion, chatbot, user profile, JWT authorizer
- **OpenSearch Serverless**: Vector search and semantic matching
- **Cognito User Pool**: Secure authentication and user management
- **API Gateway**: RESTful API with JWT authorization

### **Security Features**
- JWT-based authentication with Cognito
- API Gateway authorizer for protected endpoints
- Encrypted DynamoDB tables with point-in-time recovery
- S3 bucket policies enforcing HTTPS and TLS 1.2+
- IAM roles with least-privilege access

### **Scalability Features**
- Serverless architecture (auto-scaling)
- Pay-per-request DynamoDB billing
- OpenSearch Serverless (managed scaling)
- CloudFront distribution for global access
- Multi-certification content organization

---

## 🧪 Testing the System

### **Quick Test Script**
```bash
# Run our comprehensive test
python3 test_fresh_token.py
```

**Expected Output**:
```
🔐 Testing with fresh token...
1. Registering new user...
✅ User registered: e4f8c4f8-20d1-70d9-79ef-d85ff2cf18cf
2. Logging in to get fresh token...
✅ Fresh token obtained
3. Testing protected endpoint with fresh token...
Status Code: 200
✅ Fresh token test successful!
```

### **Manual Testing Checklist**
- [ ] User registration works
- [ ] User login returns valid JWT tokens
- [ ] Protected endpoints require authentication
- [ ] Profile CRUD operations work
- [ ] Content ingestion processes PDFs
- [ ] RAG system returns relevant answers
- [ ] Certification-specific queries work
- [ ] Password reset flow functions

---

## 🎯 Key Demo Points

### **For Technical Audience**
1. **Serverless Architecture**: Show AWS Lambda auto-scaling
2. **Vector Search**: Demonstrate semantic similarity matching
3. **JWT Security**: Explain token validation and authorization
4. **Multi-tenancy**: Show certification-specific content isolation
5. **Real-time Processing**: Upload PDF → automatic processing → queryable content

### **For Business Audience**
1. **User Experience**: Seamless registration and personalized learning
2. **Content Management**: Easy upload and organization by certification
3. **Scalability**: Handles multiple users and certifications
4. **Security**: Enterprise-grade authentication and data protection
5. **Cost Efficiency**: Pay-per-use serverless model

---

## 🚀 Next Steps

### **Potential Enhancements**
- Quiz generation from content
- Progress tracking and analytics
- Study recommendations based on performance
- Mobile app integration
- Advanced content filtering and search
- Integration with AWS Training and Certification

### **Monitoring & Observability**
- CloudWatch dashboards for system metrics
- X-Ray tracing for request flow analysis
- Custom metrics for user engagement
- Error tracking and alerting

---

## 📞 Support

For questions or issues during the demo:
- Check CloudWatch logs for detailed error information
- Verify JWT tokens haven't expired (1-hour lifetime)
- Ensure proper Content-Type headers in requests
- Validate JSON request body formatting

**API Endpoint**: `https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod/`

**Available Certifications**: CCP, AIP, SAA, DVA, SOA, MLA, DEA, DOP, SAP, MLS, SCS, ANS, GENERAL

---

*Happy Learning! 🎓*
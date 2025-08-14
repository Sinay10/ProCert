# API Gateway Enhancements Documentation

## Overview

This document describes the enhanced API Gateway configuration implemented for the ProCert Learning Platform. The enhancements include comprehensive request/response validation, CORS configuration, rate limiting, throttling, and monitoring.

## Key Features

### 1. Enhanced CORS Configuration

- **Specific Origins**: Configured to allow specific origins instead of wildcard
- **Comprehensive Headers**: Supports all necessary headers for web applications
- **Credentials Support**: Enables credential-based requests
- **Preflight Caching**: Optimized preflight request caching

```python
default_cors_preflight_options=apigateway.CorsOptions(
    allow_origins=["http://localhost:3000", "https://*.procert.app", "https://procert.app"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key",
        "X-Amz-Security-Token", "X-Requested-With", "Accept", "Origin", "Referer"
    ],
    expose_headers=["X-Request-Id", "X-Rate-Limit-Remaining"],
    allow_credentials=True,
    max_age=Duration.hours(1)
)
```

### 2. Request/Response Validation

#### JSON Schema Models

The API Gateway includes comprehensive JSON schema validation for all endpoints:

- **Chat Message Model**: Validates chat requests with message length, certification types, and mode selection
- **Quiz Generation Model**: Validates quiz parameters including difficulty, count limits, and user identification
- **Quiz Submission Model**: Validates quiz answers with proper formatting and limits
- **User Profile Model**: Validates user profile data with email format and preference constraints
- **Progress Interaction Model**: Validates progress tracking data with interaction types and content identification
- **Recommendation Feedback Model**: Validates feedback data with action types and length limits
- **Authentication Models**: Validates registration and login requests with proper email and password requirements

#### Example Schema (Chat Message):

```python
chat_message_model = api.add_model("ChatMessageModel",
    content_type="application/json",
    model_name="ChatMessageRequest",
    schema=apigateway.JsonSchema(
        schema=apigateway.JsonSchemaVersion.DRAFT4,
        title="Chat Message Request",
        type=apigateway.JsonSchemaType.OBJECT,
        properties={
            "message": apigateway.JsonSchema(
                type=apigateway.JsonSchemaType.STRING,
                min_length=1,
                max_length=2000
            ),
            "certification": apigateway.JsonSchema(
                type=apigateway.JsonSchemaType.STRING,
                enum=["general", "ccp", "aip", "saa", "dva", "soa", "mla", "dea", "dop", "sap", "mls", "scs", "ans"]
            ),
            "mode": apigateway.JsonSchema(
                type=apigateway.JsonSchemaType.STRING,
                enum=["rag", "enhanced"]
            )
        },
        required=["message"]
    )
)
```

### 3. Rate Limiting and Throttling

#### Global API Throttling

- **Rate Limit**: 1,000 requests per second
- **Burst Limit**: 2,000 requests
- **Per-method Throttling**: Customized limits based on endpoint complexity

#### Method-Specific Rate Limits

| Endpoint Category | Rate Limit (req/sec) | Burst Limit | Reasoning |
|------------------|---------------------|-------------|-----------|
| Chat Messages | 100 | 200 | High-frequency interactive use |
| Quiz Generation | 30 | 60 | Moderate computational load |
| Quiz Submission | 20 | 40 | Processing-intensive operations |
| Progress Tracking | 200 | 400 | High-frequency data collection |
| Recommendations | 30 | 60 | ML-based computations |
| Authentication | 10-20 | 20-50 | Security-sensitive operations |
| Profile Management | 5-50 | 10-100 | Varies by operation type |

#### Usage Plans

Two usage plans are configured:

1. **Basic Plan**: 
   - 500 req/sec, 1,000 burst
   - 10,000 requests per day quota

2. **Premium Plan**: 
   - 1,000 req/sec, 2,000 burst
   - 50,000 requests per day quota

### 4. Authentication and Authorization

#### JWT Token Validation

- **Custom Authorizer**: Lambda-based JWT token validation
- **Cognito Integration**: Seamless integration with AWS Cognito User Pool
- **Token Caching**: 5-minute cache TTL for performance optimization

#### Protected Endpoints

All learning platform endpoints require authentication except:
- `/auth/register`
- `/auth/login`
- `/auth/forgot-password`
- `/auth/confirm-forgot-password`

### 5. Monitoring and Alerting

#### CloudWatch Alarms

1. **Error Rate Alarm**:
   - Threshold: 50 4XX errors in 5 minutes
   - Evaluation: 2 consecutive periods

2. **Latency Alarm**:
   - Threshold: 5 seconds average latency
   - Evaluation: 3 consecutive periods

3. **Throttling Alarm**:
   - Threshold: 10 throttled requests per minute
   - Evaluation: 2 consecutive periods

#### API Keys

- **Web Application Key**: For web client identification
- **Mobile Application Key**: For mobile client identification
- **Usage Tracking**: Associated with usage plans for monitoring

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/auth/register` | User registration | 10 req/sec |
| POST | `/auth/login` | User login | 20 req/sec |
| POST | `/auth/forgot-password` | Password reset request | 5 req/sec |
| POST | `/auth/confirm-forgot-password` | Password reset confirmation | 5 req/sec |

### Chat Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/chat/message` | Send chat message | 100 req/sec |
| GET | `/chat/conversation/{id}` | Get conversation | 50 req/sec |
| DELETE | `/chat/conversation/{id}` | Delete conversation | 20 req/sec |

### Quiz Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/quiz/generate` | Generate new quiz | 30 req/sec |
| POST | `/quiz/submit` | Submit quiz answers | 20 req/sec |
| GET | `/quiz/history/{user_id}` | Get quiz history | 50 req/sec |
| GET | `/quiz/{quiz_id}` | Get quiz details | 100 req/sec |

### Progress Tracking Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/progress/{user_id}/interaction` | Record interaction | 200 req/sec |
| GET | `/progress/{user_id}/analytics` | Get analytics | 50 req/sec |
| GET | `/progress/{user_id}/trends` | Get trends | 30 req/sec |
| GET | `/progress/{user_id}/readiness` | Get readiness | 20 req/sec |
| GET | `/progress/{user_id}/achievements` | Get achievements | 30 req/sec |
| GET | `/progress/{user_id}/dashboard` | Get dashboard | 20 req/sec |

### Recommendation Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/recommendations/{user_id}` | Get recommendations | 30 req/sec |
| GET | `/recommendations/{user_id}/study-path` | Get study path | 20 req/sec |
| POST | `/recommendations/{user_id}/feedback` | Submit feedback | 50 req/sec |
| GET | `/recommendations/{user_id}/weak-areas` | Get weak areas | 20 req/sec |
| GET | `/recommendations/{user_id}/content-progression` | Get progression | 15 req/sec |

### Profile Management Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/profile/{user_id}` | Get user profile | 50 req/sec |
| PUT | `/profile/{user_id}` | Update user profile | 20 req/sec |
| DELETE | `/profile/{user_id}` | Delete user profile | 5 req/sec |

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `THROTTLED`: Rate limit exceeded
- `INTERNAL_ERROR`: Server-side error

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (validation error)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict (e.g., user already exists)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

## Testing

### Integration Tests

The API Gateway includes comprehensive integration tests:

1. **Request Validation Tests**: Verify all JSON schema validations
2. **CORS Tests**: Validate CORS headers and preflight requests
3. **Authentication Tests**: Verify JWT token validation
4. **Rate Limiting Tests**: Test throttling behavior
5. **Error Handling Tests**: Validate error response formats

### Running Tests

```bash
# Run all API Gateway tests
python scripts/test_api_gateway.py

# Run specific pytest tests
python -m pytest tests/integration/test_enhanced_api_gateway.py -v

# Run live endpoint validation
python -m pytest tests/integration/test_api_endpoint_validation.py -v
```

### Environment Variables for Testing

```bash
export API_ENDPOINT="https://your-api-id.execute-api.region.amazonaws.com/prod"
export API_KEY="your-api-key"
export TEST_JWT_TOKEN="your-test-jwt-token"
```

## Deployment

### CDK Deployment

The enhanced API Gateway is deployed as part of the main CDK stack:

```bash
cdk deploy
```

### Configuration Outputs

After deployment, the following outputs are available:

- `ApiEndpoint`: The API Gateway endpoint URL
- `ApiId`: The API Gateway ID
- `WebAppApiKeyId`: Web application API key ID
- `MobileAppApiKeyId`: Mobile application API key ID
- `BasicUsagePlanId`: Basic usage plan ID
- `PremiumUsagePlanId`: Premium usage plan ID

## Security Considerations

### Input Validation

- All requests are validated against JSON schemas
- Path parameters are validated for format and length
- Query parameters are validated for allowed values
- Request body size limits are enforced

### Rate Limiting

- Multiple layers of rate limiting (global, usage plan, method-level)
- Burst capacity to handle traffic spikes
- Gradual backoff for sustained high traffic

### Authentication

- JWT token validation with proper expiration checking
- Secure token transmission requirements
- Authorization caching for performance

### CORS Security

- Specific origin allowlisting instead of wildcards
- Controlled header exposure
- Credential handling restrictions

## Performance Optimization

### Caching

- API Gateway response caching (where appropriate)
- JWT authorizer result caching (5 minutes)
- Preflight request caching (1 hour)

### Connection Management

- Keep-alive connections
- Connection pooling in Lambda functions
- Optimized timeout settings

### Monitoring

- Real-time performance metrics
- Automated alerting on performance degradation
- Usage analytics for optimization

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check origin configuration and preflight handling
2. **Validation Errors**: Verify request format against JSON schemas
3. **Rate Limiting**: Check usage plan limits and method-specific throttling
4. **Authentication Failures**: Verify JWT token format and expiration

### Debug Tools

- CloudWatch Logs for detailed request/response logging
- X-Ray tracing for request flow analysis
- API Gateway execution logs for validation details
- Custom metrics for business logic monitoring

## Future Enhancements

### Planned Improvements

1. **Advanced Rate Limiting**: User-specific rate limiting
2. **Request/Response Transformation**: Data format standardization
3. **API Versioning**: Support for multiple API versions
4. **Enhanced Monitoring**: Business metrics and user behavior analytics
5. **Caching Optimization**: Intelligent response caching strategies

### Scalability Considerations

- Auto-scaling based on traffic patterns
- Regional deployment for global performance
- CDN integration for static content
- Database connection pooling optimization
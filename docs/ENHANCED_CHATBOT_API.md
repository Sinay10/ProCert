# Enhanced Chatbot API Documentation

## Overview

The Enhanced Chatbot Service provides intelligent conversational AI capabilities with dual-mode response system for AWS certification study. It combines curated study materials (RAG-only mode) with Claude's comprehensive AWS knowledge (enhanced mode) to provide accurate, contextual responses.

## Key Features

- **Dual-Mode Response System**: RAG-only mode for curated content, Enhanced mode for broader AWS knowledge
- **Intelligent Mode Selection**: Automatic mode selection based on content quality and relevance
- **Conversation Management**: Persistent conversation history with context awareness
- **Source Transparency**: Clear attribution of information sources
- **Certification-Specific Filtering**: Content filtering by AWS certification type
- **Backward Compatibility**: Maintains compatibility with existing `/query` endpoint

## API Endpoints

### Base URL
```
https://your-api-gateway-url.amazonaws.com/prod
```

### 1. Send Chat Message

**Endpoint:** `POST /chat/message`

**Description:** Send a message to the chatbot and receive a response.

**Request Body:**
```json
{
  "message": "What is Amazon EC2?",
  "conversation_id": "optional-conversation-id",
  "certification": "SAA",
  "mode": "rag",
  "user_id": "user123"
}
```

**Request Parameters:**
- `message` (required): The user's question or message
- `conversation_id` (optional): ID of existing conversation to continue
- `certification` (optional): AWS certification context (CCP, SAA, DVA, etc.)
- `mode` (optional): Response mode - "rag" or "enhanced"
- `user_id` (optional): User identifier (defaults to "anonymous")

**Response:**
```json
{
  "response": "Amazon EC2 (Elastic Compute Cloud) is a web service...",
  "sources": [
    {
      "content_id": "ec2-guide-1",
      "score": 0.95,
      "certification_type": "SAA",
      "source_file": "SAA-study-guide.pdf"
    }
  ],
  "mode_used": "rag",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "context_quality": {
    "parts_found": 3,
    "avg_score": 0.87
  }
}
```

### 2. Get Conversation

**Endpoint:** `GET /chat/conversation/{id}`

**Description:** Retrieve a conversation by ID.

**Path Parameters:**
- `id`: The conversation ID

**Response:**
```json
{
  "conversation": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "messages": [
      {
        "role": "user",
        "content": "What is EC2?",
        "timestamp": "2025-01-08T10:30:00Z",
        "sources": [],
        "mode_used": null,
        "metadata": {"certification": "SAA"}
      },
      {
        "role": "assistant",
        "content": "Amazon EC2 is...",
        "timestamp": "2025-01-08T10:30:02Z",
        "sources": ["ec2-guide-1"],
        "mode_used": "rag",
        "metadata": {"context_parts_count": 3}
      }
    ],
    "certification_context": "SAA",
    "preferred_mode": "rag",
    "created_at": "2025-01-08T10:30:00Z",
    "updated_at": "2025-01-08T10:30:02Z"
  }
}
```

### 3. Delete Conversation

**Endpoint:** `DELETE /chat/conversation/{id}`

**Description:** Delete a conversation and its history.

**Path Parameters:**
- `id`: The conversation ID

**Response:**
```json
{
  "success": true
}
```

### 4. Legacy Query Endpoint (Backward Compatibility)

**Endpoint:** `POST /query`

**Description:** Legacy endpoint for backward compatibility.

**Request Body:**
```json
{
  "question": "What is Amazon S3?"
}
```

**Response:**
```json
{
  "answer": "Amazon S3 (Simple Storage Service) is..."
}
```

## Response Modes

### RAG-Only Mode
- Uses only curated study materials from the knowledge base
- Provides source citations from study materials
- Responds with "insufficient information" message when content is not available
- Best for certification-specific questions with good study material coverage

### Enhanced Mode
- Combines study materials with Claude's comprehensive AWS knowledge
- Provides broader context and up-to-date information
- Clearly distinguishes between study material content and general AWS knowledge
- Best for complex scenarios, latest AWS updates, or when study materials are insufficient

### Automatic Mode Selection
The system automatically selects the appropriate mode based on:
- Content availability and relevance scores
- Question complexity and context
- User preferences and conversation history

## Error Handling

### Error Response Format
```json
{
  "error": "Error message description"
}
```

### Common Error Codes
- `400 Bad Request`: Missing required parameters or invalid input
- `404 Not Found`: Conversation not found
- `500 Internal Server Error`: Server-side processing error

## Usage Examples

### Python Example
```python
import requests

api_endpoint = "https://your-api-gateway-url.amazonaws.com/prod"
headers = {"Content-Type": "application/json"}

# Send a message
response = requests.post(
    f"{api_endpoint}/chat/message",
    headers=headers,
    json={
        "message": "What are EC2 instance types?",
        "certification": "SAA",
        "mode": "rag",
        "user_id": "user123"
    }
)

data = response.json()
print(f"Response: {data['response']}")
print(f"Mode used: {data['mode_used']}")
print(f"Conversation ID: {data['conversation_id']}")
```

### JavaScript Example
```javascript
const apiEndpoint = "https://your-api-gateway-url.amazonaws.com/prod";

async function sendMessage(message, conversationId = null) {
    const response = await fetch(`${apiEndpoint}/chat/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            conversation_id: conversationId,
            certification: "SAA",
            user_id: "user123"
        })
    });
    
    const data = await response.json();
    return data;
}

// Usage
sendMessage("What is Amazon EC2?").then(data => {
    console.log("Response:", data.response);
    console.log("Mode used:", data.mode_used);
});
```

### cURL Example
```bash
curl -X POST "https://your-api-gateway-url.amazonaws.com/prod/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Amazon EC2?",
    "certification": "SAA",
    "mode": "rag",
    "user_id": "user123"
  }'
```

## Best Practices

### For RAG-Only Mode
- Use for certification-specific questions
- Specify certification type for better filtering
- Expect source citations in responses
- Handle "insufficient information" responses gracefully

### For Enhanced Mode
- Use for complex scenarios or latest AWS information
- Understand that responses combine multiple knowledge sources
- Verify critical information against official AWS documentation
- Use when study materials don't cover the topic adequately

### Conversation Management
- Store conversation IDs for multi-turn conversations
- Use consistent user IDs for better personalization
- Clean up conversations when no longer needed
- Handle conversation expiration (7-day TTL)

### Error Handling
- Implement retry logic for transient errors
- Validate input parameters before sending requests
- Handle rate limiting gracefully
- Provide fallback responses for service unavailability

## Rate Limits and Quotas

- **Request Rate**: Limited by API Gateway throttling settings
- **Conversation TTL**: 7 days automatic cleanup
- **Message History**: Up to 10 recent messages used for context
- **Response Timeout**: 60 seconds maximum processing time

## Security Considerations

- **CORS**: Configured for cross-origin requests
- **Authentication**: Currently supports anonymous users (extend with Cognito for production)
- **Input Validation**: All inputs are validated and sanitized
- **Data Privacy**: Conversations are automatically cleaned up after TTL expiration

## Monitoring and Observability

The service includes comprehensive logging and monitoring:
- **CloudWatch Logs**: Detailed request/response logging
- **CloudWatch Metrics**: Performance and error rate metrics
- **X-Ray Tracing**: Distributed tracing for debugging
- **Custom Metrics**: Business KPIs and usage analytics

## Deployment

The enhanced chatbot service is deployed as part of the ProCert infrastructure stack:

```bash
# Deploy the infrastructure
cdk deploy

# The API endpoint will be output after successful deployment
```

## Migration from Legacy Chatbot

The enhanced chatbot maintains backward compatibility with the existing `/query` endpoint. To migrate:

1. **Immediate**: Continue using `/query` endpoint (no changes required)
2. **Gradual**: Update clients to use `/chat/message` endpoint for new features
3. **Complete**: Migrate all clients to new endpoints and deprecate `/query`

## Support and Troubleshooting

### Common Issues

1. **"Insufficient information" responses**: Switch to enhanced mode or add more study materials
2. **Conversation not found**: Check conversation ID and TTL expiration
3. **Slow responses**: Monitor CloudWatch metrics and consider increasing Lambda memory
4. **CORS errors**: Verify API Gateway CORS configuration

### Debug Information

Each response includes context quality information to help debug issues:
- `parts_found`: Number of relevant content pieces found
- `avg_score`: Average relevance score of found content
- `mode_used`: Actual mode used for the response

For additional support, check CloudWatch logs with the request ID for detailed error information.
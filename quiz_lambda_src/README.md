# Quiz Generation Service

The Quiz Generation Service is a core component of the ProCert Learning Platform that provides intelligent quiz generation, adaptive question selection, and comprehensive scoring with immediate feedback.

## Features

### 🎯 Adaptive Quiz Generation
- **Performance-Based Selection**: Questions are selected based on user's historical performance
- **Weak Area Focus**: Prioritizes topics where the user needs improvement (60% of questions)
- **Balanced Coverage**: Includes questions from untested areas (25%) and strong areas (15%)
- **Anti-Repetition Logic**: Avoids recently answered questions to prevent repetition

### 📊 Comprehensive Scoring
- **Immediate Feedback**: Provides instant results with explanations
- **Detailed Analytics**: Tracks performance by category and difficulty
- **Progress Tracking**: Records all interactions for future adaptive selection
- **Grade Calculation**: Converts scores to letter grades (A-F)

### 🔄 Session Management
- **Persistent Sessions**: Quiz sessions are stored in DynamoDB
- **Status Tracking**: Monitors quiz progress (in_progress, completed, abandoned)
- **Time Limits**: Configurable time limits per quiz
- **History Tracking**: Maintains complete quiz history for each user

## API Endpoints

### Generate Quiz
```http
POST /quiz/generate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "user_id": "user-123",
  "certification_type": "SAA",
  "question_count": 10,
  "difficulty": "mixed"
}
```

**Response:**
```json
{
  "message": "Quiz generated successfully",
  "quiz": {
    "quiz_id": "uuid-here",
    "user_id": "user-123",
    "certification_type": "SAA",
    "questions": [
      {
        "question_id": "q1",
        "question_text": "What is Amazon S3?",
        "options": ["A storage service", "A compute service", "A database service", "A networking service"],
        "category": "storage",
        "difficulty": "beginner"
      }
    ],
    "status": "in_progress",
    "started_at": "2025-01-01T12:00:00Z",
    "time_limit_minutes": 20,
    "metadata": {
      "adaptive_selection": true,
      "user_performance_considered": true
    }
  }
}
```

### Submit Quiz
```http
POST /quiz/submit
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "quiz_id": "uuid-here",
  "answers": [
    {
      "question_id": "q1",
      "selected_answer": "A storage service"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Quiz submitted successfully",
  "results": {
    "quiz_id": "uuid-here",
    "score": 85.0,
    "correct_answers": 8,
    "total_questions": 10,
    "percentage": 85.0,
    "results": [
      {
        "question_id": "q1",
        "question_text": "What is Amazon S3?",
        "user_answer": "A storage service",
        "correct_answer": "A storage service",
        "is_correct": true,
        "explanation": "Amazon S3 is indeed a storage service.",
        "category": "storage"
      }
    ],
    "completed_at": "2025-01-01T12:15:00Z",
    "performance_summary": {
      "passed": true,
      "grade": "B",
      "time_taken": "15 minutes"
    }
  }
}
```

### Get Quiz History
```http
GET /quiz/history/{user_id}?limit=20
Authorization: Bearer <jwt_token>
```

### Get Quiz Details
```http
GET /quiz/{quiz_id}
Authorization: Bearer <jwt_token>
```

## Adaptive Selection Algorithm

The quiz service uses a sophisticated adaptive selection algorithm:

1. **Performance Analysis**: Analyzes user's historical performance by category
2. **Weak Area Identification**: Identifies categories with <70% average score or <70% accuracy
3. **Question Distribution**:
   - 60% from weak areas (prioritized for improvement)
   - 25% from untested areas (for comprehensive coverage)
   - 15% from strong areas (for reinforcement)
4. **Anti-Repetition**: Excludes questions answered in the last 7 days
5. **Difficulty Balancing**: Considers user's difficulty preferences

## Question Parsing

The service can parse questions from various text formats:

```text
Question: What is Amazon S3?
A) A storage service
B) A compute service
C) A database service
D) A networking service
Answer: A) A storage service
Explanation: Amazon S3 is a storage service for the cloud.
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `QUIZ_SESSIONS_TABLE` | DynamoDB table for quiz sessions | Yes |
| `USER_PROGRESS_TABLE` | DynamoDB table for user progress | Yes |
| `CONTENT_METADATA_TABLE` | DynamoDB table for content metadata | Yes |
| `OPENSEARCH_ENDPOINT` | OpenSearch endpoint URL | Yes |
| `OPENSEARCH_INDEX` | OpenSearch index name | Yes |
| `AWS_REGION` | AWS region | Yes |

## Database Schema

### Quiz Sessions Table
- **Partition Key**: `quiz_id` (String)
- **GSI**: `UserQuizIndex` - `user_id` (Hash), `started_at` (Range)

### User Progress Table
- **Partition Key**: `user_id` (String)
- **Sort Key**: `content_id_certification` (String, format: `content_id#certification_type`)
- **GSI**: `UserCertificationIndex` - `user_id` (Hash), `certification_type` (Range)

## Error Handling

The service provides comprehensive error handling:

- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Quiz session or user not found
- **500 Internal Server Error**: Service errors with detailed logging

## Performance Considerations

- **Caching**: User performance data is cached during quiz generation
- **Batch Operations**: Progress tracking uses batch writes for efficiency
- **Connection Pooling**: OpenSearch client uses connection pooling
- **Timeout Management**: Appropriate timeouts for all external calls

## Testing

The service includes comprehensive test coverage:

- **Unit Tests**: Test individual functions and logic
- **Integration Tests**: Test end-to-end workflows
- **Mock Services**: Use mocked AWS services for testing

Run tests:
```bash
python -m pytest tests/unit/test_quiz_service.py -v
python -m pytest tests/integration/test_quiz_integration.py -v
```

## Monitoring and Logging

- **CloudWatch Logs**: Detailed logging for debugging
- **Custom Metrics**: Track quiz generation and completion rates
- **Error Tracking**: Comprehensive error logging with context
- **Performance Metrics**: Monitor response times and success rates

## Security

- **JWT Authentication**: All endpoints require valid JWT tokens
- **Input Validation**: Comprehensive validation of all inputs
- **Data Sanitization**: Proper sanitization of user-provided data
- **Access Control**: User can only access their own quizzes and progress

## Future Enhancements

- **Real-time Collaboration**: Multi-user quiz sessions
- **Advanced Analytics**: ML-powered performance predictions
- **Custom Question Types**: Support for drag-drop, multi-select questions
- **Timed Questions**: Individual question time limits
- **Explanation Enhancement**: AI-generated explanations for incorrect answers
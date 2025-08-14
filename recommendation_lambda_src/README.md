# Recommendation Engine Service

The Recommendation Engine Service provides ML-based personalized study recommendations for the ProCert Learning Platform. It analyzes user performance data to identify weak areas, suggest content difficulty progression, and generate personalized study paths.

## Features

### 1. Personalized Recommendations
- **ML-based analysis** of user performance patterns
- **Priority-based recommendations** (weak areas get higher priority)
- **Content type variety** (study materials, quizzes, reviews)
- **Automatic expiration** of recommendations to keep them fresh

### 2. Weak Area Identification
- **Performance analysis** by category and difficulty level
- **Statistical scoring** to identify areas below 70% performance
- **Severity classification** (high/medium based on score thresholds)
- **Actionable recommendations** for improvement

### 3. Content Difficulty Progression
- **Readiness assessment** for each difficulty level
- **Consistency analysis** using score variance
- **Progressive advancement** recommendations
- **Personalized pacing** based on performance

### 4. Study Path Generation
- **Multi-phase study plans** tailored to certification goals
- **Estimated time calculations** for realistic planning
- **Milestone tracking** with completion targets
- **Adaptive sequencing** based on user strengths/weaknesses

### 5. Feedback Loop
- **User feedback collection** on recommendation quality
- **Continuous improvement** through feedback analysis
- **Action tracking** (accepted, rejected, completed, skipped)
- **Recommendation refinement** based on user preferences

## API Endpoints

### GET /recommendations/{user_id}
Get personalized study recommendations for a user.

**Query Parameters:**
- `certification_type` (optional): Filter by certification (SAA, DVA, etc.)
- `limit` (optional): Maximum recommendations to return (1-50, default: 10)

**Response:**
```json
{
  "user_id": "user-123",
  "certification_type": "SAA",
  "recommendations": [
    {
      "recommendation_id": "rec-456",
      "type": "content",
      "priority": 8,
      "content_id": "content-789",
      "reasoning": "Review EC2 fundamentals - current average: 65.0%",
      "estimated_time_minutes": 45,
      "created_at": "2025-01-01T12:00:00Z",
      "expires_at": "2025-01-04T12:00:00Z"
    }
  ],
  "total_count": 1
}
```

### GET /recommendations/{user_id}/study-path
Generate a personalized study path for a certification.

**Query Parameters:**
- `certification_type` (required): Target certification type

**Response:**
```json
{
  "user_id": "user-123",
  "certification_type": "SAA",
  "study_path": {
    "study_phases": [
      {
        "phase": 1,
        "title": "Address Weak Areas",
        "description": "Focus on areas where performance is below average",
        "estimated_time_hours": 8,
        "topics": ["S3", "VPC"],
        "priority": "high"
      }
    ],
    "total_estimated_hours": 24,
    "milestones": [
      {
        "milestone": "Complete Address Weak Areas",
        "estimated_completion_hours": 8,
        "description": "Focus on areas where performance is below average"
      }
    ]
  }
}
```

### POST /recommendations/{user_id}/feedback
Record user feedback on recommendations.

**Request Body:**
```json
{
  "recommendation_id": "rec-456",
  "action": "accepted",
  "feedback_data": {
    "rating": 5,
    "comment": "Very helpful recommendation!"
  }
}
```

**Actions:** `accepted`, `rejected`, `completed`, `skipped`

### GET /recommendations/{user_id}/weak-areas
Identify weak areas from user performance data.

**Query Parameters:**
- `certification_type` (optional): Filter by certification

**Response:**
```json
{
  "user_id": "user-123",
  "weak_categories": [
    {
      "category": "S3",
      "avg_score": 65.0,
      "attempts": 5,
      "severity": "medium"
    }
  ],
  "recommendations": [
    "Focus on S3 topics",
    "Practice more S3 questions"
  ]
}
```

### GET /recommendations/{user_id}/content-progression
Get content difficulty progression recommendations.

**Query Parameters:**
- `certification_type` (optional): Filter by certification

**Response:**
```json
{
  "user_id": "user-123",
  "progression": {
    "current_level": "beginner",
    "recommended_level": "intermediate",
    "level_readiness": {
      "beginner": {
        "avg_score": 85.0,
        "readiness": 0.82
      }
    },
    "progression_path": [
      "Ready to advance from beginner to intermediate",
      "Start with easier intermediate content"
    ]
  }
}
```

## Algorithm Details

### Recommendation Scoring
1. **Weak Area Priority**: Areas with scores < 70% get priority 7-8
2. **Progression Priority**: Strong areas (>80%) ready for advancement get priority 5-6
3. **Review Priority**: Moderate areas (70-85%) get priority 3-4
4. **Foundational Priority**: New users get priority 9 for basic content

### Performance Analysis
- **Category Performance**: Average scores grouped by content category
- **Difficulty Performance**: Average scores grouped by difficulty level
- **Learning Velocity**: Interactions per day over the last 30 days
- **Consistency Scoring**: Uses standard deviation to measure score consistency

### Study Path Generation
1. **Phase 1**: Address weak areas (high priority)
2. **Phase 2**: Build skills at current level (medium priority)
3. **Phase 3**: Advance to next level if ready (low priority)

### Readiness Calculation
```
readiness = (average_score / 100) * consistency_factor
consistency_factor = 1.0 - (std_deviation / 100)
```

## Environment Variables

- `USER_PROGRESS_TABLE_NAME`: DynamoDB table for user progress data
- `CONTENT_METADATA_TABLE_NAME`: DynamoDB table for content metadata
- `RECOMMENDATIONS_TABLE_NAME`: DynamoDB table for storing recommendations
- `AWS_REGION`: AWS region (default: us-east-1)

## Dependencies

- `boto3`: AWS SDK for Python
- `numpy`: Numerical computing for statistical analysis
- `scikit-learn`: Machine learning utilities for advanced analytics

## Error Handling

The service implements comprehensive error handling:

- **Validation Errors**: Invalid input parameters return 400 status
- **Not Found Errors**: Missing resources return 404 status
- **Service Errors**: Internal failures return 500 status with generic messages
- **Graceful Degradation**: Returns empty results rather than failing completely

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/unit/test_recommendation_engine.py -v

# Integration tests
python -m pytest tests/integration/test_recommendation_lambda.py -v
```

## Example Usage

See `examples/recommendation_engine_example.py` for a complete example of using the recommendation engine programmatically.

## Performance Considerations

- **Caching**: Recommendations are cached with TTL for automatic cleanup
- **Batch Processing**: Uses DynamoDB batch operations for efficiency
- **Lazy Loading**: Content metadata is loaded on-demand
- **Memory Optimization**: Processes data in chunks to manage memory usage

## Security

- **JWT Authentication**: All endpoints require valid JWT tokens
- **Input Validation**: Comprehensive validation of all input parameters
- **Error Sanitization**: Generic error messages to prevent information leakage
- **Rate Limiting**: API Gateway throttling prevents abuse
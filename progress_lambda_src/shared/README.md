# ProCert Shared Models and Interfaces

This module contains the core data models and service interfaces for the ProCert content management system. It provides type-safe, validated data structures and clear contracts for all system components.

## Overview

The shared module is designed to be used across all Lambda functions and services in the ProCert system. It ensures consistency in data handling and provides a single source of truth for data structures.

## Components

### Data Models

#### ContentMetadata
Represents metadata for any piece of content in the system.

```python
from shared import ContentMetadata, ContentType, CertificationType, DifficultyLevel

metadata = ContentMetadata(
    content_id="aws-saa-001",
    title="EC2 Instance Types Overview",
    content_type=ContentType.STUDY_GUIDE,
    certification_type=CertificationType.AWS_SAA,
    category="Compute",
    subcategory="EC2",
    difficulty_level=DifficultyLevel.INTERMEDIATE,
    tags=["ec2", "compute", "instances"],
    source_file="ec2-guide.pdf",
    source_bucket="procert-materials-saa"
)

# Validate the model
if metadata.is_valid():
    print("Metadata is valid")
else:
    print("Validation errors:", metadata.validate())
```

#### QuestionAnswer
Represents question and answer pairs for practice tests.

```python
from shared import QuestionAnswer, DifficultyLevel

question = QuestionAnswer(
    question_id="q-ec2-001",
    content_id="aws-saa-001",
    question_text="Which EC2 instance type is optimized for compute-intensive applications?",
    answer_options=["t3.micro", "c5.large", "r5.large", "i3.large"],
    correct_answer="c5.large",
    explanation="C5 instances are optimized for compute-intensive applications.",
    category="Compute",
    difficulty=DifficultyLevel.INTERMEDIATE,
    tags=["ec2", "instance-types"]
)
```

#### UserProgress
Tracks user interactions and progress with content.

```python
from shared import UserProgress, ProgressType

progress = UserProgress(
    user_id="user-123",
    content_id="aws-saa-001",
    progress_type=ProgressType.COMPLETED,
    score=85.0,
    time_spent=1800,  # 30 minutes in seconds
    session_id="session-abc-123"
)
```

#### VectorDocument
Represents text chunks with vector embeddings for semantic search.

```python
from shared import VectorDocument, CertificationType

# Assuming you have a 1536-dimensional embedding from Titan
embedding = [0.1] * 1536  # Replace with actual embedding

vector_doc = VectorDocument(
    document_id="doc-001-chunk-0",
    content_id="aws-saa-001",
    chunk_index=0,
    text="EC2 provides scalable computing capacity in the AWS cloud...",
    vector_embedding=embedding,
    certification_type=CertificationType.AWS_SAA,
    metadata={"source_page": 1, "section": "Introduction"}
)
```

### Service Interfaces

The module provides abstract interfaces for all major services:

- `IContentIngestionService` - Content upload and initial processing
- `IContentProcessor` - Content transformation and analysis
- `IStorageManager` - Data persistence across storage systems
- `ISearchService` - Content search and retrieval
- `IProgressTracker` - User progress tracking
- `IServiceFactory` - Dependency injection factory
- `IConfiguration` - System configuration management

### Validation

All models include built-in validation:

```python
from shared import validate_model, validate_models

# Validate a single model
try:
    validate_model(metadata)
    print("Model is valid")
except ValueError as e:
    print(f"Validation failed: {e}")

# Validate multiple models
models = [metadata, question, progress]
try:
    validate_models(models)
    print("All models are valid")
except ValueError as e:
    print(f"Validation failed: {e}")
```

### Serialization

All models support dictionary serialization for storage and API responses:

```python
# Convert to dictionary
data_dict = metadata.to_dict()

# Restore from dictionary
restored_metadata = ContentMetadata.from_dict(data_dict)
```

## Usage in Lambda Functions

### Import in Lambda Functions

```python
# Add to your Lambda function
import sys
import os

# Add shared module to path (adjust path as needed)
sys.path.append('/opt/python')  # If using Lambda layers
# OR
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from shared import ContentMetadata, QuestionAnswer, CertificationType
```

### Example: Content Processing Lambda

```python
from shared import (
    ContentMetadata, ContentType, CertificationType, 
    IContentProcessor, ProcessingResult
)

def lambda_handler(event, context):
    # Extract S3 event details
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Detect certification type from bucket or path
    cert_type = CertificationType.AWS_SAA if 'saa' in bucket else CertificationType.GENERAL
    
    # Create metadata
    metadata = ContentMetadata(
        content_id=f"content-{key.replace('/', '-')}",
        title=key.split('/')[-1],
        content_type=ContentType.STUDY_GUIDE,
        certification_type=cert_type,
        category="General",
        source_file=key,
        source_bucket=bucket
    )
    
    # Validate before processing
    if not metadata.is_valid():
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid metadata',
                'details': metadata.validate()
            })
        }
    
    # Continue with processing...
```

## Enumerations

The module provides several enumerations for type safety:

- `ContentType`: QUESTION, STUDY_GUIDE, PRACTICE_EXAM, DOCUMENTATION
- `CertificationType`: AWS_SAA, AWS_DVA, AWS_SOA, GENERAL
- `DifficultyLevel`: BEGINNER, INTERMEDIATE, ADVANCED
- `ProgressType`: VIEWED, ANSWERED, COMPLETED

## Best Practices

1. **Always validate models** before storing or processing
2. **Use enumerations** instead of string literals for type safety
3. **Include meaningful metadata** in all content items
4. **Handle validation errors** gracefully in your Lambda functions
5. **Use the interfaces** to define service contracts clearly

## Testing

Run the included test suite to verify the models work correctly:

```bash
python3 test_models.py
```

## Dependencies

The shared module uses only Python standard library components and has no external dependencies for the core functionality. This ensures it can be easily included in Lambda functions without additional packages.
# StorageManager Implementation

## Overview

The `StorageManager` class provides a comprehensive implementation of the `IStorageManager` interface for the ProCert content management system. It handles all interactions with DynamoDB tables for storing and retrieving content metadata, user progress, and maintaining relationships between content items.

## Features

### Content Metadata Management
- **Store content metadata** with automatic versioning
- **Retrieve content** by ID and certification type
- **Update content metadata** with version increment
- **Query content** by certification type and category
- **Soft delete** content (marks as inactive)
- **Version history** tracking

### User Progress Tracking
- **Store user progress** with relationship validation
- **Retrieve progress** by user and certification type
- **Automatic certification type** detection from content
- **Composite key structure** for efficient querying

### Data Integrity
- **Input validation** using model validation methods
- **Relationship integrity** between content and progress
- **Error handling** with detailed logging
- **Type conversion** for DynamoDB compatibility (Decimal handling)

## Architecture

### DynamoDB Table Structure

#### Content Metadata Table
- **Partition Key**: `content_id` (String)
- **Sort Key**: `certification_type` (String)
- **GSI 1**: `CertificationTypeIndex` - Query by certification and category
- **GSI 2**: `ContentTypeIndex` - Query by content type and creation date

#### User Progress Table
- **Partition Key**: `user_id` (String)
- **Sort Key**: `content_id_certification` (String) - Format: `content_id#certification_type`
- **GSI 1**: `UserCertificationIndex` - Query by user and certification
- **GSI 2**: `ProgressTimeIndex` - Query by certification and timestamp

## Usage

### Basic Initialization

```python
from shared import StorageManager, ContentMetadata, CertificationType

# Initialize with your DynamoDB table names
storage_manager = StorageManager(
    content_metadata_table_name='procert-content-metadata-123456789012',
    user_progress_table_name='procert-user-progress-123456789012',
    region_name='us-east-1'
)
```

### Storing Content Metadata

```python
from shared import ContentMetadata, ContentType, CertificationType, DifficultyLevel

content = ContentMetadata(
    content_id='aws-lambda-guide-001',
    title='AWS Lambda Best Practices',
    content_type=ContentType.STUDY_GUIDE,
    certification_type=CertificationType.SAA,
    category='Compute',
    subcategory='Serverless',
    difficulty_level=DifficultyLevel.INTERMEDIATE,
    tags=['lambda', 'serverless', 'aws'],
    version='1.0',
    source_file='lambda-guide.pdf',
    source_bucket='procert-materials-saa',
    chunk_count=5,
    question_count=10
)

content_id = storage_manager.store_content_metadata(content)
```

### Retrieving Content

```python
# Retrieve by ID and certification type
content = storage_manager.retrieve_content_by_id(
    'aws-lambda-guide-001', 
    CertificationType.SAA
)

# Retrieve all content for a certification
saa_content = storage_manager.retrieve_content_by_certification(
    CertificationType.SAA, 
    limit=50
)

# Retrieve content by category
compute_content = storage_manager.retrieve_content_by_category(
    'Compute',
    certification_type=CertificationType.SAA
)
```

### Updating Content

```python
updates = {
    'title': 'AWS Lambda Best Practices - Updated',
    'tags': ['lambda', 'serverless', 'aws', 'updated'],
    'chunk_count': 7
}

success = storage_manager.update_content_metadata(
    'aws-lambda-guide-001',
    CertificationType.SAA,
    updates
)
```

### User Progress Tracking

```python
from shared import UserProgress, ProgressType

# Store user progress
progress = UserProgress(
    user_id='user-123',
    content_id='aws-lambda-guide-001',
    progress_type=ProgressType.COMPLETED,
    score=85.5,
    time_spent=1800,  # 30 minutes
    session_id='session-456'
)

success = storage_manager.store_user_progress('user-123', progress)

# Retrieve user progress
progress_list = storage_manager.get_user_progress(
    'user-123',
    certification_type=CertificationType.SAA
)
```

## Versioning System

The StorageManager implements automatic content versioning:

1. **New Content**: Uses the provided version (default: "1.0")
2. **Updates**: Automatically increments the patch version (1.0 → 1.0.1)
3. **Version Format**: Follows semantic versioning (major.minor.patch)

### Version Increment Logic
- `1.0` → `1.0.1`
- `1.0.0` → `1.0.1`
- `2.1.5` → `2.1.6`
- Invalid versions default to `1.0.1`

## Error Handling

The StorageManager provides comprehensive error handling:

### Validation Errors
- **ValueError**: Raised for invalid model data
- **Detailed messages**: Specific validation failure reasons

### DynamoDB Errors
- **ClientError**: AWS service errors with error codes
- **RuntimeError**: Wrapped DynamoDB errors with context
- **Graceful degradation**: Returns None/False for retrieval failures

### Logging
- **Structured logging**: All operations logged with context
- **Error details**: Full error information for debugging
- **Success tracking**: Confirmation of successful operations

## Data Type Handling

### DynamoDB Compatibility
- **Float to Decimal**: Automatic conversion for scores
- **Enum serialization**: Converts enums to string values
- **DateTime formatting**: ISO format for timestamps
- **List preservation**: Maintains array structures

### Type Conversions
```python
# Float scores converted to Decimal for DynamoDB
score = 85.5  # Input
stored_score = Decimal('85.5')  # Stored in DynamoDB
retrieved_score = 85.5  # Converted back on retrieval
```

## Performance Considerations

### Query Optimization
- **GSI Usage**: Leverages Global Secondary Indexes for efficient queries
- **Composite Keys**: Optimized key structure for common access patterns
- **Limit Parameters**: Configurable result limits to control response size

### Connection Management
- **Resource Reuse**: Single DynamoDB resource per instance
- **Region Configuration**: Configurable AWS region
- **Connection Pooling**: Handled by boto3 automatically

## Testing

The StorageManager includes comprehensive unit tests:

### Test Coverage
- **Content metadata operations**: Store, retrieve, update, delete
- **User progress tracking**: Store and retrieve progress data
- **Versioning logic**: Version increment and history
- **Error handling**: Validation and service errors
- **Helper methods**: Data conversion and utility functions

### Running Tests
```bash
# Install test dependencies
pip install pytest moto boto3

# Run all StorageManager tests
python -m pytest tests/unit/test_storage_manager.py -v

# Run specific test class
python -m pytest tests/unit/test_storage_manager.py::TestStorageManagerContentMetadata -v
```

## Integration with Other Services

### Lambda Functions
```python
import os
from shared import StorageManager

# Initialize from environment variables
storage_manager = StorageManager(
    content_metadata_table_name=os.environ['CONTENT_METADATA_TABLE'],
    user_progress_table_name=os.environ['USER_PROGRESS_TABLE'],
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)
```

### CDK Infrastructure
The StorageManager works with the DynamoDB tables defined in the CDK stack:
- `procert-content-metadata-{account}`
- `procert-user-progress-{account}`

## Future Enhancements

### Planned Features
1. **Batch Operations**: Support for bulk insert/update operations
2. **Caching Layer**: Integration with ElastiCache for frequently accessed data
3. **Full Version History**: Separate table for complete version tracking
4. **Audit Logging**: Detailed change tracking for compliance
5. **Data Archival**: Lifecycle policies for old content versions

### Performance Optimizations
1. **Connection Pooling**: Custom connection management
2. **Parallel Queries**: Concurrent operations for bulk data
3. **Compression**: Content compression for large metadata
4. **Indexing Strategy**: Additional GSIs for complex queries

## Troubleshooting

### Common Issues

#### Float Type Errors
**Problem**: `Float types are not supported. Use Decimal types instead.`
**Solution**: The StorageManager automatically converts floats to Decimals. Ensure you're using the latest version.

#### Validation Errors
**Problem**: `Validation failed: content_id is required and cannot be empty`
**Solution**: Ensure all required fields are populated in your data models.

#### Permission Errors
**Problem**: `User: arn:aws:iam::123456789012:user/example is not authorized to perform: dynamodb:PutItem`
**Solution**: Verify IAM permissions for DynamoDB operations.

### Debug Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('shared.storage_manager')
logger.setLevel(logging.DEBUG)
```

## Security Considerations

### IAM Permissions
Required DynamoDB permissions:
- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query`
- `dynamodb:Scan`

### Data Encryption
- **Encryption at Rest**: Enabled on DynamoDB tables
- **Encryption in Transit**: HTTPS for all API calls
- **Key Management**: AWS managed keys for table encryption

### Access Control
- **Least Privilege**: Minimal required permissions
- **Resource-Level**: Permissions scoped to specific tables
- **Condition Keys**: Additional security constraints where needed
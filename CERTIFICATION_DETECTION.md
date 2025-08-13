# Certification Detection System

This document explains how the ProCert system detects and classifies content by AWS certification type.

## Overview

The system supports two methods for certification detection:

1. **Automatic Detection** - From filename patterns (3-letter codes)
2. **Admin Override** - Manual selection via admin interface

## Supported Certifications

### Foundational Level
- **CCP** - AWS Certified Cloud Practitioner
- **AIP** - AWS Certified AI Practitioner

### Associate Level
- **MLA** - AWS Certified Machine Learning Engineer - Associate ❌❌❌
- **DEA** - AWS Certified Data Engineer - Associate
- **DVA** - AWS Certified Developer - Associate
- **SAA** - AWS Certified Solutions Architect - Associate
- **SOA** - AWS Certified SysOps Administrator - Associate

### Professional Level
- **DOP** - AWS Certified DevOps Engineer - Professional
- **SAP** - AWS Certified Solutions Architect - Professional 

### Specialty Level
- **ANS** - AWS Certified Advanced Networking - Specialty
- **MLS** - AWS Certified Machine Learning - Specialty  ❌❌❌
- **SCS** - AWS Certified Security - Specialty   ❌❌❌

### General
- **GENERAL** - Content not specific to any certification  ❌❌❌

## Filename Detection Rules

### Preferred Format
Files should be named with the certification code at the beginning:
```
{CODE}-{description}.{extension}
```

**Examples:**
- `SAA-1.pdf` → Solutions Architect Associate
- `CCP-study-guide.pdf` → Cloud Practitioner
- `DVA-practice-exam.docx` → Developer Associate
- `MLS-specialty-guide.pdf` → Machine Learning Specialty

### Fallback Detection
If the preferred format isn't used, the system looks for the code anywhere in the filename:
```
study-guide-SAA.pdf → Solutions Architect Associate
aws-CCP-materials.pdf → Cloud Practitioner
```

### Default Behavior
Files without any certification code are automatically labeled as **GENERAL**:
```
random-document.pdf → GENERAL
study-materials.pdf → GENERAL
```

## Admin Override System

### How It Works
Admins can override automatic detection by selecting from a dropdown menu:

1. **Upload Interface**: Admin selects certification from dropdown
2. **Override Priority**: Admin selection takes precedence over filename detection
3. **Validation**: System validates admin selection against supported certifications

### Example Scenarios

| Filename | Admin Selection | Final Result | Reason |
|----------|----------------|--------------|---------|
| `SAA-exam.pdf` | None | SAA | Automatic detection |
| `random-file.pdf` | None | GENERAL | No code found |
| `random-file.pdf` | CCP | CCP | Admin override |
| `DVA-guide.pdf` | SAA | SAA | Admin override wins |

## Implementation Details

### Core Functions

```python
from shared import detect_certification_from_filename

# Automatic detection
cert = detect_certification_from_filename("SAA-practice.pdf")
# Returns: CertificationType.SAA

# With admin override
cert = detect_certification_from_filename("random.pdf", "CCP")
# Returns: CertificationType.CCP
```

### Admin Interface Support

```python
from shared import get_certifications_for_dropdown

# Get options for dropdown
options = get_certifications_for_dropdown()
# Returns: [{"code": "CCP", "name": "AWS Certified Cloud Practitioner", "level": "Foundational"}, ...]
```

### Validation

```python
from shared import validate_certification_code

# Validate admin input
is_valid = validate_certification_code("SAA")  # True
is_valid = validate_certification_code("INVALID")  # False
```

## Lambda Function Integration

### Document Processing Lambda

The document processing Lambda automatically detects certification type:

```python
def handler(event, context):
    # ... extract S3 event details ...
    
    # Detect certification from filename
    cert_type = detect_certification_from_filename(key)
    
    # Create metadata with detected certification
    content_metadata = {
        'content_id': content_id,
        'certification_type': cert_type.value,
        # ... other metadata ...
    }
    
    # Process and store with certification context
    store_embeddings(chunks, embeddings, key, content_metadata)
```

### Admin Upload Lambda

For admin uploads with override capability:

```python
def admin_upload_handler(event, context):
    filename = body.get("filename")
    admin_override = body.get("admin_selected_certification")
    
    # Detect with admin override
    cert_type = detect_certification_from_filename(filename, admin_override)
    
    # Validate admin selection
    if admin_override and not validate_certification_code(admin_override):
        return {"statusCode": 400, "body": "Invalid certification code"}
    
    # Continue with processing...
```

## Vector Storage Enhancement

### OpenSearch Document Structure

With certification detection, vector documents include certification context:

```json
{
  "document_id": "content-SAA-exam-chunk-0",
  "content_id": "content-SAA-exam",
  "chunk_index": 0,
  "text": "EC2 instances provide scalable computing capacity...",
  "vector_embedding": [0.1, 0.2, ...],
  "certification_type": "SAA",
  "metadata": {
    "source_file": "SAA-exam.pdf",
    "chunk_size": 1000,
    "processed_at": "2024-01-15T10:30:00Z"
  }
}
```

### Search Filtering

This enables certification-specific searches:

```python
# Search only SAA content
query = {
    "query": {
        "bool": {
            "must": [{"knn": {"vector_field": {"vector": embedding, "k": 5}}}],
            "filter": [{"term": {"certification_type": "SAA"}}]
        }
    }
}
```

## Benefits

1. **Automatic Organization** - Content is automatically categorized
2. **Flexible Override** - Admins can correct or specify certification
3. **Improved Search** - Users can filter by certification type
4. **Better RAG** - Chatbot can provide certification-specific answers
5. **Analytics** - Track content distribution across certifications
6. **User Experience** - Personalized content recommendations

## Error Handling

### Invalid Admin Input
- System validates admin selections
- Falls back to filename detection if invalid
- Logs warnings for invalid overrides

### Missing Certification Codes
- Files without codes default to GENERAL
- System continues processing normally
- No errors thrown for unrecognized patterns

### Fallback Behavior
- If shared models unavailable, system uses basic storage
- Graceful degradation ensures system reliability
- Logs warnings about missing functionality

## Testing

The system includes comprehensive tests for:
- Filename pattern recognition
- Admin override functionality
- Validation logic
- Edge cases and error conditions

Run tests with:
```bash
python3 test_models.py
python3 admin_upload_example.py
```

## Future Enhancements

1. **Machine Learning Detection** - Use LLM to analyze content for certification relevance
2. **Confidence Scoring** - Provide confidence levels for automatic detection
3. **Bulk Classification** - Admin tools for reclassifying existing content
4. **Analytics Dashboard** - Visual breakdown of content by certification
5. **User Preferences** - Remember user's preferred certifications for filtering
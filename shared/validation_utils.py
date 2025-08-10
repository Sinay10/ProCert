"""
Validation utilities for input validation and data sanitization.

This module provides comprehensive validation functions for API endpoints,
service methods, and data models to ensure data integrity and security.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Type
try:
    from .exceptions import (
        InputValidationException, ModelValidationException, 
        ContentValidationException
    )
    from .models import CertificationType, ContentType, DifficultyLevel, ProgressType
except ImportError:
    # Fallback for direct imports (e.g., in tests)
    from exceptions import (
        InputValidationException, ModelValidationException, 
        ContentValidationException
    )
    from models import CertificationType, ContentType, DifficultyLevel, ProgressType


# Type validation functions
def validate_string(value: Any, field_name: str, min_length: int = 0, 
                   max_length: int = 10000, pattern: Optional[str] = None,
                   required: bool = True) -> str:
    """
    Validate string input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Optional regex pattern to match
        required: Whether the field is required
        
    Returns:
        Validated string value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None or value == "":
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return ""
    
    if not isinstance(value, str):
        raise InputValidationException(
            f"{field_name} must be a string, got {type(value).__name__}",
            error_code="INVALID_TYPE",
            details={"field": field_name, "expected_type": "string", "actual_type": type(value).__name__}
        )
    
    # Trim whitespace
    value = value.strip()
    
    # Check length constraints
    if len(value) < min_length:
        raise InputValidationException(
            f"{field_name} must be at least {min_length} characters long",
            error_code="STRING_TOO_SHORT",
            details={"field": field_name, "min_length": min_length, "actual_length": len(value)}
        )
    
    if len(value) > max_length:
        raise InputValidationException(
            f"{field_name} must be at most {max_length} characters long",
            error_code="STRING_TOO_LONG",
            details={"field": field_name, "max_length": max_length, "actual_length": len(value)}
        )
    
    # Check pattern if provided
    if pattern and not re.match(pattern, value):
        raise InputValidationException(
            f"{field_name} does not match required pattern",
            error_code="PATTERN_MISMATCH",
            details={"field": field_name, "pattern": pattern, "value": value}
        )
    
    return value


def validate_integer(value: Any, field_name: str, min_value: Optional[int] = None,
                    max_value: Optional[int] = None, required: bool = True) -> Optional[int]:
    """
    Validate integer input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: Whether the field is required
        
    Returns:
        Validated integer value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    # Try to convert to int
    try:
        if isinstance(value, str):
            value = int(value)
        elif not isinstance(value, int):
            raise ValueError()
    except (ValueError, TypeError):
        raise InputValidationException(
            f"{field_name} must be an integer, got {type(value).__name__}",
            error_code="INVALID_TYPE",
            details={"field": field_name, "expected_type": "integer", "actual_type": type(value).__name__}
        )
    
    # Check range constraints
    if min_value is not None and value < min_value:
        raise InputValidationException(
            f"{field_name} must be at least {min_value}",
            error_code="VALUE_TOO_SMALL",
            details={"field": field_name, "min_value": min_value, "actual_value": value}
        )
    
    if max_value is not None and value > max_value:
        raise InputValidationException(
            f"{field_name} must be at most {max_value}",
            error_code="VALUE_TOO_LARGE",
            details={"field": field_name, "max_value": max_value, "actual_value": value}
        )
    
    return value


def validate_float(value: Any, field_name: str, min_value: Optional[float] = None,
                  max_value: Optional[float] = None, required: bool = True) -> Optional[float]:
    """
    Validate float input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: Whether the field is required
        
    Returns:
        Validated float value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    # Try to convert to float
    try:
        if isinstance(value, str):
            value = float(value)
        elif not isinstance(value, (int, float)):
            raise ValueError()
    except (ValueError, TypeError):
        raise InputValidationException(
            f"{field_name} must be a number, got {type(value).__name__}",
            error_code="INVALID_TYPE",
            details={"field": field_name, "expected_type": "float", "actual_type": type(value).__name__}
        )
    
    # Check range constraints
    if min_value is not None and value < min_value:
        raise InputValidationException(
            f"{field_name} must be at least {min_value}",
            error_code="VALUE_TOO_SMALL",
            details={"field": field_name, "min_value": min_value, "actual_value": value}
        )
    
    if max_value is not None and value > max_value:
        raise InputValidationException(
            f"{field_name} must be at most {max_value}",
            error_code="VALUE_TOO_LARGE",
            details={"field": field_name, "max_value": max_value, "actual_value": value}
        )
    
    return float(value)


def validate_boolean(value: Any, field_name: str, required: bool = True) -> Optional[bool]:
    """
    Validate boolean input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        required: Whether the field is required
        
    Returns:
        Validated boolean value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes', 'on'):
            return True
        elif value_lower in ('false', '0', 'no', 'off'):
            return False
    
    raise InputValidationException(
        f"{field_name} must be a boolean value",
        error_code="INVALID_TYPE",
        details={"field": field_name, "expected_type": "boolean", "actual_type": type(value).__name__}
    )


def validate_list(value: Any, field_name: str, item_validator: Optional[Callable] = None,
                 min_length: int = 0, max_length: int = 1000, required: bool = True) -> Optional[List]:
    """
    Validate list input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        item_validator: Optional function to validate each item
        min_length: Minimum list length
        max_length: Maximum list length
        required: Whether the field is required
        
    Returns:
        Validated list value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    if not isinstance(value, list):
        raise InputValidationException(
            f"{field_name} must be a list, got {type(value).__name__}",
            error_code="INVALID_TYPE",
            details={"field": field_name, "expected_type": "list", "actual_type": type(value).__name__}
        )
    
    # Check length constraints
    if len(value) < min_length:
        raise InputValidationException(
            f"{field_name} must have at least {min_length} items",
            error_code="LIST_TOO_SHORT",
            details={"field": field_name, "min_length": min_length, "actual_length": len(value)}
        )
    
    if len(value) > max_length:
        raise InputValidationException(
            f"{field_name} must have at most {max_length} items",
            error_code="LIST_TOO_LONG",
            details={"field": field_name, "max_length": max_length, "actual_length": len(value)}
        )
    
    # Validate each item if validator provided
    if item_validator:
        validated_items = []
        for i, item in enumerate(value):
            try:
                validated_item = item_validator(item, f"{field_name}[{i}]")
                validated_items.append(validated_item)
            except InputValidationException as e:
                # Re-raise with context about the list item
                raise InputValidationException(
                    f"Invalid item at index {i} in {field_name}: {e.message}",
                    error_code=e.error_code,
                    details={**e.details, "list_field": field_name, "item_index": i}
                )
        return validated_items
    
    return value


def validate_enum(value: Any, field_name: str, enum_class: Type, required: bool = True) -> Optional[Any]:
    """
    Validate enum input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        enum_class: Enum class to validate against
        required: Whether the field is required
        
    Returns:
        Validated enum value
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    # If already an instance of the enum, return it
    if isinstance(value, enum_class):
        return value
    
    # Try to convert string to enum
    if isinstance(value, str):
        try:
            # First try the value as-is
            return enum_class(value)
        except ValueError:
            try:
                # Then try uppercase (for certification types)
                return enum_class(value.upper())
            except ValueError:
                try:
                    # Then try lowercase (for difficulty levels, etc.)
                    return enum_class(value.lower())
                except ValueError:
                    valid_values = [e.value for e in enum_class]
                    raise InputValidationException(
                        f"{field_name} must be one of {valid_values}, got '{value}'",
                        error_code="INVALID_ENUM_VALUE",
                        details={"field": field_name, "valid_values": valid_values, "actual_value": value}
                    )
    
    raise InputValidationException(
        f"{field_name} must be a string or {enum_class.__name__} enum",
        error_code="INVALID_TYPE",
        details={"field": field_name, "expected_type": enum_class.__name__, "actual_type": type(value).__name__}
    )


def validate_uuid(value: Any, field_name: str, required: bool = True) -> Optional[str]:
    """
    Validate UUID input.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        required: Whether the field is required
        
    Returns:
        Validated UUID string
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    if not isinstance(value, str):
        raise InputValidationException(
            f"{field_name} must be a string UUID",
            error_code="INVALID_TYPE",
            details={"field": field_name, "expected_type": "string", "actual_type": type(value).__name__}
        )
    
    try:
        # Validate UUID format
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except ValueError:
        raise InputValidationException(
            f"{field_name} must be a valid UUID",
            error_code="INVALID_UUID_FORMAT",
            details={"field": field_name, "value": value}
        )


def validate_datetime(value: Any, field_name: str, required: bool = True) -> Optional[datetime]:
    """
    Validate datetime input.
    
    Args:
        value: Value to validate (datetime object or ISO string)
        field_name: Name of the field for error messages
        required: Whether the field is required
        
    Returns:
        Validated datetime object
        
    Raises:
        InputValidationException: If validation fails
    """
    if value is None:
        if required:
            raise InputValidationException(
                f"{field_name} is required",
                error_code="REQUIRED_FIELD_MISSING",
                details={"field": field_name}
            )
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise InputValidationException(
                f"{field_name} must be a valid ISO datetime string",
                error_code="INVALID_DATETIME_FORMAT",
                details={"field": field_name, "value": value}
            )
    
    raise InputValidationException(
        f"{field_name} must be a datetime object or ISO string",
        error_code="INVALID_TYPE",
        details={"field": field_name, "expected_type": "datetime", "actual_type": type(value).__name__}
    )


# Content-specific validation functions
def validate_content_id(content_id: str) -> str:
    """Validate content ID format."""
    return validate_string(
        content_id, 
        "content_id", 
        min_length=1, 
        max_length=255,
        pattern=r'^[a-zA-Z0-9\-_]+$'
    )


def validate_user_id(user_id: str) -> str:
    """Validate user ID format."""
    return validate_string(
        user_id, 
        "user_id", 
        min_length=1, 
        max_length=255,
        pattern=r'^[a-zA-Z0-9\-_@.]+$'
    )


def validate_certification_type(cert_type: Any) -> CertificationType:
    """Validate certification type."""
    return validate_enum(cert_type, "certification_type", CertificationType)


def validate_content_type(content_type: Any) -> ContentType:
    """Validate content type."""
    return validate_enum(content_type, "content_type", ContentType)


def validate_difficulty_level(difficulty: Any) -> DifficultyLevel:
    """Validate difficulty level."""
    return validate_enum(difficulty, "difficulty_level", DifficultyLevel)


def validate_progress_type(progress_type: Any) -> ProgressType:
    """Validate progress type."""
    return validate_enum(progress_type, "progress_type", ProgressType)


def validate_tags(tags: Any) -> List[str]:
    """Validate tags list."""
    if tags is None:
        return []
    
    validated_tags = validate_list(
        tags, 
        "tags", 
        item_validator=lambda tag, field: validate_string(tag, field, min_length=1, max_length=50),
        max_length=20
    )
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in validated_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)
    
    return unique_tags


def validate_score(score: Any) -> Optional[float]:
    """Validate score value."""
    return validate_float(score, "score", min_value=0.0, max_value=100.0, required=False)


def validate_embedding_vector(embedding: Any) -> List[float]:
    """Validate embedding vector."""
    if not isinstance(embedding, list):
        raise InputValidationException(
            "Embedding must be a list of numbers",
            error_code="INVALID_EMBEDDING_TYPE"
        )
    
    if len(embedding) != 1536:  # Titan embedding dimension
        raise InputValidationException(
            f"Embedding must have 1536 dimensions, got {len(embedding)}",
            error_code="INVALID_EMBEDDING_DIMENSION",
            details={"expected_dimension": 1536, "actual_dimension": len(embedding)}
        )
    
    # Validate each dimension is a number
    for i, value in enumerate(embedding):
        if not isinstance(value, (int, float)):
            raise InputValidationException(
                f"Embedding dimension {i} must be a number, got {type(value).__name__}",
                error_code="INVALID_EMBEDDING_VALUE",
                details={"dimension_index": i, "value_type": type(value).__name__}
            )
    
    return [float(x) for x in embedding]


# API request validation functions
def validate_search_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate search API request.
    
    Args:
        request_data: Request data dictionary
        
    Returns:
        Validated request data
        
    Raises:
        InputValidationException: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['query'] = validate_string(request_data.get('query'), 'query', min_length=1, max_length=1000)
    
    # Optional fields
    if 'certification_type' in request_data:
        validated['certification_type'] = validate_certification_type(request_data['certification_type'])
    
    if 'limit' in request_data:
        validated['limit'] = validate_integer(request_data['limit'], 'limit', min_value=1, max_value=100, required=False)
    
    if 'filters' in request_data:
        validated['filters'] = validate_search_filters(request_data['filters'])
    
    return validated


def validate_search_filters(filters: Any) -> Dict[str, Any]:
    """
    Validate search filters.
    
    Args:
        filters: Filters dictionary
        
    Returns:
        Validated filters
        
    Raises:
        InputValidationException: If validation fails
    """
    if not isinstance(filters, dict):
        raise InputValidationException(
            "Filters must be a dictionary",
            error_code="INVALID_FILTERS_TYPE"
        )
    
    validated = {}
    
    # Validate each filter
    for key, value in filters.items():
        if key == 'category':
            validated[key] = validate_string(value, f'filters.{key}', max_length=100)
        elif key == 'difficulty_level':
            validated[key] = validate_difficulty_level(value).value
        elif key == 'content_type':
            validated[key] = validate_content_type(value).value
        elif key == 'tags':
            validated[key] = validate_tags(value)
        else:
            # Allow other filters but validate as strings
            validated[key] = validate_string(value, f'filters.{key}', max_length=255, required=False)
    
    return validated


def validate_interaction_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate interaction data for progress tracking.
    
    Args:
        data: Interaction data dictionary
        
    Returns:
        Validated interaction data
        
    Raises:
        InputValidationException: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['user_id'] = validate_user_id(data.get('user_id'))
    validated['content_id'] = validate_content_id(data.get('content_id'))
    validated['interaction_type'] = validate_string(
        data.get('interaction_type'), 
        'interaction_type', 
        pattern=r'^(view|answer|complete)$'
    )
    
    # Optional fields
    if 'score' in data:
        validated['score'] = validate_score(data['score'])
    
    if 'time_spent' in data:
        validated['time_spent'] = validate_integer(
            data['time_spent'], 
            'time_spent', 
            min_value=0, 
            max_value=86400,  # Max 24 hours
            required=False
        )
    
    if 'session_id' in data:
        validated['session_id'] = validate_string(data['session_id'], 'session_id', max_length=255, required=False)
    
    if 'additional_data' in data:
        if not isinstance(data['additional_data'], dict):
            raise InputValidationException(
                "additional_data must be a dictionary",
                error_code="INVALID_ADDITIONAL_DATA_TYPE"
            )
        validated['additional_data'] = data['additional_data']
    
    return validated


# Sanitization functions
def sanitize_text_content(text: str) -> str:
    """
    Sanitize text content for safe storage and processing.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and other control characters, but preserve spaces
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
    
    # Normalize whitespace (collapse multiple spaces/newlines into single spaces)
    text = re.sub(r'\s+', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unknown"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 250 - len(ext)
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename
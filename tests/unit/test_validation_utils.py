"""
Unit tests for the validation utilities and input validation functions.

This module tests the comprehensive validation system for the ProCert
content management system, including type validation, content validation,
and API request validation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

# Import the validation utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from validation_utils import (
    validate_string, validate_integer, validate_float, validate_boolean,
    validate_list, validate_enum, validate_uuid, validate_datetime,
    validate_content_id, validate_user_id, validate_certification_type,
    validate_content_type, validate_difficulty_level, validate_progress_type,
    validate_tags, validate_score, validate_embedding_vector,
    validate_search_request, validate_search_filters, validate_interaction_data,
    sanitize_text_content, sanitize_filename
)
from exceptions import InputValidationException

# Mock the models module for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
try:
    from models import CertificationType, ContentType, DifficultyLevel, ProgressType
except ImportError:
    # Create mock enums for testing
    from enum import Enum
    
    class CertificationType(Enum):
        CCP = "CCP"
        SAA = "SAA"
        DVA = "DVA"
        GENERAL = "GENERAL"
    
    class ContentType(Enum):
        STUDY_GUIDE = "study_guide"
        PRACTICE_EXAM = "practice_exam"
    
    class DifficultyLevel(Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"
    
    class ProgressType(Enum):
        VIEWED = "viewed"
        ANSWERED = "answered"
        COMPLETED = "completed"


class TestStringValidation:
    """Test string validation functions."""
    
    def test_valid_string(self):
        """Test validation of valid strings."""
        result = validate_string("test string", "field_name")
        assert result == "test string"
    
    def test_string_with_whitespace_trimming(self):
        """Test that whitespace is trimmed."""
        result = validate_string("  test string  ", "field_name")
        assert result == "test string"
    
    def test_empty_string_required(self):
        """Test that empty string raises error when required."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string("", "field_name", required=True)
        assert "field_name is required" in str(exc_info.value)
    
    def test_empty_string_not_required(self):
        """Test that empty string is allowed when not required."""
        result = validate_string("", "field_name", required=False)
        assert result == ""
    
    def test_none_value_required(self):
        """Test that None raises error when required."""
        with pytest.raises(InputValidationException):
            validate_string(None, "field_name", required=True)
    
    def test_none_value_not_required(self):
        """Test that None returns empty string when not required."""
        result = validate_string(None, "field_name", required=False)
        assert result == ""
    
    def test_non_string_type(self):
        """Test that non-string types raise error."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string(123, "field_name")
        assert "must be a string" in str(exc_info.value)
    
    def test_string_too_short(self):
        """Test minimum length validation."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string("ab", "field_name", min_length=5)
        assert "at least 5 characters" in str(exc_info.value)
    
    def test_string_too_long(self):
        """Test maximum length validation."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string("a" * 100, "field_name", max_length=50)
        assert "at most 50 characters" in str(exc_info.value)
    
    def test_pattern_matching_valid(self):
        """Test pattern matching with valid input."""
        result = validate_string("abc123", "field_name", pattern=r'^[a-z0-9]+$')
        assert result == "abc123"
    
    def test_pattern_matching_invalid(self):
        """Test pattern matching with invalid input."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string("ABC123", "field_name", pattern=r'^[a-z0-9]+$')
        assert "does not match required pattern" in str(exc_info.value)


class TestIntegerValidation:
    """Test integer validation functions."""
    
    def test_valid_integer(self):
        """Test validation of valid integers."""
        result = validate_integer(42, "field_name")
        assert result == 42
    
    def test_string_to_integer_conversion(self):
        """Test conversion of string to integer."""
        result = validate_integer("42", "field_name")
        assert result == 42
    
    def test_invalid_string_conversion(self):
        """Test invalid string conversion raises error."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_integer("not_a_number", "field_name")
        assert "must be an integer" in str(exc_info.value)
    
    def test_float_type_error(self):
        """Test that float types raise error."""
        with pytest.raises(InputValidationException):
            validate_integer(42.5, "field_name")
    
    def test_integer_too_small(self):
        """Test minimum value validation."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_integer(5, "field_name", min_value=10)
        assert "at least 10" in str(exc_info.value)
    
    def test_integer_too_large(self):
        """Test maximum value validation."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_integer(100, "field_name", max_value=50)
        assert "at most 50" in str(exc_info.value)
    
    def test_none_value_not_required(self):
        """Test None value when not required."""
        result = validate_integer(None, "field_name", required=False)
        assert result is None


class TestFloatValidation:
    """Test float validation functions."""
    
    def test_valid_float(self):
        """Test validation of valid floats."""
        result = validate_float(42.5, "field_name")
        assert result == 42.5
    
    def test_integer_to_float_conversion(self):
        """Test conversion of integer to float."""
        result = validate_float(42, "field_name")
        assert result == 42.0
    
    def test_string_to_float_conversion(self):
        """Test conversion of string to float."""
        result = validate_float("42.5", "field_name")
        assert result == 42.5
    
    def test_invalid_string_conversion(self):
        """Test invalid string conversion raises error."""
        with pytest.raises(InputValidationException):
            validate_float("not_a_number", "field_name")
    
    def test_float_range_validation(self):
        """Test float range validation."""
        with pytest.raises(InputValidationException):
            validate_float(5.5, "field_name", min_value=10.0, max_value=50.0)


class TestBooleanValidation:
    """Test boolean validation functions."""
    
    def test_valid_boolean_true(self):
        """Test validation of boolean True."""
        result = validate_boolean(True, "field_name")
        assert result is True
    
    def test_valid_boolean_false(self):
        """Test validation of boolean False."""
        result = validate_boolean(False, "field_name")
        assert result is False
    
    def test_string_true_conversion(self):
        """Test conversion of string 'true' to boolean."""
        for value in ['true', 'True', 'TRUE', '1', 'yes', 'on']:
            result = validate_boolean(value, "field_name")
            assert result is True
    
    def test_string_false_conversion(self):
        """Test conversion of string 'false' to boolean."""
        for value in ['false', 'False', 'FALSE', '0', 'no', 'off']:
            result = validate_boolean(value, "field_name")
            assert result is False
    
    def test_invalid_string_conversion(self):
        """Test invalid string conversion raises error."""
        with pytest.raises(InputValidationException):
            validate_boolean("maybe", "field_name")


class TestListValidation:
    """Test list validation functions."""
    
    def test_valid_list(self):
        """Test validation of valid lists."""
        result = validate_list([1, 2, 3], "field_name")
        assert result == [1, 2, 3]
    
    def test_non_list_type(self):
        """Test that non-list types raise error."""
        with pytest.raises(InputValidationException):
            validate_list("not_a_list", "field_name")
    
    def test_list_too_short(self):
        """Test minimum length validation."""
        with pytest.raises(InputValidationException):
            validate_list([1, 2], "field_name", min_length=5)
    
    def test_list_too_long(self):
        """Test maximum length validation."""
        with pytest.raises(InputValidationException):
            validate_list([1] * 100, "field_name", max_length=50)
    
    def test_list_item_validation(self):
        """Test item validation with validator function."""
        def string_validator(item, field_name):
            return validate_string(item, field_name)
        
        result = validate_list(["a", "b", "c"], "field_name", item_validator=string_validator)
        assert result == ["a", "b", "c"]
    
    def test_list_item_validation_failure(self):
        """Test item validation failure."""
        def string_validator(item, field_name):
            return validate_string(item, field_name, min_length=5)
        
        with pytest.raises(InputValidationException) as exc_info:
            validate_list(["a", "b", "c"], "field_name", item_validator=string_validator)
        assert "Invalid item at index" in str(exc_info.value)


class TestEnumValidation:
    """Test enum validation functions."""
    
    def test_valid_enum_instance(self):
        """Test validation of valid enum instances."""
        result = validate_enum(CertificationType.SAA, "field_name", CertificationType)
        assert result == CertificationType.SAA
    
    def test_string_to_enum_conversion(self):
        """Test conversion of string to enum."""
        result = validate_enum("saa", "field_name", CertificationType)
        assert result == CertificationType.SAA
    
    def test_invalid_enum_value(self):
        """Test invalid enum value raises error."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_enum("INVALID", "field_name", CertificationType)
        assert "must be one of" in str(exc_info.value)
    
    def test_non_string_enum_type(self):
        """Test non-string enum type raises error."""
        with pytest.raises(InputValidationException):
            validate_enum(123, "field_name", CertificationType)


class TestContentSpecificValidation:
    """Test content-specific validation functions."""
    
    def test_valid_content_id(self):
        """Test validation of valid content IDs."""
        result = validate_content_id("content-123-abc")
        assert result == "content-123-abc"
    
    def test_invalid_content_id_characters(self):
        """Test invalid characters in content ID."""
        with pytest.raises(InputValidationException):
            validate_content_id("content@123")
    
    def test_valid_user_id(self):
        """Test validation of valid user IDs."""
        result = validate_user_id("user@example.com")
        assert result == "user@example.com"
    
    def test_valid_certification_type(self):
        """Test certification type validation."""
        result = validate_certification_type("SAA")
        assert result == CertificationType.SAA
    
    def test_valid_tags(self):
        """Test tags validation."""
        result = validate_tags(["aws", "ec2", "s3"])
        assert result == ["aws", "ec2", "s3"]
    
    def test_tags_deduplication(self):
        """Test that duplicate tags are removed."""
        result = validate_tags(["aws", "AWS", "ec2", "aws"])
        assert result == ["aws", "ec2"]  # Duplicates removed, case-insensitive
    
    def test_valid_score(self):
        """Test score validation."""
        result = validate_score(85.5)
        assert result == 85.5
    
    def test_invalid_score_range(self):
        """Test invalid score range."""
        with pytest.raises(InputValidationException):
            validate_score(150.0)  # Over 100
    
    def test_valid_embedding_vector(self):
        """Test embedding vector validation."""
        vector = [0.1] * 1536  # Titan embedding dimension
        result = validate_embedding_vector(vector)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)
    
    def test_invalid_embedding_dimension(self):
        """Test invalid embedding dimension."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_embedding_vector([0.1] * 512)  # Wrong dimension
        assert "1536 dimensions" in str(exc_info.value)
    
    def test_invalid_embedding_values(self):
        """Test invalid embedding values."""
        vector = [0.1] * 1535 + ["not_a_number"]
        with pytest.raises(InputValidationException) as exc_info:
            validate_embedding_vector(vector)
        assert "must be a number" in str(exc_info.value)


class TestAPIRequestValidation:
    """Test API request validation functions."""
    
    def test_valid_search_request(self):
        """Test validation of valid search requests."""
        request_data = {
            "query": "What is AWS Lambda?",
            "certification_type": "SAA",
            "limit": 10
        }
        result = validate_search_request(request_data)
        assert result["query"] == "What is AWS Lambda?"
        assert result["certification_type"] == CertificationType.SAA
        assert result["limit"] == 10
    
    def test_search_request_missing_query(self):
        """Test search request with missing query."""
        with pytest.raises(InputValidationException):
            validate_search_request({})
    
    def test_search_request_optional_fields(self):
        """Test search request with only required fields."""
        request_data = {"query": "test query"}
        result = validate_search_request(request_data)
        assert result["query"] == "test query"
        assert "certification_type" not in result
        assert "limit" not in result
    
    def test_valid_search_filters(self):
        """Test validation of search filters."""
        filters = {
            "category": "compute",
            "difficulty_level": "intermediate",
            "tags": ["ec2", "lambda"]
        }
        result = validate_search_filters(filters)
        assert result["category"] == "compute"
        assert result["difficulty_level"] == "intermediate"
        assert result["tags"] == ["ec2", "lambda"]
    
    def test_invalid_search_filters_type(self):
        """Test invalid search filters type."""
        with pytest.raises(InputValidationException):
            validate_search_filters("not_a_dict")
    
    def test_valid_interaction_data(self):
        """Test validation of interaction data."""
        data = {
            "user_id": "user123",
            "content_id": "content-456",
            "interaction_type": "view",
            "score": 85.0,
            "time_spent": 300
        }
        result = validate_interaction_data(data)
        assert result["user_id"] == "user123"
        assert result["content_id"] == "content-456"
        assert result["interaction_type"] == "view"
        assert result["score"] == 85.0
        assert result["time_spent"] == 300
    
    def test_interaction_data_invalid_type(self):
        """Test invalid interaction type."""
        data = {
            "user_id": "user123",
            "content_id": "content-456",
            "interaction_type": "invalid_type"
        }
        with pytest.raises(InputValidationException):
            validate_interaction_data(data)


class TestSanitizationFunctions:
    """Test text sanitization functions."""
    
    def test_sanitize_text_content(self):
        """Test text content sanitization."""
        dirty_text = "Hello\x00World\n\n\n   with   spaces   "
        result = sanitize_text_content(dirty_text)
        assert result == "Hello World with spaces"
    
    def test_sanitize_empty_text(self):
        """Test sanitization of empty text."""
        result = sanitize_text_content("")
        assert result == ""
    
    def test_sanitize_none_text(self):
        """Test sanitization of None text."""
        result = sanitize_text_content(None)
        assert result == ""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dirty_filename = "file<>name|with?bad*chars.pdf"
        result = sanitize_filename(dirty_filename)
        assert result == "file__name_with_bad_chars.pdf"
    
    def test_sanitize_long_filename(self):
        """Test sanitization of long filenames."""
        long_filename = "a" * 300 + ".pdf"
        result = sanitize_filename(long_filename)
        assert len(result) <= 255
        assert result.endswith(".pdf")
    
    def test_sanitize_empty_filename(self):
        """Test sanitization of empty filename."""
        result = sanitize_filename("")
        assert result == "unknown"


class TestValidationIntegration:
    """Test validation integration scenarios."""
    
    def test_nested_validation_errors(self):
        """Test that nested validation errors are properly handled."""
        data = {
            "items": [
                {"name": "valid"},
                {"name": ""},  # Invalid - empty name
                {"name": "also_valid"}
            ]
        }
        
        def item_validator(item, field_name):
            return {
                "name": validate_string(item["name"], f"{field_name}.name", min_length=1)
            }
        
        with pytest.raises(InputValidationException) as exc_info:
            validate_list(data["items"], "items", item_validator=item_validator)
        
        assert "Invalid item at index 1" in str(exc_info.value)
    
    def test_validation_error_details(self):
        """Test that validation errors include detailed information."""
        with pytest.raises(InputValidationException) as exc_info:
            validate_string("ab", "test_field", min_length=5)
        
        error = exc_info.value
        assert error.error_code == "STRING_TOO_SHORT"
        assert error.details["field"] == "test_field"
        assert error.details["min_length"] == 5
        assert error.details["actual_length"] == 2
    
    def test_multiple_validation_steps(self):
        """Test multiple validation steps in sequence."""
        # This simulates a complex validation scenario
        raw_data = {
            "query": "  What is AWS?  ",
            "certification_type": "saa",
            "limit": "10",
            "filters": {
                "category": "compute",
                "tags": ["ec2", "EC2", "lambda"]  # Has duplicates
            }
        }
        
        # Validate search request (includes nested filter validation)
        result = validate_search_request(raw_data)
        
        # Check that all validations were applied
        assert result["query"] == "What is AWS?"  # Trimmed
        assert result["certification_type"] == CertificationType.SAA  # Converted
        assert result["limit"] == 10  # Converted to int
        assert result["filters"]["tags"] == ["ec2", "lambda"]  # Deduplicated


if __name__ == '__main__':
    pytest.main([__file__])
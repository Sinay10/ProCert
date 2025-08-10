"""
Unit tests for the custom exception classes and error handling utilities.

This module tests the exception hierarchy, error classification, and utility functions
for the ProCert content management system error handling.
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

# Import the exception classes and utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from exceptions import (
    ProCertBaseException, StorageException, DynamoDBException, OpenSearchException, S3Exception,
    ValidationException, ModelValidationException, InputValidationException,
    ProcessingException, SearchException, ProgressTrackingException,
    RetryableException, ThrottlingException, TemporaryServiceException,
    BedrockException, ExternalServiceException, ConfigurationException,
    create_storage_exception, is_retryable_error, get_retry_delay
)


class TestProCertBaseException:
    """Test the base exception class."""
    
    def test_base_exception_creation(self):
        """Test basic exception creation with message only."""
        exc = ProCertBaseException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.error_code == "ProCertBaseException"
        assert exc.details == {}
    
    def test_base_exception_with_error_code(self):
        """Test exception creation with custom error code."""
        exc = ProCertBaseException("Test error", error_code="CUSTOM_ERROR")
        assert exc.error_code == "CUSTOM_ERROR"
    
    def test_base_exception_with_details(self):
        """Test exception creation with details dictionary."""
        details = {"field": "test_field", "value": "test_value"}
        exc = ProCertBaseException("Test error", details=details)
        assert exc.details == details


class TestSpecificExceptions:
    """Test specific exception types."""
    
    def test_storage_exception_hierarchy(self):
        """Test that storage exceptions inherit properly."""
        exc = StorageException("Storage error")
        assert isinstance(exc, ProCertBaseException)
        assert isinstance(exc, StorageException)
    
    def test_dynamodb_exception(self):
        """Test DynamoDB-specific exception."""
        exc = DynamoDBException("DynamoDB error", error_code="THROTTLING")
        assert isinstance(exc, StorageException)
        assert exc.error_code == "THROTTLING"
    
    def test_validation_exception_hierarchy(self):
        """Test validation exception hierarchy."""
        exc = InputValidationException("Invalid input")
        assert isinstance(exc, ValidationException)
        assert isinstance(exc, ProCertBaseException)
    
    def test_retryable_exception_properties(self):
        """Test retryable exception with retry properties."""
        exc = RetryableException("Temporary error", retry_after=5, max_retries=3)
        assert exc.retry_after == 5
        assert exc.max_retries == 3
        assert isinstance(exc, ProCertBaseException)


class TestCreateStorageException:
    """Test the storage exception factory function."""
    
    def test_create_dynamodb_exception(self):
        """Test creating DynamoDB exception."""
        original_error = Exception("Original error")
        exc = create_storage_exception('dynamodb', 'put_item', original_error)
        
        assert isinstance(exc, DynamoDBException)
        assert 'dynamodb put_item' in str(exc)
        assert exc.details['service'] == 'dynamodb'
        assert exc.details['operation'] == 'put_item'
        assert exc.details['original_error'] == 'Original error'
    
    def test_create_opensearch_exception(self):
        """Test creating OpenSearch exception."""
        original_error = Exception("Search failed")
        exc = create_storage_exception('opensearch', 'search', original_error)
        
        assert isinstance(exc, OpenSearchException)
        assert 'opensearch search' in str(exc)
    
    def test_create_s3_exception(self):
        """Test creating S3 exception."""
        original_error = Exception("Access denied")
        exc = create_storage_exception('s3', 'get_object', original_error)
        
        assert isinstance(exc, S3Exception)
        assert 's3 get_object' in str(exc)
    
    def test_create_generic_storage_exception(self):
        """Test creating generic storage exception for unknown service."""
        original_error = Exception("Unknown service error")
        exc = create_storage_exception('unknown', 'operation', original_error)
        
        assert isinstance(exc, StorageException)
        assert not isinstance(exc, DynamoDBException)


class TestIsRetryableError:
    """Test the retryable error detection function."""
    
    def test_retryable_exception_is_retryable(self):
        """Test that RetryableException instances are retryable."""
        exc = RetryableException("Temporary error")
        assert is_retryable_error(exc) is True
    
    def test_throttling_exception_is_retryable(self):
        """Test that ThrottlingException instances are retryable."""
        exc = ThrottlingException("Rate limited")
        assert is_retryable_error(exc) is True
    
    def test_aws_throttling_error_is_retryable(self):
        """Test AWS throttling errors are detected as retryable."""
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate exceeded'
            }
        }
        exc = ClientError(error_response, 'put_item')
        assert is_retryable_error(exc) is True
    
    def test_aws_provisioned_throughput_error_is_retryable(self):
        """Test AWS provisioned throughput errors are retryable."""
        error_response = {
            'Error': {
                'Code': 'ProvisionedThroughputExceededException',
                'Message': 'Throughput exceeded'
            }
        }
        exc = ClientError(error_response, 'put_item')
        assert is_retryable_error(exc) is True
    
    def test_aws_validation_error_not_retryable(self):
        """Test AWS validation errors are not retryable."""
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid parameter'
            }
        }
        exc = ClientError(error_response, 'put_item')
        assert is_retryable_error(exc) is False
    
    def test_network_errors_are_retryable(self):
        """Test that network-related errors are retryable."""
        # Create custom exception classes for testing
        class ConnectionError(Exception):
            pass
        
        class TimeoutError(Exception):
            pass
        
        connection_error = ConnectionError("Connection failed")
        assert is_retryable_error(connection_error) is True
        
        timeout_error = TimeoutError("Request timed out")
        assert is_retryable_error(timeout_error) is True
    
    def test_regular_exception_not_retryable(self):
        """Test that regular exceptions are not retryable."""
        exc = ValueError("Invalid value")
        assert is_retryable_error(exc) is False


class TestGetRetryDelay:
    """Test the retry delay calculation function."""
    
    def test_exponential_backoff_progression(self):
        """Test that retry delays increase exponentially."""
        delay_0 = get_retry_delay(0, base_delay=1.0, max_delay=60.0)
        delay_1 = get_retry_delay(1, base_delay=1.0, max_delay=60.0)
        delay_2 = get_retry_delay(2, base_delay=1.0, max_delay=60.0)
        
        # Delays should generally increase (accounting for jitter)
        assert delay_0 < delay_1 * 1.5  # Allow for jitter variation
        assert delay_1 < delay_2 * 1.5  # Allow for jitter variation
    
    def test_max_delay_respected(self):
        """Test that maximum delay is not exceeded."""
        delay = get_retry_delay(10, base_delay=1.0, max_delay=5.0)
        assert delay <= 5.0
    
    def test_minimum_delay_non_negative(self):
        """Test that delay is never negative."""
        delay = get_retry_delay(0, base_delay=0.1, max_delay=60.0)
        assert delay >= 0
    
    def test_jitter_variation(self):
        """Test that jitter adds variation to delays."""
        delays = [get_retry_delay(1, base_delay=2.0, max_delay=60.0) for _ in range(10)]
        
        # With jitter, we should see some variation in delays
        unique_delays = set(delays)
        assert len(unique_delays) > 1  # Should have some variation due to jitter


class TestExceptionIntegration:
    """Test exception integration with real-world scenarios."""
    
    def test_exception_chaining(self):
        """Test that exceptions can be properly chained."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise DynamoDBException("DynamoDB operation failed") from e
        except DynamoDBException as exc:
            assert exc.__cause__ is not None
            assert isinstance(exc.__cause__, ValueError)
    
    def test_exception_details_serialization(self):
        """Test that exception details can be serialized."""
        details = {
            "field": "test_field",
            "value": 123,
            "nested": {"key": "value"}
        }
        exc = ValidationException("Validation failed", details=details)
        
        # Should be able to access all details
        assert exc.details["field"] == "test_field"
        assert exc.details["value"] == 123
        assert exc.details["nested"]["key"] == "value"
    
    def test_aws_error_response_handling(self):
        """Test handling of AWS error responses."""
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Table not found'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id'
            }
        }
        
        original_error = ClientError(error_response, 'describe_table')
        storage_exc = create_storage_exception('dynamodb', 'describe_table', original_error)
        
        assert isinstance(storage_exc, DynamoDBException)
        assert 'Table not found' in str(storage_exc)
        assert storage_exc.details['original_error_type'] == 'ClientError'


if __name__ == '__main__':
    pytest.main([__file__])
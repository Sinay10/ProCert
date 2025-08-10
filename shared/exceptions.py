"""
Custom exception classes for the ProCert content management system.

This module defines specific exception types for different error scenarios
to enable better error handling and debugging throughout the system.
"""

from typing import Optional, Dict, Any


class ProCertBaseException(Exception):
    """Base exception class for all ProCert-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


# Storage-related exceptions
class StorageException(ProCertBaseException):
    """Base class for storage-related errors."""
    pass


class DynamoDBException(StorageException):
    """Exception for DynamoDB-specific errors."""
    pass


class OpenSearchException(StorageException):
    """Exception for OpenSearch-specific errors."""
    pass


class S3Exception(StorageException):
    """Exception for S3-specific errors."""
    pass


class VectorStorageException(StorageException):
    """Exception for vector storage operations."""
    pass


# Validation-related exceptions
class ValidationException(ProCertBaseException):
    """Base class for validation errors."""
    pass


class ModelValidationException(ValidationException):
    """Exception for data model validation errors."""
    pass


class InputValidationException(ValidationException):
    """Exception for input parameter validation errors."""
    pass


class ContentValidationException(ValidationException):
    """Exception for content validation errors."""
    pass


# Processing-related exceptions
class ProcessingException(ProCertBaseException):
    """Base class for content processing errors."""
    pass


class ContentExtractionException(ProcessingException):
    """Exception for content extraction errors."""
    pass


class EmbeddingGenerationException(ProcessingException):
    """Exception for embedding generation errors."""
    pass


class CertificationDetectionException(ProcessingException):
    """Exception for certification type detection errors."""
    pass


# Search-related exceptions
class SearchException(ProCertBaseException):
    """Base class for search-related errors."""
    pass


class QueryException(SearchException):
    """Exception for search query errors."""
    pass


class IndexException(SearchException):
    """Exception for search index errors."""
    pass


# Progress tracking exceptions
class ProgressTrackingException(ProCertBaseException):
    """Base class for progress tracking errors."""
    pass


class InteractionRecordingException(ProgressTrackingException):
    """Exception for interaction recording errors."""
    pass


class AnalyticsException(ProgressTrackingException):
    """Exception for analytics calculation errors."""
    pass


# External service exceptions
class ExternalServiceException(ProCertBaseException):
    """Base class for external service errors."""
    pass


class BedrockException(ExternalServiceException):
    """Exception for AWS Bedrock service errors."""
    pass


class LambdaException(ExternalServiceException):
    """Exception for AWS Lambda execution errors."""
    pass


# Configuration and setup exceptions
class ConfigurationException(ProCertBaseException):
    """Exception for configuration-related errors."""
    pass


class InitializationException(ProCertBaseException):
    """Exception for service initialization errors."""
    pass


# Retry-related exceptions
class RetryableException(ProCertBaseException):
    """Base class for errors that can be retried."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, 
                 max_retries: Optional[int] = None, **kwargs):
        """
        Initialize retryable exception.
        
        Args:
            message: Error message
            retry_after: Suggested retry delay in seconds
            max_retries: Maximum number of retries recommended
            **kwargs: Additional arguments for base exception
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.max_retries = max_retries


class ThrottlingException(RetryableException):
    """Exception for service throttling errors."""
    pass


class TemporaryServiceException(RetryableException):
    """Exception for temporary service unavailability."""
    pass


class NetworkException(RetryableException):
    """Exception for network-related errors."""
    pass


# Utility functions for exception handling
def create_storage_exception(service: str, operation: str, original_error: Exception) -> StorageException:
    """
    Create appropriate storage exception based on service and error.
    
    Args:
        service: Storage service name (dynamodb, opensearch, s3)
        operation: Operation being performed
        original_error: Original exception
        
    Returns:
        Appropriate storage exception
    """
    error_message = f"Error in {service} {operation}: {str(original_error)}"
    details = {
        'service': service,
        'operation': operation,
        'original_error': str(original_error),
        'original_error_type': type(original_error).__name__
    }
    
    if service.lower() == 'dynamodb':
        return DynamoDBException(error_message, details=details)
    elif service.lower() == 'opensearch':
        return OpenSearchException(error_message, details=details)
    elif service.lower() == 's3':
        return S3Exception(error_message, details=details)
    else:
        return StorageException(error_message, details=details)


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error is retryable
    """
    if isinstance(exception, RetryableException):
        return True
    
    # Check for specific AWS error codes that are retryable
    if hasattr(exception, 'response') and 'Error' in exception.response:
        error_code = exception.response['Error']['Code']
        retryable_codes = {
            'ThrottlingException', 'ProvisionedThroughputExceededException',
            'RequestLimitExceeded', 'ServiceUnavailable', 'InternalServerError',
            'TooManyRequestsException', 'LimitExceededException'
        }
        return error_code in retryable_codes
    
    # Check for network-related errors
    network_error_types = {
        'ConnectionError', 'TimeoutError', 'ConnectTimeoutError',
        'ReadTimeoutError', 'SSLError'
    }
    return type(exception).__name__ in network_error_types


def get_retry_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds
    """
    import random
    
    # Exponential backoff with jitter
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter (±25% of delay)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    final_delay = max(0, delay + jitter)
    # Ensure we don't exceed max_delay even with jitter
    return min(final_delay, max_delay)
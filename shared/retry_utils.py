"""
Retry utilities for handling transient failures in external service calls.

This module provides decorators and utilities for implementing retry logic
with exponential backoff for various AWS services and external dependencies.
"""

import time
import logging
import functools
from typing import Callable, Type, Tuple, Optional, Any, Union
try:
    from .exceptions import (
        RetryableException, ThrottlingException, TemporaryServiceException,
        NetworkException, is_retryable_error, get_retry_delay
    )
except ImportError:
    from exceptions import (
        RetryableException, ThrottlingException, TemporaryServiceException,
        NetworkException, is_retryable_error, get_retry_delay
    )


logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (RetryableException,),
    backoff_multiplier: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retryable_exceptions: Tuple of exception types that should trigger retries
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Whether to add random jitter to delays
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Check if the exception is retryable
                    if not (isinstance(e, retryable_exceptions) or is_retryable_error(e)):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay for next attempt
                    if jitter:
                        delay = get_retry_delay(attempt, base_delay, max_delay)
                    else:
                        delay = min(base_delay * (backoff_multiplier ** attempt), max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} of {func.__name__} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator


def retry_aws_operation(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Specialized retry decorator for AWS operations.
    
    This decorator handles common AWS error patterns including throttling,
    service unavailability, and transient network issues.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function with AWS-specific retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(f"AWS operation {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Check for AWS-specific retryable errors
                    if not _is_aws_retryable_error(e):
                        logger.error(f"Non-retryable AWS error in {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with AWS-specific logic
                    delay = _calculate_aws_retry_delay(e, attempt, base_delay, max_delay)
                    
                    logger.warning(
                        f"AWS operation {func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
            
        return wrapper
    return decorator


def retry_opensearch_operation(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 120.0
):
    """
    Specialized retry decorator for OpenSearch operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated function with OpenSearch-specific retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(f"OpenSearch operation {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Check for OpenSearch-specific retryable errors
                    if not _is_opensearch_retryable_error(e):
                        logger.error(f"Non-retryable OpenSearch error in {func.__name__}: {e}")
                        raise
                    
                    # Use longer delays for OpenSearch operations
                    delay = get_retry_delay(attempt, base_delay, max_delay)
                    
                    logger.warning(
                        f"OpenSearch operation {func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
            
        return wrapper
    return decorator


class RetryContext:
    """Context manager for retry operations with custom logic."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, operation_name: str = "operation"):
        """
        Initialize retry context.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            operation_name: Name of the operation for logging
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.operation_name = operation_name
        self.attempt = 0
        self.last_exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # This context manager doesn't handle exceptions automatically
        # It's used for manual retry loops with should_retry() method
        return False
    
    def should_retry(self, exception: Exception = None) -> bool:
        """
        Check if operation should be retried and handle retry logic.
        
        This method should be called in the exception handler of a manual retry loop.
        It will check if retries are available, handle delays, and update attempt count.
        
        Args:
            exception: The exception that occurred (optional, for retryability check)
        
        Returns:
            True if the operation should be retried, False otherwise
        """
        import sys
        
        # If no exception provided, try to get it from the current exception context
        if exception is None:
            exc_info = sys.exc_info()
            if exc_info[1] is not None:
                exception = exc_info[1]
        
        # Check if the exception is retryable (if we have one)
        if exception is not None and not is_retryable_error(exception):
            logger.error(f"Non-retryable error in {self.operation_name}: {exception}")
            return False
        
        # Check if we've exceeded max retries
        if self.attempt >= self.max_retries:
            logger.error(f"Operation {self.operation_name} failed after {self.max_retries} retries")
            return False
        
        # For the first attempt, don't sleep or increment
        if self.attempt == 0:
            self.attempt += 1
            return True
        
        # Calculate delay and sleep for subsequent attempts
        delay = get_retry_delay(self.attempt - 1, self.base_delay, self.max_delay)
        logger.warning(
            f"Operation {self.operation_name} attempt {self.attempt} failed. "
            f"Retrying in {delay:.2f} seconds..."
        )
        
        time.sleep(delay)
        self.attempt += 1
        return True


# Helper functions for AWS-specific error handling
def _is_aws_retryable_error(exception: Exception) -> bool:
    """Check if an AWS error is retryable."""
    if is_retryable_error(exception):
        return True
    
    # Check for boto3/botocore specific errors
    if hasattr(exception, 'response') and 'Error' in exception.response:
        error_code = exception.response['Error']['Code']
        
        # AWS service-specific retryable errors
        aws_retryable_codes = {
            # DynamoDB
            'ProvisionedThroughputExceededException',
            'RequestLimitExceeded',
            'ThrottlingException',
            'UnrecognizedClientException',
            'InternalServerError',
            'ServiceUnavailable',
            
            # S3
            'SlowDown',
            'RequestTimeout',
            'RequestTimeTooSkewed',
            
            # Bedrock
            'ThrottlingException',
            'ModelTimeoutException',
            'InternalServerException',
            
            # General AWS errors
            'TooManyRequestsException',
            'LimitExceededException'
        }
        
        return error_code in aws_retryable_codes
    
    return False


def _is_opensearch_retryable_error(exception: Exception) -> bool:
    """Check if an OpenSearch error is retryable."""
    if is_retryable_error(exception):
        return True
    
    # Check for OpenSearch-specific error patterns
    error_message = str(exception).lower()
    
    opensearch_retryable_patterns = [
        'connection timeout',
        'read timeout',
        'connection pool timeout',
        'service unavailable',
        'too many requests',
        'circuit breaker',
        'cluster block',
        'node not connected'
    ]
    
    return any(pattern in error_message for pattern in opensearch_retryable_patterns)


def _calculate_aws_retry_delay(exception: Exception, attempt: int, 
                              base_delay: float, max_delay: float) -> float:
    """Calculate retry delay for AWS operations with service-specific logic."""
    # Check for Retry-After header in throttling responses
    if hasattr(exception, 'response') and 'ResponseMetadata' in exception.response:
        headers = exception.response['ResponseMetadata'].get('HTTPHeaders', {})
        retry_after = headers.get('Retry-After') or headers.get('retry-after')
        
        if retry_after:
            try:
                return min(float(retry_after), max_delay)
            except (ValueError, TypeError):
                pass
    
    # Use exponential backoff with jitter
    return get_retry_delay(attempt, base_delay, max_delay)


# Convenience functions for common retry patterns
def with_retries(func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
    """
    Execute a function with retry logic.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    @retry_with_backoff(max_retries=max_retries)
    def wrapper():
        return func(*args, **kwargs)
    
    return wrapper()


def with_aws_retries(func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
    """
    Execute an AWS operation with retry logic.
    
    Args:
        func: AWS operation function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    @retry_aws_operation(max_retries=max_retries)
    def wrapper():
        return func(*args, **kwargs)
    
    return wrapper()
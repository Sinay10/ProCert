"""
Unit tests for the retry utilities and decorators.

This module tests the retry logic, exponential backoff, and AWS-specific
retry strategies for the ProCert content management system.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Import the retry utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from retry_utils import (
    retry_with_backoff, retry_aws_operation, retry_opensearch_operation,
    RetryContext, with_retries, with_aws_retries
)
from exceptions import (
    RetryableException, ThrottlingException, BedrockException,
    OpenSearchException
)


class TestRetryWithBackoff:
    """Test the general retry decorator."""
    
    def test_successful_operation_no_retry(self):
        """Test that successful operations don't trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_operation()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_retryable_exception(self):
        """Test that retryable exceptions trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)  # Fast retry for testing
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableException("Temporary failure")
            return "success"
        
        result = failing_then_success()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that max retries are respected."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise RetryableException("Always fails")
        
        with pytest.raises(RetryableException):
            always_failing()
        
        assert call_count == 3  # Initial call + 2 retries
    
    def test_non_retryable_exception_no_retry(self):
        """Test that non-retryable exceptions don't trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def non_retryable_failure():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            non_retryable_failure()
        
        assert call_count == 1  # No retries
    
    def test_custom_retryable_exceptions(self):
        """Test retry with custom retryable exception types."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01, 
                           retryable_exceptions=(ValueError, TypeError))
        def custom_retryable():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Custom retryable")
            return "success"
        
        result = custom_retryable()
        assert result == "success"
        assert call_count == 2
    
    @patch('time.sleep')
    def test_backoff_timing(self, mock_sleep):
        """Test that backoff delays are applied."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=1.0, jitter=False)
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RetryableException("Temporary failure")
            return "success"
        
        result = failing_operation()
        assert result == "success"
        
        # Should have called sleep twice (after first and second failures)
        assert mock_sleep.call_count == 2
        
        # Check that delays increase exponentially
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 1.0  # First delay
        assert calls[1][0][0] == 2.0  # Second delay (doubled)


class TestRetryAwsOperation:
    """Test the AWS-specific retry decorator."""
    
    def test_aws_throttling_retry(self):
        """Test retry on AWS throttling errors."""
        call_count = 0
        
        @retry_aws_operation(max_retries=2, base_delay=0.01)
        def throttled_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error_response = {
                    'Error': {
                        'Code': 'ThrottlingException',
                        'Message': 'Rate exceeded'
                    }
                }
                raise ClientError(error_response, 'put_item')
            return "success"
        
        result = throttled_operation()
        assert result == "success"
        assert call_count == 2
    
    def test_aws_non_retryable_error(self):
        """Test that non-retryable AWS errors don't trigger retries."""
        call_count = 0
        
        @retry_aws_operation(max_retries=3)
        def validation_error():
            nonlocal call_count
            call_count += 1
            error_response = {
                'Error': {
                    'Code': 'ValidationException',
                    'Message': 'Invalid parameter'
                }
            }
            raise ClientError(error_response, 'put_item')
        
        with pytest.raises(ClientError):
            validation_error()
        
        assert call_count == 1  # No retries for validation errors
    
    @patch('time.sleep')
    def test_retry_after_header_handling(self, mock_sleep):
        """Test handling of Retry-After headers in AWS responses."""
        call_count = 0
        
        @retry_aws_operation(max_retries=1, base_delay=1.0)
        def operation_with_retry_after():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error_response = {
                    'Error': {
                        'Code': 'ThrottlingException',
                        'Message': 'Rate exceeded'
                    },
                    'ResponseMetadata': {
                        'HTTPHeaders': {
                            'Retry-After': '5'
                        }
                    }
                }
                raise ClientError(error_response, 'put_item')
            return "success"
        
        result = operation_with_retry_after()
        assert result == "success"
        
        # Should use the Retry-After value
        mock_sleep.assert_called_once_with(5.0)


class TestRetryOpensearchOperation:
    """Test the OpenSearch-specific retry decorator."""
    
    def test_opensearch_connection_timeout_retry(self):
        """Test retry on OpenSearch connection timeouts."""
        call_count = 0
        
        @retry_opensearch_operation(max_retries=2, base_delay=0.01)
        def timeout_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("connection timeout")
            return "success"
        
        result = timeout_operation()
        assert result == "success"
        assert call_count == 2
    
    def test_opensearch_circuit_breaker_retry(self):
        """Test retry on OpenSearch circuit breaker errors."""
        call_count = 0
        
        @retry_opensearch_operation(max_retries=2, base_delay=0.01)
        def circuit_breaker_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("circuit breaker open")
            return "success"
        
        result = circuit_breaker_operation()
        assert result == "success"
        assert call_count == 2


class TestRetryContext:
    """Test the RetryContext context manager."""
    
    def test_successful_operation_no_retry(self):
        """Test successful operation with RetryContext."""
        attempt_count = 0
        
        with RetryContext(max_retries=3, base_delay=0.01, operation_name="test_op") as retry_ctx:
            while True:
                try:
                    attempt_count += 1
                    # Simulate successful operation
                    result = "success"
                    break
                except Exception:
                    if not retry_ctx.should_retry():
                        raise
        
        assert result == "success"
        assert attempt_count == 1
        assert retry_ctx.attempt == 0
    
    def test_retry_with_context_manager(self):
        """Test retry logic with RetryContext."""
        attempt_count = 0
        
        with RetryContext(max_retries=2, base_delay=0.01, operation_name="test_op") as retry_ctx:
            while True:
                try:
                    attempt_count += 1
                    if attempt_count < 3:
                        raise RetryableException("Temporary failure")
                    result = "success"
                    break
                except Exception:
                    if not retry_ctx.should_retry():
                        raise
        
        assert result == "success"
        assert attempt_count == 3
        assert retry_ctx.attempt == 2
    
    def test_max_retries_with_context_manager(self):
        """Test max retries exceeded with RetryContext."""
        attempt_count = 0
        
        with pytest.raises(RetryableException):
            with RetryContext(max_retries=2, base_delay=0.01) as retry_ctx:
                while True:
                    try:
                        attempt_count += 1
                        raise RetryableException("Always fails")
                    except Exception:
                        if not retry_ctx.should_retry():
                            raise
        
        assert attempt_count == 3  # Initial + 2 retries
    
    def test_non_retryable_with_context_manager(self):
        """Test non-retryable exception with RetryContext."""
        attempt_count = 0
        
        with pytest.raises(ValueError):
            with RetryContext(max_retries=3, base_delay=0.01) as retry_ctx:
                while True:
                    try:
                        attempt_count += 1
                        raise ValueError("Not retryable")
                    except Exception:
                        if not retry_ctx.should_retry():
                            raise
        
        assert attempt_count == 1  # No retries


class TestConvenienceFunctions:
    """Test the convenience functions for retry operations."""
    
    def test_with_retries_success(self):
        """Test with_retries function with successful operation."""
        def successful_func(x, y):
            return x + y
        
        result = with_retries(successful_func, 5, 10, max_retries=3)
        assert result == 15
    
    def test_with_retries_failure_then_success(self):
        """Test with_retries function with initial failures."""
        call_count = 0
        
        def failing_then_success(value):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableException("Temporary failure")
            return value * 2
        
        result = with_retries(failing_then_success, 5, max_retries=3)
        assert result == 10
        assert call_count == 3
    
    def test_with_aws_retries_throttling(self):
        """Test with_aws_retries function with throttling."""
        call_count = 0
        
        def throttled_aws_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error_response = {
                    'Error': {
                        'Code': 'ThrottlingException',
                        'Message': 'Rate exceeded'
                    }
                }
                raise ClientError(error_response, 'put_item')
            return "aws_success"
        
        result = with_aws_retries(throttled_aws_operation, max_retries=2)
        assert result == "aws_success"
        assert call_count == 2


class TestRetryIntegration:
    """Test retry integration with real-world scenarios."""
    
    @patch('time.sleep')
    def test_nested_retry_decorators(self, mock_sleep):
        """Test that nested retry decorators work correctly."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        @retry_aws_operation(max_retries=1, base_delay=0.01)
        def nested_retry_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableException("Temporary failure")
            return "success"
        
        result = nested_retry_operation()
        assert result == "success"
        # The inner decorator should handle the retry
        assert call_count == 2
    
    def test_retry_with_different_exception_types(self):
        """Test retry behavior with different exception types."""
        scenarios = [
            (RetryableException("retryable"), True),
            (ThrottlingException("throttled"), True),
            (ValueError("not retryable"), False),
            (KeyError("not retryable"), False)
        ]
        
        for exception, should_retry in scenarios:
            call_count = 0
            
            @retry_with_backoff(max_retries=2, base_delay=0.01)
            def test_operation():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise exception
                return "success"
            
            if should_retry:
                result = test_operation()
                assert result == "success"
                assert call_count == 2
            else:
                with pytest.raises(type(exception)):
                    test_operation()
                assert call_count == 1
    
    @patch('time.sleep')
    def test_performance_with_many_retries(self, mock_sleep):
        """Test performance characteristics with many retries."""
        call_count = 0
        max_retries = 5
        
        @retry_with_backoff(max_retries=max_retries, base_delay=0.01, jitter=False)
        def many_retries_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= max_retries:
                raise RetryableException("Keep failing")
            return "success"
        
        result = many_retries_operation()
        assert result == "success"
        assert call_count == max_retries + 1
        assert mock_sleep.call_count == max_retries
        
        # Verify exponential backoff progression
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        expected_delays = [0.01 * (2 ** i) for i in range(max_retries)]
        assert delays == expected_delays


if __name__ == '__main__':
    pytest.main([__file__])
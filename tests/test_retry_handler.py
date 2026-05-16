"""
Unit tests for core/retry_handler.py

Tests retry logic with exponential backoff.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from core.exceptions import NetworkError
from core.retry_handler import (
    AGGRESSIVE_RETRY,
    CONSERVATIVE_RETRY,
    NO_JITTER_RETRY,
    STANDARD_RETRY,
    RetryConfig,
    calculate_backoff,
    retry_with_backoff,
)


class TestCalculateBackoff:
    """Test backoff calculation logic."""
    
    def test_calculate_backoff_no_jitter(self):
        """Test backoff calculation without jitter."""
        # Attempt 0: 1.0 * (2^0) = 1.0
        assert calculate_backoff(0, 1.0, 2.0, 60.0, False) == 1.0
        
        # Attempt 1: 1.0 * (2^1) = 2.0
        assert calculate_backoff(1, 1.0, 2.0, 60.0, False) == 2.0
        
        # Attempt 2: 1.0 * (2^2) = 4.0
        assert calculate_backoff(2, 1.0, 2.0, 60.0, False) == 4.0
        
        # Attempt 3: 1.0 * (2^3) = 8.0
        assert calculate_backoff(3, 1.0, 2.0, 60.0, False) == 8.0
    
    def test_calculate_backoff_max_delay(self):
        """Test that backoff respects max delay."""
        # Attempt 10 would be 1024, but max is 60
        assert calculate_backoff(10, 1.0, 2.0, 60.0, False) == 60.0
        
        # Attempt 5 would be 32, but max is 10
        assert calculate_backoff(5, 1.0, 2.0, 10.0, False) == 10.0
    
    def test_calculate_backoff_with_jitter(self):
        """Test that jitter adds randomness."""
        # With jitter, result should be between 0.5x and 1.5x the base delay
        delay = calculate_backoff(0, 1.0, 2.0, 60.0, True)
        assert 0.5 <= delay <= 1.5
        
        # For attempt 1, base is 2.0, so range is 1.0 to 3.0
        delay = calculate_backoff(1, 1.0, 2.0, 60.0, True)
        assert 1.0 <= delay <= 3.0
    
    def test_calculate_backoff_custom_base(self):
        """Test backoff with custom exponential base."""
        # Base 3: 1.0 * (3^2) = 9.0
        assert calculate_backoff(2, 1.0, 3.0, 60.0, False) == 9.0
        
        # Base 1.5: 2.0 * (1.5^3) = 6.75
        assert calculate_backoff(3, 2.0, 1.5, 60.0, False) == 6.75


class TestRetryWithBackoff:
    """Test retry decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Test that successful calls don't retry."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_http_error(self):
        """Test retry on HTTP errors."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.HTTPError("Connection failed")
            return "success"
        
        result = await failing_func()
        assert result == "success"
        assert call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """Test retry on NetworkError."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network timeout")
            return "success"
        
        result = await failing_func()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test that exception is raised after max retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPError("Always fails")
        
        with pytest.raises(httpx.HTTPError, match="Always fails"):
            await always_failing_func()
        
        assert call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_no_retry_on_unexpected_exception(self):
        """Test that unexpected exceptions are not retried."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def unexpected_error_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Unexpected error")
        
        with pytest.raises(ValueError, match="Unexpected error"):
            await unexpected_error_func()
        
        assert call_count == 1  # No retries
    
    @pytest.mark.asyncio
    async def test_custom_retry_exceptions(self):
        """Test retry with custom exception types."""
        call_count = 0
        
        @retry_with_backoff(
            max_retries=2,
            base_delay=0.1,
            jitter=False,
            retry_on=(ValueError,)
        )
        async def custom_exception_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Custom error")
            return "success"
        
        result = await custom_exception_func()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_backoff_timing(self):
        """Test that backoff delays are applied."""
        call_times = []
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def timed_func():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise httpx.HTTPError("Retry me")
            return "success"
        
        await timed_func()
        
        # Check that delays were applied (approximately)
        # First retry: ~0.1s delay
        # Second retry: ~0.2s delay
        assert len(call_times) == 3
        assert call_times[1] - call_times[0] >= 0.09  # Allow small timing variance
        assert call_times[2] - call_times[1] >= 0.18


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_retry_config_initialization(self):
        """Test RetryConfig initialization."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
    
    @pytest.mark.asyncio
    async def test_retry_config_as_decorator(self):
        """Test using RetryConfig as a decorator."""
        call_count = 0
        config = RetryConfig(max_retries=2, base_delay=0.1, jitter=False)
        
        @config
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.HTTPError("Retry")
            return "success"
        
        result = await decorated_func()
        assert result == "success"
        assert call_count == 2
    
    def test_predefined_configs(self):
        """Test predefined retry configurations."""
        # Conservative
        assert CONSERVATIVE_RETRY.max_retries == 2
        assert CONSERVATIVE_RETRY.base_delay == 0.5
        assert CONSERVATIVE_RETRY.max_delay == 5.0
        
        # Standard
        assert STANDARD_RETRY.max_retries == 3
        assert STANDARD_RETRY.base_delay == 1.0
        assert STANDARD_RETRY.max_delay == 30.0
        
        # Aggressive
        assert AGGRESSIVE_RETRY.max_retries == 5
        assert AGGRESSIVE_RETRY.base_delay == 2.0
        assert AGGRESSIVE_RETRY.max_delay == 120.0
        
        # No jitter
        assert NO_JITTER_RETRY.jitter is False
    
    @pytest.mark.asyncio
    async def test_predefined_config_usage(self):
        """Test using predefined configurations."""
        call_count = 0
        
        @CONSERVATIVE_RETRY
        async def func_with_conservative_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.HTTPError("Retry")
            return "success"
        
        result = await func_with_conservative_retry()
        assert result == "success"
        assert call_count == 2


class TestRetryIntegration:
    """Integration tests for retry functionality."""
    
    @pytest.mark.asyncio
    async def test_retry_with_async_context_manager(self):
        """Test retry with async context managers."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def func_with_context():
            nonlocal call_count
            call_count += 1
            async with AsyncMock() as mock_client:
                if call_count < 2:
                    raise httpx.HTTPError("Retry")
                return "success"
        
        result = await func_with_context()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @retry_with_backoff()
        async def documented_func():
            """This is a documented function."""
            return "result"
        
        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a documented function."
    
    @pytest.mark.asyncio
    async def test_retry_with_args_and_kwargs(self):
        """Test retry with function arguments."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1, jitter=False)
        async def func_with_args(x: int, y: int, z: int = 0):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.HTTPError("Retry")
            return x + y + z
        
        result = await func_with_args(1, 2, z=3)
        assert result == 6
        assert call_count == 2

# Made with Bob

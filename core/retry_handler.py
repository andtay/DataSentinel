"""
Retry logic with exponential backoff for resilient API calls.

This module provides a decorator for async functions that automatically
retries failed operations with exponential backoff and jitter.
"""

import asyncio
import random
from functools import wraps
from typing import Any, Callable, Type, TypeVar

import httpx
from loguru import logger

from core.exceptions import NetworkError

T = TypeVar('T')


def calculate_backoff(
    attempt: int,
    base_delay: float,
    exponential_base: float,
    max_delay: float,
    jitter: bool
) -> float:
    """
    Calculate delay with exponential backoff and optional jitter.
    
    Formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)
    With jitter: delay = delay * random(0.5, 1.5)
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        exponential_base: Base for exponential calculation (typically 2)
        max_delay: Maximum delay cap in seconds
        jitter: Whether to add random jitter
        
    Returns:
        Calculated delay in seconds
        
    Examples:
        >>> calculate_backoff(0, 1.0, 2.0, 60.0, False)
        1.0
        >>> calculate_backoff(1, 1.0, 2.0, 60.0, False)
        2.0
        >>> calculate_backoff(2, 1.0, 2.0, 60.0, False)
        4.0
    """
    # Calculate exponential delay
    delay = base_delay * (exponential_base ** attempt)
    
    # Apply max delay cap
    delay = min(delay, max_delay)
    
    # Add jitter to prevent thundering herd
    if jitter:
        jitter_factor = random.uniform(0.5, 1.5)
        delay *= jitter_factor
    
    return delay


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple[Type[Exception], ...] = (httpx.HTTPError, NetworkError)
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for async functions with exponential backoff retry logic.
    
    This decorator will automatically retry failed async function calls with
    exponential backoff. It's particularly useful for network operations that
    may experience transient failures.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retry_on: Tuple of exception types to retry on (default: httpx.HTTPError, NetworkError)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        ```python
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data(url: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        ```
    
    Raises:
        The last exception encountered if all retries are exhausted
    """
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            
            # Initial attempt + retries
            for attempt in range(max_retries + 1):
                try:
                    # Attempt the function call
                    result = await func(*args, **kwargs)
                    
                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded after {attempt} retries"
                        )
                    
                    return result
                    
                except retry_on as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise the exception
                    if attempt >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate backoff delay
                    delay = calculate_backoff(
                        attempt=attempt,
                        base_delay=base_delay,
                        exponential_base=exponential_base,
                        max_delay=max_delay,
                        jitter=jitter
                    )
                    
                    # Log retry attempt
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(
                        f"Function {func.__name__} failed with unexpected exception: {e}"
                    )
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed without exception")
        
        return wrapper
    
    return decorator


class RetryConfig:
    """
    Configuration for retry behavior.
    
    This class provides a convenient way to define and reuse retry configurations.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: tuple[Type[Exception], ...] = (httpx.HTTPError, NetworkError)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on
    
    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Allow RetryConfig to be used as a decorator.
        
        Example:
            ```python
            retry_config = RetryConfig(max_retries=5, base_delay=2.0)
            
            @retry_config
            async def fetch_data(url: str) -> dict:
                ...
            ```
        """
        return retry_with_backoff(
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter,
            retry_on=self.retry_on
        )(func)


# Predefined retry configurations for common scenarios

# Conservative retry: Few retries, short delays
CONSERVATIVE_RETRY = RetryConfig(
    max_retries=2,
    base_delay=0.5,
    max_delay=5.0
)

# Standard retry: Balanced approach
STANDARD_RETRY = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0
)

# Aggressive retry: Many retries, longer delays
AGGRESSIVE_RETRY = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0
)

# No jitter: Useful for testing
NO_JITTER_RETRY = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    jitter=False
)

# Made with Bob

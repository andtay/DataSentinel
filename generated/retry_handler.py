"""
Simple retry handler for the generated API validation service.
"""
import asyncio
import functools
from typing import Callable, TypeVar, Any
from loguru import logger

T = TypeVar('T')


def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. Last error: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# Made with Bob
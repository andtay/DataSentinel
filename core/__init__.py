"""
Core infrastructure for DataSentinel.

This package contains the foundational components used throughout the framework:
- Exception hierarchy
- Base provider for API interactions
- Retry logic with exponential backoff
- Authentication management
- Utility functions
"""

from core.auth_manager import (
    AuthHandler,
    AuthManager,
    AuthType,
    NoAuth,
    APIKeyAuth,
    BearerAuth,
    OAuth2Auth,
)
from core.base_provider import BaseProvider, SimpleProvider
from core.exceptions import (
    DataSentinelError,
    ParserError,
    GeneratorError,
    ValidationError,
    AuthenticationError,
    SchemaDriftError,
    ConfigurationError,
    NetworkError,
    TemplateError,
)
from core.retry_handler import (
    retry_with_backoff,
    calculate_backoff,
    RetryConfig,
    CONSERVATIVE_RETRY,
    STANDARD_RETRY,
    AGGRESSIVE_RETRY,
)

__all__ = [
    # Exceptions
    "DataSentinelError",
    "ParserError",
    "GeneratorError",
    "ValidationError",
    "AuthenticationError",
    "SchemaDriftError",
    "ConfigurationError",
    "NetworkError",
    "TemplateError",
    # Authentication
    "AuthHandler",
    "AuthManager",
    "AuthType",
    "NoAuth",
    "APIKeyAuth",
    "BearerAuth",
    "OAuth2Auth",
    # Providers
    "BaseProvider",
    "SimpleProvider",
    # Retry
    "retry_with_backoff",
    "calculate_backoff",
    "RetryConfig",
    "CONSERVATIVE_RETRY",
    "STANDARD_RETRY",
    "AGGRESSIVE_RETRY",
]

# Made with Bob

"""
Custom exception hierarchy for DataSentinel.

This module defines all domain-specific exceptions used throughout the framework.
"""


class DataSentinelError(Exception):
    """
    Base exception for all DataSentinel errors.
    
    All custom exceptions in DataSentinel inherit from this base class,
    making it easy to catch all framework-specific errors.
    """
    
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ParserError(DataSentinelError):
    """
    Raised when parsing an API specification fails.
    
    This can occur when:
    - The specification file is malformed
    - Required fields are missing
    - The specification format is not supported
    - Network errors occur when fetching remote specifications
    """
    pass


# Alias for backward compatibility
ParsingError = ParserError


class GeneratorError(DataSentinelError):
    """
    Raised when code generation fails.
    
    This can occur when:
    - Template rendering fails
    - Generated code is invalid
    - File writing fails
    - Required data is missing from the schema
    """
    pass


# Alias for backward compatibility
GenerationError = GeneratorError


class ValidationError(DataSentinelError):
    """
    Raised when validation fails.
    
    This can occur when:
    - API response doesn't match expected schema
    - Field validation fails
    - Type conversion fails
    """
    pass


class AuthenticationError(DataSentinelError):
    """
    Raised when authentication fails.
    
    This can occur when:
    - Invalid credentials provided
    - Token has expired
    - OAuth2 token refresh fails
    - API key is rejected
    """
    pass


class SchemaDriftError(DataSentinelError):
    """
    Raised when schema drift is detected.
    
    This occurs when the current API schema differs from the stored schema,
    indicating that the API structure has changed.
    """
    
    def __init__(self, message: str, old_schema: dict | None = None, new_schema: dict | None = None):
        super().__init__(message)
        self.old_schema = old_schema
        self.new_schema = new_schema


class ConfigurationError(DataSentinelError):
    """
    Raised when configuration is invalid.
    
    This can occur when:
    - Required configuration values are missing
    - Configuration values are invalid
    - Environment variables are not set
    """
    pass


class NetworkError(DataSentinelError):
    """
    Raised when network operations fail.
    
    This can occur when:
    - HTTP requests timeout
    - Connection is refused
    - DNS resolution fails
    - SSL/TLS errors occur
    """
    pass


class TemplateError(DataSentinelError):
    """
    Raised when template operations fail.
    
    This can occur when:
    - Template file is not found
    - Template syntax is invalid
    - Required template variables are missing
    """
    pass

# Made with Bob

"""
Simple exceptions for the generated API validation service.
"""
from typing import Optional


class ValidationException(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None, errors: Optional[list] = None):
        self.message = message
        self.details = details or {}
        self.errors = errors or []
        super().__init__(self.message)


class APIException(Exception):
    """Raised when API call fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SchemaException(Exception):
    """Raised when schema validation fails."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# Made with Bob

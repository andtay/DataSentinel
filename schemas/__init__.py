"""
Data structures and schemas for DataSentinel.

This package contains all internal data structures used throughout the framework:
- API schema representations
- Field schema definitions
- Configuration models
"""

from schemas.api_schema import (
    APISchema,
    AuthConfig,
    Endpoint,
    ModelSchema,
    Parameter,
)
from schemas.config_schema import (
    GenerationConfig,
    GeneratorConfig,
    ParserConfig,
)
from schemas.field_schema import (
    FieldSchema,
    FieldType,
    ValidatorConfig,
    OPENAPI_TYPE_MAP,
    GRAPHQL_TYPE_MAP,
    PYTHON_TYPE_MAP,
)

__all__ = [
    # API Schema
    "APISchema",
    "AuthConfig",
    "Endpoint",
    "ModelSchema",
    "Parameter",
    # Field Schema
    "FieldSchema",
    "FieldType",
    "ValidatorConfig",
    "OPENAPI_TYPE_MAP",
    "GRAPHQL_TYPE_MAP",
    "PYTHON_TYPE_MAP",
    # Configuration
    "GenerationConfig",
    "GeneratorConfig",
    "ParserConfig",
]

# Made with Bob

"""
Configuration models for the generation pipeline.

This module defines configuration structures used throughout DataSentinel
for controlling parsing and generation behavior.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class AuthType(str, Enum):
    """Authentication type enumeration."""
    NONE = "none"
    API_KEY = "api-key"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class AuthConfig(BaseModel):
    """
    Authentication configuration for API access.
    
    Supports multiple authentication strategies:
    - API Key (in header or query parameter)
    - Bearer token
    - OAuth2
    - Basic authentication
    """
    
    auth_type: AuthType = Field(
        default=AuthType.NONE,
        description="Type of authentication to use"
    )
    
    # API Key authentication
    api_key: str | None = Field(
        None,
        description="API key for authentication"
    )
    header_name: str | None = Field(
        None,
        description="Custom header name for API key (default: X-API-Key)"
    )
    
    # Bearer token authentication
    bearer_token: str | None = Field(
        None,
        description="Bearer token for authentication"
    )
    
    # OAuth2 authentication
    client_id: str | None = Field(
        None,
        description="OAuth2 client ID"
    )
    client_secret: str | None = Field(
        None,
        description="OAuth2 client secret"
    )
    token_url: str | None = Field(
        None,
        description="OAuth2 token endpoint URL"
    )
    
    # Basic authentication
    username: str | None = Field(
        None,
        description="Username for basic authentication"
    )
    password: str | None = Field(
        None,
        description="Password for basic authentication"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "auth_type": "api-key",
                    "api_key": "your-api-key-here",
                    "header_name": "X-API-Key"
                },
                {
                    "auth_type": "bearer",
                    "bearer_token": "your-bearer-token-here"
                },
                {
                    "auth_type": "basic",
                    "username": "user",
                    "password": "pass"
                }
            ]
        }
    }


class GenerationConfig(BaseModel):
    """
    Configuration for code generation pipeline.
    
    This is created from CLI arguments and passed through the orchestration
    to control how code is generated.
    """
    
    # Input configuration
    input_type: str = Field(..., description="Input type: openapi, graphql, json")
    source: str = Field(..., description="File path or URL to API specification")
    
    # Output configuration
    output_dir: Path = Field(..., description="Output directory for generated files")
    project_name: str = Field(..., description="Project name (used in generated code)")
    
    # Authentication (optional)
    auth_type: str | None = Field(None, description="Auth type: api_key, bearer, oauth2")
    auth_value: str | None = Field(None, description="Auth token/key value")
    
    # Generation options
    generate_tests: bool = Field(True, description="Whether to generate test suite")
    generate_docs: bool = Field(True, description="Whether to generate documentation")
    generate_docker: bool = Field(True, description="Whether to generate Dockerfile")
    generate_readme: bool = Field(True, description="Whether to generate README")
    
    # Code style options
    use_black: bool = Field(True, description="Format code with black")
    use_isort: bool = Field(True, description="Sort imports with isort")
    line_length: int = Field(88, description="Maximum line length", ge=60, le=120)
    
    # Advanced options
    verbose: bool = Field(False, description="Verbose logging")
    dry_run: bool = Field(False, description="Dry run without writing files")
    overwrite: bool = Field(False, description="Overwrite existing files")
    
    @field_validator('input_type')
    @classmethod
    def validate_input_type(cls, v: str) -> str:
        """Validate input type is supported."""
        allowed = ['openapi', 'graphql', 'json']
        if v.lower() not in allowed:
            raise ValueError(f"input_type must be one of {allowed}")
        return v.lower()
    
    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v: str | None) -> str | None:
        """Validate auth type if provided."""
        if v is None:
            return v
        allowed = ['api_key', 'bearer', 'oauth2', 'none']
        if v.lower() not in allowed:
            raise ValueError(f"auth_type must be one of {allowed}")
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "input_type": "openapi",
                "source": "examples/openapi/petstore.yaml",
                "output_dir": "./output/petstore",
                "project_name": "petstore",
                "auth_type": "bearer",
                "auth_value": "secret_token",
                "generate_tests": True,
                "generate_docs": True,
                "generate_docker": True,
                "use_black": True,
                "line_length": 88,
                "verbose": False
            }
        }
    }


class ParserConfig(BaseModel):
    """
    Configuration specific to parsers.
    
    Controls how API specifications are parsed.
    """
    
    source: str = Field(..., description="Source file or URL")
    timeout: int = Field(30, description="Timeout for HTTP requests (seconds)", ge=1)
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    
    # OpenAPI specific
    resolve_refs: bool = Field(True, description="Resolve $ref references")
    
    # GraphQL specific
    introspection_query: str | None = Field(
        None,
        description="Custom introspection query"
    )
    
    # JSON inference specific
    infer_patterns: bool = Field(True, description="Detect patterns in string values")
    multiple_samples: int | None = Field(
        None,
        description="Number of samples to analyze",
        ge=1
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "https://api.example.com/openapi.json",
                "timeout": 30,
                "follow_redirects": True,
                "verify_ssl": True,
                "resolve_refs": True
            }
        }
    }


class GeneratorConfig(BaseModel):
    """
    Configuration specific to generators.
    
    Controls how code artifacts are generated.
    """
    
    template_dir: Path = Field(..., description="Directory containing Jinja2 templates")
    output_dir: Path = Field(..., description="Output directory")
    
    # Code generation options
    add_type_hints: bool = Field(True, description="Add type hints to generated code")
    add_docstrings: bool = Field(True, description="Add docstrings to generated code")
    add_examples: bool = Field(True, description="Add usage examples")
    
    # Validation options
    strict_validation: bool = Field(True, description="Use Pydantic strict mode")
    validate_assignment: bool = Field(True, description="Validate on assignment")
    
    # Testing options
    test_coverage_target: int = Field(
        80,
        description="Target test coverage percentage",
        ge=0,
        le=100
    )
    generate_mocks: bool = Field(True, description="Generate mock data with polyfactory")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "template_dir": "./templates",
                "output_dir": "./output/petstore",
                "add_type_hints": True,
                "add_docstrings": True,
                "strict_validation": True,
                "test_coverage_target": 80
            }
        }
    }

# Made with Bob

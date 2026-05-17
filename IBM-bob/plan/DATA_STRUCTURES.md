# Data Structures & Interfaces - DataSentinel

This document defines all internal data structures, schemas, and interface contracts used throughout DataSentinel.

---

## Core Schema Definitions

### [`schemas/api_schema.py`](schemas/api_schema.py)

Complete API specification representation that serves as the normalized output from all parsers.

```python
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class APISchema(BaseModel):
    """
    Complete API specification - normalized output from all parsers.
    
    This is the central data structure that flows through the entire pipeline:
    Parser → APISchema → Generators
    """
    title: str = Field(..., description="API title")
    version: str = Field(..., description="API version")
    base_url: str = Field(..., description="Base URL for API endpoints")
    description: Optional[str] = Field(None, description="API description")
    endpoints: List['Endpoint'] = Field(default_factory=list, description="All API endpoints")
    models: Dict[str, 'ModelSchema'] = Field(default_factory=dict, description="All data models")
    auth_config: Optional['AuthConfig'] = Field(None, description="Authentication configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Pet Store API",
                "version": "1.0.0",
                "base_url": "https://api.petstore.com",
                "description": "A sample Pet Store API",
                "endpoints": [],
                "models": {},
                "auth_config": None
            }
        }


class Endpoint(BaseModel):
    """
    API endpoint definition.
    
    Represents a single API operation (GET /users, POST /orders, etc.)
    """
    path: str = Field(..., description="Endpoint path (e.g., /users/{id})")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    summary: Optional[str] = Field(None, description="Short summary of endpoint")
    description: Optional[str] = Field(None, description="Detailed description")
    operation_id: Optional[str] = Field(None, description="Unique operation identifier")
    
    # Request/Response models
    request_model: Optional['ModelSchema'] = Field(None, description="Request body model")
    response_model: 'ModelSchema' = Field(..., description="Response body model")
    
    # Parameters
    parameters: List['Parameter'] = Field(default_factory=list, description="Path, query, header parameters")
    
    # Metadata
    auth_required: bool = Field(True, description="Whether authentication is required")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags for organization")
    deprecated: bool = Field(False, description="Whether endpoint is deprecated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "/users/{id}",
                "method": "GET",
                "summary": "Get user by ID",
                "description": "Retrieve a single user by their unique identifier",
                "operation_id": "getUser",
                "request_model": None,
                "response_model": {"name": "User", "fields": []},
                "parameters": [],
                "auth_required": True,
                "tags": ["users"],
                "deprecated": False
            }
        }


class Parameter(BaseModel):
    """
    Endpoint parameter (path, query, header, cookie).
    """
    name: str = Field(..., description="Parameter name")
    location: str = Field(..., description="Parameter location: path, query, header, cookie")
    required: bool = Field(True, description="Whether parameter is required")
    schema: 'FieldSchema' = Field(..., description="Parameter schema")
    description: Optional[str] = Field(None, description="Parameter description")
    deprecated: bool = Field(False, description="Whether parameter is deprecated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "id",
                "location": "path",
                "required": True,
                "schema": {"name": "id", "type": "integer"},
                "description": "User ID",
                "deprecated": False
            }
        }


class ModelSchema(BaseModel):
    """
    Data model definition - represents a Pydantic model to be generated.
    """
    name: str = Field(..., description="Model name (PascalCase)")
    fields: List['FieldSchema'] = Field(..., description="Model fields")
    description: Optional[str] = Field(None, description="Model description")
    example: Optional[Dict] = Field(None, description="Example instance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "integer", "required": True},
                    {"name": "email", "type": "email", "required": True},
                    {"name": "name", "type": "string", "required": False}
                ],
                "description": "User model",
                "example": {"id": 1, "email": "user@example.com", "name": "John Doe"}
            }
        }


class AuthConfig(BaseModel):
    """
    Authentication configuration for the API.
    """
    type: str = Field(..., description="Auth type: api_key, bearer, oauth2, none")
    location: Optional[str] = Field(None, description="Location: header, query")
    name: Optional[str] = Field(None, description="Parameter/header name")
    scheme: Optional[str] = Field(None, description="Auth scheme (e.g., Bearer)")
    
    # OAuth2 specific
    token_url: Optional[str] = Field(None, description="OAuth2 token URL")
    authorization_url: Optional[str] = Field(None, description="OAuth2 authorization URL")
    scopes: Optional[Dict[str, str]] = Field(None, description="OAuth2 scopes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "bearer",
                "location": "header",
                "name": "Authorization",
                "scheme": "Bearer"
            }
        }
```

---

### [`schemas/field_schema.py`](schemas/field_schema.py)

Field-level schema definitions with validation rules.

```python
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """
    Supported field types - maps to Pydantic types.
    """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    UUID = "uuid"
    EMAIL = "email"
    URL = "url"
    ANY = "any"


class FieldSchema(BaseModel):
    """
    Field definition with validation rules.
    
    This represents a single field in a Pydantic model, including:
    - Type information
    - Validation constraints
    - Default values
    - Documentation
    """
    name: str = Field(..., description="Field name (snake_case)")
    type: FieldType = Field(..., description="Field type")
    required: bool = Field(True, description="Whether field is required")
    description: Optional[str] = Field(None, description="Field description")
    default: Optional[Any] = Field(None, description="Default value")
    
    # String validation
    pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    min_length: Optional[int] = Field(None, description="Minimum string length")
    max_length: Optional[int] = Field(None, description="Maximum string length")
    
    # Numeric validation
    min_value: Optional[float] = Field(None, description="Minimum numeric value")
    max_value: Optional[float] = Field(None, description="Maximum numeric value")
    multiple_of: Optional[float] = Field(None, description="Value must be multiple of this")
    
    # Enum validation
    enum_values: Optional[List[Any]] = Field(None, description="Allowed enum values")
    
    # Array-specific
    item_type: Optional[FieldType] = Field(None, description="Type of array items")
    min_items: Optional[int] = Field(None, description="Minimum array length")
    max_items: Optional[int] = Field(None, description="Maximum array length")
    unique_items: bool = Field(False, description="Whether array items must be unique")
    
    # Object-specific
    nested_model: Optional[str] = Field(None, description="Reference to nested ModelSchema name")
    additional_properties: bool = Field(True, description="Whether additional properties allowed")
    
    # Metadata
    example: Optional[Any] = Field(None, description="Example value")
    deprecated: bool = Field(False, description="Whether field is deprecated")
    read_only: bool = Field(False, description="Whether field is read-only")
    write_only: bool = Field(False, description="Whether field is write-only")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "email",
                "type": "email",
                "required": True,
                "description": "User email address",
                "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$",
                "example": "user@example.com"
            }
        }


class ValidatorConfig(BaseModel):
    """
    Custom validator configuration for complex validation rules.
    
    Used when standard Pydantic validators aren't sufficient.
    """
    field_name: str = Field(..., description="Field to validate")
    validator_type: str = Field(..., description="Validator type: regex, range, custom, cross_field")
    validator_code: str = Field(..., description="Python code for validator")
    error_message: str = Field(..., description="Error message on validation failure")
    depends_on: Optional[List[str]] = Field(None, description="Other fields this validator depends on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "password",
                "validator_type": "custom",
                "validator_code": "len(v) >= 8 and any(c.isupper() for c in v)",
                "error_message": "Password must be at least 8 characters with one uppercase letter",
                "depends_on": None
            }
        }
```

---

### [`schemas/config_schema.py`](schemas/config_schema.py)

Configuration models for the generation pipeline.

```python
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GenerationConfig(BaseModel):
    """
    Configuration for code generation pipeline.
    
    This is created from CLI arguments and passed through the orchestration.
    """
    # Input configuration
    input_type: str = Field(..., description="Input type: openapi, graphql, json")
    source: str = Field(..., description="File path or URL to API specification")
    
    # Output configuration
    output_dir: Path = Field(..., description="Output directory for generated files")
    project_name: str = Field(..., description="Project name (used in generated code)")
    
    # Authentication (optional)
    auth_type: Optional[str] = Field(None, description="Auth type: api_key, bearer, oauth2")
    auth_value: Optional[str] = Field(None, description="Auth token/key value")
    
    # Generation options
    generate_tests: bool = Field(True, description="Whether to generate test suite")
    generate_docs: bool = Field(True, description="Whether to generate documentation")
    generate_docker: bool = Field(True, description="Whether to generate Dockerfile")
    generate_readme: bool = Field(True, description="Whether to generate README")
    
    # Code style options
    use_black: bool = Field(True, description="Format code with black")
    use_isort: bool = Field(True, description="Sort imports with isort")
    line_length: int = Field(88, description="Maximum line length")
    
    # Advanced options
    verbose: bool = Field(False, description="Verbose logging")
    dry_run: bool = Field(False, description="Dry run without writing files")
    overwrite: bool = Field(False, description="Overwrite existing files")
    
    @field_validator('input_type')
    @classmethod
    def validate_input_type(cls, v: str) -> str:
        """Validate input type is supported."""
        allowed = ['openapi', 'graphql', 'json']
        if v not in allowed:
            raise ValueError(f"input_type must be one of {allowed}")
        return v
    
    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate auth type if provided."""
        if v is None:
            return v
        allowed = ['api_key', 'bearer', 'oauth2', 'none']
        if v not in allowed:
            raise ValueError(f"auth_type must be one of {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
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


class ParserConfig(BaseModel):
    """
    Configuration specific to parsers.
    """
    source: str = Field(..., description="Source file or URL")
    timeout: int = Field(30, description="Timeout for HTTP requests (seconds)")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    
    # OpenAPI specific
    resolve_refs: bool = Field(True, description="Resolve $ref references")
    
    # GraphQL specific
    introspection_query: Optional[str] = Field(None, description="Custom introspection query")
    
    # JSON inference specific
    infer_patterns: bool = Field(True, description="Detect patterns in string values")
    multiple_samples: Optional[int] = Field(None, description="Number of samples to analyze")


class GeneratorConfig(BaseModel):
    """
    Configuration specific to generators.
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
    test_coverage_target: int = Field(80, description="Target test coverage percentage")
    generate_mocks: bool = Field(True, description="Generate mock data with polyfactory")
```

---

## Type Mappings

### OpenAPI to FieldType

```python
OPENAPI_TYPE_MAP = {
    ("string", None): FieldType.STRING,
    ("string", "date"): FieldType.DATE,
    ("string", "date-time"): FieldType.DATETIME,
    ("string", "uuid"): FieldType.UUID,
    ("string", "email"): FieldType.EMAIL,
    ("string", "uri"): FieldType.URL,
    ("string", "url"): FieldType.URL,
    ("integer", None): FieldType.INTEGER,
    ("integer", "int32"): FieldType.INTEGER,
    ("integer", "int64"): FieldType.INTEGER,
    ("number", None): FieldType.FLOAT,
    ("number", "float"): FieldType.FLOAT,
    ("number", "double"): FieldType.FLOAT,
    ("boolean", None): FieldType.BOOLEAN,
    ("array", None): FieldType.ARRAY,
    ("object", None): FieldType.OBJECT,
}
```

### GraphQL to FieldType

```python
GRAPHQL_TYPE_MAP = {
    "String": FieldType.STRING,
    "Int": FieldType.INTEGER,
    "Float": FieldType.FLOAT,
    "Boolean": FieldType.BOOLEAN,
    "ID": FieldType.STRING,
    "Date": FieldType.DATE,
    "DateTime": FieldType.DATETIME,
    "UUID": FieldType.UUID,
    "Email": FieldType.EMAIL,
    "URL": FieldType.URL,
}
```

### Python to FieldType

```python
PYTHON_TYPE_MAP = {
    int: FieldType.INTEGER,
    float: FieldType.FLOAT,
    str: FieldType.STRING,
    bool: FieldType.BOOLEAN,
    list: FieldType.ARRAY,
    dict: FieldType.OBJECT,
}
```

---

## Validation Result Models

### ValidationResult

Used by generated validators to return validation results.

```python
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """
    Result of API validation.
    
    Generated validators return this model to provide structured feedback.
    """
    valid: bool = Field(..., description="Whether validation passed")
    data: Optional[Any] = Field(None, description="Validated data if successful")
    errors: List['ValidationError'] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    
    # Metadata
    endpoint: str = Field(..., description="Endpoint that was validated")
    timestamp: str = Field(..., description="Validation timestamp (ISO 8601)")
    duration_ms: float = Field(..., description="Validation duration in milliseconds")
    
    # Schema drift detection
    schema_changed: bool = Field(False, description="Whether schema drift was detected")
    schema_diff: Optional[Dict] = Field(None, description="Schema differences if drift detected")


class ValidationError(BaseModel):
    """
    Individual validation error.
    """
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type: type_error, value_error, missing")
    input_value: Optional[Any] = Field(None, description="Value that caused error")
```

---

## Interface Contracts

### Parser Interface

All parsers must implement this interface:

```python
from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path


class BaseParser(ABC):
    """
    Abstract base for all API specification parsers.
    
    Contract:
    1. Accept source (file path or URL) in __init__
    2. Implement async parse() returning APISchema
    3. Handle errors gracefully with ParserError
    """
    
    def __init__(self, source: Union[Path, str]):
        self.source = source
    
    @abstractmethod
    async def parse(self) -> APISchema:
        """
        Parse input and return normalized APISchema.
        
        Returns:
            APISchema: Normalized API specification
            
        Raises:
            ParserError: If parsing fails
        """
        pass
```

### Generator Interface

All generators must implement this interface:

```python
from abc import ABC, abstractmethod
from pathlib import Path


class BaseGenerator(ABC):
    """
    Abstract base for all code generators.
    
    Contract:
    1. Accept template_dir and output_dir in __init__
    2. Implement async generate() accepting APISchema
    3. Return Path to generated file
    4. Handle errors gracefully with GeneratorError
    """
    
    def __init__(self, template_dir: Path, output_dir: Path):
        self.template_dir = template_dir
        self.output_dir = output_dir
    
    @abstractmethod
    async def generate(self, api_schema: APISchema) -> Path:
        """
        Generate artifact from APISchema.
        
        Args:
            api_schema: Normalized API specification
            
        Returns:
            Path: Path to generated file
            
        Raises:
            GeneratorError: If generation fails
        """
        pass
```

---

## Data Flow

### Complete Pipeline

```
Input (OpenAPI/GraphQL/JSON)
    ↓
Parser (openapi_parser/graphql_parser/json_inference_parser)
    ↓
APISchema (normalized representation)
    ↓
Schema Normalizer (validation & normalization)
    ↓
APISchema (validated)
    ↓
Generators (parallel execution)
    ├→ ModelGenerator → models.py
    ├→ ValidatorGenerator → validators.py
    ├→ TestGenerator → test_api.py
    ├→ AppGenerator → app.py
    ├→ DocGenerator → data_dict.md
    └→ DockerGenerator → Dockerfile
    ↓
Output (complete project)
```

### Data Transformations

1. **Parser Output → APISchema**
   - OpenAPI paths → List[Endpoint]
   - OpenAPI components → Dict[str, ModelSchema]
   - GraphQL types → Dict[str, ModelSchema]
   - JSON structure → ModelSchema

2. **APISchema → Generated Code**
   - ModelSchema → Pydantic BaseModel class
   - Endpoint → Validator method
   - Endpoint → Test function
   - Endpoint → FastAPI route

---

## Summary

This document defines:
- ✅ Complete schema hierarchy (APISchema, ModelSchema, FieldSchema)
- ✅ Configuration models (GenerationConfig, ParserConfig, GeneratorConfig)
- ✅ Type mappings (OpenAPI, GraphQL, Python → FieldType)
- ✅ Validation result models
- ✅ Interface contracts for parsers and generators
- ✅ Data flow through the pipeline

All data structures use Pydantic for:
- Type safety
- Validation
- Serialization/deserialization
- Documentation generation
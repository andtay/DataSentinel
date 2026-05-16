# API Reference

Complete API reference for DataSentinel framework and generated services.

## Table of Contents

1. [DataSentinel CLI](#datasentinel-cli)
2. [Core Modules](#core-modules)
3. [Parsers](#parsers)
4. [Generators](#generators)
5. [Generated API](#generated-api)
6. [Configuration](#configuration)

---

## DataSentinel CLI

### Command-Line Interface

```bash
python auto_sentinel.py --api <SOURCE> [OPTIONS]
```

### Arguments

#### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--api` | API source (URL, file path, or endpoint) | `--api ./spec.yaml` |

#### Optional Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--output` | `-o` | Output directory | `./generated` |
| `--format` | `-f` | Input format (`json`, `openapi`, `graphql`) | Auto-detect |
| `--verbose` | `-v` | Enable verbose logging | `False` |
| `--dry-run` | | Show what would be generated | `False` |
| `--log-file` | | Write logs to file | None |
| `--version` | | Show version and exit | |

#### Authentication Options

| Argument | Description | Example |
|----------|-------------|---------|
| `--auth-type` | Authentication type | `bearer`, `api-key`, `basic`, `oauth2` |
| `--auth-token` | Authentication token or API key | `--auth-token YOUR_TOKEN` |
| `--auth-header` | Custom authentication header name | `--auth-header X-API-Key` |
| `--auth-username` | Username for basic auth | `--auth-username user` |

#### Generation Options

| Argument | Description |
|----------|-------------|
| `--skip-models` | Skip models.py generation |
| `--skip-validators` | Skip validators.py generation |
| `--skip-tests` | Skip test_api.py generation |
| `--skip-app` | Skip app.py generation |
| `--skip-docs` | Skip documentation generation |
| `--skip-docker` | Skip Dockerfile generation |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generation failed |

### Examples

```bash
# Basic usage
python auto_sentinel.py --api ./spec.yaml

# With authentication
python auto_sentinel.py \
  --api https://api.example.com/openapi.json \
  --auth-type bearer \
  --auth-token $TOKEN

# Dry run
python auto_sentinel.py --api ./spec.yaml --dry-run

# Verbose mode
python auto_sentinel.py --api ./spec.yaml --verbose

# Skip specific generators
python auto_sentinel.py \
  --api ./spec.yaml \
  --skip-tests \
  --skip-docker
```

---

## Core Modules

### BaseProvider

Abstract base class for API providers with retry and authentication.

```python
from core.base_provider import BaseProvider

class MyProvider(BaseProvider):
    async def fetch(self, url: str, **kwargs) -> dict:
        """Fetch data from URL with retry and auth."""
        return await super().fetch(url, **kwargs)
```

#### Methods

##### `fetch(url: str, **kwargs) -> dict`

Fetch data from URL with automatic retry and authentication.

**Parameters:**
- `url` (str): URL to fetch
- `**kwargs`: Additional arguments for httpx

**Returns:**
- `dict`: Response data

**Raises:**
- `NetworkError`: On network failures
- `AuthenticationError`: On auth failures

##### `introspect_endpoint(url: str) -> dict`

Introspect an API endpoint.

**Parameters:**
- `url` (str): Endpoint URL

**Returns:**
- `dict`: Endpoint metadata

### RetryHandler

Provides retry logic with exponential backoff.

```python
from core.retry_handler import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=2.0)
async def my_function():
    """Function with automatic retry."""
    pass
```

#### Decorator: `@retry_with_backoff`

**Parameters:**
- `max_retries` (int): Maximum retry attempts (default: 3)
- `backoff_factor` (float): Backoff multiplier (default: 2.0)
- `max_backoff` (float): Maximum backoff time (default: 60.0)
- `jitter` (bool): Add random jitter (default: True)

### AuthManager

Manages authentication strategies.

```python
from core.auth_manager import AuthManager, AuthType

# Create auth manager
auth = AuthManager.create(
    auth_type=AuthType.BEARER,
    token="your-token"
)

# Inject auth into headers
headers = auth.inject_auth({})
```

#### Methods

##### `create(auth_type: AuthType, **kwargs) -> AuthHandler`

Factory method to create auth handler.

**Parameters:**
- `auth_type` (AuthType): Type of authentication
- `**kwargs`: Auth-specific parameters

**Returns:**
- `AuthHandler`: Configured auth handler

### Exceptions

```python
from core.exceptions import (
    DataSentinelError,
    ConfigurationError,
    ParsingError,
    GenerationError,
    ValidationFailedError,
    NetworkError,
    AuthenticationError
)
```

#### Exception Hierarchy

```
DataSentinelError (base)
├── ConfigurationError
├── ParsingError
├── GenerationError
├── ValidationFailedError
├── NetworkError
└── AuthenticationError
```

---

## Parsers

### BaseParser

Abstract base class for all parsers.

```python
from parsers.base_parser import BaseParser

class MyParser(BaseParser):
    async def parse(self) -> APISchema:
        """Parse input and return normalized schema."""
        pass
```

### JSONInferenceParser

Infers schema from JSON samples.

```python
from parsers.json_inference_parser import JSONInferenceParser

parser = JSONInferenceParser("./sample.json")
schema = await parser.parse()
```

#### Constructor

```python
JSONInferenceParser(source: str)
```

**Parameters:**
- `source` (str): File path or URL to JSON

#### Methods

##### `parse() -> APISchema`

Parse JSON and infer schema.

**Returns:**
- `APISchema`: Normalized API schema

### OpenAPIParser

Parses OpenAPI/Swagger specifications.

```python
from parsers.openapi_parser import OpenAPIParser

parser = OpenAPIParser("./openapi.yaml")
schema = await parser.parse()
```

#### Constructor

```python
OpenAPIParser(source: str)
```

**Parameters:**
- `source` (str): File path or URL to OpenAPI spec

#### Methods

##### `parse() -> APISchema`

Parse OpenAPI specification.

**Returns:**
- `APISchema`: Normalized API schema

**Features:**
- Resolves $ref references
- Supports OpenAPI 3.x and Swagger 2.0
- Extracts validation constraints

### GraphQLParser

Parses GraphQL schemas via introspection.

```python
from parsers.graphql_parser import GraphQLParser

parser = GraphQLParser("https://api.example.com/graphql")
schema = await parser.parse()
```

#### Constructor

```python
GraphQLParser(endpoint: str, auth_token: Optional[str] = None)
```

**Parameters:**
- `endpoint` (str): GraphQL endpoint URL
- `auth_token` (Optional[str]): Authentication token

#### Methods

##### `parse() -> APISchema`

Execute introspection and parse schema.

**Returns:**
- `APISchema`: Normalized API schema

---

## Generators

### BaseGenerator

Abstract base class for all generators.

```python
from generators.base_generator import BaseGenerator

class MyGenerator(BaseGenerator):
    def generate(self) -> Path:
        """Generate artifact."""
        pass
```

### ModelsGenerator

Generates Pydantic v2 models.

```python
from generators.models_generator import ModelsGenerator

generator = ModelsGenerator(api_schema, output_dir)
models_file = generator.generate()
```

#### Constructor

```python
ModelsGenerator(api_schema: APISchema, output_dir: Path)
```

#### Methods

##### `generate() -> Path`

Generate models.py file.

**Returns:**
- `Path`: Path to generated file

### ValidatorsGenerator

Generates validation logic.

```python
from generators.validators_generator import ValidatorsGenerator

generator = ValidatorsGenerator(api_schema, output_dir)
validators_file = generator.generate()
```

### TestsGenerator

Generates pytest test suite.

```python
from generators.tests_generator import TestsGenerator

generator = TestsGenerator(api_schema, output_dir)
tests_file = generator.generate()
```

### AppGenerator

Generates FastAPI application.

```python
from generators.app_generator import AppGenerator

generator = AppGenerator(api_schema, output_dir)
app_file = generator.generate()
```

### DocsGenerator

Generates documentation.

```python
from generators.docs_generator import DocsGenerator

generator = DocsGenerator(api_schema, output_dir)
docs_file = generator.generate()
```

### DockerfileGenerator

Generates Docker configuration.

```python
from generators.dockerfile_generator import DockerfileGenerator

generator = DockerfileGenerator(api_schema, output_dir)
dockerfile = generator.generate()
```

---

## Generated API

### Models

Generated Pydantic models with validation.

```python
from models import User

# Create instance
user = User(
    id=1,
    name="John Doe",
    email="john@example.com"
)

# Validate data
try:
    user = User(**data)
except ValidationError as e:
    print(e.errors())

# Serialize
json_str = user.model_dump_json()
dict_data = user.model_dump()

# Deserialize
user = User.model_validate_json(json_str)
user = User.model_validate(dict_data)
```

### Validators

Generated validators with retry and drift detection.

```python
from validators import UserValidator

# Initialize
validator = UserValidator(
    base_url="https://api.example.com",
    auth_token="your-token"
)

# Validate single record
result = await validator.validate_user(data)

# Batch validation
results = await validator.validate_batch([data1, data2])

# Drift detection
drift_result = await validator.detect_drift("/users/1")
```

#### ValidationResult

```python
class ValidationResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    timestamp: datetime
    drift_detected: bool
```

### FastAPI Endpoints

Generated FastAPI application endpoints.

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "validator"
}
```

#### Validate Single Record

```http
POST /validate
Content-Type: application/json

{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {...},
  "errors": [],
  "warnings": [],
  "timestamp": "2024-01-15T10:30:00Z",
  "drift_detected": false
}
```

#### Batch Validation

```http
POST /validate/batch
Content-Type: application/json

[
  {"id": 1, "name": "John"},
  {"id": 2, "name": "Jane"}
]
```

**Response:**
```json
[
  {
    "success": true,
    "data": {...},
    "errors": []
  },
  {
    "success": true,
    "data": {...},
    "errors": []
  }
]
```

#### Drift Detection

```http
GET /drift/users/1
```

**Response:**
```json
{
  "success": true,
  "drift_detected": false,
  "warnings": [],
  "errors": []
}
```

---

## Configuration

### Settings

Configuration via environment variables or `.env` file.

```python
from config.settings import Settings

settings = Settings()
```

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (`json` or `text`) | `json` |
| `DEFAULT_TIMEOUT` | HTTP timeout (seconds) | `30` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `RETRY_BACKOFF_FACTOR` | Backoff multiplier | `2.0` |
| `OUTPUT_DIR` | Default output directory | `./output` |
| `TEMPLATE_DIR` | Templates directory | `./templates` |

### Logging

Configure logging with Loguru.

```python
from config.logging_config import setup_logging

# Setup logging
setup_logging(
    level="DEBUG",
    log_file="app.log"
)

# Use logger
from loguru import logger

logger.info("Message")
logger.error("Error message")
logger.debug("Debug message")
```

---

## Data Structures

### APISchema

Main schema representing the API.

```python
class APISchema(BaseModel):
    title: str
    version: str
    description: Optional[str]
    base_url: str
    models: Dict[str, ModelSchema]
    endpoints: List[Endpoint]
```

### ModelSchema

Represents a data model.

```python
class ModelSchema(BaseModel):
    name: str
    description: Optional[str]
    fields: List[FieldSchema]
```

### FieldSchema

Represents a model field.

```python
class FieldSchema(BaseModel):
    name: str
    type: FieldType
    required: bool
    description: Optional[str]
    validators: List[Validator]
    default: Optional[Any]
```

### Endpoint

Represents an API endpoint.

```python
class Endpoint(BaseModel):
    path: str
    method: str
    operation_id: str
    description: Optional[str]
    parameters: List[Parameter]
    request_body: Optional[ModelSchema]
    response: Optional[ModelSchema]
```

---

## Type System

### FieldType

Supported field types:

| Type | Python Type | Pydantic Type |
|------|-------------|---------------|
| `string` | `str` | `str` |
| `integer` | `int` | `int` |
| `number` | `float` | `float` |
| `boolean` | `bool` | `bool` |
| `array` | `List` | `List[T]` |
| `object` | `Dict` | Nested model |
| `email` | `str` | `EmailStr` |
| `url` | `str` | `HttpUrl` |
| `uuid` | `str` | `UUID` |
| `datetime` | `datetime` | `datetime` |
| `date` | `date` | `date` |

### Validators

Supported validation types:

| Validator | Description | Example |
|-----------|-------------|---------|
| `min_length` | Minimum string length | `min_length=1` |
| `max_length` | Maximum string length | `max_length=100` |
| `minimum` | Minimum numeric value | `ge=0` |
| `maximum` | Maximum numeric value | `le=150` |
| `pattern` | Regex pattern | `pattern=r'^[A-Z]'` |
| `email` | Email format | `EmailStr` |
| `url` | URL format | `HttpUrl` |
| `uuid` | UUID format | `UUID` |

---

## Error Handling

### Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## Best Practices

### 1. Use Type Hints

Always use type hints for better IDE support:

```python
from typing import List, Optional, Dict, Any

async def validate_data(data: Dict[str, Any]) -> ValidationResult:
    pass
```

### 2. Handle Exceptions

Always handle exceptions gracefully:

```python
try:
    result = await validator.validate_user(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
except NetworkError as e:
    logger.error(f"Network error: {e}")
```

### 3. Use Async/Await

Leverage async for I/O operations:

```python
async def process_batch(items: List[Dict]) -> List[ValidationResult]:
    tasks = [validate_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

### 4. Configure Logging

Use structured logging:

```python
logger.info("Validation started", extra={
    "user_id": user_id,
    "timestamp": datetime.now()
})
```

---

## Examples

### Complete Example

```python
import asyncio
from parsers.openapi_parser import OpenAPIParser
from generators.models_generator import ModelsGenerator
from generators.app_generator import AppGenerator

async def main():
    # Parse OpenAPI spec
    parser = OpenAPIParser("./openapi.yaml")
    schema = await parser.parse()
    
    # Generate models
    models_gen = ModelsGenerator(schema, Path("./output"))
    models_file = models_gen.generate()
    
    # Generate FastAPI app
    app_gen = AppGenerator(schema, Path("./output"))
    app_file = app_gen.generate()
    
    print(f"Generated: {models_file}, {app_file}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

- 📖 [Getting Started](getting_started.md) - Quick start guide
- 🎯 [Input Formats](input_formats.md) - Supported input formats
- 🚀 [Deployment](deployment.md) - Deploy your service

---

## Need Help?

- 📝 [GitHub Issues](https://github.com/yourusername/datasentinel/issues)
- 💬 [Discussions](https://github.com/yourusername/datasentinel/discussions)
- 📧 Email: support@datasentinel.dev
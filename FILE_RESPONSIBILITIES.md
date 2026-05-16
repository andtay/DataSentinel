# File Responsibilities - DataSentinel

This document provides detailed responsibilities, key classes, and functions for each file in the DataSentinel project.

---

## Entry Point

### [`auto_sentinel.py`](auto_sentinel.py)

**Purpose:** CLI orchestrator that coordinates the entire generation pipeline.

**Key Responsibilities:**
- Parse CLI arguments (--input-type, --source, --output, --auth)
- Detect input type if not explicitly provided
- Route to appropriate parser based on input type
- Coordinate generator execution
- Validate generated output
- Provide user feedback and error handling

**Key Classes & Functions:**
```python
class InputDetector:
    """Explicit input type detection based on industry standards."""
    
    @staticmethod
    def detect_input_type(source: str) -> InputType:
        """Detect whether source is OpenAPI, GraphQL, or JSON."""

async def orchestrate_generation(config: GenerationConfig) -> None:
    """Main orchestration function coordinating parsers and generators."""

def validate_output(output_dir: Path) -> bool:
    """Ensure all required files were generated successfully."""

def main() -> None:
    """CLI entry point with argument parsing."""
```

**CLI Interface:**
```bash
python auto_sentinel.py \
  --input-type {openapi|graphql|json} \
  --source <file_or_url> \
  --output <directory> \
  --project-name <name> \
  [--auth-type {api_key|bearer|oauth2}] \
  [--auth-value <token>] \
  [--verbose]
```

---

## Configuration

### [`config/settings.py`](config/settings.py)

**Purpose:** Centralized configuration using Pydantic Settings.

**Key Responsibilities:**
- Load environment variables from .env
- Define default values for all settings
- Validate configuration on startup
- Provide type-safe access to settings

**Key Classes:**
```python
class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    default_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # Generation Configuration
    output_dir: Path = Path("./output")
    template_dir: Path = Path("./templates")
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
```

### [`config/logging_config.py`](config/logging_config.py)

**Purpose:** Configure Loguru for structured logging.

**Key Responsibilities:**
- Set up log handlers (console, file, JSON)
- Configure log rotation and retention
- Define log formats for different environments
- Integrate with FastAPI logging

**Key Functions:**
```python
def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure Loguru with appropriate handlers and formats."""

def get_logger(name: str) -> Logger:
    """Get a logger instance for a specific module."""
```

---

## Core Infrastructure

### [`core/base_provider.py`](core/base_provider.py)

**Purpose:** Abstract base class for all API interactions.

**Key Responsibilities:**
- Define common interface for HTTP operations
- Implement retry logic integration
- Handle authentication injection
- Provide error handling patterns
- Support both sync and async operations

**Key Classes:**
```python
class BaseProvider(ABC):
    """Abstract base for API providers with retry and auth support."""
    
    def __init__(self, base_url: str, auth_manager: Optional[AuthManager] = None):
        self.base_url = base_url
        self.auth_manager = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @abstractmethod
    async def fetch(self, url: str, method: str = "GET", **kwargs) -> dict:
        """Core HTTP method with retry and auth."""
    
    async def introspect_endpoint(self, url: str) -> EndpointSchema:
        """Auto-discover endpoint schema via OPTIONS or sample request."""
    
    def _inject_auth(self, request: httpx.Request) -> httpx.Request:
        """Inject authentication headers into request."""
    
    async def close(self) -> None:
        """Close HTTP client connection."""
```

### [`core/retry_handler.py`](core/retry_handler.py)

**Purpose:** Exponential backoff with jitter for resilient API calls.

**Key Responsibilities:**
- Implement retry decorator for async functions
- Calculate exponential backoff with jitter
- Handle transient errors (network, rate limits, 5xx)
- Log retry attempts with context
- Support configurable retry policies

**Key Functions:**
```python
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (httpx.HTTPError,)
):
    """
    Decorator for async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to prevent thundering herd
        retry_on: Tuple of exception types to retry on
    """

def calculate_backoff(
    attempt: int,
    base_delay: float,
    exponential_base: float,
    max_delay: float,
    jitter: bool
) -> float:
    """Calculate delay with exponential backoff and optional jitter."""
```

### [`core/auth_manager.py`](core/auth_manager.py)

**Purpose:** Unified authentication handling for multiple strategies.

**Key Responsibilities:**
- Factory pattern for auth strategies
- Support API Key, Bearer Token, OAuth2
- Handle token refresh for OAuth2
- Inject auth headers into requests
- Validate auth credentials

**Key Classes:**
```python
class AuthType(str, Enum):
    """Supported authentication types."""
    API_KEY = "api_key"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    NONE = "none"

class AuthHandler(ABC):
    """Abstract base for authentication handlers."""
    
    @abstractmethod
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """Inject authentication into request."""

class APIKeyAuth(AuthHandler):
    """API Key authentication (header or query parameter)."""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name

class BearerAuth(AuthHandler):
    """Bearer token authentication."""
    
    def __init__(self, token: str):
        self.token = token

class OAuth2Auth(AuthHandler):
    """OAuth2 authentication with token refresh."""
    
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
    
    async def refresh_token(self) -> None:
        """Refresh OAuth2 access token when expired."""

class AuthManager:
    """Factory for creating auth handlers."""
    
    @staticmethod
    def get_auth_handler(auth_type: AuthType, **kwargs) -> AuthHandler:
        """Create appropriate auth handler based on type."""
```

### [`core/exceptions.py`](core/exceptions.py)

**Purpose:** Custom exception hierarchy for DataSentinel.

**Key Responsibilities:**
- Define domain-specific exceptions
- Provide clear error messages
- Support error context and metadata
- Enable structured error handling

**Key Classes:**
```python
class DataSentinelError(Exception):
    """Base exception for DataSentinel."""

class ParserError(DataSentinelError):
    """Raised when parsing API specification fails."""

class GeneratorError(DataSentinelError):
    """Raised when code generation fails."""

class ValidationError(DataSentinelError):
    """Raised when validation fails."""

class AuthenticationError(DataSentinelError):
    """Raised when authentication fails."""

class SchemaDriftError(DataSentinelError):
    """Raised when schema drift is detected."""

class ConfigurationError(DataSentinelError):
    """Raised when configuration is invalid."""
```

### [`core/utils.py`](core/utils.py)

**Purpose:** Shared utility functions.

**Key Responsibilities:**
- File I/O helpers
- String manipulation utilities
- Type conversion helpers
- Path resolution utilities
- Hash calculation for drift detection

**Key Functions:**
```python
def load_json_file(path: Path) -> dict:
    """Load and parse JSON file."""

def load_yaml_file(path: Path) -> dict:
    """Load and parse YAML file."""

def write_json_file(path: Path, data: dict) -> None:
    """Write data to JSON file."""

def calculate_schema_hash(schema: dict) -> str:
    """Calculate SHA256 hash of schema for drift detection."""

def normalize_field_name(name: str) -> str:
    """Convert field name to snake_case."""

def is_url(source: str) -> bool:
    """Check if source is a URL."""
```

---

## Parsers

### [`parsers/base_parser.py`](parsers/base_parser.py)

**Purpose:** Abstract interface for all parsers.

**Key Responsibilities:**
- Define common parser interface
- Enforce contract for parse() method
- Provide helper methods for schema extraction
- Support async parsing operations

**Key Classes:**
```python
class BaseParser(ABC):
    """Abstract base for all API specification parsers."""
    
    def __init__(self, source: Union[Path, str]):
        self.source = source
    
    @abstractmethod
    async def parse(self) -> APISchema:
        """Parse input and return normalized APISchema."""
    
    @abstractmethod
    def extract_endpoints(self) -> List[Endpoint]:
        """Extract all endpoints from specification."""
    
    @abstractmethod
    def extract_models(self) -> Dict[str, ModelSchema]:
        """Extract all data models from specification."""
    
    def validate_source(self) -> bool:
        """Validate that source is accessible and valid."""
```

### [`parsers/openapi_parser.py`](parsers/openapi_parser.py)

**Purpose:** Deterministic parser for OpenAPI 3.x and Swagger 2.x specifications.

**Key Responsibilities:**
- Parse OpenAPI/Swagger files (YAML/JSON)
- Resolve $ref references using prance
- Extract endpoints from paths
- Extract models from components/schemas
- Map OpenAPI types to Pydantic types
- Extract validation constraints
- Handle oneOf, anyOf, allOf schemas
- Support both local files and remote URLs

**Key Classes & Functions:**
```python
class OpenAPIParser(BaseParser):
    """Deterministic parser for OpenAPI/Swagger specifications."""
    
    async def parse(self) -> APISchema:
        """Parse OpenAPI specification with full $ref resolution."""
    
    def _resolve_references(self, spec: dict) -> dict:
        """Resolve all $ref using prance library."""
    
    def _extract_schema(self, spec: dict) -> APISchema:
        """Extract APISchema from resolved OpenAPI spec."""
    
    def _parse_paths(self, paths: dict) -> List[Endpoint]:
        """Convert OpenAPI paths to Endpoint objects."""
    
    def _parse_components(self, components: dict) -> Dict[str, ModelSchema]:
        """Convert OpenAPI components/schemas to ModelSchema objects."""
    
    def _map_openapi_type(self, openapi_type: str, format: Optional[str] = None) -> FieldType:
        """Map OpenAPI types to FieldType enum."""
    
    def _extract_validators(self, schema: dict) -> List[ValidatorConfig]:
        """Extract validation rules from OpenAPI schema."""
    
    def _handle_complex_schema(self, schema: dict) -> ModelSchema:
        """Handle oneOf, anyOf, allOf schemas."""
```

### [`parsers/graphql_parser.py`](parsers/graphql_parser.py)

**Purpose:** Parser using GraphQL introspection to retrieve schema.

**Key Responsibilities:**
- Execute introspection query against GraphQL endpoint
- Parse introspection result
- Convert GraphQL types to Pydantic models
- Map queries to GET endpoints
- Map mutations to POST endpoints
- Handle nested types and lists
- Support custom scalars
- Extract field descriptions

**Key Classes & Functions:**
```python
class GraphQLParser(BaseParser):
    """Parser using GraphQL introspection."""
    
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        types {
          kind
          name
          description
          fields {
            name
            description
            type { kind name ofType { kind name } }
            args { name type { kind name } }
          }
        }
      }
    }
    """
    
    async def parse(self) -> APISchema:
        """Execute introspection and parse result."""
    
    async def _execute_introspection(self) -> dict:
        """Execute introspection query via POST."""
    
    def _build_schema_from_introspection(self, result: dict) -> APISchema:
        """Convert introspection result to APISchema."""
    
    def _parse_graphql_types(self, types: List[dict]) -> Dict[str, ModelSchema]:
        """Convert GraphQL types to ModelSchema."""
    
    def _parse_graphql_operations(self, schema_data: dict) -> List[Endpoint]:
        """Convert queries/mutations to Endpoint objects."""
    
    def _map_graphql_type(self, graphql_type: dict) -> FieldType:
        """Map GraphQL types to FieldType enum."""
    
    def _handle_custom_scalar(self, scalar_name: str) -> FieldType:
        """Handle custom GraphQL scalars."""
```

### [`parsers/json_inference_parser.py`](parsers/json_inference_parser.py)

**Purpose:** Type inference engine for raw JSON data.

**Key Responsibilities:**
- Infer schema from JSON structure
- Detect field types from values
- Identify patterns (email, URL, UUID, dates)
- Handle nested objects recursively
- Infer array item types
- Detect optional fields
- Generate field descriptions
- Support both local files and live endpoints

**Key Classes & Functions:**
```python
class JSONInferenceParser(BaseParser):
    """Type inference engine for raw JSON data."""
    
    async def parse(self) -> APISchema:
        """Infer schema from JSON sample or live endpoint."""
    
    def _infer_model_from_json(self, data: Any, model_name: str = "InferredModel") -> ModelSchema:
        """Recursively infer Pydantic model from JSON structure."""
    
    def _infer_field_type(self, value: Any) -> FieldType:
        """Infer field type from value."""
    
    def _detect_string_pattern(self, value: str) -> Optional[str]:
        """Detect common patterns in string values (email, URL, UUID, dates)."""
    
    def _analyze_multiple_samples(self, samples: List[dict]) -> ModelSchema:
        """Analyze multiple samples to detect optional fields and type variations."""
    
    def _infer_array_type(self, array: List[Any]) -> FieldType:
        """Infer item type from array elements."""
    
    def _generate_field_description(self, field_name: str, value: Any) -> str:
        """Generate descriptive text for inferred field."""
```

### [`parsers/schema_normalizer.py`](parsers/schema_normalizer.py)

**Purpose:** Normalize all parser outputs to consistent APISchema format.

**Key Responsibilities:**
- Validate parsed schemas
- Normalize field names (snake_case)
- Resolve type conflicts
- Merge duplicate models
- Validate schema completeness

**Key Functions:**
```python
def normalize_schema(api_schema: APISchema) -> APISchema:
    """Normalize and validate APISchema."""

def normalize_field_names(model: ModelSchema) -> ModelSchema:
    """Convert all field names to snake_case."""

def resolve_type_conflicts(models: Dict[str, ModelSchema]) -> Dict[str, ModelSchema]:
    """Resolve conflicting type definitions."""

def merge_duplicate_models(models: Dict[str, ModelSchema]) -> Dict[str, ModelSchema]:
    """Merge models with identical structures."""

def validate_schema_completeness(api_schema: APISchema) -> bool:
    """Ensure schema has all required information."""
```

---

## Generators

### [`generators/base_generator.py`](generators/base_generator.py)

**Purpose:** Abstract interface for all generators.

**Key Responsibilities:**
- Define common generator interface
- Provide template rendering utilities
- Handle file writing operations
- Support dry-run mode
- Format generated code

**Key Classes:**
```python
class BaseGenerator(ABC):
    """Abstract base for all code generators."""
    
    def __init__(self, template_dir: Path, output_dir: Path):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.jinja_env = self._setup_jinja_environment()
    
    @abstractmethod
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate artifact and return output path."""
    
    def _setup_jinja_environment(self) -> jinja2.Environment:
        """Configure Jinja2 environment with custom filters."""
    
    def _render_template(self, template_name: str, context: dict) -> str:
        """Render Jinja2 template with context."""
    
    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file with proper formatting."""
    
    def _format_code(self, code: str, language: str = "python") -> str:
        """Format code using black/prettier."""
```

### [`generators/model_generator.py`](generators/model_generator.py)

**Purpose:** Generate Pydantic v2 models with validators.

**Key Responsibilities:**
- Generate Pydantic BaseModel classes
- Add field type annotations
- Generate Field() definitions with constraints
- Create @field_validator decorators
- Handle nested models
- Support custom validators
- Add docstrings
- Format code with black

**Key Classes & Functions:**
```python
class ModelGenerator(BaseGenerator):
    """Generate Pydantic v2 models."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate models.py file."""
    
    def _collect_imports(self, models: Dict[str, ModelSchema]) -> Set[str]:
        """Collect all required imports."""
    
    def _generate_field_definition(self, field: FieldSchema) -> str:
        """Generate Field() definition with constraints."""
    
    def _generate_validators(self, model: ModelSchema) -> List[str]:
        """Generate @field_validator decorators."""
    
    def _handle_nested_model(self, field: FieldSchema) -> str:
        """Generate code for nested model reference."""
```

### [`generators/validator_generator.py`](generators/validator_generator.py)

**Purpose:** Generate validation logic with retry & drift detection.

**Key Responsibilities:**
- Generate validator classes for each endpoint
- Integrate retry logic
- Add schema drift detection
- Generate validation result models
- Handle error cases
- Log validation attempts
- Support batch validation

**Key Classes & Functions:**
```python
class ValidatorGenerator(BaseGenerator):
    """Generate validation logic with retry and drift detection."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate validators.py file."""
    
    def _generate_endpoint_validator(self, endpoint: Endpoint) -> str:
        """Generate validator method for endpoint."""
    
    def _add_schema_drift_detection(self, validator: str) -> str:
        """Add drift detection logic to validator."""
    
    def _generate_validation_result_model(self) -> str:
        """Generate ValidationResult Pydantic model."""
    
    def _generate_batch_validator(self, endpoints: List[Endpoint]) -> str:
        """Generate batch validation method."""
```

### [`generators/test_generator.py`](generators/test_generator.py)

**Purpose:** Generate pytest test suite with polyfactory mocks.

**Key Responsibilities:**
- Generate test functions for each endpoint
- Create polyfactory factories for models
- Generate success test cases
- Generate error test cases
- Add edge case tests
- Mock external API calls
- Support async tests

**Key Classes & Functions:**
```python
class TestGenerator(BaseGenerator):
    """Generate pytest test suite."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate test_api.py file."""
    
    def _generate_factories(self, models: Dict[str, ModelSchema]) -> Dict[str, str]:
        """Generate polyfactory factories for all models."""
    
    def _generate_endpoint_tests(self, endpoint: Endpoint) -> List[str]:
        """Generate test cases for endpoint (success, error, edge cases)."""
    
    def _generate_mock_setup(self, endpoint: Endpoint) -> str:
        """Generate mock setup for external API calls."""
    
    def _generate_fixtures(self, models: Dict[str, ModelSchema]) -> str:
        """Generate pytest fixtures."""
```

### [`generators/app_generator.py`](generators/app_generator.py)

**Purpose:** Generate FastAPI application exposing validators as REST service.

**Key Responsibilities:**
- Generate FastAPI app instance
- Create validation endpoints
- Add health check endpoint
- Configure CORS
- Add API documentation
- Integrate with validators
- Add error handlers

**Key Classes & Functions:**
```python
class AppGenerator(BaseGenerator):
    """Generate FastAPI application."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate app.py file."""
    
    def _generate_validation_endpoint(self, endpoint: Endpoint) -> str:
        """Generate FastAPI endpoint for validation."""
    
    def _generate_health_check(self) -> str:
        """Generate health check endpoint."""
    
    def _generate_error_handlers(self) -> str:
        """Generate custom error handlers."""
    
    def _generate_cors_config(self) -> str:
        """Generate CORS middleware configuration."""
```

### [`generators/doc_generator.py`](generators/doc_generator.py)

**Purpose:** Generate markdown data dictionary.

**Key Responsibilities:**
- Generate data dictionary with all fields
- Document field types and constraints
- Add field descriptions
- Create endpoint documentation
- Generate usage examples
- Add validation rules documentation

**Key Classes & Functions:**
```python
class DocGenerator(BaseGenerator):
    """Generate markdown documentation."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate data_dict.md file."""
    
    def _generate_model_documentation(self, model: ModelSchema) -> str:
        """Generate documentation for a model."""
    
    def _generate_endpoint_documentation(self, endpoint: Endpoint) -> str:
        """Generate documentation for an endpoint."""
    
    def _generate_usage_examples(self, api_schema: APISchema) -> str:
        """Generate usage examples."""
```

### [`generators/docker_generator.py`](generators/docker_generator.py)

**Purpose:** Generate production-ready Dockerfile.

**Key Responsibilities:**
- Generate multi-stage Dockerfile
- Optimize layer caching
- Add health check
- Configure non-root user
- Set up proper entrypoint
- Generate .dockerignore

**Key Classes & Functions:**
```python
class DockerGenerator(BaseGenerator):
    """Generate Dockerfile and .dockerignore."""
    
    async def generate(self, api_schema: APISchema) -> Path:
        """Generate Dockerfile."""
    
    def _generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
    
    def _generate_multistage_dockerfile(self, project_name: str) -> str:
        """Generate optimized multi-stage Dockerfile."""
```

---

## Data Structures

See [DATA_STRUCTURES.md](DATA_STRUCTURES.md) for complete schema definitions.

---

## Summary

This document provides explicit responsibilities for all 40+ files in the DataSentinel project. Each file has:
- Clear purpose statement
- List of key responsibilities
- Signature of key classes and functions
- Usage examples where applicable

Use this as a reference when implementing each component to ensure consistency and completeness.
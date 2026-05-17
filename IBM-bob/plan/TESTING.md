# Testing Strategy - DataSentinel

This document outlines the comprehensive testing approach for DataSentinel, including unit tests, integration tests, and testing of generated code.

---

## Testing Philosophy

**Core Principles:**
1. **Test-Driven Development (TDD):** Write tests before implementation where possible
2. **High Coverage:** Target 90%+ code coverage across all modules
3. **Fast Feedback:** Unit tests should run in < 5 seconds
4. **Realistic Scenarios:** Integration tests use real-world API examples
5. **Generated Code Quality:** Ensure generated code is not just syntactically correct but functionally correct

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared pytest fixtures
│
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_core.py              # Core infrastructure tests
│   ├── test_parsers.py           # Parser tests
│   ├── test_generators.py        # Generator tests
│   └── test_schemas.py           # Schema validation tests
│
├── integration/                   # Integration tests (slower, end-to-end)
│   ├── __init__.py
│   ├── test_openapi_flow.py     # OpenAPI → generated code
│   ├── test_graphql_flow.py     # GraphQL → generated code
│   └── test_json_flow.py        # JSON → generated code
│
└── fixtures/                      # Test data
    ├── sample_openapi.yaml
    ├── sample_response.json
    └── mock_graphql_schema.json
```

---

## Unit Tests

### Coverage Goals

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `core/` | 95% | Critical |
| `parsers/` | 90% | Critical |
| `generators/` | 90% | Critical |
| `schemas/` | 100% | Critical |
| `config/` | 85% | High |
| `auto_sentinel.py` | 80% | High |

### Test Categories

#### 1. Core Infrastructure Tests

**File:** [`tests/unit/test_core.py`](tests/unit/test_core.py)

**Test Cases:**

```python
import pytest
import httpx
from core.retry_handler import retry_with_backoff, calculate_backoff
from core.auth_manager import AuthManager, APIKeyAuth, BearerAuth, OAuth2Auth
from core.base_provider import BaseProvider
from core.exceptions import DataSentinelError, AuthenticationError


class TestRetryHandler:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful retry after transient failures."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.HTTPError("Transient error")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """Test that max retries are respected."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPError("Permanent error")
        
        with pytest.raises(httpx.HTTPError):
            await always_fails()
        
        assert call_count == 4  # Initial + 3 retries
    
    def test_calculate_backoff_exponential(self):
        """Test exponential backoff calculation."""
        delay1 = calculate_backoff(1, base_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
        delay2 = calculate_backoff(2, base_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
        delay3 = calculate_backoff(3, base_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
        
        assert delay1 == 2.0  # 1 * 2^1
        assert delay2 == 4.0  # 1 * 2^2
        assert delay3 == 8.0  # 1 * 2^3
    
    def test_calculate_backoff_max_delay(self):
        """Test that max delay is respected."""
        delay = calculate_backoff(10, base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False)
        assert delay == 10.0


class TestAuthManager:
    """Test authentication management."""
    
    def test_api_key_auth_injection(self):
        """Test API key authentication."""
        auth = APIKeyAuth(api_key="test_key", header_name="X-API-Key")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        authenticated_request = auth.inject_auth(request)
        
        assert authenticated_request.headers["X-API-Key"] == "test_key"
    
    def test_bearer_auth_injection(self):
        """Test Bearer token authentication."""
        auth = BearerAuth(token="test_token")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        authenticated_request = auth.inject_auth(request)
        
        assert authenticated_request.headers["Authorization"] == "Bearer test_token"
    
    @pytest.mark.asyncio
    async def test_oauth2_token_refresh(self):
        """Test OAuth2 token refresh."""
        # Mock OAuth2 token endpoint
        # Test token refresh logic
        pass
    
    def test_auth_manager_factory(self):
        """Test AuthManager factory pattern."""
        api_key_auth = AuthManager.get_auth_handler("api_key", api_key="test")
        assert isinstance(api_key_auth, APIKeyAuth)
        
        bearer_auth = AuthManager.get_auth_handler("bearer", token="test")
        assert isinstance(bearer_auth, BearerAuth)


class TestBaseProvider:
    """Test base provider functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_success(self, httpx_mock):
        """Test successful HTTP fetch."""
        httpx_mock.add_response(json={"data": "test"})
        
        provider = BaseProvider(base_url="https://api.example.com")
        result = await provider.fetch("/endpoint")
        
        assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry(self, httpx_mock):
        """Test fetch with retry on failure."""
        # First call fails, second succeeds
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(json={"data": "test"})
        
        provider = BaseProvider(base_url="https://api.example.com")
        result = await provider.fetch("/endpoint")
        
        assert result == {"data": "test"}
```

#### 2. Parser Tests

**File:** [`tests/unit/test_parsers.py`](tests/unit/test_parsers.py)

**Test Cases:**

```python
import pytest
from pathlib import Path
from parsers.openapi_parser import OpenAPIParser
from parsers.graphql_parser import GraphQLParser
from parsers.json_inference_parser import JSONInferenceParser
from schemas.api_schema import APISchema, FieldType


class TestOpenAPIParser:
    """Test OpenAPI/Swagger parser."""
    
    @pytest.mark.asyncio
    async def test_parse_openapi_3_file(self, sample_openapi_file):
        """Test parsing OpenAPI 3.x file."""
        parser = OpenAPIParser(sample_openapi_file)
        api_schema = await parser.parse()
        
        assert isinstance(api_schema, APISchema)
        assert api_schema.title == "Pet Store API"
        assert len(api_schema.endpoints) > 0
        assert len(api_schema.models) > 0
    
    @pytest.mark.asyncio
    async def test_parse_swagger_2_file(self, sample_swagger_file):
        """Test parsing Swagger 2.x file."""
        parser = OpenAPIParser(sample_swagger_file)
        api_schema = await parser.parse()
        
        assert isinstance(api_schema, APISchema)
        assert api_schema.version is not None
    
    def test_map_openapi_types(self):
        """Test OpenAPI type mapping."""
        parser = OpenAPIParser("dummy")
        
        assert parser._map_openapi_type("string", None) == FieldType.STRING
        assert parser._map_openapi_type("string", "date") == FieldType.DATE
        assert parser._map_openapi_type("string", "email") == FieldType.EMAIL
        assert parser._map_openapi_type("integer", None) == FieldType.INTEGER
        assert parser._map_openapi_type("boolean", None) == FieldType.BOOLEAN
    
    def test_extract_validators(self):
        """Test extraction of validation rules."""
        parser = OpenAPIParser("dummy")
        schema = {
            "type": "string",
            "minLength": 5,
            "maxLength": 100,
            "pattern": "^[a-z]+$"
        }
        
        validators = parser._extract_validators(schema)
        
        assert len(validators) > 0
        # Verify min_length, max_length, pattern are extracted


class TestGraphQLParser:
    """Test GraphQL introspection parser."""
    
    @pytest.mark.asyncio
    async def test_execute_introspection(self, httpx_mock):
        """Test GraphQL introspection query execution."""
        httpx_mock.add_response(json={
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "types": []
                }
            }
        })
        
        parser = GraphQLParser("https://api.example.com/graphql")
        result = await parser._execute_introspection()
        
        assert "data" in result
        assert "__schema" in result["data"]
    
    def test_map_graphql_types(self):
        """Test GraphQL type mapping."""
        parser = GraphQLParser("dummy")
        
        assert parser._map_graphql_type({"kind": "SCALAR", "name": "String"}) == FieldType.STRING
        assert parser._map_graphql_type({"kind": "SCALAR", "name": "Int"}) == FieldType.INTEGER
        assert parser._map_graphql_type({"kind": "SCALAR", "name": "Boolean"}) == FieldType.BOOLEAN


class TestJSONInferenceParser:
    """Test JSON type inference parser."""
    
    @pytest.mark.asyncio
    async def test_infer_from_simple_json(self):
        """Test inference from simple JSON structure."""
        json_data = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "active": True
        }
        
        parser = JSONInferenceParser("dummy")
        model = parser._infer_model_from_json(json_data)
        
        assert model.name == "InferredModel"
        assert len(model.fields) == 4
        
        # Check field types
        id_field = next(f for f in model.fields if f.name == "id")
        assert id_field.type == FieldType.INTEGER
        
        email_field = next(f for f in model.fields if f.name == "email")
        assert email_field.type == FieldType.EMAIL
    
    def test_detect_string_patterns(self):
        """Test pattern detection in strings."""
        parser = JSONInferenceParser("dummy")
        
        assert parser._detect_string_pattern("user@example.com") is not None
        assert parser._detect_string_pattern("https://example.com") is not None
        assert parser._detect_string_pattern("550e8400-e29b-41d4-a716-446655440000") is not None
        assert parser._detect_string_pattern("2024-01-15T10:30:00Z") is not None
    
    @pytest.mark.asyncio
    async def test_infer_nested_objects(self):
        """Test inference of nested object structures."""
        json_data = {
            "user": {
                "id": 1,
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        
        parser = JSONInferenceParser("dummy")
        model = parser._infer_model_from_json(json_data)
        
        # Verify nested models are created
        assert any(f.type == FieldType.OBJECT for f in model.fields)
```

#### 3. Generator Tests

**File:** [`tests/unit/test_generators.py`](tests/unit/test_generators.py)

**Test Cases:**

```python
import pytest
from pathlib import Path
from generators.model_generator import ModelGenerator
from generators.validator_generator import ValidatorGenerator
from generators.test_generator import TestGenerator
from schemas.api_schema import APISchema, ModelSchema, FieldSchema, FieldType


class TestModelGenerator:
    """Test Pydantic model generation."""
    
    @pytest.mark.asyncio
    async def test_generate_simple_model(self, tmp_path, sample_api_schema):
        """Test generation of simple Pydantic model."""
        generator = ModelGenerator(
            template_dir=Path("templates"),
            output_dir=tmp_path
        )
        
        output_path = await generator.generate(sample_api_schema)
        
        assert output_path.exists()
        assert output_path.name == "models.py"
        
        # Verify generated code is valid Python
        with open(output_path) as f:
            code = f.read()
            assert "from pydantic import BaseModel" in code
            assert "class" in code
    
    def test_generate_field_definition(self):
        """Test field definition generation."""
        generator = ModelGenerator(Path("templates"), Path("output"))
        
        field = FieldSchema(
            name="email",
            type=FieldType.EMAIL,
            required=True,
            description="User email",
            pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"
        )
        
        field_def = generator._generate_field_definition(field)
        
        assert "email: str" in field_def or "email: EmailStr" in field_def
        assert "Field(" in field_def
    
    @pytest.mark.asyncio
    async def test_generated_model_is_importable(self, tmp_path, sample_api_schema):
        """Test that generated model can be imported."""
        generator = ModelGenerator(Path("templates"), tmp_path)
        output_path = await generator.generate(sample_api_schema)
        
        # Add to sys.path and try to import
        import sys
        sys.path.insert(0, str(tmp_path))
        
        try:
            import models
            # Verify model classes exist
            assert hasattr(models, sample_api_schema.models[0].name)
        finally:
            sys.path.remove(str(tmp_path))


class TestValidatorGenerator:
    """Test validator generation."""
    
    @pytest.mark.asyncio
    async def test_generate_validators(self, tmp_path, sample_api_schema):
        """Test generation of validator classes."""
        generator = ValidatorGenerator(Path("templates"), tmp_path)
        output_path = await generator.generate(sample_api_schema)
        
        assert output_path.exists()
        assert output_path.name == "validators.py"
        
        with open(output_path) as f:
            code = f.read()
            assert "async def validate" in code
            assert "ValidationResult" in code


class TestTestGenerator:
    """Test pytest suite generation."""
    
    @pytest.mark.asyncio
    async def test_generate_test_suite(self, tmp_path, sample_api_schema):
        """Test generation of pytest test suite."""
        generator = TestGenerator(Path("templates"), tmp_path)
        output_path = await generator.generate(sample_api_schema)
        
        assert output_path.exists()
        assert output_path.name == "test_api.py"
        
        with open(output_path) as f:
            code = f.read()
            assert "import pytest" in code
            assert "def test_" in code or "async def test_" in code
            assert "ModelFactory" in code  # polyfactory
```

---

## Integration Tests

### Test Scenarios

#### 1. OpenAPI End-to-End Flow

**File:** [`tests/integration/test_openapi_flow.py`](tests/integration/test_openapi_flow.py)

```python
import pytest
from pathlib import Path
import subprocess
from auto_sentinel import orchestrate_generation
from schemas.config_schema import GenerationConfig


class TestOpenAPIFlow:
    """Test complete OpenAPI → generated code flow."""
    
    @pytest.mark.asyncio
    async def test_petstore_generation(self, tmp_path):
        """Test generation from Petstore OpenAPI spec."""
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path / "petstore",
            project_name="petstore"
        )
        
        await orchestrate_generation(config)
        
        # Verify all files were generated
        assert (tmp_path / "petstore" / "models.py").exists()
        assert (tmp_path / "petstore" / "validators.py").exists()
        assert (tmp_path / "petstore" / "test_api.py").exists()
        assert (tmp_path / "petstore" / "app.py").exists()
        assert (tmp_path / "petstore" / "data_dict.md").exists()
        assert (tmp_path / "petstore" / "Dockerfile").exists()
    
    @pytest.mark.asyncio
    async def test_generated_code_runs(self, tmp_path):
        """Test that generated code actually runs."""
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path / "petstore",
            project_name="petstore"
        )
        
        await orchestrate_generation(config)
        
        # Try to import generated models
        import sys
        sys.path.insert(0, str(tmp_path / "petstore"))
        
        try:
            from models import Pet
            
            # Create instance
            pet = Pet(id=1, name="Fluffy", status="available")
            assert pet.name == "Fluffy"
        finally:
            sys.path.remove(str(tmp_path / "petstore"))
    
    @pytest.mark.asyncio
    async def test_generated_tests_pass(self, tmp_path):
        """Test that generated test suite passes."""
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path / "petstore",
            project_name="petstore"
        )
        
        await orchestrate_generation(config)
        
        # Run generated tests
        result = subprocess.run(
            ["pytest", str(tmp_path / "petstore" / "test_api.py"), "-v"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Tests failed: {result.stdout}"
    
    @pytest.mark.asyncio
    async def test_generated_app_starts(self, tmp_path):
        """Test that generated FastAPI app starts."""
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path / "petstore",
            project_name="petstore"
        )
        
        await orchestrate_generation(config)
        
        # Try to import and create app
        import sys
        sys.path.insert(0, str(tmp_path / "petstore"))
        
        try:
            from app import app
            assert app is not None
            assert hasattr(app, "routes")
        finally:
            sys.path.remove(str(tmp_path / "petstore"))
```

#### 2. GraphQL End-to-End Flow

**File:** [`tests/integration/test_graphql_flow.py`](tests/integration/test_graphql_flow.py)

```python
@pytest.mark.asyncio
async def test_graphql_introspection_and_generation(tmp_path, httpx_mock):
    """Test GraphQL introspection → generation flow."""
    # Mock GraphQL introspection response
    httpx_mock.add_response(json={
        "data": {
            "__schema": {
                "queryType": {"name": "Query"},
                "types": [
                    {
                        "kind": "OBJECT",
                        "name": "User",
                        "fields": [
                            {"name": "id", "type": {"kind": "SCALAR", "name": "ID"}},
                            {"name": "name", "type": {"kind": "SCALAR", "name": "String"}}
                        ]
                    }
                ]
            }
        }
    })
    
    config = GenerationConfig(
        input_type="graphql",
        source="https://api.example.com/graphql",
        output_dir=tmp_path / "graphql_api",
        project_name="graphql_api"
    )
    
    await orchestrate_generation(config)
    
    # Verify generation
    assert (tmp_path / "graphql_api" / "models.py").exists()
```

#### 3. JSON Inference End-to-End Flow

**File:** [`tests/integration/test_json_flow.py`](tests/integration/test_json_flow.py)

```python
@pytest.mark.asyncio
async def test_json_inference_and_generation(tmp_path):
    """Test JSON inference → generation flow."""
    config = GenerationConfig(
        input_type="json",
        source="examples/json/user_sample.json",
        output_dir=tmp_path / "json_api",
        project_name="json_api"
    )
    
    await orchestrate_generation(config)
    
    # Verify generation
    assert (tmp_path / "json_api" / "models.py").exists()
    
    # Verify inferred types are reasonable
    import sys
    sys.path.insert(0, str(tmp_path / "json_api"))
    
    try:
        from models import InferredModel
        # Test model can be instantiated
    finally:
        sys.path.remove(str(tmp_path / "json_api"))
```

---

## Performance Tests

**File:** [`tests/performance/test_performance.py`](tests/performance/test_performance.py)

```python
import pytest
import time
from auto_sentinel import orchestrate_generation


class TestPerformance:
    """Performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_parse_time_openapi(self, tmp_path):
        """Test OpenAPI parsing performance."""
        start = time.time()
        
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path,
            project_name="perf_test"
        )
        
        await orchestrate_generation(config)
        
        duration = time.time() - start
        
        # Should complete in < 10 seconds
        assert duration < 10.0, f"Generation took {duration}s, expected < 10s"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, tmp_path):
        """Test memory usage during generation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        config = GenerationConfig(
            input_type="openapi",
            source="examples/openapi/petstore.yaml",
            output_dir=tmp_path,
            project_name="mem_test"
        )
        
        await orchestrate_generation(config)
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        # Should use < 100MB additional memory
        assert mem_increase < 100, f"Memory increased by {mem_increase}MB"
```

---

## Pytest Configuration

**File:** [`tests/conftest.py`](tests/conftest.py)

```python
import pytest
from pathlib import Path
from schemas.api_schema import APISchema, ModelSchema, Endpoint, FieldSchema, FieldType


@pytest.fixture
def sample_api_schema():
    """Sample APISchema for testing."""
    return APISchema(
        title="Test API",
        version="1.0.0",
        base_url="https://api.test.com",
        endpoints=[
            Endpoint(
                path="/users/{id}",
                method="GET",
                response_model=ModelSchema(
                    name="User",
                    fields=[
                        FieldSchema(name="id", type=FieldType.INTEGER, required=True),
                        FieldSchema(name="name", type=FieldType.STRING, required=True),
                        FieldSchema(name="email", type=FieldType.EMAIL, required=True)
                    ]
                )
            )
        ],
        models={
            "User": ModelSchema(
                name="User",
                fields=[
                    FieldSchema(name="id", type=FieldType.INTEGER, required=True),
                    FieldSchema(name="name", type=FieldType.STRING, required=True),
                    FieldSchema(name="email", type=FieldType.EMAIL, required=True)
                ]
            )
        }
    )


@pytest.fixture
def sample_openapi_file():
    """Path to sample OpenAPI file."""
    return Path("tests/fixtures/sample_openapi.yaml")


@pytest.fixture
def sample_swagger_file():
    """Path to sample Swagger file."""
    return Path("tests/fixtures/sample_swagger.yaml")


@pytest.fixture
def httpx_mock():
    """Mock httpx for testing HTTP calls."""
    from pytest_httpx import HTTPXMock
    return HTTPXMock()
```

**File:** [`pyproject.toml`](pyproject.toml) - pytest configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=.",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=90"
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests"
]
```

---

## Continuous Integration

**File:** [`.github/workflows/test.yml`](.github/workflows/test.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit -v --cov
      
      - name: Run integration tests
        run: pytest tests/integration -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Execution

### Running Tests Locally

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_parsers.py -v

# Run specific test
pytest tests/unit/test_parsers.py::TestOpenAPIParser::test_parse_openapi_3_file -v

# Run tests matching pattern
pytest -k "test_openapi" -v

# Run tests with markers
pytest -m "not slow" -v
```

### Test Scripts

**File:** [`scripts/run_tests.sh`](scripts/run_tests.sh)

```bash
#!/bin/bash
set -e

echo "Running unit tests..."
pytest tests/unit -v --cov

echo "Running integration tests..."
pytest tests/integration -v

echo "Checking coverage..."
pytest --cov=. --cov-report=term-missing --cov-fail-under=90

echo "All tests passed!"
```

---

## Summary

This testing strategy provides:
- ✅ Comprehensive unit test coverage (90%+ target)
- ✅ End-to-end integration tests for all input types
- ✅ Performance benchmarks
- ✅ Generated code quality validation
- ✅ CI/CD integration
- ✅ Clear test organization and fixtures
- ✅ Fast feedback loop for developers

**Key Metrics:**
- Unit tests: < 5 seconds
- Integration tests: < 30 seconds
- Total test suite: < 1 minute
- Code coverage: 90%+
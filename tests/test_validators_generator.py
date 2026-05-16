"""
Tests for validators generator.
"""

import ast
from pathlib import Path

import pytest

from generators.validators_generator import ValidatorsGenerator
from schemas.api_schema import APISchema, Endpoint, ModelSchema, Parameter
from schemas.field_schema import FieldSchema, FieldType


@pytest.fixture
def sample_api_schema():
    """Create a sample API schema for testing."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(
                name="id",
                type=FieldType.INTEGER,
                required=True,
                description="User ID",
                min_value=1,
            ),
            FieldSchema(
                name="email",
                type=FieldType.EMAIL,
                required=True,
                description="User email",
            ),
            FieldSchema(
                name="name",
                type=FieldType.STRING,
                required=False,
                description="User name",
                max_length=100,
            ),
        ],
        description="User model",
    )
    
    endpoint = Endpoint(
        path="/users/{id}",
        method="GET",
        summary="Get user by ID",
        description="Retrieve a user by their ID",
        operation_id="getUser",
        response_model=user_model,
        parameters=[
            Parameter(
                name="id",
                location="path",
                required=True,
                field_schema=FieldSchema(
                    name="id",
                    type=FieldType.INTEGER,
                    required=True,
                ),
                description="User ID",
            ),
        ],
    )
    
    return APISchema(
        title="Test API",
        version="1.0.0",
        base_url="https://api.example.com",
        description="Test API for validators",
        endpoints=[endpoint],
        models={"User": user_model},
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_validators_generator_basic(sample_api_schema, temp_output_dir):
    """Test basic validators generation."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    assert output_file.exists()
    assert output_file.name == "validators.py"
    
    content = output_file.read_text(encoding="utf-8")
    assert "class APIValidator:" in content
    assert "async def validate_get_user(" in content


def test_validators_generator_syntax_valid(sample_api_schema, temp_output_dir):
    """Test that generated validators.py is syntactically valid."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    # Should parse without syntax errors
    content = output_file.read_text(encoding="utf-8")
    ast.parse(content)
    
    # Validate using generator method
    assert generator.validate_generation(output_file)


def test_validators_generator_imports(sample_api_schema, temp_output_dir):
    """Test that validators.py has correct imports."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for required imports
    assert "from typing import" in content
    assert "import httpx" in content
    assert "from loguru import logger" in content
    assert "from pydantic import ValidationError" in content
    assert "from models import User" in content
    assert "from core.exceptions import" in content
    assert "from core.retry_handler import with_retry" in content


def test_validators_generator_api_validator_class(sample_api_schema, temp_output_dir):
    """Test that APIValidator class is generated correctly."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for APIValidator class
    assert "class APIValidator:" in content
    assert "def __init__(" in content
    assert "async def __aenter__(" in content
    assert "async def __aexit__(" in content
    assert "def _get_cache_key(" in content
    assert "def _detect_schema_drift(" in content
    assert "async def _make_request(" in content


def test_validators_generator_endpoint_methods(sample_api_schema, temp_output_dir):
    """Test that validator methods are generated for each endpoint."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for endpoint validator method
    assert "async def validate_get_user(" in content
    assert "id: int" in content  # Path parameter
    assert "-> User:" in content  # Return type
    assert 'endpoint_path = "/users/{id}"' in content
    assert "response = await self._make_request(" in content
    assert "User.model_validate(data)" in content


def test_validators_generator_retry_decorator(sample_api_schema, temp_output_dir):
    """Test that retry decorator is applied."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for retry decorator
    assert "@with_retry(max_attempts=3, base_delay=1.0)" in content


def test_validators_generator_schema_drift_detection(sample_api_schema, temp_output_dir):
    """Test that schema drift detection is included."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for drift detection
    assert "expected_fields = set(User.model_fields.keys())" in content
    assert "drift = self._detect_schema_drift(expected_fields, actual_fields)" in content
    assert 'logger.warning(f"Schema drift detected' in content


def test_validators_generator_validation_report(sample_api_schema, temp_output_dir):
    """Test that ValidationReport class is generated."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for ValidationReport class
    assert "class ValidationReport:" in content
    assert "def add_result(" in content
    assert "def get_summary(" in content
    assert "def get_failed_endpoints(" in content
    assert "def get_drift_endpoints(" in content


def test_validators_generator_caching(sample_api_schema, temp_output_dir):
    """Test that caching logic is included."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for caching
    assert "enable_cache: bool = False" in content
    assert "self._cache: Dict[str, Any] = {}" in content
    assert "cache_key = self._get_cache_key(" in content
    assert "cached = self._check_cache(cache_key)" in content
    assert "self._update_cache(cache_key, validated)" in content


def test_validators_generator_error_handling(sample_api_schema, temp_output_dir):
    """Test that error handling is included."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for error handling
    assert "except ValidationError as e:" in content
    assert "raise ValidationException(" in content
    assert "except httpx.HTTPStatusError as e:" in content
    assert "raise APIException(" in content


def test_validators_generator_multiple_endpoints(temp_output_dir):
    """Test generation with multiple endpoints."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
            FieldSchema(name="name", type=FieldType.STRING, required=True),
        ],
    )
    
    post_model = ModelSchema(
        name="Post",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
            FieldSchema(name="title", type=FieldType.STRING, required=True),
        ],
    )
    
    api_schema = APISchema(
        title="Multi-Endpoint API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[
            Endpoint(
                path="/users",
                method="GET",
                operation_id="listUsers",
                response_model=user_model,
            ),
            Endpoint(
                path="/posts",
                method="GET",
                operation_id="listPosts",
                response_model=post_model,
            ),
        ],
        models={"User": user_model, "Post": post_model},
    )
    
    generator = ValidatorsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check both endpoints are generated
    assert "async def validate_list_users(" in content
    assert "async def validate_list_posts(" in content
    assert "from models import User, Post" in content


def test_validators_generator_query_parameters(temp_output_dir):
    """Test generation with query parameters."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
        ],
    )
    
    endpoint = Endpoint(
        path="/users",
        method="GET",
        operation_id="searchUsers",
        response_model=user_model,
        parameters=[
            Parameter(
                name="name",
                location="query",
                required=False,
                field_schema=FieldSchema(
                    name="name",
                    type=FieldType.STRING,
                    required=False,
                ),
                description="Filter by name",
            ),
            Parameter(
                name="limit",
                location="query",
                required=False,
                field_schema=FieldSchema(
                    name="limit",
                    type=FieldType.INTEGER,
                    required=False,
                ),
                description="Result limit",
            ),
        ],
    )
    
    api_schema = APISchema(
        title="Query Params API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[endpoint],
        models={"User": user_model},
    )
    
    generator = ValidatorsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check query parameters
    assert "name: Optional[str] = None" in content
    assert "limit: Optional[int] = None" in content
    assert 'params["name"] = name' in content
    assert 'params["limit"] = limit' in content


def test_validators_generator_get_stats(sample_api_schema, temp_output_dir):
    """Test generation statistics."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    
    stats = generator.get_generation_stats()
    
    assert stats["api_title"] == "Test API"
    assert stats["api_version"] == "1.0.0"
    assert stats["total_endpoints"] == 1
    assert stats["total_models"] == 1
    assert stats["validator_methods"] == 1
    assert stats["endpoints_by_method"]["GET"] == 1


def test_validators_generator_method_names(sample_api_schema, temp_output_dir):
    """Test validator method name generation."""
    generator = ValidatorsGenerator(sample_api_schema, temp_output_dir)
    
    methods = generator.get_validator_methods()
    
    assert len(methods) == 1
    assert "validate_get_user" in methods

# Made with Bob

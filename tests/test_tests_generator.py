"""
Tests for test suite generator.
"""

import ast
from pathlib import Path

import pytest

from generators.tests_generator import TestsGenerator
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
            ),
            FieldSchema(
                name="email",
                type=FieldType.EMAIL,
                required=True,
                description="User email",
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
        description="Test API",
        endpoints=[endpoint],
        models={"User": user_model},
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_tests_generator_basic(sample_api_schema, temp_output_dir):
    """Test basic test suite generation."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    assert output_file.exists()
    assert output_file.name == "test_api.py"
    
    content = output_file.read_text(encoding="utf-8")
    assert "import pytest" in content
    assert "from polyfactory.factories.pydantic_factory import ModelFactory" in content
    assert "class UserFactory(ModelFactory[User]):" in content


def test_tests_generator_syntax_valid(sample_api_schema, temp_output_dir):
    """Test that generated test_api.py is syntactically valid."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    # Should parse without syntax errors
    content = output_file.read_text(encoding="utf-8")
    ast.parse(content)
    
    # Validate using generator method
    assert generator.validate_generation(output_file)


def test_tests_generator_imports(sample_api_schema, temp_output_dir):
    """Test that test_api.py has correct imports."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for required imports
    assert "import pytest" in content
    assert "from typing import" in content
    assert "from polyfactory.factories.pydantic_factory import ModelFactory" in content
    assert "from models import User" in content
    assert "from validators import APIValidator" in content


def test_tests_generator_factories(sample_api_schema, temp_output_dir):
    """Test that polyfactory factories are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for factory class
    assert "class UserFactory(ModelFactory[User]):" in content
    assert "__model__ = User" in content


def test_tests_generator_fixtures(sample_api_schema, temp_output_dir):
    """Test that pytest fixtures are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for fixtures
    assert "@pytest.fixture" in content
    assert "def api_base_url():" in content
    assert "async def api_validator(api_base_url):" in content
    assert "def mock_response_data():" in content


def test_tests_generator_success_tests(sample_api_schema, temp_output_dir):
    """Test that success tests are generated for each endpoint."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for success test
    assert "async def test_get_user_success(" in content
    assert "httpx_mock.add_response(" in content
    assert "await api_validator.validate_get_user(" in content


def test_tests_generator_validation_error_tests(sample_api_schema, temp_output_dir):
    """Test that validation error tests are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for validation error test
    assert "async def test_get_user_validation_error(" in content
    assert "from core.exceptions import ValidationException" in content
    assert "with pytest.raises(ValidationException):" in content


def test_tests_generator_http_error_tests(sample_api_schema, temp_output_dir):
    """Test that HTTP error tests are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for HTTP error test
    assert "async def test_get_user_http_error(" in content
    assert "from core.exceptions import APIException" in content
    assert "status_code=404" in content
    assert "with pytest.raises(APIException):" in content


def test_tests_generator_schema_drift_tests(sample_api_schema, temp_output_dir):
    """Test that schema drift tests are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for schema drift test
    assert "async def test_get_user_schema_drift(" in content
    assert '"extra_field"' in content


def test_tests_generator_parameter_tests(sample_api_schema, temp_output_dir):
    """Test that parameter tests are generated for endpoints with parameters."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for parameter test
    assert "async def test_get_user_with_parameters(" in content
    assert "id=123" in content


def test_tests_generator_integration_tests(sample_api_schema, temp_output_dir):
    """Test that integration tests are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for integration tests
    assert "async def test_api_validator_context_manager(" in content
    assert "async def test_api_validator_caching(" in content
    assert "async def test_validation_report():" in content
    assert "async def test_concurrent_requests(" in content


def test_tests_generator_edge_case_tests(sample_api_schema, temp_output_dir):
    """Test that edge case tests are generated."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for edge case tests
    assert "async def test_empty_response(" in content
    assert "async def test_malformed_json(" in content


def test_tests_generator_test_markers(sample_api_schema, temp_output_dir):
    """Test that pytest markers are used."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for markers
    assert "@pytest.mark.asyncio" in content
    assert "@pytest.mark.slow" in content


def test_tests_generator_multiple_endpoints(temp_output_dir):
    """Test generation with multiple endpoints."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
        ],
    )
    
    post_model = ModelSchema(
        name="Post",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
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
    
    generator = TestsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check both endpoints have tests
    assert "async def test_list_users_success(" in content
    assert "async def test_list_posts_success(" in content
    
    # Check both factories
    assert "class UserFactory(ModelFactory[User]):" in content
    assert "class PostFactory(ModelFactory[Post]):" in content


def test_tests_generator_mock_param_values(sample_api_schema, temp_output_dir):
    """Test that mock parameter values are generated correctly."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    
    # Test different parameter types
    int_param = Parameter(
        name="id",
        location="path",
        required=True,
        field_schema=FieldSchema(name="id", type=FieldType.INTEGER, required=True),
    )
    assert generator._get_mock_param_value(int_param) == "123"
    
    str_param = Parameter(
        name="name",
        location="query",
        required=False,
        field_schema=FieldSchema(name="name", type=FieldType.STRING, required=False),
    )
    assert generator._get_mock_param_value(str_param) == '"test_value"'
    
    email_param = Parameter(
        name="email",
        location="query",
        required=False,
        field_schema=FieldSchema(name="email", type=FieldType.EMAIL, required=False),
    )
    assert generator._get_mock_param_value(email_param) == '"test@example.com"'


def test_tests_generator_test_count(sample_api_schema, temp_output_dir):
    """Test test count calculation."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    
    counts = generator.get_test_count()
    
    assert counts["endpoint_tests"] == 4  # 1 endpoint * 4 tests
    assert counts["parameter_tests"] == 1  # 1 endpoint with parameters
    assert counts["integration_tests"] == 4
    assert counts["edge_case_tests"] == 2
    assert counts["total"] == 11


def test_tests_generator_get_stats(sample_api_schema, temp_output_dir):
    """Test generation statistics."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    
    stats = generator.get_generation_stats()
    
    assert stats["api_title"] == "Test API"
    assert stats["api_version"] == "1.0.0"
    assert stats["total_endpoints"] == 1
    assert stats["total_models"] == 1
    assert stats["factory_count"] == 1
    assert stats["test_counts"]["total"] == 11
    assert stats["endpoints_by_method"]["GET"] == 1


def test_tests_generator_required_fixtures(sample_api_schema, temp_output_dir):
    """Test required fixtures list."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    
    fixtures = generator.get_required_fixtures()
    
    assert "api_base_url" in fixtures
    assert "api_validator" in fixtures
    assert "mock_response_data" in fixtures


def test_tests_generator_test_markers_list(sample_api_schema, temp_output_dir):
    """Test markers list."""
    generator = TestsGenerator(sample_api_schema, temp_output_dir)
    
    markers = generator.get_test_markers()
    
    assert "asyncio" in markers
    assert "slow" in markers


def test_tests_generator_no_endpoints(temp_output_dir):
    """Test generation with no endpoints."""
    api_schema = APISchema(
        title="Empty API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[],
        models={},
    )
    
    generator = TestsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Should still have integration tests
    assert "async def test_api_validator_context_manager(" in content
    assert "async def test_validation_report():" in content


def test_tests_generator_query_parameters(temp_output_dir):
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
            ),
        ],
    )
    
    api_schema = APISchema(
        title="Query API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[endpoint],
        models={"User": user_model},
    )
    
    generator = TestsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Should have parameter test
    assert "async def test_search_users_with_parameters(" in content


def test_tests_generator_skips_phantom_response_models(temp_output_dir):
    """Endpoints must not reference factories for models missing from models.py."""
    list_model = ModelSchema(
        name="Locations",
        fields=[
            FieldSchema(name="info", type=FieldType.OBJECT, required=False),
        ],
        description="Phantom list response not in models dict",
    )
    endpoint = Endpoint(
        path="/query/locations",
        method="GET",
        operation_id="locations",
        response_model=list_model,
        parameters=[],
    )
    api_schema = APISchema(
        title="Query API",
        version="1.0.0",
        base_url="https://rickandmortyapi.com",
        endpoints=[endpoint],
        models={"Character": ModelSchema(name="Character", fields=[])},
    )

    generator = TestsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    content = output_file.read_text(encoding="utf-8")

    assert "LocationsFactory" not in content
    assert "isinstance(result, Locations)" not in content
    assert "async def test_locations_success(" in content

# Made with Bob

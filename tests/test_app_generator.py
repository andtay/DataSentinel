"""
Tests for FastAPI app generator.
"""

import ast
from pathlib import Path

import pytest

from generators.app_generator import AppGenerator
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


def test_app_generator_basic(sample_api_schema, temp_output_dir):
    """Test basic FastAPI app generation."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    assert output_file.exists()
    assert output_file.name == "app.py"
    
    content = output_file.read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in content
    assert "app = FastAPI(" in content


def test_app_generator_syntax_valid(sample_api_schema, temp_output_dir):
    """Test that generated app.py is syntactically valid."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    # Should parse without syntax errors
    content = output_file.read_text(encoding="utf-8")
    ast.parse(content)
    
    # Validate using generator method
    assert generator.validate_generation(output_file)


def test_app_generator_imports(sample_api_schema, temp_output_dir):
    """Test that app.py has correct imports."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for required imports
    assert "from fastapi import FastAPI" in content
    assert "from fastapi.middleware.cors import CORSMiddleware" in content
    assert "from pydantic import BaseModel" in content
    assert "from loguru import logger" in content
    assert "from models import User" in content
    assert "from validators import APIValidator" in content


def test_app_generator_cors_middleware(sample_api_schema, temp_output_dir):
    """Test that CORS middleware is added."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for CORS middleware
    assert "app.add_middleware(" in content
    assert "CORSMiddleware" in content
    assert "allow_origins" in content


def test_app_generator_exception_handlers(sample_api_schema, temp_output_dir):
    """Test that exception handlers are generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for exception handlers
    assert "@app.exception_handler(ValidationException)" in content
    assert "@app.exception_handler(APIException)" in content
    assert "@app.exception_handler(SchemaException)" in content


def test_app_generator_health_endpoint(sample_api_schema, temp_output_dir):
    """Test that health check endpoint is generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for health endpoint
    assert '@app.get("/health"' in content
    assert "async def health_check():" in content
    assert "HealthResponse" in content


def test_app_generator_validation_endpoint(sample_api_schema, temp_output_dir):
    """Test that validation endpoint is generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for validation endpoint
    assert '@app.post("/validate"' in content
    assert "async def validate_api(" in content
    assert "ValidationRequest" in content
    assert "ValidationResponse" in content


def test_app_generator_individual_endpoints(sample_api_schema, temp_output_dir):
    """Test that individual validation endpoints are generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for individual endpoint
    assert '"/validate/users/{id}"' in content
    assert "async def validate_get_user(" in content
    assert "target_url: str" in content


def test_app_generator_request_models(sample_api_schema, temp_output_dir):
    """Test that request models are generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for request models
    assert "class ValidationRequest(BaseModel):" in content
    assert "target_url: str" in content


def test_app_generator_response_models(sample_api_schema, temp_output_dir):
    """Test that response models are generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for response models
    assert "class ValidationResult(BaseModel):" in content
    assert "class ValidationResponse(BaseModel):" in content
    assert "class HealthResponse(BaseModel):" in content


def test_app_generator_lifespan(sample_api_schema, temp_output_dir):
    """Test that lifespan management is included."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for lifespan
    assert "@asynccontextmanager" in content
    assert "async def lifespan(app: FastAPI):" in content
    assert "lifespan=lifespan" in content


def test_app_generator_root_endpoint(sample_api_schema, temp_output_dir):
    """Test that root endpoint is generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for root endpoint
    assert '@app.get("/", tags=["Root"])' in content
    assert "async def root():" in content


def test_app_generator_openapi_endpoint(sample_api_schema, temp_output_dir):
    """Test that OpenAPI endpoint is generated."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for OpenAPI endpoint
    assert '@app.get("/openapi.json"' in content
    assert "async def get_openapi_schema():" in content


def test_app_generator_uvicorn_runner(sample_api_schema, temp_output_dir):
    """Test that uvicorn runner is included."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for uvicorn runner
    assert 'if __name__ == "__main__":' in content
    assert "import uvicorn" in content
    assert "uvicorn.run(" in content


def test_app_generator_multiple_endpoints(temp_output_dir):
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
    
    generator = AppGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check both endpoints
    assert "async def validate_list_users(" in content
    assert "async def validate_list_posts(" in content


def test_app_generator_endpoint_count(sample_api_schema, temp_output_dir):
    """Test endpoint count calculation."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    counts = generator.get_endpoint_count()
    
    assert counts["health"] == 1
    assert counts["validate_all"] == 1
    assert counts["validate_individual"] == 1
    assert counts["root"] == 1
    assert counts["openapi"] == 1
    assert counts["total"] == 4


def test_app_generator_get_stats(sample_api_schema, temp_output_dir):
    """Test generation statistics."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    stats = generator.get_generation_stats()
    
    assert stats["api_title"] == "Test API"
    assert stats["api_version"] == "1.0.0"
    assert stats["total_endpoints"] == 1
    assert stats["total_models"] == 1
    assert stats["has_cors"] is True
    assert stats["has_exception_handlers"] is True


def test_app_generator_required_dependencies(sample_api_schema, temp_output_dir):
    """Test required dependencies list."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    deps = generator.get_required_dependencies()
    
    assert "fastapi" in deps
    assert "uvicorn[standard]" in deps
    assert "httpx" in deps
    assert "pydantic" in deps
    assert "loguru" in deps


def test_app_generator_middleware_list(sample_api_schema, temp_output_dir):
    """Test middleware list."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    middleware = generator.get_middleware_list()
    
    assert "CORSMiddleware" in middleware


def test_app_generator_exception_handlers_list(sample_api_schema, temp_output_dir):
    """Test exception handlers list."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    handlers = generator.get_exception_handlers()
    
    assert "ValidationException" in handlers
    assert "APIException" in handlers
    assert "SchemaException" in handlers


def test_app_generator_default_param_values(sample_api_schema, temp_output_dir):
    """Test default parameter value generation."""
    generator = AppGenerator(sample_api_schema, temp_output_dir)
    
    # Test different parameter types
    int_param = Parameter(
        name="id",
        location="path",
        required=True,
        field_schema=FieldSchema(name="id", type=FieldType.INTEGER, required=True),
    )
    assert generator._get_default_param_value(int_param) == "1"
    
    str_param = Parameter(
        name="name",
        location="query",
        required=False,
        field_schema=FieldSchema(name="name", type=FieldType.STRING, required=False),
    )
    assert generator._get_default_param_value(str_param) == '"default"'


def test_app_generator_no_endpoints(temp_output_dir):
    """Test generation with no endpoints."""
    api_schema = APISchema(
        title="Empty API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[],
        models={},
    )
    
    generator = AppGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Should still have health and root endpoints
    assert '@app.get("/health"' in content
    assert '@app.get("/", tags=["Root"])' in content

# Made with Bob

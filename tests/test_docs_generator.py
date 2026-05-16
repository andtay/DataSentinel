"""
Tests for documentation generator.
"""

from pathlib import Path

import pytest

from generators.docs_generator import DocsGenerator
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
                example=123,
            ),
            FieldSchema(
                name="email",
                type=FieldType.EMAIL,
                required=True,
                description="User email",
                example="user@example.com",
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
        description="Test API for documentation",
        endpoints=[endpoint],
        models={"User": user_model},
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_docs_generator_basic(sample_api_schema, temp_output_dir):
    """Test basic documentation generation."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    assert output_file.exists()
    assert output_file.name == "data_dict.md"
    
    content = output_file.read_text(encoding="utf-8")
    assert "# Test API - Data Dictionary" in content
    assert "**Version:** 1.0.0" in content


def test_docs_generator_models_section(sample_api_schema, temp_output_dir):
    """Test that models section is generated."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for models section
    assert "## Data Models" in content
    assert "### User" in content
    assert "| Field Name | Type | Required | Description | Constraints | Example |" in content
    assert "| `id` |" in content
    assert "| `email` |" in content


def test_docs_generator_endpoints_section(sample_api_schema, temp_output_dir):
    """Test that endpoints section is generated."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for endpoints section
    assert "## API Endpoints" in content
    assert "### GET /users/{id}" in content
    assert "**Method:** `GET`" in content
    assert "**Path:** `/users/{id}`" in content


def test_docs_generator_table_of_contents(sample_api_schema, temp_output_dir):
    """Test that table of contents is generated."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for TOC
    assert "## Table of Contents" in content
    assert "[Overview](#overview)" in content
    assert "[Data Models](#data-models)" in content
    assert "[API Endpoints](#api-endpoints)" in content


def test_docs_generator_field_constraints(sample_api_schema, temp_output_dir):
    """Test that field constraints are documented."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for constraints
    assert "min: 1" in content  # min_value constraint


def test_docs_generator_examples(sample_api_schema, temp_output_dir):
    """Test that examples are included."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for examples
    assert "`123`" in content  # id example
    assert "`\"user@example.com\"`" in content  # email example


def test_docs_generator_curl_examples(sample_api_schema, temp_output_dir):
    """Test that curl examples are generated."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for curl example
    assert "```bash" in content
    assert "curl -X GET" in content
    assert "https://api.example.com/users/{id}" in content


def test_docs_generator_field_type_reference(sample_api_schema, temp_output_dir):
    """Test that field type reference is included."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for field type reference
    assert "## Field Type Reference" in content
    assert "| Type | Description | Python Type | Validation |" in content


def test_docs_generator_validation_rules(sample_api_schema, temp_output_dir):
    """Test that validation rules are documented."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for validation rules
    assert "## Validation Rules" in content
    assert "### String Validation" in content
    assert "### Numeric Validation" in content


def test_docs_generator_error_responses(sample_api_schema, temp_output_dir):
    """Test that error responses are documented."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check for error responses
    assert "## Error Responses" in content
    assert "### 400 Bad Request" in content
    assert "### 404 Not Found" in content
    assert "### 422 Unprocessable Entity" in content


def test_docs_generator_statistics(sample_api_schema, temp_output_dir):
    """Test generation statistics."""
    generator = DocsGenerator(sample_api_schema, temp_output_dir)
    
    stats = generator.get_generation_stats()
    
    assert stats["api_title"] == "Test API"
    assert stats["api_version"] == "1.0.0"
    assert stats["total_models"] == 1
    assert stats["total_endpoints"] == 1
    assert stats["total_fields"] == 2


def test_docs_generator_multiple_models(temp_output_dir):
    """Test generation with multiple models."""
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
        title="Multi-Model API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[],
        models={"User": user_model, "Post": post_model},
    )
    
    generator = DocsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Check both models
    assert "### User" in content
    assert "### Post" in content


def test_docs_generator_no_description(temp_output_dir):
    """Test generation without API description."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
        ],
    )
    
    api_schema = APISchema(
        title="No Description API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[],
        models={"User": user_model},
    )
    
    generator = DocsGenerator(api_schema, temp_output_dir)
    output_file = generator.generate()
    
    content = output_file.read_text(encoding="utf-8")
    
    # Should still generate
    assert "# No Description API - Data Dictionary" in content

# Made with Bob

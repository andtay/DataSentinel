"""
Tests for schema normalizer.

This module tests the schema normalization and validation layer that ensures
consistency and correctness before code generation.
"""

import pytest

from core.exceptions import ParserError
from parsers.schema_normalizer import SchemaNormalizer
from schemas import (
    APISchema,
    AuthConfig,
    Endpoint,
    FieldSchema,
    FieldType,
    ModelSchema,
    Parameter,
)


def create_valid_schema() -> APISchema:
    """Create a valid API schema for testing."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(
                name="id",
                type=FieldType.INTEGER,
                required=True,
                description="User ID",
                default=None,
                pattern=None,
                min_length=None,
                max_length=None,
                min_value=None,
                max_value=None,
                multiple_of=None,
                enum_values=None,
                item_type=None,
                min_items=None,
                max_items=None,
                unique_items=False,
                nested_model=None,
                additional_properties=False,
                example=1,
                deprecated=False,
                read_only=False,
                write_only=False
            ),
            FieldSchema(
                name="email",
                type=FieldType.EMAIL,
                required=True,
                description="User email",
                default=None,
                pattern=None,
                min_length=None,
                max_length=None,
                min_value=None,
                max_value=None,
                multiple_of=None,
                enum_values=None,
                item_type=None,
                min_items=None,
                max_items=None,
                unique_items=False,
                nested_model=None,
                additional_properties=False,
                example="user@example.com",
                deprecated=False,
                read_only=False,
                write_only=False
            ),
        ],
        description="User model",
        example=None
    )
    
    endpoint = Endpoint(
        path="/users",
        method="GET",
        summary="List users",
        description="Get all users",
        operation_id="listUsers",
        request_model=None,
        response_model=user_model,
        parameters=[],
        auth_required=True,
        tags=["users"],
        deprecated=False
    )
    
    return APISchema(
        title="Test API",
        version="1.0.0",
        base_url="https://api.example.com",
        description="Test API",
        endpoints=[endpoint],
        models={"User": user_model},
        auth_config=None
    )


def test_normalizer_valid_schema():
    """Test normalizer with valid schema."""
    schema = create_valid_schema()
    normalizer = SchemaNormalizer(schema)
    
    normalized = normalizer.normalize()
    
    assert normalized == schema
    assert len(normalizer.errors) == 0


def test_normalizer_missing_title():
    """Test normalizer detects missing title."""
    schema = create_valid_schema()
    schema.title = ""
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert "title is required" in normalizer.errors[0].lower()


def test_normalizer_missing_version():
    """Test normalizer detects missing version."""
    schema = create_valid_schema()
    schema.version = ""
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert "version is required" in normalizer.errors[0].lower()


def test_normalizer_invalid_base_url():
    """Test normalizer warns about invalid base URL."""
    schema = create_valid_schema()
    schema.base_url = "invalid-url"
    
    normalizer = SchemaNormalizer(schema)
    normalized = normalizer.normalize()
    
    assert len(normalizer.warnings) > 0
    assert any("http" in w.lower() for w in normalizer.warnings)


def test_normalizer_duplicate_endpoints():
    """Test normalizer detects duplicate endpoints."""
    schema = create_valid_schema()
    
    # Add duplicate endpoint
    duplicate = Endpoint(
        path="/users",
        method="GET",
        summary="Duplicate",
        description="Duplicate endpoint",
        operation_id="duplicate",
        request_model=None,
        response_model=schema.models["User"],
        parameters=[],
        auth_required=True,
        tags=[],
        deprecated=False
    )
    schema.endpoints.append(duplicate)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("duplicate" in e.lower() for e in normalizer.errors)


def test_normalizer_invalid_http_method():
    """Test normalizer detects invalid HTTP method."""
    schema = create_valid_schema()
    schema.endpoints[0].method = "INVALID"
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("invalid http method" in e.lower() for e in normalizer.errors)


def test_normalizer_duplicate_field_names():
    """Test normalizer detects duplicate field names."""
    schema = create_valid_schema()
    
    # Add duplicate field
    duplicate_field = FieldSchema(
        name="id",  # Duplicate
        type=FieldType.STRING,
        required=True,
        description="Duplicate",
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=None,
        min_items=None,
        max_items=None,
        unique_items=False,
        nested_model=None,
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(duplicate_field)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("duplicate field" in e.lower() for e in normalizer.errors)


def test_normalizer_invalid_array_constraints():
    """Test normalizer detects invalid array constraints."""
    schema = create_valid_schema()
    
    # Add field with invalid constraints
    invalid_field = FieldSchema(
        name="items",
        type=FieldType.ARRAY,
        required=True,
        description="Items",
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=FieldType.STRING,
        min_items=10,  # Invalid: min > max
        max_items=5,
        unique_items=False,
        nested_model=None,
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(invalid_field)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("min_items" in e and "max_items" in e for e in normalizer.errors)


def test_normalizer_invalid_string_constraints():
    """Test normalizer detects invalid string constraints."""
    schema = create_valid_schema()
    
    # Add field with invalid constraints
    invalid_field = FieldSchema(
        name="name",
        type=FieldType.STRING,
        required=True,
        description="Name",
        default=None,
        pattern=None,
        min_length=100,  # Invalid: min > max
        max_length=10,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=None,
        min_items=None,
        max_items=None,
        unique_items=False,
        nested_model=None,
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(invalid_field)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("min_length" in e and "max_length" in e for e in normalizer.errors)


def test_normalizer_invalid_numeric_constraints():
    """Test normalizer detects invalid numeric constraints."""
    schema = create_valid_schema()
    
    # Add field with invalid constraints
    invalid_field = FieldSchema(
        name="age",
        type=FieldType.INTEGER,
        required=True,
        description="Age",
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=100,  # Invalid: min > max
        max_value=10,
        multiple_of=None,
        enum_values=None,
        item_type=None,
        min_items=None,
        max_items=None,
        unique_items=False,
        nested_model=None,
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(invalid_field)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("min_value" in e and "max_value" in e for e in normalizer.errors)


def test_normalizer_missing_nested_model():
    """Test normalizer detects missing nested model reference."""
    schema = create_valid_schema()
    
    # Add field with non-existent nested model
    invalid_field = FieldSchema(
        name="profile",
        type=FieldType.OBJECT,
        required=True,
        description="Profile",
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=None,
        min_items=None,
        max_items=None,
        unique_items=False,
        nested_model="NonExistentModel",
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(invalid_field)
    
    normalizer = SchemaNormalizer(schema)
    
    with pytest.raises(ParserError):
        normalizer.normalize()
    
    assert any("nonexistentmodel" in e.lower() for e in normalizer.errors)


def test_normalizer_field_name_normalization():
    """Test normalizer normalizes field names to snake_case."""
    schema = create_valid_schema()
    
    # Add field with camelCase name
    camel_field = FieldSchema(
        name="firstName",  # Should be normalized to first_name
        type=FieldType.STRING,
        required=True,
        description="First name",
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=None,
        min_items=None,
        max_items=None,
        unique_items=False,
        nested_model=None,
        additional_properties=False,
        example=None,
        deprecated=False,
        read_only=False,
        write_only=False
    )
    schema.models["User"].fields.append(camel_field)
    
    normalizer = SchemaNormalizer(schema)
    normalized = normalizer.normalize()
    
    # Check that field name was normalized
    field_names = {f.name for f in normalized.models["User"].fields}
    assert "first_name" in field_names
    assert "firstName" not in field_names


def test_normalizer_validation_report():
    """Test normalizer validation report."""
    schema = create_valid_schema()
    normalizer = SchemaNormalizer(schema)
    
    normalizer.normalize()
    report = normalizer.get_validation_report()
    
    assert report["valid"] is True
    assert len(report["errors"]) == 0
    assert "stats" in report
    assert report["stats"]["endpoints"] == 1
    assert report["stats"]["models"] == 1


def test_normalizer_no_endpoints_warning():
    """Test normalizer warns about no endpoints."""
    schema = create_valid_schema()
    schema.endpoints = []
    
    normalizer = SchemaNormalizer(schema)
    normalized = normalizer.normalize()
    
    assert len(normalizer.warnings) > 0
    assert any("no endpoints" in w.lower() for w in normalizer.warnings)


def test_normalizer_no_models_warning():
    """Test normalizer warns about no models."""
    schema = create_valid_schema()
    schema.models = {}
    schema.endpoints = []  # Remove endpoints too since they reference models
    
    normalizer = SchemaNormalizer(schema)
    normalized = normalizer.normalize()
    
    assert len(normalizer.warnings) > 0
    assert any("no models" in w.lower() for w in normalizer.warnings)


def test_normalizer_empty_model_warning():
    """Test normalizer warns about empty models."""
    schema = create_valid_schema()
    
    # Add empty model
    empty_model = ModelSchema(
        name="EmptyModel",
        fields=[],
        description="Empty",
        example=None
    )
    schema.models["EmptyModel"] = empty_model
    
    normalizer = SchemaNormalizer(schema)
    normalized = normalizer.normalize()
    
    assert len(normalizer.warnings) > 0
    assert any("no fields" in w.lower() for w in normalizer.warnings)

# Made with Bob

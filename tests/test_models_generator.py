"""
Tests for Pydantic models generator.

This module tests the code generator that creates Pydantic BaseModel classes
from APISchema.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from generators.models_generator import ModelsGenerator
from schemas import APISchema, FieldSchema, FieldType, ModelSchema


def create_test_schema() -> APISchema:
    """Create a test API schema."""
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
                min_value=1,
                max_value=None,
                multiple_of=None,
                enum_values=None,
                item_type=None,
                min_items=None,
                max_items=None,
                unique_items=False,
                nested_model=None,
                additional_properties=False,
                example=123,
                deprecated=False,
                read_only=False,
                write_only=False
            ),
            FieldSchema(
                name="email",
                type=FieldType.EMAIL,
                required=True,
                description="User email address",
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
            FieldSchema(
                name="name",
                type=FieldType.STRING,
                required=False,
                description="User name",
                default=None,
                pattern=None,
                min_length=1,
                max_length=100,
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
                example="John Doe",
                deprecated=False,
                read_only=False,
                write_only=False
            ),
        ],
        description="User model",
        example={"id": 123, "email": "user@example.com", "name": "John Doe"}
    )
    
    return APISchema(
        title="Test API",
        version="1.0.0",
        base_url="https://api.example.com",
        description="Test API",
        endpoints=[],
        models={"User": user_model},
        auth_config=None
    )


def test_models_generator_basic():
    """Test basic models generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        output_file = generator.generate()
        
        assert output_file.exists()
        assert output_file.name == "models.py"
        
        # Read generated content
        content = output_file.read_text()
        
        # Check for basic structure
        assert "class User(BaseModel):" in content
        assert "from pydantic import" in content


def test_models_generator_field_types():
    """Test field type generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        output_file = generator.generate()
        
        content = output_file.read_text()
        
        # Check field types
        assert "id: int" in content
        assert "email: EmailStr" in content
        assert "name: Optional[str]" in content


def test_models_generator_field_constraints():
    """Test field constraint generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        output_file = generator.generate()
        
        content = output_file.read_text()
        
        # Check constraints
        assert "ge=1" in content  # min_value for id
        assert "min_length=1" in content  # min_length for name
        assert "max_length=100" in content  # max_length for name


def test_models_generator_descriptions():
    """Test field description generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        output_file = generator.generate()
        
        content = output_file.read_text()
        
        # Check descriptions
        assert "User ID" in content
        assert "User email address" in content
        assert "User name" in content


def test_models_generator_imports():
    """Test import generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        
        imports = generator.get_imports()
        
        # Check required imports
        assert any("BaseModel" in imp for imp in imports)
        assert any("EmailStr" in imp for imp in imports)
        assert any("Optional" in imp for imp in imports)


def test_models_generator_type_annotation():
    """Test type annotation generation."""
    schema = create_test_schema()
    generator = ModelsGenerator(schema, Path("."))
    
    # Test various field types
    int_field = FieldSchema(
        name="test",
        type=FieldType.INTEGER,
        required=True,
        description=None,
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
    assert generator._get_field_type_annotation(int_field) == "int"
    
    # Test optional field
    optional_field = FieldSchema(
        name="test",
        type=FieldType.STRING,
        required=False,
        description=None,
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
    assert generator._get_field_type_annotation(optional_field) == "Optional[str]"
    
    # Test array field
    array_field = FieldSchema(
        name="test",
        type=FieldType.ARRAY,
        required=True,
        description=None,
        default=None,
        pattern=None,
        min_length=None,
        max_length=None,
        min_value=None,
        max_value=None,
        multiple_of=None,
        enum_values=None,
        item_type=FieldType.STRING,
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
    assert generator._get_field_type_annotation(array_field) == "List[str]"


def test_models_generator_has_field_args():
    """Test field args detection."""
    schema = create_test_schema()
    generator = ModelsGenerator(schema, Path("."))
    
    # Field with description needs Field()
    field_with_desc = FieldSchema(
        name="test",
        type=FieldType.STRING,
        required=True,
        description="Test field",
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
    assert generator._has_field_args(field_with_desc) is True
    
    # Simple required field without constraints doesn't need Field()
    simple_field = FieldSchema(
        name="test",
        type=FieldType.STRING,
        required=True,
        description=None,
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
    assert generator._has_field_args(simple_field) is False


def test_models_generator_metadata():
    """Test metadata generation."""
    schema = create_test_schema()
    
    with TemporaryDirectory() as tmpdir:
        generator = ModelsGenerator(schema, Path(tmpdir))
        output_file = generator.generate()
        
        content = output_file.read_text()
        
        # Check metadata
        assert "Test API" in content
        assert "1.0.0" in content
        assert "Auto-generated" in content
        assert "DataSentinel" in content

# Made with Bob

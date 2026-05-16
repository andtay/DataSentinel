"""
Tests for JSON inference parser.

This module tests the type inference engine that analyzes JSON data
and automatically infers Pydantic model schemas.
"""

import pytest
from pathlib import Path

from parsers.json_inference_parser import JSONInferenceParser
from schemas import FieldType


@pytest.mark.asyncio
async def test_simple_json_inference():
    """Test inference from simple JSON object."""
    # Create a temporary JSON file
    test_data = {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "active": True,
        "score": 95.5
    }
    
    # Create parser with dict (simulating loaded JSON)
    parser = JSONInferenceParser("test.json")
    
    # Manually set the data for testing
    model = parser._infer_model_from_json(test_data, "User")
    
    # Verify model structure
    assert model.name == "User"
    assert len(model.fields) == 6
    
    # Verify field types
    field_types = {f.name: f.type for f in model.fields}
    assert field_types["id"] == FieldType.INTEGER
    assert field_types["name"] == FieldType.STRING
    assert field_types["email"] == FieldType.EMAIL  # Should detect email pattern
    assert field_types["age"] == FieldType.INTEGER
    assert field_types["active"] == FieldType.BOOLEAN
    assert field_types["score"] == FieldType.FLOAT


@pytest.mark.asyncio
async def test_nested_json_inference():
    """Test inference from nested JSON object."""
    test_data = {
        "user": {
            "id": 1,
            "name": "Alice"
        },
        "posts": [
            {
                "id": 101,
                "title": "First Post",
                "content": "Hello World"
            }
        ]
    }
    
    parser = JSONInferenceParser("test.json")
    model = parser._infer_model_from_json(test_data, "Response")
    
    # Verify nested structures
    assert model.name == "Response"
    assert len(model.fields) == 2
    
    # Check user field (nested object)
    user_field = next(f for f in model.fields if f.name == "user")
    assert user_field.type == FieldType.OBJECT
    assert user_field.nested_model == "User"
    
    # Check posts field (array)
    posts_field = next(f for f in model.fields if f.name == "posts")
    assert posts_field.type == FieldType.ARRAY
    assert posts_field.item_type == FieldType.OBJECT


@pytest.mark.asyncio
async def test_pattern_detection():
    """Test pattern detection in string values."""
    test_data = {
        "email": "test@example.com",
        "website": "https://example.com",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "date": "2024-01-15",
        "datetime": "2024-01-15T10:30:00Z"
    }
    
    parser = JSONInferenceParser("test.json")
    model = parser._infer_model_from_json(test_data, "Patterns")
    
    # Verify pattern detection
    field_types = {f.name: f.type for f in model.fields}
    assert field_types["email"] == FieldType.EMAIL
    assert field_types["website"] == FieldType.URL
    assert field_types["uuid"] == FieldType.UUID
    # date and datetime should have patterns detected
    date_field = next(f for f in model.fields if f.name == "date")
    assert date_field.pattern is not None


@pytest.mark.asyncio
async def test_multiple_samples_analysis():
    """Test analyzing multiple samples to detect optional fields."""
    samples = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob"},  # Missing email
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
    ]
    
    parser = JSONInferenceParser("test.json")
    model = parser.analyze_multiple_samples(samples)
    
    # Verify required vs optional fields
    field_required = {f.name: f.required for f in model.fields}
    assert field_required["id"] is True  # Present in all samples
    assert field_required["name"] is True  # Present in all samples
    assert field_required["email"] is False  # Missing in one sample


@pytest.mark.asyncio
async def test_array_type_inference():
    """Test inference of array item types."""
    test_data = {
        "numbers": [1, 2, 3, 4, 5],
        "strings": ["a", "b", "c"],
        "objects": [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"}
        ]
    }
    
    parser = JSONInferenceParser("test.json")
    model = parser._infer_model_from_json(test_data, "Arrays")
    
    # Verify array item types
    numbers_field = next(f for f in model.fields if f.name == "numbers")
    assert numbers_field.type == FieldType.ARRAY
    assert numbers_field.item_type == FieldType.INTEGER
    
    strings_field = next(f for f in model.fields if f.name == "strings")
    assert strings_field.type == FieldType.ARRAY
    assert strings_field.item_type == FieldType.STRING
    
    objects_field = next(f for f in model.fields if f.name == "objects")
    assert objects_field.type == FieldType.ARRAY
    assert objects_field.item_type == FieldType.OBJECT
    assert objects_field.nested_model is not None


def test_field_name_normalization():
    """Test field name normalization."""
    parser = JSONInferenceParser("test.json")
    
    # Test various field name formats
    assert parser._normalize_field_name("user_name") == "user_name"
    assert parser._normalize_field_name("userName") == "user_name"
    assert parser._normalize_field_name("UserName") == "user_name"
    assert parser._normalize_field_name("user-name") == "user_name"
    assert parser._normalize_field_name("user name") == "user_name"


def test_model_name_normalization():
    """Test model name normalization."""
    parser = JSONInferenceParser("test.json")
    
    # Test various model name formats
    assert parser._normalize_model_name("user_model") == "UserModel"
    assert parser._normalize_model_name("user-model") == "UserModel"
    assert parser._normalize_model_name("user model") == "UserModel"
    assert parser._normalize_model_name("userModel") == "UserModel"

# Made with Bob

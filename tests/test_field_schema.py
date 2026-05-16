"""
Unit tests for schemas/field_schema.py

Tests FieldType enum, FieldSchema model, and Validator class.
"""

import pytest
from pydantic import ValidationError

from schemas.field_schema import FieldSchema, FieldType, Validator


class TestFieldType:
    """Test FieldType enum."""
    
    def test_field_type_values(self):
        """Test that all field types have correct values."""
        assert FieldType.STRING.value == "string"
        assert FieldType.INTEGER.value == "integer"
        assert FieldType.FLOAT.value == "float"
        assert FieldType.BOOLEAN.value == "boolean"
        assert FieldType.ARRAY.value == "array"
        assert FieldType.OBJECT.value == "object"
        assert FieldType.DATE.value == "date"
        assert FieldType.DATETIME.value == "datetime"
        assert FieldType.UUID.value == "uuid"
        assert FieldType.EMAIL.value == "email"
        assert FieldType.URL.value == "url"
        assert FieldType.ANY.value == "any"
    
    def test_field_type_python_type_basic(self):
        """Test python_type property for basic types."""
        assert FieldType.STRING.python_type == "str"
        assert FieldType.INTEGER.python_type == "int"
        assert FieldType.FLOAT.python_type == "float"
        assert FieldType.BOOLEAN.python_type == "bool"
    
    def test_field_type_python_type_special(self):
        """Test python_type property for special types."""
        assert FieldType.DATE.python_type == "str"
        assert FieldType.DATETIME.python_type == "str"
        assert FieldType.UUID.python_type == "str"
        assert FieldType.EMAIL.python_type == "str"
        assert FieldType.URL.python_type == "str"
    
    def test_field_type_python_type_complex(self):
        """Test python_type property for complex types."""
        assert FieldType.ARRAY.python_type == "list"
        assert FieldType.OBJECT.python_type == "dict"
        assert FieldType.ANY.python_type == "Any"


class TestValidator:
    """Test Validator class."""
    
    def test_validator_creation(self):
        """Test creating Validator instances."""
        validator = Validator("min_length", 5)
        assert validator.type == "min_length"
        assert validator.value == 5
    
    def test_validator_without_value(self):
        """Test creating Validator without value."""
        validator = Validator("email")
        assert validator.type == "email"
        assert validator.value is None
    
    def test_validator_repr(self):
        """Test Validator string representation."""
        validator = Validator("max_length", 100)
        repr_str = repr(validator)
        assert "Validator" in repr_str
        assert "max_length" in repr_str
        assert "100" in repr_str


class TestFieldSchemaCreation:
    """Test FieldSchema creation and validation."""
    
    def test_create_simple_field(self):
        """Test creating a simple field."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            required=True,
            description="User's username"
        )
        
        assert field.name == "username"
        assert field.type == FieldType.STRING
        assert field.required is True
        assert field.description == "User's username"
    
    def test_create_field_with_constraints(self):
        """Test creating field with validation constraints."""
        field = FieldSchema(
            name="age",
            type=FieldType.INTEGER,
            required=True,
            min_value=0,
            max_value=150
        )
        
        assert field.min_value == 0
        assert field.max_value == 150
    
    def test_create_field_with_default(self):
        """Test creating field with default value."""
        field = FieldSchema(
            name="is_active",
            type=FieldType.BOOLEAN,
            required=False,
            default=True
        )
        
        assert field.default is True
        assert field.required is False
    
    def test_create_array_field(self):
        """Test creating array field."""
        field = FieldSchema(
            name="tags",
            type=FieldType.ARRAY,
            item_type=FieldType.STRING,
            min_items=1,
            max_items=10
        )
        
        assert field.type == FieldType.ARRAY
        assert field.item_type == FieldType.STRING
        assert field.min_items == 1
        assert field.max_items == 10
    
    def test_create_object_field(self):
        """Test creating object field with nested model."""
        field = FieldSchema(
            name="address",
            type=FieldType.OBJECT,
            nested_model="Address"
        )
        
        assert field.type == FieldType.OBJECT
        assert field.nested_model == "Address"


class TestGetPythonType:
    """Test get_python_type method."""
    
    def test_get_python_type_string(self):
        """Test Python type for string field."""
        field = FieldSchema(name="name", type=FieldType.STRING)
        assert field.get_python_type() == "str"
    
    def test_get_python_type_integer(self):
        """Test Python type for integer field."""
        field = FieldSchema(name="age", type=FieldType.INTEGER)
        assert field.get_python_type() == "int"
    
    def test_get_python_type_float(self):
        """Test Python type for float field."""
        field = FieldSchema(name="price", type=FieldType.FLOAT)
        assert field.get_python_type() == "float"
    
    def test_get_python_type_boolean(self):
        """Test Python type for boolean field."""
        field = FieldSchema(name="is_active", type=FieldType.BOOLEAN)
        assert field.get_python_type() == "bool"
    
    def test_get_python_type_date(self):
        """Test Python type for date field."""
        field = FieldSchema(name="birth_date", type=FieldType.DATE)
        assert field.get_python_type() == "date"
    
    def test_get_python_type_datetime(self):
        """Test Python type for datetime field."""
        field = FieldSchema(name="created_at", type=FieldType.DATETIME)
        assert field.get_python_type() == "datetime"
    
    def test_get_python_type_uuid(self):
        """Test Python type for UUID field."""
        field = FieldSchema(name="id", type=FieldType.UUID)
        assert field.get_python_type() == "UUID"
    
    def test_get_python_type_email(self):
        """Test Python type for email field."""
        field = FieldSchema(name="email", type=FieldType.EMAIL)
        assert field.get_python_type() == "EmailStr"
    
    def test_get_python_type_url(self):
        """Test Python type for URL field."""
        field = FieldSchema(name="website", type=FieldType.URL)
        assert field.get_python_type() == "HttpUrl"
    
    def test_get_python_type_array_with_item_type(self):
        """Test Python type for array with item type."""
        field = FieldSchema(
            name="tags",
            type=FieldType.ARRAY,
            item_type=FieldType.STRING
        )
        assert field.get_python_type() == "list[str]"
    
    def test_get_python_type_array_without_item_type(self):
        """Test Python type for array without item type."""
        field = FieldSchema(name="items", type=FieldType.ARRAY)
        assert field.get_python_type() == "list[Any]"
    
    def test_get_python_type_object_with_nested_model(self):
        """Test Python type for object with nested model."""
        field = FieldSchema(
            name="address",
            type=FieldType.OBJECT,
            nested_model="Address"
        )
        assert field.get_python_type() == "Address"
    
    def test_get_python_type_object_without_nested_model(self):
        """Test Python type for object without nested model."""
        field = FieldSchema(name="metadata", type=FieldType.OBJECT)
        assert field.get_python_type() == "dict[str, Any]"
    
    def test_get_python_type_any(self):
        """Test Python type for any field."""
        field = FieldSchema(name="data", type=FieldType.ANY)
        assert field.get_python_type() == "Any"


class TestGetPydanticFieldArgs:
    """Test get_pydantic_field_args method."""
    
    def test_field_args_with_description(self):
        """Test field args with description."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            description="User's username"
        )
        args = field.get_pydantic_field_args()
        assert args["description"] == "User's username"
    
    def test_field_args_with_default(self):
        """Test field args with default value."""
        field = FieldSchema(
            name="is_active",
            type=FieldType.BOOLEAN,
            default=True
        )
        args = field.get_pydantic_field_args()
        assert args["default"] is True
    
    def test_field_args_optional_without_default(self):
        """Test field args for optional field without default."""
        field = FieldSchema(
            name="nickname",
            type=FieldType.STRING,
            required=False
        )
        args = field.get_pydantic_field_args()
        assert args["default"] is None
    
    def test_field_args_string_constraints(self):
        """Test field args with string constraints."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            pattern=r"^[a-z0-9_]+$",
            min_length=3,
            max_length=20
        )
        args = field.get_pydantic_field_args()
        assert args["pattern"] == r"^[a-z0-9_]+$"
        assert args["min_length"] == 3
        assert args["max_length"] == 20
    
    def test_field_args_numeric_constraints(self):
        """Test field args with numeric constraints."""
        field = FieldSchema(
            name="age",
            type=FieldType.INTEGER,
            min_value=0,
            max_value=150,
            multiple_of=1
        )
        args = field.get_pydantic_field_args()
        assert args["ge"] == 0
        assert args["le"] == 150
        assert args["multiple_of"] == 1
    
    def test_field_args_array_constraints(self):
        """Test field args with array constraints."""
        field = FieldSchema(
            name="tags",
            type=FieldType.ARRAY,
            min_items=1,
            max_items=10
        )
        args = field.get_pydantic_field_args()
        assert args["min_length"] == 1
        assert args["max_length"] == 10
    
    def test_field_args_with_example(self):
        """Test field args with example."""
        field = FieldSchema(
            name="email",
            type=FieldType.EMAIL,
            example="user@example.com"
        )
        args = field.get_pydantic_field_args()
        assert args["examples"] == ["user@example.com"]
    
    def test_field_args_deprecated(self):
        """Test field args for deprecated field."""
        field = FieldSchema(
            name="old_field",
            type=FieldType.STRING,
            deprecated=True
        )
        args = field.get_pydantic_field_args()
        assert args["deprecated"] is True
    
    def test_field_args_empty_for_simple_field(self):
        """Test that simple required field has minimal args."""
        field = FieldSchema(
            name="id",
            type=FieldType.INTEGER,
            required=True
        )
        args = field.get_pydantic_field_args()
        # Should not have default for required field
        assert "default" not in args


class TestValidatorsProperty:
    """Test validators property."""
    
    def test_validators_string_pattern(self):
        """Test validators for string with pattern."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            pattern=r"^[a-z]+$"
        )
        validators = field.validators
        assert validators is not None
        assert len(validators) == 1
        assert validators[0].type == "pattern"
        assert validators[0].value == r"^[a-z]+$"
    
    def test_validators_string_length(self):
        """Test validators for string with length constraints."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            min_length=3,
            max_length=20
        )
        validators = field.validators
        assert validators is not None
        assert len(validators) == 2
        validator_types = {v.type for v in validators}
        assert "min_length" in validator_types
        assert "max_length" in validator_types
    
    def test_validators_numeric_range(self):
        """Test validators for numeric with range."""
        field = FieldSchema(
            name="age",
            type=FieldType.INTEGER,
            min_value=0,
            max_value=150
        )
        validators = field.validators
        assert validators is not None
        assert len(validators) == 2
        validator_types = {v.type for v in validators}
        assert "minimum" in validator_types
        assert "maximum" in validator_types
    
    def test_validators_multiple_of(self):
        """Test validators for multiple_of constraint."""
        field = FieldSchema(
            name="quantity",
            type=FieldType.INTEGER,
            multiple_of=5
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "multiple_of" and v.value == 5 for v in validators)
    
    def test_validators_array_constraints(self):
        """Test validators for array constraints."""
        field = FieldSchema(
            name="tags",
            type=FieldType.ARRAY,
            min_items=1,
            max_items=10,
            unique_items=True
        )
        validators = field.validators
        assert validators is not None
        validator_types = {v.type for v in validators}
        assert "min_items" in validator_types
        assert "max_items" in validator_types
        assert "unique_items" in validator_types
    
    def test_validators_enum(self):
        """Test validators for enum values."""
        field = FieldSchema(
            name="status",
            type=FieldType.STRING,
            enum_values=["active", "inactive", "pending"]
        )
        validators = field.validators
        assert validators is not None
        enum_validator = next(v for v in validators if v.type == "enum")
        assert enum_validator.value == ["active", "inactive", "pending"]
    
    def test_validators_email_type(self):
        """Test validators for email type."""
        field = FieldSchema(
            name="email",
            type=FieldType.EMAIL
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "email" for v in validators)
    
    def test_validators_url_type(self):
        """Test validators for URL type."""
        field = FieldSchema(
            name="website",
            type=FieldType.URL
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "url" for v in validators)
    
    def test_validators_uuid_type(self):
        """Test validators for UUID type."""
        field = FieldSchema(
            name="id",
            type=FieldType.UUID
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "uuid" for v in validators)
    
    def test_validators_date_type(self):
        """Test validators for date type."""
        field = FieldSchema(
            name="birth_date",
            type=FieldType.DATE
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "date" for v in validators)
    
    def test_validators_datetime_type(self):
        """Test validators for datetime type."""
        field = FieldSchema(
            name="created_at",
            type=FieldType.DATETIME
        )
        validators = field.validators
        assert validators is not None
        assert any(v.type == "datetime" for v in validators)
    
    def test_validators_none_for_simple_field(self):
        """Test that simple field without constraints has no validators."""
        field = FieldSchema(
            name="name",
            type=FieldType.STRING
        )
        validators = field.validators
        assert validators is None
    
    def test_validators_combined_constraints(self):
        """Test validators with multiple combined constraints."""
        field = FieldSchema(
            name="username",
            type=FieldType.STRING,
            pattern=r"^[a-z0-9_]+$",
            min_length=3,
            max_length=20
        )
        validators = field.validators
        assert validators is not None
        assert len(validators) == 3
        validator_types = {v.type for v in validators}
        assert "pattern" in validator_types
        assert "min_length" in validator_types
        assert "max_length" in validator_types


class TestFieldSchemaEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_field_with_all_metadata(self):
        """Test field with all metadata fields."""
        field = FieldSchema(
            name="special_field",
            type=FieldType.STRING,
            required=True,
            description="A special field",
            default="default_value",
            example="example_value",
            deprecated=True,
            read_only=True,
            write_only=False
        )
        
        assert field.description == "A special field"
        assert field.default == "default_value"
        assert field.example == "example_value"
        assert field.deprecated is True
        assert field.read_only is True
        assert field.write_only is False
    
    def test_field_with_nested_array(self):
        """Test array field with nested object items."""
        field = FieldSchema(
            name="users",
            type=FieldType.ARRAY,
            item_type=FieldType.OBJECT,
            nested_model="User"
        )
        
        assert field.type == FieldType.ARRAY
        assert field.item_type == FieldType.OBJECT
        assert field.nested_model == "User"
    
    def test_field_additional_properties(self):
        """Test object field with additional properties."""
        field = FieldSchema(
            name="metadata",
            type=FieldType.OBJECT,
            additional_properties=True
        )
        
        assert field.additional_properties is True

# Made with Bob

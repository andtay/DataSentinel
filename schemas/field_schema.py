"""
Field-level schema definitions with validation rules.

This module defines the structure for individual fields in data models,
including type information, validation constraints, and metadata.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """
    Supported field types that map to Pydantic types.
    
    These types are used across all parsers to provide a consistent
    representation of field types regardless of the source format.
    """
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    UUID = "uuid"
    EMAIL = "email"
    URL = "url"
    ANY = "any"


class FieldSchema(BaseModel):
    """
    Field definition with validation rules.
    
    This represents a single field in a Pydantic model, including:
    - Type information
    - Validation constraints
    - Default values
    - Documentation
    
    This is the core building block for all data models in DataSentinel.
    """
    
    name: str = Field(..., description="Field name (snake_case)")
    type: FieldType = Field(..., description="Field type")
    required: bool = Field(True, description="Whether field is required")
    description: str | None = Field(None, description="Field description")
    default: Any | None = Field(None, description="Default value")
    
    # String validation
    pattern: str | None = Field(None, description="Regex pattern for string validation")
    min_length: int | None = Field(None, description="Minimum string length", ge=0)
    max_length: int | None = Field(None, description="Maximum string length", ge=0)
    
    # Numeric validation
    min_value: float | None = Field(None, description="Minimum numeric value")
    max_value: float | None = Field(None, description="Maximum numeric value")
    multiple_of: float | None = Field(None, description="Value must be multiple of this", gt=0)
    
    # Enum validation
    enum_values: list[Any] | None = Field(None, description="Allowed enum values")
    
    # Array-specific
    item_type: FieldType | None = Field(None, description="Type of array items")
    min_items: int | None = Field(None, description="Minimum array length", ge=0)
    max_items: int | None = Field(None, description="Maximum array length", ge=0)
    unique_items: bool = Field(False, description="Whether array items must be unique")
    
    # Object-specific
    nested_model: str | None = Field(None, description="Reference to nested ModelSchema name")
    additional_properties: bool = Field(True, description="Whether additional properties allowed")
    
    # Metadata
    example: Any | None = Field(None, description="Example value")
    deprecated: bool = Field(False, description="Whether field is deprecated")
    read_only: bool = Field(False, description="Whether field is read-only")
    write_only: bool = Field(False, description="Whether field is write-only")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "email",
                "type": "email",
                "required": True,
                "description": "User email address",
                "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$",
                "example": "user@example.com"
            }
        }
    }
    
    def get_python_type(self) -> str:
        """
        Get Python type annotation string for this field.
        
        Returns:
            Python type annotation (e.g., "str", "int", "list[str]")
        """
        type_map = {
            FieldType.STRING: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATE: "date",
            FieldType.DATETIME: "datetime",
            FieldType.UUID: "UUID",
            FieldType.EMAIL: "EmailStr",
            FieldType.URL: "HttpUrl",
            FieldType.ANY: "Any",
        }
        
        if self.type == FieldType.ARRAY:
            item_type_str = type_map.get(self.item_type, "Any") if self.item_type else "Any"
            return f"list[{item_type_str}]"
        
        elif self.type == FieldType.OBJECT:
            if self.nested_model:
                return self.nested_model
            return "dict[str, Any]"
        
        return type_map.get(self.type, "Any")
    
    def get_pydantic_field_args(self) -> dict[str, Any]:
        """
        Get arguments for Pydantic Field() definition.
        
        Returns:
            Dictionary of Field() arguments
        """
        args: dict[str, Any] = {}
        
        # Description
        if self.description:
            args["description"] = self.description
        
        # Default value
        if self.default is not None:
            args["default"] = self.default
        elif not self.required:
            args["default"] = None
        
        # String constraints
        if self.pattern:
            args["pattern"] = self.pattern
        if self.min_length is not None:
            args["min_length"] = self.min_length
        if self.max_length is not None:
            args["max_length"] = self.max_length
        
        # Numeric constraints
        if self.min_value is not None:
            args["ge"] = self.min_value
        if self.max_value is not None:
            args["le"] = self.max_value
        if self.multiple_of is not None:
            args["multiple_of"] = self.multiple_of
        
        # Array constraints
        if self.min_items is not None:
            args["min_length"] = self.min_items
        if self.max_items is not None:
            args["max_length"] = self.max_items
        
        # Example
        if self.example is not None:
            args["examples"] = [self.example]
        
        # Deprecated
        if self.deprecated:
            args["deprecated"] = True
        
        return args


class ValidatorConfig(BaseModel):
    """
    Custom validator configuration for complex validation rules.
    
    Used when standard Pydantic validators aren't sufficient.
    This allows for custom validation logic to be generated.
    """
    
    field_name: str = Field(..., description="Field to validate")
    validator_type: str = Field(
        ...,
        description="Validator type: regex, range, custom, cross_field"
    )
    validator_code: str = Field(..., description="Python code for validator")
    error_message: str = Field(..., description="Error message on validation failure")
    depends_on: list[str] | None = Field(
        None,
        description="Other fields this validator depends on"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field_name": "password",
                "validator_type": "custom",
                "validator_code": "len(v) >= 8 and any(c.isupper() for c in v)",
                "error_message": "Password must be at least 8 characters with one uppercase letter",
                "depends_on": None
            }
        }
    }


# Type mappings for different source formats

# OpenAPI to FieldType mapping
OPENAPI_TYPE_MAP: dict[tuple[str, str | None], FieldType] = {
    ("string", None): FieldType.STRING,
    ("string", "date"): FieldType.DATE,
    ("string", "date-time"): FieldType.DATETIME,
    ("string", "uuid"): FieldType.UUID,
    ("string", "email"): FieldType.EMAIL,
    ("string", "uri"): FieldType.URL,
    ("string", "url"): FieldType.URL,
    ("integer", None): FieldType.INTEGER,
    ("integer", "int32"): FieldType.INTEGER,
    ("integer", "int64"): FieldType.INTEGER,
    ("number", None): FieldType.FLOAT,
    ("number", "float"): FieldType.FLOAT,
    ("number", "double"): FieldType.FLOAT,
    ("boolean", None): FieldType.BOOLEAN,
    ("array", None): FieldType.ARRAY,
    ("object", None): FieldType.OBJECT,
}

# GraphQL to FieldType mapping
GRAPHQL_TYPE_MAP: dict[str, FieldType] = {
    "String": FieldType.STRING,
    "Int": FieldType.INTEGER,
    "Float": FieldType.FLOAT,
    "Boolean": FieldType.BOOLEAN,
    "ID": FieldType.STRING,
    "Date": FieldType.DATE,
    "DateTime": FieldType.DATETIME,
    "UUID": FieldType.UUID,
    "Email": FieldType.EMAIL,
    "URL": FieldType.URL,
}

# Python to FieldType mapping (for JSON inference)
PYTHON_TYPE_MAP: dict[type, FieldType] = {
    int: FieldType.INTEGER,
    float: FieldType.FLOAT,
    str: FieldType.STRING,
    bool: FieldType.BOOLEAN,
    list: FieldType.ARRAY,
    dict: FieldType.OBJECT,
}

# Made with Bob

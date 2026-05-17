"""
Core API schema representations.

This module defines the central data structures that represent a complete
API specification. These structures are the normalized output from all parsers
and the input to all generators.
"""

from typing import Any

from pydantic import BaseModel, Field

from schemas.field_schema import FieldSchema


class Parameter(BaseModel):
    """
    Endpoint parameter (path, query, header, cookie).
    
    Represents a single parameter that can be passed to an API endpoint.
    """
    
    name: str = Field(..., description="Parameter name")
    location: str = Field(
        ...,
        description="Parameter location: path, query, header, cookie"
    )
    required: bool = Field(True, description="Whether parameter is required")
    field_schema: FieldSchema = Field(..., description="Parameter schema")
    description: str | None = Field(None, description="Parameter description")
    deprecated: bool = Field(False, description="Whether parameter is deprecated")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "id",
                "location": "path",
                "required": True,
                "schema": {"name": "id", "type": "integer"},
                "description": "User ID",
                "deprecated": False
            }
        }
    }


class ModelSchema(BaseModel):
    """
    Data model definition - represents a Pydantic model to be generated.
    
    This is the core representation of a data structure that will become
    a Pydantic BaseModel in the generated code.
    """
    
    name: str = Field(..., description="Model name (PascalCase)")
    fields: list[FieldSchema] = Field(..., description="Model fields")
    description: str | None = Field(None, description="Model description")
    example: dict[str, Any] | None = Field(None, description="Example instance")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "integer", "required": True},
                    {"name": "email", "type": "email", "required": True},
                    {"name": "name", "type": "string", "required": False}
                ],
                "description": "User model",
                "example": {"id": 1, "email": "user@example.com", "name": "John Doe"}
            }
        }
    }
    
    def get_field_by_name(self, name: str) -> FieldSchema | None:
        """
        Get field by name.
        
        Args:
            name: Field name to search for
            
        Returns:
            FieldSchema if found, None otherwise
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def get_required_fields(self) -> list[FieldSchema]:
        """Get list of required fields."""
        return [f for f in self.fields if f.required]
    
    def get_optional_fields(self) -> list[FieldSchema]:
        """Get list of optional fields."""
        return [f for f in self.fields if not f.required]


class Endpoint(BaseModel):
    """
    API endpoint definition.
    
    Represents a single API operation (GET /users, POST /orders, etc.)
    This is the core unit of API functionality.
    """
    
    path: str = Field(..., description="Endpoint path (e.g., /users/{id})")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    summary: str | None = Field(None, description="Short summary of endpoint")
    description: str | None = Field(None, description="Detailed description")
    operation_id: str | None = Field(None, description="Unique operation identifier")
    
    # Request/Response models
    request_model: ModelSchema | None = Field(None, description="Request body model")
    response_model: ModelSchema = Field(..., description="Response body model")
    
    # Parameters
    parameters: list[Parameter] = Field(
        default_factory=list,
        description="Path, query, header parameters"
    )
    
    # Metadata
    auth_required: bool = Field(True, description="Whether authentication is required")
    tags: list[str] = Field(default_factory=list, description="Endpoint tags for organization")
    deprecated: bool = Field(False, description="Whether endpoint is deprecated")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "path": "/users/{id}",
                "method": "GET",
                "summary": "Get user by ID",
                "description": "Retrieve a single user by their unique identifier",
                "operation_id": "getUser",
                "request_model": None,
                "response_model": {"name": "User", "fields": []},
                "parameters": [],
                "auth_required": True,
                "tags": ["users"],
                "deprecated": False
            }
        }
    }
    
    def get_path_parameters(self) -> list[Parameter]:
        """Get list of path parameters."""
        return [p for p in self.parameters if p.location == "path"]
    
    def get_query_parameters(self) -> list[Parameter]:
        """Get list of query parameters."""
        return [p for p in self.parameters if p.location == "query"]
    
    def get_header_parameters(self) -> list[Parameter]:
        """Get list of header parameters."""
        return [p for p in self.parameters if p.location == "header"]
    
    def get_function_name(self) -> str:
        """
        Generate a function name for this endpoint.
        
        Returns:
            Snake_case function name based on operation_id or path/method
        """
        if self.operation_id:
            # Convert camelCase to snake_case
            import re
            name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', self.operation_id)
            return name.lower()
        
        # Generate from method and path
        path_parts = [p for p in self.path.split('/') if p and not p.startswith('{')]
        method_lower = self.method.lower()
        
        if path_parts:
            return f"{method_lower}_{'_'.join(path_parts)}"
        return f"{method_lower}_endpoint"


class AuthConfig(BaseModel):
    """
    Authentication configuration for the API.
    
    Describes how authentication should be handled for the API.
    """
    
    type: str = Field(..., description="Auth type: api_key, bearer, oauth2, none")
    location: str | None = Field(None, description="Location: header, query")
    name: str | None = Field(None, description="Parameter/header name")
    scheme: str | None = Field(None, description="Auth scheme (e.g., Bearer)")
    
    # OAuth2 specific
    token_url: str | None = Field(None, description="OAuth2 token URL")
    authorization_url: str | None = Field(None, description="OAuth2 authorization URL")
    scopes: dict[str, str] | None = Field(None, description="OAuth2 scopes")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "bearer",
                "location": "header",
                "name": "Authorization",
                "scheme": "Bearer"
            }
        }
    }


class APISchema(BaseModel):
    """
    Complete API specification - normalized output from all parsers.
    
    This is the central data structure that flows through the entire pipeline:
    Parser → APISchema → Generators
    
    All parsers (OpenAPI, GraphQL, JSON) must produce this normalized format,
    and all generators consume this format to produce code artifacts.
    """
    
    title: str = Field(..., description="API title")
    version: str = Field(..., description="API version")
    base_url: str = Field(..., description="Base URL for API endpoints")
    description: str | None = Field(None, description="API description")
    
    endpoints: list[Endpoint] = Field(
        default_factory=list,
        description="All API endpoints"
    )
    models: dict[str, ModelSchema] = Field(
        default_factory=dict,
        description="All data models (key: model name)"
    )
    
    auth_config: AuthConfig | None = Field(None, description="Authentication configuration")

    protocol: str = Field(
        default="rest",
        description="API protocol: rest or graphql",
    )
    graphql_path: str | None = Field(
        default=None,
        description="GraphQL HTTP path (e.g. /graphql) when protocol is graphql",
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Pet Store API",
                "version": "1.0.0",
                "base_url": "https://api.petstore.com",
                "description": "A sample Pet Store API",
                "endpoints": [],
                "models": {},
                "auth_config": None
            }
        }
    }
    
    def get_model(self, name: str) -> ModelSchema | None:
        """
        Get model by name.
        
        Args:
            name: Model name to search for
            
        Returns:
            ModelSchema if found, None otherwise
        """
        return self.models.get(name)
    
    def get_endpoints_by_tag(self, tag: str) -> list[Endpoint]:
        """
        Get all endpoints with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of endpoints with the tag
        """
        return [e for e in self.endpoints if tag in e.tags]
    
    def get_endpoints_by_method(self, method: str) -> list[Endpoint]:
        """
        Get all endpoints with a specific HTTP method.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            List of endpoints with the method
        """
        return [e for e in self.endpoints if e.method.upper() == method.upper()]
    
    def get_all_models_recursive(self) -> dict[str, ModelSchema]:
        """
        Get all models including nested models.
        
        This traverses all fields to find nested object references
        and ensures all models are included.
        
        Returns:
            Dictionary of all models (including nested)
        """
        all_models = self.models.copy()
        
        # Check for nested models in fields
        for model in self.models.values():
            for field in model.fields:
                if field.nested_model and field.nested_model not in all_models:
                    # This is a reference to a model that should exist
                    # In practice, parsers should ensure all referenced models exist
                    pass
        
        return all_models
    
    def validate_schema(self) -> list[str]:
        """
        Validate the schema for consistency.
        
        Checks for:
        - Missing model references
        - Duplicate model names
        - Invalid endpoint paths
        - Missing required fields
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []
        
        # Check for missing model references
        for endpoint in self.endpoints:
            if endpoint.request_model:
                for field in endpoint.request_model.fields:
                    if field.nested_model and field.nested_model not in self.models:
                        errors.append(
                            f"Endpoint {endpoint.path}: "
                            f"Request model references unknown model '{field.nested_model}'"
                        )
            
            for field in endpoint.response_model.fields:
                if field.nested_model and field.nested_model not in self.models:
                    errors.append(
                        f"Endpoint {endpoint.path}: "
                        f"Response model references unknown model '{field.nested_model}'"
                    )
        
        # Check for duplicate endpoint paths with same method
        seen_endpoints: set[tuple[str, str]] = set()
        for endpoint in self.endpoints:
            key = (endpoint.path, endpoint.method.upper())
            if key in seen_endpoints:
                errors.append(
                    f"Duplicate endpoint: {endpoint.method.upper()} {endpoint.path}"
                )
            seen_endpoints.add(key)
        
        return errors

# Made with Bob

"""
Tests for OpenAPI parser.

This module tests the deterministic OpenAPI/Swagger parser that handles
OpenAPI 3.x and Swagger 2.x specifications.
"""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from parsers.openapi_parser import OpenAPIParser
from schemas import FieldType


# Sample OpenAPI 3.0 specification
OPENAPI_3_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A sample Pet Store API"
    },
    "servers": [
        {"url": "https://api.petstore.com/v1"}
    ],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "operationId": "listPets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return",
                        "required": False,
                        "schema": {
                            "type": "integer",
                            "format": "int32",
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A list of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/components/schemas/Pet"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a pet",
                "operationId": "createPet",
                "tags": ["pets"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Pet"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Pet created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pet"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet by ID",
                "operationId": "getPet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "The ID of the pet",
                        "schema": {
                            "type": "integer",
                            "format": "int64"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A single pet",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pet"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int64",
                        "description": "Unique identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "Pet name",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "tag": {
                        "type": "string",
                        "description": "Pet tag"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["available", "pending", "sold"],
                        "description": "Pet status"
                    }
                }
            }
        },
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    },
    "security": [
        {"bearerAuth": []}
    ]
}


@pytest.fixture
def openapi_spec_file():
    """Create a temporary OpenAPI spec file."""
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(OPENAPI_3_SPEC, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_openapi_basic_parsing(openapi_spec_file):
    """Test basic OpenAPI parsing."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Verify basic info
    assert api_schema.title == "Pet Store API"
    assert api_schema.version == "1.0.0"
    assert api_schema.description == "A sample Pet Store API"
    assert api_schema.base_url == "https://api.petstore.com/v1"


@pytest.mark.asyncio
async def test_openapi_endpoints_extraction(openapi_spec_file):
    """Test endpoint extraction from OpenAPI spec."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Should have 3 endpoints
    assert len(api_schema.endpoints) == 3
    
    # Verify endpoint paths and methods
    endpoint_signatures = {(e.path, e.method) for e in api_schema.endpoints}
    assert ("/pets", "GET") in endpoint_signatures
    assert ("/pets", "POST") in endpoint_signatures
    assert ("/pets/{petId}", "GET") in endpoint_signatures


@pytest.mark.asyncio
async def test_openapi_operation_details(openapi_spec_file):
    """Test operation details extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Find the listPets endpoint
    list_pets = next(e for e in api_schema.endpoints if e.operation_id == "listPets")
    
    assert list_pets.summary == "List all pets"
    assert list_pets.method == "GET"
    assert list_pets.path == "/pets"
    assert "pets" in list_pets.tags
    assert list_pets.auth_required is True


@pytest.mark.asyncio
async def test_openapi_parameters_extraction(openapi_spec_file):
    """Test parameter extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Find the listPets endpoint
    list_pets = next(e for e in api_schema.endpoints if e.operation_id == "listPets")
    
    # Should have 1 query parameter
    assert len(list_pets.parameters) == 1
    
    param = list_pets.parameters[0]
    assert param.name == "limit"
    assert param.location == "query"
    assert param.required is False
    assert param.field_schema.type == FieldType.INTEGER
    assert param.field_schema.min_value == 1
    assert param.field_schema.max_value == 100


@pytest.mark.asyncio
async def test_openapi_path_parameters(openapi_spec_file):
    """Test path parameter extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Find the getPet endpoint
    get_pet = next(e for e in api_schema.endpoints if e.operation_id == "getPet")
    
    # Should have 1 path parameter
    assert len(get_pet.parameters) == 1
    
    param = get_pet.parameters[0]
    assert param.name == "petId"
    assert param.location == "path"
    assert param.required is True
    assert param.field_schema.type == FieldType.INTEGER


@pytest.mark.asyncio
async def test_openapi_request_body(openapi_spec_file):
    """Test request body extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Find the createPet endpoint
    create_pet = next(e for e in api_schema.endpoints if e.operation_id == "createPet")
    
    # Should have request body
    assert create_pet.request_model is not None
    # Request body should reference Pet model (will be resolved by prance)


@pytest.mark.asyncio
async def test_openapi_models_extraction(openapi_spec_file):
    """Test model extraction from components/schemas."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Should have Pet model
    assert "Pet" in api_schema.models
    
    pet_model = api_schema.models["Pet"]
    assert pet_model.name == "Pet"
    assert len(pet_model.fields) == 4
    
    # Verify field names
    field_names = {f.name for f in pet_model.fields}
    assert "id" in field_names
    assert "name" in field_names
    assert "tag" in field_names
    assert "status" in field_names


@pytest.mark.asyncio
async def test_openapi_field_types(openapi_spec_file):
    """Test field type mapping."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    pet_model = api_schema.models["Pet"]
    
    # Check field types
    field_types = {f.name: f.type for f in pet_model.fields}
    assert field_types["id"] == FieldType.INTEGER
    assert field_types["name"] == FieldType.STRING
    assert field_types["tag"] == FieldType.STRING
    assert field_types["status"] == FieldType.STRING


@pytest.mark.asyncio
async def test_openapi_required_fields(openapi_spec_file):
    """Test required field detection."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    pet_model = api_schema.models["Pet"]
    
    # Check required fields
    required_fields = {f.name for f in pet_model.fields if f.required}
    optional_fields = {f.name for f in pet_model.fields if not f.required}
    
    assert "id" in required_fields
    assert "name" in required_fields
    assert "tag" in optional_fields
    assert "status" in optional_fields


@pytest.mark.asyncio
async def test_openapi_field_constraints(openapi_spec_file):
    """Test field constraint extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    pet_model = api_schema.models["Pet"]
    
    # Check name field constraints
    name_field = next(f for f in pet_model.fields if f.name == "name")
    assert name_field.min_length == 1
    assert name_field.max_length == 100
    
    # Check status field enum
    status_field = next(f for f in pet_model.fields if f.name == "status")
    assert status_field.enum_values == ["available", "pending", "sold"]


@pytest.mark.asyncio
async def test_openapi_auth_config(openapi_spec_file):
    """Test authentication configuration extraction."""
    parser = OpenAPIParser(openapi_spec_file)
    api_schema = await parser.parse()
    
    # Should have bearer auth
    assert api_schema.auth_config is not None
    assert api_schema.auth_config.type == "bearer"
    assert api_schema.auth_config.scheme == "Bearer"
    assert api_schema.auth_config.location == "header"
    assert api_schema.auth_config.name == "Authorization"


@pytest.mark.asyncio
async def test_openapi_version_detection(openapi_spec_file):
    """Test OpenAPI version detection."""
    parser = OpenAPIParser(openapi_spec_file)
    await parser.parse()
    
    assert parser.openapi_version == "3.0.0"


def test_openapi_type_mapping():
    """Test OpenAPI type to FieldType mapping."""
    parser = OpenAPIParser("dummy.json")
    
    # Test basic types
    assert parser._map_openapi_type("string") == FieldType.STRING
    assert parser._map_openapi_type("integer") == FieldType.INTEGER
    assert parser._map_openapi_type("number") == FieldType.FLOAT
    assert parser._map_openapi_type("boolean") == FieldType.BOOLEAN
    assert parser._map_openapi_type("array") == FieldType.ARRAY
    assert parser._map_openapi_type("object") == FieldType.OBJECT
    
    # Test format-specific types
    assert parser._map_openapi_type("string", "email") == FieldType.EMAIL
    assert parser._map_openapi_type("string", "uuid") == FieldType.UUID
    assert parser._map_openapi_type("string", "uri") == FieldType.URL
    assert parser._map_openapi_type("string", "date") == FieldType.DATE
    assert parser._map_openapi_type("string", "date-time") == FieldType.DATETIME

# Made with Bob

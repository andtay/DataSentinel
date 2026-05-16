"""
Tests for GraphQL parser.

This module tests the GraphQL introspection-based parser that extracts
schema information from GraphQL APIs.
"""

import pytest
from unittest.mock import AsyncMock, patch

from parsers.graphql_parser import GraphQLParser
from schemas import FieldType


# Sample GraphQL introspection response
SAMPLE_INTROSPECTION = {
    "__schema": {
        "queryType": {"name": "Query"},
        "mutationType": {"name": "Mutation"},
        "subscriptionType": None,
        "types": [
            {
                "kind": "OBJECT",
                "name": "Query",
                "description": "Root query type",
                "fields": [
                    {
                        "name": "user",
                        "description": "Get user by ID",
                        "args": [
                            {
                                "name": "id",
                                "description": "User ID",
                                "type": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "SCALAR",
                                        "name": "ID",
                                        "ofType": None
                                    }
                                },
                                "defaultValue": None
                            }
                        ],
                        "type": {
                            "kind": "OBJECT",
                            "name": "User",
                            "ofType": None
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    },
                    {
                        "name": "users",
                        "description": "List all users",
                        "args": [],
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "OBJECT",
                                "name": "User",
                                "ofType": None
                            }
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    }
                ],
                "inputFields": None,
                "interfaces": [],
                "enumValues": None,
                "possibleTypes": None
            },
            {
                "kind": "OBJECT",
                "name": "Mutation",
                "description": "Root mutation type",
                "fields": [
                    {
                        "name": "createUser",
                        "description": "Create a new user",
                        "args": [
                            {
                                "name": "input",
                                "description": "User input",
                                "type": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "INPUT_OBJECT",
                                        "name": "CreateUserInput",
                                        "ofType": None
                                    }
                                },
                                "defaultValue": None
                            }
                        ],
                        "type": {
                            "kind": "OBJECT",
                            "name": "User",
                            "ofType": None
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    }
                ],
                "inputFields": None,
                "interfaces": [],
                "enumValues": None,
                "possibleTypes": None
            },
            {
                "kind": "OBJECT",
                "name": "User",
                "description": "User type",
                "fields": [
                    {
                        "name": "id",
                        "description": "User ID",
                        "args": [],
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "ID",
                                "ofType": None
                            }
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    },
                    {
                        "name": "email",
                        "description": "User email",
                        "args": [],
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None
                            }
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    },
                    {
                        "name": "name",
                        "description": "User name",
                        "args": [],
                        "type": {
                            "kind": "SCALAR",
                            "name": "String",
                            "ofType": None
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    },
                    {
                        "name": "age",
                        "description": "User age",
                        "args": [],
                        "type": {
                            "kind": "SCALAR",
                            "name": "Int",
                            "ofType": None
                        },
                        "isDeprecated": False,
                        "deprecationReason": None
                    }
                ],
                "inputFields": None,
                "interfaces": [],
                "enumValues": None,
                "possibleTypes": None
            },
            {
                "kind": "INPUT_OBJECT",
                "name": "CreateUserInput",
                "description": "Input for creating a user",
                "fields": None,
                "inputFields": [
                    {
                        "name": "email",
                        "description": "User email",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None
                            }
                        },
                        "defaultValue": None
                    },
                    {
                        "name": "name",
                        "description": "User name",
                        "type": {
                            "kind": "SCALAR",
                            "name": "String",
                            "ofType": None
                        },
                        "defaultValue": None
                    }
                ],
                "interfaces": None,
                "enumValues": None,
                "possibleTypes": None
            }
        ],
        "directives": []
    }
}


@pytest.fixture
def mock_introspection():
    """Mock GraphQL introspection response."""
    return {"data": SAMPLE_INTROSPECTION}


@pytest.mark.asyncio
async def test_graphql_basic_parsing(mock_introspection):
    """Test basic GraphQL parsing."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    # Mock the introspection query
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Verify basic info
        assert api_schema.title == "Query API"
        assert api_schema.version == "1.0.0"
        assert api_schema.base_url == "https://api.example.com/graphql"


@pytest.mark.asyncio
async def test_graphql_endpoints_extraction(mock_introspection):
    """Test endpoint extraction from queries and mutations."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Should have 2 queries + 1 mutation = 3 endpoints
        assert len(api_schema.endpoints) == 3
        
        # Verify endpoint paths
        endpoint_paths = {e.path for e in api_schema.endpoints}
        assert "/query/user" in endpoint_paths
        assert "/query/users" in endpoint_paths
        assert "/mutation/createUser" in endpoint_paths


@pytest.mark.asyncio
async def test_graphql_query_endpoint(mock_introspection):
    """Test query endpoint details."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Find the user query
        user_query = next(e for e in api_schema.endpoints if e.operation_id == "user")
        
        assert user_query.method == "GET"
        assert user_query.path == "/query/user"
        assert user_query.summary == "user"
        assert user_query.description == "Get user by ID"
        assert "query" in user_query.tags


@pytest.mark.asyncio
async def test_graphql_mutation_endpoint(mock_introspection):
    """Test mutation endpoint details."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Find the createUser mutation
        create_user = next(e for e in api_schema.endpoints if e.operation_id == "createUser")
        
        assert create_user.method == "POST"
        assert create_user.path == "/mutation/createUser"
        assert create_user.summary == "createUser"
        assert create_user.description == "Create a new user"
        assert "mutation" in create_user.tags


@pytest.mark.asyncio
async def test_graphql_parameters_extraction(mock_introspection):
    """Test parameter extraction from arguments."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Find the user query
        user_query = next(e for e in api_schema.endpoints if e.operation_id == "user")
        
        # Should have 1 parameter (id)
        assert len(user_query.parameters) == 1
        
        param = user_query.parameters[0]
        assert param.name == "id"
        assert param.location == "query"
        assert param.required is True
        assert param.description == "User ID"


@pytest.mark.asyncio
async def test_graphql_models_extraction(mock_introspection):
    """Test model extraction from types."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        # Should have User and CreateUserInput models
        assert "User" in api_schema.models
        assert "CreateUserInput" in api_schema.models


@pytest.mark.asyncio
async def test_graphql_model_fields(mock_introspection):
    """Test model field extraction."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        user_model = api_schema.models["User"]
        
        # Should have 4 fields
        assert len(user_model.fields) == 4
        
        # Verify field names
        field_names = {f.name for f in user_model.fields}
        assert "id" in field_names
        assert "email" in field_names
        assert "name" in field_names
        assert "age" in field_names


@pytest.mark.asyncio
async def test_graphql_field_types(mock_introspection):
    """Test field type mapping."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        user_model = api_schema.models["User"]
        
        # Check field types
        field_types = {f.name: f.type for f in user_model.fields}
        assert field_types["id"] == FieldType.STRING  # ID maps to STRING
        assert field_types["email"] == FieldType.STRING
        assert field_types["name"] == FieldType.STRING
        assert field_types["age"] == FieldType.INTEGER


@pytest.mark.asyncio
async def test_graphql_required_fields(mock_introspection):
    """Test required field detection."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        user_model = api_schema.models["User"]
        
        # Check required fields (NON_NULL types)
        required_fields = {f.name for f in user_model.fields if f.required}
        optional_fields = {f.name for f in user_model.fields if not f.required}
        
        assert "id" in required_fields
        assert "email" in required_fields
        assert "name" in optional_fields
        assert "age" in optional_fields


@pytest.mark.asyncio
async def test_graphql_input_object(mock_introspection):
    """Test input object parsing."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    with patch.object(parser, '_execute_introspection', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = SAMPLE_INTROSPECTION["__schema"]
        
        api_schema = await parser.parse()
        
        input_model = api_schema.models["CreateUserInput"]
        
        # Should have 2 fields
        assert len(input_model.fields) == 2
        
        # Verify field names
        field_names = {f.name for f in input_model.fields}
        assert "email" in field_names
        assert "name" in field_names


def test_graphql_type_mapping():
    """Test GraphQL type to FieldType mapping."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    # Test basic types
    assert parser._map_graphql_type("String") == FieldType.STRING
    assert parser._map_graphql_type("Int") == FieldType.INTEGER
    assert parser._map_graphql_type("Float") == FieldType.FLOAT
    assert parser._map_graphql_type("Boolean") == FieldType.BOOLEAN
    assert parser._map_graphql_type("ID") == FieldType.STRING
    
    # Test special types
    assert parser._map_graphql_type("Date") == FieldType.DATE
    assert parser._map_graphql_type("DateTime") == FieldType.DATETIME
    assert parser._map_graphql_type("UUID") == FieldType.UUID
    assert parser._map_graphql_type("Email") == FieldType.EMAIL
    assert parser._map_graphql_type("URL") == FieldType.URL


def test_graphql_type_unwrapping():
    """Test unwrapping of NON_NULL and LIST types."""
    parser = GraphQLParser("https://api.example.com/graphql")
    
    # Test NON_NULL unwrapping
    non_null_type = {
        "kind": "NON_NULL",
        "name": None,
        "ofType": {
            "kind": "SCALAR",
            "name": "String",
            "ofType": None
        }
    }
    unwrapped = parser._unwrap_type(non_null_type)
    assert unwrapped["kind"] == "SCALAR"
    assert unwrapped["name"] == "String"
    
    # Test LIST unwrapping
    list_type = {
        "kind": "LIST",
        "name": None,
        "ofType": {
            "kind": "SCALAR",
            "name": "Int",
            "ofType": None
        }
    }
    unwrapped = parser._unwrap_type(list_type)
    assert unwrapped["kind"] == "SCALAR"
    assert unwrapped["name"] == "Int"


@pytest.mark.asyncio
async def test_graphql_invalid_source():
    """Test error handling for invalid source."""
    parser = GraphQLParser("not-a-url")
    
    with pytest.raises(Exception):  # Should raise ParserError
        await parser.parse()

# Made with Bob

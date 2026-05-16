"""
Pytest configuration and shared fixtures for DataSentinel tests.

This module provides common fixtures used across unit and integration tests.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import pytest
from unittest.mock import Mock, AsyncMock

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test outputs.
    
    Yields:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="datasentinel_test_"))
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_json_data() -> Dict[str, Any]:
    """Sample JSON data for testing."""
    return {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "age": 25,
                "is_active": False,
                "created_at": "2024-02-20T14:45:00Z"
            }
        ]
    }


@pytest.fixture
def sample_openapi_spec() -> Dict[str, Any]:
    """Sample OpenAPI 3.0 specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "A test API for integration testing"
        },
        "servers": [
            {"url": "https://api.example.com/v1"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "operationId": "listUsers",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "operationId": "createUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreate"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/users/{user_id}": {
                "get": {
                    "summary": "Get user by ID",
                    "operationId": "getUser",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["id", "name", "email"],
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "User ID"
                        },
                        "name": {
                            "type": "string",
                            "description": "User's full name",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "User's email address"
                        },
                        "age": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 150,
                            "description": "User's age"
                        },
                        "is_active": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether the user is active"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Account creation timestamp"
                        }
                    }
                },
                "UserCreate": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "email": {
                            "type": "string",
                            "format": "email"
                        },
                        "age": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 150
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_graphql_schema() -> str:
    """Sample GraphQL schema for testing."""
    return """
    type User {
        id: ID!
        name: String!
        email: String!
        age: Int
        isActive: Boolean!
        createdAt: DateTime!
    }
    
    type Query {
        users: [User!]!
        user(id: ID!): User
    }
    
    type Mutation {
        createUser(name: String!, email: String!, age: Int): User!
        updateUser(id: ID!, name: String, email: String, age: Int): User!
        deleteUser(id: ID!): Boolean!
    }
    
    scalar DateTime
    """


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {"status": "ok"}
    mock.text = '{"status": "ok"}'
    mock.headers = {"content-type": "application/json"}
    return mock


@pytest.fixture
def mock_async_http_client():
    """Create a mock async HTTP client."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"status": "ok"})
    mock_response.text = '{"status": "ok"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


# Performance testing helpers
@pytest.fixture
def performance_threshold():
    """Performance thresholds for integration tests."""
    return {
        "parse_time": 5.0,  # seconds
        "generate_time": 10.0,  # seconds
        "total_time": 15.0,  # seconds
    }


# Test data files
@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Get the test fixtures directory."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    return fixtures_dir

# Made with Bob

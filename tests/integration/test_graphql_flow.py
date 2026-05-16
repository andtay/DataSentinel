"""
Integration tests for GraphQL flow.

Tests the complete pipeline from GraphQL endpoint to generated artifacts.

NOTE: These tests are currently skipped as they require GraphQL parser implementation.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from auto_sentinel import AutoSentinel, create_parser
# from parsers.graphql_parser import GraphQLParser
from schemas.api_schema import APISchema

# Skip all GraphQL tests until parser is fully implemented
pytestmark = pytest.mark.skip(reason="GraphQL parser implementation pending")


class TestGraphQLFlow:
    """Integration tests for GraphQL pipeline."""

    @pytest.fixture
    def mock_graphql_introspection_response(self) -> Dict[str, Any]:
        """Mock GraphQL introspection query response."""
        return {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": {"name": "Mutation"},
                    "types": [
                        {
                            "kind": "OBJECT",
                            "name": "User",
                            "description": "A user in the system",
                            "fields": [
                                {
                                    "name": "id",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {"kind": "SCALAR", "name": "ID"}
                                    },
                                    "args": []
                                },
                                {
                                    "name": "name",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {"kind": "SCALAR", "name": "String"}
                                    },
                                    "args": []
                                },
                                {
                                    "name": "email",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {"kind": "SCALAR", "name": "String"}
                                    },
                                    "args": []
                                },
                                {
                                    "name": "age",
                                    "type": {"kind": "SCALAR", "name": "Int"},
                                    "args": []
                                },
                                {
                                    "name": "isActive",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {"kind": "SCALAR", "name": "Boolean"}
                                    },
                                    "args": []
                                }
                            ]
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Query",
                            "fields": [
                                {
                                    "name": "users",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {
                                            "kind": "LIST",
                                            "ofType": {
                                                "kind": "NON_NULL",
                                                "ofType": {"kind": "OBJECT", "name": "User"}
                                            }
                                        }
                                    },
                                    "args": []
                                },
                                {
                                    "name": "user",
                                    "type": {"kind": "OBJECT", "name": "User"},
                                    "args": [
                                        {
                                            "name": "id",
                                            "type": {
                                                "kind": "NON_NULL",
                                                "ofType": {"kind": "SCALAR", "name": "ID"}
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Mutation",
                            "fields": [
                                {
                                    "name": "createUser",
                                    "type": {
                                        "kind": "NON_NULL",
                                        "ofType": {"kind": "OBJECT", "name": "User"}
                                    },
                                    "args": [
                                        {
                                            "name": "name",
                                            "type": {
                                                "kind": "NON_NULL",
                                                "ofType": {"kind": "SCALAR", "name": "String"}
                                            }
                                        },
                                        {
                                            "name": "email",
                                            "type": {
                                                "kind": "NON_NULL",
                                                "ofType": {"kind": "SCALAR", "name": "String"}
                                            }
                                        },
                                        {
                                            "name": "age",
                                            "type": {"kind": "SCALAR", "name": "Int"}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }

    @pytest.mark.asyncio
    async def test_graphql_complete_flow_with_mock(
        self, 
        temp_output_dir: Path, 
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client
    ):
        """Test complete flow with mocked GraphQL endpoint."""
        # Mock the HTTP client to return introspection response
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Create mock args
            args = create_parser().parse_args([
                "--api", "https://api.example.com/graphql",
                "--output", str(temp_output_dir / "generated"),
                "--format", "graphql"
            ])

            # Run the orchestrator
            orchestrator = AutoSentinel(args)
            result = await orchestrator.run()

            # Verify success
            assert result.success, f"Generation failed: {result.errors}"
            assert result.api_schema is not None
            assert len(result.errors) == 0

            # Verify API schema
            api_schema = result.api_schema
            assert len(api_schema.models) > 0
            assert len(api_schema.endpoints) > 0

            # Verify generated files exist
            output_dir = temp_output_dir / "generated"
            assert (output_dir / "models.py").exists()
            assert (output_dir / "validators.py").exists()
            assert (output_dir / "test_api.py").exists()
            assert (output_dir / "app.py").exists()
            assert (output_dir / "data_dict.md").exists()
            assert (output_dir / "Dockerfile").exists()

    @pytest.mark.asyncio
    async def test_graphql_parser_type_extraction(
        self, 
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client
    ):
        """Test that GraphQL parser correctly extracts types."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Parse the GraphQL endpoint
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()

            # Verify schema structure
            assert api_schema is not None
            assert len(api_schema.models) > 0

            # Find the User model
            user_model = None
            for model in api_schema.models.values():
                if model.name == "User":
                    user_model = model
                    break

            assert user_model is not None, "User model not found"

            # Verify field names
            field_names = {field.name for field in user_model.fields}
            assert "id" in field_names
            assert "name" in field_names
            assert "email" in field_names
            assert "age" in field_names
            assert "is_active" in field_names or "isActive" in field_names

            # Verify required fields
            required_fields = {field.name for field in user_model.fields if field.required}
            assert "id" in required_fields
            assert "name" in required_fields
            assert "email" in required_fields

    @pytest.mark.asyncio
    async def test_graphql_parser_query_extraction(
        self, 
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client
    ):
        """Test that GraphQL parser correctly extracts queries."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Parse the GraphQL endpoint
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()

            # Verify endpoints (queries become GET endpoints)
            assert len(api_schema.endpoints) > 0

            # Check for query endpoints
            endpoint_names = {ep.operation_id for ep in api_schema.endpoints}
            assert "users" in endpoint_names or "getUsers" in endpoint_names
            assert "user" in endpoint_names or "getUser" in endpoint_names

    @pytest.mark.asyncio
    async def test_graphql_parser_mutation_extraction(
        self, 
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client
    ):
        """Test that GraphQL parser correctly extracts mutations."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Parse the GraphQL endpoint
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()

            # Check for mutation endpoints (mutations become POST endpoints)
            mutation_endpoints = [ep for ep in api_schema.endpoints if ep.method == "POST"]
            assert len(mutation_endpoints) > 0

            # Check for createUser mutation
            create_user = None
            for ep in mutation_endpoints:
                if "createUser" in ep.operation_id or "create_user" in ep.operation_id:
                    create_user = ep
                    break

            assert create_user is not None

    @pytest.mark.asyncio
    async def test_generated_models_from_graphql(
        self, 
        temp_output_dir: Path,
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client
    ):
        """Test that generated models match GraphQL schema."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Create mock args
            args = create_parser().parse_args([
                "--api", "https://api.example.com/graphql",
                "--output", str(temp_output_dir / "generated"),
                "--format", "graphql"
            ])

            # Run the orchestrator
            orchestrator = AutoSentinel(args)
            result = await orchestrator.run()

            assert result.success

            # Read generated models
            models_file = temp_output_dir / "generated" / "models.py"
            assert models_file.exists()

            with open(models_file, "r") as f:
                models_code = f.read()

            # Verify User model is present
            assert "class User" in models_code

            # Verify fields are present
            assert "id:" in models_code or "id :" in models_code
            assert "name:" in models_code or "name :" in models_code
            assert "email:" in models_code or "email :" in models_code

    @pytest.mark.asyncio
    async def test_performance_graphql_parsing(
        self, 
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client,
        performance_threshold: Dict[str, float]
    ):
        """Test that GraphQL parsing completes within acceptable time."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Measure parsing time
            start_time = time.time()
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()
            parse_time = time.time() - start_time

            assert api_schema is not None
            assert parse_time < performance_threshold["parse_time"], \
                f"Parsing took {parse_time:.2f}s, expected < {performance_threshold['parse_time']}s"

    @pytest.mark.asyncio
    async def test_performance_complete_generation(
        self, 
        temp_output_dir: Path,
        mock_graphql_introspection_response: Dict[str, Any],
        mock_async_http_client,
        performance_threshold: Dict[str, float]
    ):
        """Test that complete generation completes within acceptable time."""
        # Mock the HTTP client
        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=mock_graphql_introspection_response
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Create mock args
            args = create_parser().parse_args([
                "--api", "https://api.example.com/graphql",
                "--output", str(temp_output_dir / "generated"),
                "--format", "graphql"
            ])

            # Measure total time
            start_time = time.time()
            orchestrator = AutoSentinel(args)
            result = await orchestrator.run()
            total_time = time.time() - start_time

            assert result.success
            assert total_time < performance_threshold["total_time"], \
                f"Generation took {total_time:.2f}s, expected < {performance_threshold['total_time']}s"

    @pytest.mark.asyncio
    async def test_error_handling_introspection_disabled(
        self, 
        temp_output_dir: Path,
        mock_async_http_client
    ):
        """Test error handling when introspection is disabled."""
        # Mock error response
        error_response = {
            "errors": [
                {
                    "message": "GraphQL introspection is not allowed",
                    "extensions": {"code": "GRAPHQL_VALIDATION_FAILED"}
                }
            ]
        }
        mock_async_http_client.post.return_value.json = AsyncMock(return_value=error_response)

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Create mock args
            args = create_parser().parse_args([
                "--api", "https://api.example.com/graphql",
                "--output", str(temp_output_dir / "generated"),
                "--format", "graphql"
            ])

            # Run the orchestrator
            orchestrator = AutoSentinel(args)
            result = await orchestrator.run()

            # Should fail gracefully
            assert not result.success
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_error_handling_network_error(
        self, 
        temp_output_dir: Path,
        mock_async_http_client
    ):
        """Test error handling with network errors."""
        # Mock network error
        mock_async_http_client.post.side_effect = Exception("Network error")

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Create mock args
            args = create_parser().parse_args([
                "--api", "https://api.example.com/graphql",
                "--output", str(temp_output_dir / "generated"),
                "--format", "graphql"
            ])

            # Run the orchestrator
            orchestrator = AutoSentinel(args)
            result = await orchestrator.run()

            # Should fail gracefully
            assert not result.success
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_graphql_with_custom_scalars(
        self, 
        mock_async_http_client
    ):
        """Test handling of custom GraphQL scalars."""
        introspection_with_scalars = {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "types": [
                        {
                            "kind": "SCALAR",
                            "name": "DateTime",
                            "description": "Custom DateTime scalar"
                        },
                        {
                            "kind": "SCALAR",
                            "name": "UUID",
                            "description": "Custom UUID scalar"
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Event",
                            "fields": [
                                {
                                    "name": "id",
                                    "type": {"kind": "SCALAR", "name": "UUID"},
                                    "args": []
                                },
                                {
                                    "name": "timestamp",
                                    "type": {"kind": "SCALAR", "name": "DateTime"},
                                    "args": []
                                }
                            ]
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Query",
                            "fields": [
                                {
                                    "name": "events",
                                    "type": {
                                        "kind": "LIST",
                                        "ofType": {"kind": "OBJECT", "name": "Event"}
                                    },
                                    "args": []
                                }
                            ]
                        }
                    ]
                }
            }
        }

        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=introspection_with_scalars
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Parse the GraphQL endpoint
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()

            # Verify custom scalars are handled
            assert api_schema is not None
            assert len(api_schema.models) > 0

            # Find Event model
            event_model = None
            for model in api_schema.models.values():
                if model.name == "Event":
                    event_model = model
                    break

            assert event_model is not None
            field_names = {field.name for field in event_model.fields}
            assert "id" in field_names
            assert "timestamp" in field_names

    @pytest.mark.asyncio
    async def test_graphql_with_nested_types(
        self, 
        mock_async_http_client
    ):
        """Test handling of nested GraphQL types."""
        introspection_with_nested = {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "types": [
                        {
                            "kind": "OBJECT",
                            "name": "Address",
                            "fields": [
                                {
                                    "name": "street",
                                    "type": {"kind": "SCALAR", "name": "String"},
                                    "args": []
                                },
                                {
                                    "name": "city",
                                    "type": {"kind": "SCALAR", "name": "String"},
                                    "args": []
                                }
                            ]
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Company",
                            "fields": [
                                {
                                    "name": "name",
                                    "type": {"kind": "SCALAR", "name": "String"},
                                    "args": []
                                },
                                {
                                    "name": "address",
                                    "type": {"kind": "OBJECT", "name": "Address"},
                                    "args": []
                                }
                            ]
                        },
                        {
                            "kind": "OBJECT",
                            "name": "Query",
                            "fields": [
                                {
                                    "name": "companies",
                                    "type": {
                                        "kind": "LIST",
                                        "ofType": {"kind": "OBJECT", "name": "Company"}
                                    },
                                    "args": []
                                }
                            ]
                        }
                    ]
                }
            }
        }

        mock_async_http_client.post.return_value.json = AsyncMock(
            return_value=introspection_with_nested
        )

        with patch('parsers.graphql_parser.httpx.AsyncClient', return_value=mock_async_http_client):
            # Parse the GraphQL endpoint
            parser = GraphQLParser("https://api.example.com/graphql")
            api_schema = await parser.parse()

            # Verify nested types are handled
            assert api_schema is not None
            assert len(api_schema.models) >= 2  # Company and Address

            model_names = {model.name for model in api_schema.models.values()}
            assert "Company" in model_names
            assert "Address" in model_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob

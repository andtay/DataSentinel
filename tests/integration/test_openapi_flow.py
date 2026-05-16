"""
Integration tests for OpenAPI/Swagger flow.

Tests the complete pipeline from OpenAPI specification to generated artifacts.
"""

import asyncio
import json
import yaml
import time
from pathlib import Path
from typing import Dict, Any
import pytest

from auto_sentinel import AutoSentinel, create_parser
from parsers.openapi_parser import OpenAPIParser
from schemas.api_schema import APISchema


class TestOpenAPIFlow:
    """Integration tests for OpenAPI/Swagger pipeline."""

    @pytest.mark.asyncio
    async def test_openapi_yaml_complete_flow(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test complete flow with OpenAPI YAML file."""
        # Create a temporary OpenAPI YAML file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
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
        assert api_schema.title == "Test API"
        assert api_schema.version == "1.0.0"
        assert len(api_schema.models) >= 2  # User and UserCreate
        assert len(api_schema.endpoints) >= 3  # GET /users, POST /users, GET /users/{id}

        # Verify generated files exist
        output_dir = temp_output_dir / "generated"
        assert (output_dir / "models.py").exists()
        assert (output_dir / "validators.py").exists()
        assert (output_dir / "test_api.py").exists()
        assert (output_dir / "app.py").exists()
        assert (output_dir / "data_dict.md").exists()
        assert (output_dir / "Dockerfile").exists()
        assert (output_dir / ".dockerignore").exists()

    @pytest.mark.asyncio
    async def test_openapi_json_complete_flow(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test complete flow with OpenAPI JSON file."""
        # Create a temporary OpenAPI JSON file
        openapi_file = temp_output_dir / "openapi.json"
        with open(openapi_file, "w") as f:
            json.dump(sample_openapi_spec, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        # Verify success
        assert result.success, f"Generation failed: {result.errors}"
        assert result.api_schema is not None

    @pytest.mark.asyncio
    async def test_openapi_parser_schema_extraction(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test that OpenAPI parser correctly extracts schemas."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Parse the OpenAPI spec
        parser = OpenAPIParser(str(openapi_file))
        api_schema = await parser.parse()

        # Verify schema structure
        assert api_schema is not None
        assert api_schema.title == "Test API"
        assert api_schema.version == "1.0.0"
        assert api_schema.base_url == "https://api.example.com/v1"

        # Verify models
        assert len(api_schema.models) >= 2
        model_names = {model.name for model in api_schema.models.values()}
        assert any("user" in name.lower() for name in model_names)

        # Find User model
        user_model = None
        for model in api_schema.models.values():
            if model.name == "User":
                user_model = model
                break

        assert user_model is not None
        field_names = {field.name for field in user_model.fields}
        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names

        # Verify required fields
        required_fields = {field.name for field in user_model.fields if field.required}
        assert "id" in required_fields
        assert "name" in required_fields
        assert "email" in required_fields

    @pytest.mark.asyncio
    async def test_openapi_parser_endpoints_extraction(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test that OpenAPI parser correctly extracts endpoints."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Parse the OpenAPI spec
        parser = OpenAPIParser(str(openapi_file))
        api_schema = await parser.parse()

        # Verify endpoints
        assert len(api_schema.endpoints) >= 3

        # Check for specific endpoints
        endpoint_paths = {ep.path for ep in api_schema.endpoints}
        assert "/users" in endpoint_paths
        assert "/users/{user_id}" in endpoint_paths

        # Check for specific methods
        get_users = None
        post_users = None
        for ep in api_schema.endpoints:
            if ep.path == "/users" and ep.method == "GET":
                get_users = ep
            elif ep.path == "/users" and ep.method == "POST":
                post_users = ep

        assert get_users is not None
        assert post_users is not None
        assert get_users.operation_id == "listUsers"
        assert post_users.operation_id == "createUser"

    @pytest.mark.asyncio
    async def test_openapi_parser_validation_constraints(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test that OpenAPI parser extracts validation constraints."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Parse the OpenAPI spec
        parser = OpenAPIParser(str(openapi_file))
        api_schema = await parser.parse()

        # Find User model
        user_model = None
        for model in api_schema.models.values():
            if model.name == "User":
                user_model = model
                break

        assert user_model is not None

        # Check validation constraints
        for field in user_model.fields:
            if field.name == "name":
                # Should have min/max length
                assert field.validators is not None
                validator_types = {v.type for v in field.validators}
                assert "min_length" in validator_types or "max_length" in validator_types
            elif field.name == "email":
                # Should have email format
                assert field.validators is not None
                validator_types = {v.type for v in field.validators}
                assert "email" in validator_types or "format" in validator_types
            elif field.name == "age":
                # Should have min/max value
                assert field.validators is not None
                validator_types = {v.type for v in field.validators}
                assert "minimum" in validator_types or "maximum" in validator_types

    @pytest.mark.asyncio
    async def test_generated_models_match_openapi_spec(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test that generated models match OpenAPI specification."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
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

        # Verify model classes are present
        assert "class User" in models_code
        assert "class UserCreate" in models_code

        # Verify fields are present
        assert "id:" in models_code or "id :" in models_code
        assert "name:" in models_code or "name :" in models_code
        assert "email:" in models_code or "email :" in models_code

    @pytest.mark.asyncio
    async def test_generated_app_has_correct_endpoints(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any]):
        """Test that generated FastAPI app has correct endpoints."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Read generated app
        app_file = temp_output_dir / "generated" / "app.py"
        assert app_file.exists()

        with open(app_file, "r") as f:
            app_code = f.read()

        # Verify endpoints are present
        assert "@app.get" in app_code or "@router.get" in app_code
        assert "@app.post" in app_code or "@router.post" in app_code
        assert "/users" in app_code

    @pytest.mark.asyncio
    async def test_performance_openapi_parsing(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any], performance_threshold: Dict[str, float]):
        """Test that OpenAPI parsing completes within acceptable time."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Measure parsing time
        start_time = time.time()
        parser = OpenAPIParser(str(openapi_file))
        api_schema = await parser.parse()
        parse_time = time.time() - start_time

        assert api_schema is not None
        assert parse_time < performance_threshold["parse_time"], \
            f"Parsing took {parse_time:.2f}s, expected < {performance_threshold['parse_time']}s"

    @pytest.mark.asyncio
    async def test_performance_complete_generation(self, temp_output_dir: Path, sample_openapi_spec: Dict[str, Any], performance_threshold: Dict[str, float]):
        """Test that complete generation completes within acceptable time."""
        # Create a temporary OpenAPI file
        openapi_file = temp_output_dir / "openapi.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
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
    async def test_error_handling_invalid_openapi(self, temp_output_dir: Path):
        """Test error handling with invalid OpenAPI spec."""
        # Create a file with invalid OpenAPI
        openapi_file = temp_output_dir / "invalid.yaml"
        with open(openapi_file, "w") as f:
            f.write("invalid: yaml: content:")

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        # Should fail gracefully
        assert not result.success
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_error_handling_missing_required_fields(self, temp_output_dir: Path):
        """Test error handling with OpenAPI spec missing required fields."""
        # Create an incomplete OpenAPI spec
        incomplete_spec = {
            "openapi": "3.0.0",
            # Missing info section
            "paths": {}
        }

        openapi_file = temp_output_dir / "incomplete.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(incomplete_spec, f)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(openapi_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "openapi"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        # Should handle gracefully
        assert result.end_time is not None

    @pytest.mark.asyncio
    async def test_openapi_with_refs(self, temp_output_dir: Path):
        """Test OpenAPI spec with $ref references."""
        spec_with_refs = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API with Refs",
                "version": "1.0.0"
            },
            "paths": {
                "/items": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Item"}
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
                    "Item": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "category": {"$ref": "#/components/schemas/Category"}
                        }
                    },
                    "Category": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }

        openapi_file = temp_output_dir / "refs.yaml"
        with open(openapi_file, "w") as f:
            yaml.dump(spec_with_refs, f)

        # Parse the spec
        parser = OpenAPIParser(str(openapi_file))
        api_schema = await parser.parse()

        # Verify refs were resolved
        assert api_schema is not None
        assert len(api_schema.models) >= 2  # Item and Category

    @pytest.mark.asyncio
    async def test_swagger_2_0_support(self, temp_output_dir: Path):
        """Test support for Swagger 2.0 specifications."""
        swagger_spec = {
            "swagger": "2.0",
            "info": {
                "title": "Swagger 2.0 API",
                "version": "1.0.0"
            },
            "host": "api.example.com",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/definitions/User"}
                                }
                            }
                        }
                    }
                }
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }

        swagger_file = temp_output_dir / "swagger.yaml"
        with open(swagger_file, "w") as f:
            yaml.dump(swagger_spec, f)

        # Parse the spec
        parser = OpenAPIParser(str(swagger_file))
        api_schema = await parser.parse()

        # Verify parsing succeeded
        assert api_schema is not None
        assert api_schema.title == "Swagger 2.0 API"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob

"""
Integration tests for JSON inference flow.

Tests the complete pipeline from JSON input to generated artifacts.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
import pytest
import time

from auto_sentinel import AutoSentinel, create_parser
from parsers.json_inference_parser import JSONInferenceParser
from schemas.api_schema import APISchema


class TestJSONInferenceFlow:
    """Integration tests for JSON inference pipeline."""

    @pytest.mark.asyncio
    async def test_json_file_complete_flow(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test complete flow with JSON file input."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
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
        assert api_schema.title is not None
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
        assert (output_dir / ".dockerignore").exists()

    @pytest.mark.asyncio
    async def test_json_parser_type_inference(self, sample_json_data: Dict[str, Any], temp_output_dir: Path):
        """Test that JSON parser correctly infers types."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Parse the JSON
        parser = JSONInferenceParser(str(json_file))
        api_schema = await parser.parse()

        # Verify schema structure
        assert api_schema is not None
        assert len(api_schema.models) > 0

        # Find the User model
        user_model = None
        for model in api_schema.models.values():
            if "user" in model.name.lower():
                user_model = model
                break

        assert user_model is not None, "User model not found"

        # Verify field types
        field_names = {field.name for field in user_model.fields}
        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names
        assert "age" in field_names
        assert "is_active" in field_names
        assert "created_at" in field_names

        # Verify specific field types
        for field in user_model.fields:
            if field.name == "id":
                assert field.type.python_type == "int"
            elif field.name == "name":
                assert field.type.python_type == "str"
            elif field.name == "email":
                assert field.type.python_type == "str"
                # Should detect email pattern
            elif field.name == "age":
                assert field.type.python_type == "int"
            elif field.name == "is_active":
                assert field.type.python_type == "bool"
            elif field.name == "created_at":
                assert field.type.python_type == "str"
                # Should detect datetime pattern

    @pytest.mark.asyncio
    async def test_generated_models_are_valid_python(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test that generated models.py is valid Python code."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Try to compile the generated models.py
        models_file = temp_output_dir / "generated" / "models.py"
        assert models_file.exists()

        with open(models_file, "r") as f:
            code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(code, str(models_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated models.py has syntax errors: {e}")

    @pytest.mark.asyncio
    async def test_generated_validators_are_valid_python(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test that generated validators.py is valid Python code."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Try to compile the generated validators.py
        validators_file = temp_output_dir / "generated" / "validators.py"
        assert validators_file.exists()

        with open(validators_file, "r") as f:
            code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(code, str(validators_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated validators.py has syntax errors: {e}")

    @pytest.mark.asyncio
    async def test_generated_tests_are_valid_python(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test that generated test_api.py is valid Python code."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Try to compile the generated test_api.py
        tests_file = temp_output_dir / "generated" / "test_api.py"
        assert tests_file.exists()

        with open(tests_file, "r") as f:
            code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(code, str(tests_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated test_api.py has syntax errors: {e}")

    @pytest.mark.asyncio
    async def test_generated_app_is_valid_python(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test that generated app.py is valid Python code."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Try to compile the generated app.py
        app_file = temp_output_dir / "generated" / "app.py"
        assert app_file.exists()

        with open(app_file, "r") as f:
            code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(code, str(app_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated app.py has syntax errors: {e}")

    @pytest.mark.asyncio
    async def test_performance_json_parsing(self, temp_output_dir: Path, sample_json_data: Dict[str, Any], performance_threshold: Dict[str, float]):
        """Test that JSON parsing completes within acceptable time."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Measure parsing time
        start_time = time.time()
        parser = JSONInferenceParser(str(json_file))
        api_schema = await parser.parse()
        parse_time = time.time() - start_time

        assert api_schema is not None
        assert parse_time < performance_threshold["parse_time"], \
            f"Parsing took {parse_time:.2f}s, expected < {performance_threshold['parse_time']}s"

    @pytest.mark.asyncio
    async def test_performance_complete_generation(self, temp_output_dir: Path, sample_json_data: Dict[str, Any], performance_threshold: Dict[str, float]):
        """Test that complete generation completes within acceptable time."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
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
    async def test_error_handling_invalid_json(self, temp_output_dir: Path):
        """Test error handling with invalid JSON."""
        # Create a file with invalid JSON
        json_file = temp_output_dir / "invalid.json"
        with open(json_file, "w") as f:
            f.write("{ invalid json }")

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        # Should fail gracefully
        assert not result.success
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_error_handling_empty_json(self, temp_output_dir: Path):
        """Test error handling with empty JSON."""
        # Create an empty JSON file
        json_file = temp_output_dir / "empty.json"
        with open(json_file, "w") as f:
            f.write("{}")

        # Create mock args
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        # Should handle gracefully (might succeed with minimal schema or fail)
        # Either way, should not crash
        assert result.end_time is not None

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, temp_output_dir: Path, sample_json_data: Dict[str, Any]):
        """Test dry-run mode doesn't create files."""
        # Create a temporary JSON file
        json_file = temp_output_dir / "sample.json"
        with open(json_file, "w") as f:
            json.dump(sample_json_data, f, indent=2)

        # Create mock args with dry-run
        args = create_parser().parse_args([
            "--api", str(json_file),
            "--output", str(temp_output_dir / "generated"),
            "--format", "json",
            "--dry-run"
        ])

        # Run the orchestrator
        orchestrator = AutoSentinel(args)
        result = await orchestrator.run()

        assert result.success

        # Verify no files were created
        output_dir = temp_output_dir / "generated"
        if output_dir.exists():
            generated_files = list(output_dir.glob("*.py"))
            assert len(generated_files) == 0, "Files were created in dry-run mode"

    @pytest.mark.asyncio
    async def test_nested_json_structures(self, temp_output_dir: Path):
        """Test handling of nested JSON structures."""
        nested_data = {
            "company": {
                "id": 1,
                "name": "Acme Corp",
                "address": {
                    "street": "123 Main St",
                    "city": "Springfield",
                    "country": "USA",
                    "postal_code": "12345"
                },
                "employees": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "position": "Engineer",
                        "salary": 75000.50
                    }
                ]
            }
        }

        # Create a temporary JSON file
        json_file = temp_output_dir / "nested.json"
        with open(json_file, "w") as f:
            json.dump(nested_data, f, indent=2)

        # Parse the JSON
        parser = JSONInferenceParser(str(json_file))
        api_schema = await parser.parse()

        # Verify nested models were created
        assert api_schema is not None
        assert len(api_schema.models) >= 3  # Company, Address, Employee

        # Verify relationships
        company_model = None
        for model in api_schema.models.values():
            if "company" in model.name.lower():
                company_model = model
                break

        assert company_model is not None
        field_names = {field.name for field in company_model.fields}
        assert "address" in field_names
        assert "employees" in field_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob

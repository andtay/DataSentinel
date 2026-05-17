"""
Test suite generator for DataSentinel.

Generates test_api.py with pytest tests using polyfactory for mock data.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.api_schema import APISchema, Endpoint, Parameter
from schemas.field_schema import FieldType


class TestsGenerator:
    """
    Generates test_api.py from APISchema.
    
    Creates:
    - Polyfactory factories for each model
    - Success tests for each endpoint
    - Validation error tests
    - HTTP error tests
    - Schema drift tests
    - Parameter tests
    - Integration tests
    - Performance tests
    - Edge case tests
    """
    
    def __init__(
        self,
        api_schema: APISchema,
        output_dir: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the tests generator.
        
        Args:
            api_schema: Normalized API schema
            output_dir: Directory to write test_api.py
            template_dir: Directory containing Jinja2 templates
        """
        self.api_schema = api_schema
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Register custom filters and globals
        self.env.globals["_get_response_model_name"] = self._get_response_model_name
        self.env.globals["_get_response_model"] = self._get_response_model
        self.env.globals["_get_mock_param_value"] = self._get_mock_param_value
        
        logger.info(f"Initialized TestsGenerator for {api_schema.title}")
    
    def _get_response_model_name(self, endpoint: Endpoint) -> str:
        """
        Get the response model name for an endpoint.

        Only returns names that exist in api_schema.models so generated
        tests reference real ModelFactory classes and imports.

        Args:
            endpoint: Endpoint schema

        Returns:
            Model class name or "Any" if no model
        """
        if (
            endpoint.response_model
            and endpoint.response_model.name in self.api_schema.models
        ):
            return endpoint.response_model.name
        return "Any"

    def _get_response_model(self, endpoint: Endpoint) -> Optional[str]:
        """
        Get the response model for an endpoint (for validation).

        Returns None when the endpoint references a model that was not
        materialized in models.py (e.g. phantom \"Locations\" from GraphQL).

        Args:
            endpoint: Endpoint schema

        Returns:
            Model name or None
        """
        if (
            endpoint.response_model
            and endpoint.response_model.name in self.api_schema.models
        ):
            return endpoint.response_model.name
        return None
    
    def _get_mock_param_value(self, param: Parameter) -> str:
        """
        Get a mock value for a parameter based on its type.
        
        Args:
            param: Parameter schema
        
        Returns:
            String representation of mock value
        """
        field_type = param.field_schema.type
        
        # Type-specific mock values
        mock_values = {
            FieldType.STRING: '"test_value"',
            FieldType.INTEGER: '123',
            FieldType.FLOAT: '123.45',
            FieldType.BOOLEAN: 'True',
            FieldType.UUID: '"550e8400-e29b-41d4-a716-446655440000"',
            FieldType.EMAIL: '"test@example.com"',
            FieldType.URL: '"https://example.com"',
            FieldType.DATE: '"2024-01-01"',
            FieldType.DATETIME: '"2024-01-01T00:00:00Z"',
            FieldType.ARRAY: '[]',
            FieldType.OBJECT: '{}',
            FieldType.ANY: '"test"',
        }
        
        return mock_values.get(field_type, '"test"')
    
    def _get_model_names(self) -> List[str]:
        """
        Get list of all model names to import.
        
        Returns:
            List of model class names
        """
        return list(self.api_schema.models.keys())
    
    def _prepare_template_context(self) -> Dict[str, Any]:
        """
        Prepare context data for Jinja2 template.
        
        Returns:
            Template context dictionary
        """
        return {
            "api_schema": self.api_schema,
            "model_names": self._get_model_names(),
            "generation_timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    def generate(self) -> Path:
        """
        Generate test_api.py file.
        
        Returns:
            Path to generated file
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating test_api.py...")
        
        try:
            # Load template
            template = self.env.get_template("test_api.py.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / "test_api.py"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated test_api.py at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate test_api.py: {e}")
            raise
    
    def validate_generation(self, output_file: Path) -> bool:
        """
        Validate that the generated file is syntactically correct.
        
        Args:
            output_file: Path to generated test_api.py
        
        Returns:
            True if valid, False otherwise
        """
        try:
            import ast
            
            content = output_file.read_text(encoding="utf-8")
            ast.parse(content)
            
            logger.success("Generated test_api.py is syntactically valid")
            return True
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated test_api.py: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def get_test_count(self) -> Dict[str, int]:
        """
        Get count of tests that will be generated.
        
        Returns:
            Dictionary with test counts by category
        """
        endpoint_count = len(self.api_schema.endpoints)
        
        # Each endpoint gets 4-5 tests
        tests_per_endpoint = 4  # success, validation_error, http_error, schema_drift
        
        # Add parameter tests for endpoints with parameters
        param_tests = sum(1 for e in self.api_schema.endpoints if e.parameters)
        
        # Integration and edge case tests
        integration_tests = 4  # context_manager, caching, validation_report, concurrent
        edge_case_tests = 2  # empty_response, malformed_json
        
        return {
            "endpoint_tests": endpoint_count * tests_per_endpoint,
            "parameter_tests": param_tests,
            "integration_tests": integration_tests,
            "edge_case_tests": edge_case_tests,
            "total": (endpoint_count * tests_per_endpoint) + param_tests + integration_tests + edge_case_tests,
        }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what will be generated.
        
        Returns:
            Dictionary with generation statistics
        """
        test_counts = self.get_test_count()
        
        return {
            "api_title": self.api_schema.title,
            "api_version": self.api_schema.version,
            "total_endpoints": len(self.api_schema.endpoints),
            "total_models": len(self.api_schema.models),
            "factory_count": len(self._get_model_names()),
            "test_counts": test_counts,
            "endpoints_by_method": self._count_endpoints_by_method(),
        }
    
    def _count_endpoints_by_method(self) -> Dict[str, int]:
        """
        Count endpoints by HTTP method.
        
        Returns:
            Dictionary mapping method to count
        """
        counts: Dict[str, int] = {}
        for endpoint in self.api_schema.endpoints:
            method = endpoint.method.upper()
            counts[method] = counts.get(method, 0) + 1
        return counts
    
    def get_required_fixtures(self) -> List[str]:
        """
        Get list of pytest fixtures that will be generated.
        
        Returns:
            List of fixture names
        """
        return [
            "api_base_url",
            "api_validator",
            "mock_response_data",
        ]
    
    def get_test_markers(self) -> List[str]:
        """
        Get list of pytest markers used in tests.
        
        Returns:
            List of marker names
        """
        return [
            "asyncio",
            "slow",
        ]


def generate_tests(
    api_schema: APISchema,
    output_dir: Path,
    template_dir: Optional[Path] = None,
) -> Path:
    """
    Convenience function to generate test_api.py.
    
    Args:
        api_schema: Normalized API schema
        output_dir: Directory to write test_api.py
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        Path to generated file
    """
    generator = TestsGenerator(api_schema, output_dir, template_dir)
    output_file = generator.generate()
    generator.validate_generation(output_file)
    return output_file

# Made with Bob

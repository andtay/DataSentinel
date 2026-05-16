"""
FastAPI app generator for DataSentinel.

Generates app.py with FastAPI application exposing validators as REST endpoints.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.api_schema import APISchema, Endpoint, Parameter
from schemas.field_schema import FieldType


class AppGenerator:
    """
    Generates app.py from APISchema.
    
    Creates:
    - FastAPI application with CORS middleware
    - Health check endpoint
    - Validation endpoints for each API endpoint
    - Exception handlers
    - OpenAPI schema endpoint
    - Request/Response models
    """
    
    def __init__(
        self,
        api_schema: APISchema,
        output_dir: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the app generator.
        
        Args:
            api_schema: Normalized API schema
            output_dir: Directory to write app.py
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
        self.env.globals["_get_param_type_annotation"] = self._get_param_type_annotation
        self.env.globals["_get_default_param_value"] = self._get_default_param_value
        
        logger.info(f"Initialized AppGenerator for {api_schema.title}")
    
    def _get_response_model_name(self, endpoint: Endpoint) -> str:
        """
        Get the response model name for an endpoint.
        
        Args:
            endpoint: Endpoint schema
        
        Returns:
            Model class name or "Any" if no model
        """
        if endpoint.response_model:
            return endpoint.response_model.name
        return "Any"
    
    def _get_param_type_annotation(self, param: Parameter) -> str:
        """
        Get Python type annotation for a parameter.
        
        Args:
            param: Parameter schema
        
        Returns:
            Type annotation string
        """
        # Map FieldType to Python type
        type_map = {
            FieldType.STRING: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.ARRAY: "List[Any]",
            FieldType.OBJECT: "Dict[str, Any]",
            FieldType.EMAIL: "str",
            FieldType.URL: "str",
            FieldType.UUID: "str",
            FieldType.DATE: "str",
            FieldType.DATETIME: "str",
            FieldType.ANY: "Any",
        }
        
        base_type = type_map.get(param.field_schema.type, "Any")
        
        # Wrap in Optional if not required
        if not param.required:
            return f"Optional[{base_type}]"
        
        return base_type
    
    def _get_default_param_value(self, param: Parameter) -> str:
        """
        Get a default value for a parameter based on its type.
        
        Args:
            param: Parameter schema
        
        Returns:
            String representation of default value
        """
        field_type = param.field_schema.type
        
        # Type-specific default values
        default_values = {
            FieldType.STRING: '"default"',
            FieldType.INTEGER: '1',
            FieldType.FLOAT: '1.0',
            FieldType.BOOLEAN: 'True',
            FieldType.UUID: '"00000000-0000-0000-0000-000000000000"',
            FieldType.EMAIL: '"default@example.com"',
            FieldType.URL: '"https://example.com"',
            FieldType.DATE: '"2024-01-01"',
            FieldType.DATETIME: '"2024-01-01T00:00:00Z"',
            FieldType.ARRAY: '[]',
            FieldType.OBJECT: '{}',
            FieldType.ANY: 'None',
        }
        
        return default_values.get(field_type, 'None')
    
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
        Generate app.py file.
        
        Returns:
            Path to generated file
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating app.py...")
        
        try:
            # Load template
            template = self.env.get_template("app.py.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / "app.py"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated app.py at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate app.py: {e}")
            raise
    
    def validate_generation(self, output_file: Path) -> bool:
        """
        Validate that the generated file is syntactically correct.
        
        Args:
            output_file: Path to generated app.py
        
        Returns:
            True if valid, False otherwise
        """
        try:
            import ast
            
            content = output_file.read_text(encoding="utf-8")
            ast.parse(content)
            
            logger.success("Generated app.py is syntactically valid")
            return True
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated app.py: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def get_endpoint_count(self) -> Dict[str, int]:
        """
        Get count of endpoints that will be generated.
        
        Returns:
            Dictionary with endpoint counts
        """
        return {
            "health": 1,
            "validate_all": 1,
            "validate_individual": len(self.api_schema.endpoints),
            "root": 1,
            "openapi": 1,
            "total": 3 + len(self.api_schema.endpoints),
        }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what will be generated.
        
        Returns:
            Dictionary with generation statistics
        """
        endpoint_counts = self.get_endpoint_count()
        
        return {
            "api_title": self.api_schema.title,
            "api_version": self.api_schema.version,
            "total_endpoints": len(self.api_schema.endpoints),
            "total_models": len(self.api_schema.models),
            "fastapi_endpoints": endpoint_counts,
            "endpoints_by_method": self._count_endpoints_by_method(),
            "has_cors": True,
            "has_exception_handlers": True,
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
    
    def get_required_dependencies(self) -> List[str]:
        """
        Get list of required Python packages.
        
        Returns:
            List of package names
        """
        return [
            "fastapi",
            "uvicorn[standard]",
            "httpx",
            "pydantic",
            "loguru",
        ]
    
    def get_middleware_list(self) -> List[str]:
        """
        Get list of middleware that will be added.
        
        Returns:
            List of middleware names
        """
        return [
            "CORSMiddleware",
        ]
    
    def get_exception_handlers(self) -> List[str]:
        """
        Get list of exception handlers.
        
        Returns:
            List of exception types
        """
        return [
            "ValidationException",
            "APIException",
            "SchemaException",
        ]


def generate_app(
    api_schema: APISchema,
    output_dir: Path,
    template_dir: Optional[Path] = None,
) -> Path:
    """
    Convenience function to generate app.py.
    
    Args:
        api_schema: Normalized API schema
        output_dir: Directory to write app.py
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        Path to generated file
    """
    generator = AppGenerator(api_schema, output_dir, template_dir)
    output_file = generator.generate()
    generator.validate_generation(output_file)
    return output_file

# Made with Bob

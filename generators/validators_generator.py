"""
Validators generator for DataSentinel.

Generates validators.py with API validation logic, retry handling,
and schema drift detection.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.api_schema import APISchema, Endpoint, Parameter
from schemas.field_schema import FieldType


class ValidatorsGenerator:
    """
    Generates validators.py from APISchema.
    
    Creates:
    - APIValidator class with retry logic
    - Validation methods for each endpoint
    - Schema drift detection
    - Response caching
    - ValidationReport for summary reporting
    """
    
    def __init__(
        self,
        api_schema: APISchema,
        output_dir: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the validators generator.
        
        Args:
            api_schema: Normalized API schema
            output_dir: Directory to write validators.py
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
        self.env.filters["lower"] = str.lower
        self.env.filters["replace"] = str.replace
        self.env.globals["_get_param_type_annotation"] = self._get_param_type_annotation
        self.env.globals["_get_response_model_name"] = self._get_response_model_name
        self.env.globals["_get_response_model"] = self._get_response_model
        
        logger.info(f"Initialized ValidatorsGenerator for {api_schema.title}")
    
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
    
    def _get_response_model_name(self, endpoint: Endpoint) -> str:
        """
        Get the response model name for an endpoint.

        Falls back to Any when the endpoint's response_model isn't a
        real model in api_schema.models (e.g. references to types the
        parser didn't materialize).

        Args:
            endpoint: Endpoint schema

        Returns:
            Model class name or "Any" if no model
        """
        if endpoint.response_model and endpoint.response_model.name in self.api_schema.models:
            return endpoint.response_model.name
        return "Any"

    def _get_response_model(self, endpoint: Endpoint) -> Optional[str]:
        """
        Get the response model for an endpoint (for validation).

        Returns None when the endpoint references a model that isn't in
        api_schema.models, so the template skips schema-drift validation
        instead of emitting an undefined name.

        Args:
            endpoint: Endpoint schema

        Returns:
            Model name or None
        """
        if endpoint.response_model and endpoint.response_model.name in self.api_schema.models:
            return endpoint.response_model.name
        return None
    
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
        Generate validators.py file.
        
        Returns:
            Path to generated file
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating validators.py...")
        
        try:
            # Load template
            template = self.env.get_template("validators.py.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / "validators.py"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated validators.py at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate validators.py: {e}")
            raise
    
    def validate_generation(self, output_file: Path) -> bool:
        """
        Validate that the generated file is syntactically correct.
        
        Args:
            output_file: Path to generated validators.py
        
        Returns:
            True if valid, False otherwise
        """
        try:
            import ast
            
            content = output_file.read_text(encoding="utf-8")
            ast.parse(content)
            
            logger.success("Generated validators.py is syntactically valid")
            return True
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated validators.py: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def get_validator_methods(self) -> List[str]:
        """
        Get list of validator method names that will be generated.
        
        Returns:
            List of method names
        """
        methods = []
        for endpoint in self.api_schema.endpoints:
            # Use get_function_name() method from Endpoint
            method_name = f"validate_{endpoint.get_function_name()}"
            methods.append(method_name)
        return methods
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what will be generated.
        
        Returns:
            Dictionary with generation statistics
        """
        return {
            "api_title": self.api_schema.title,
            "api_version": self.api_schema.version,
            "total_endpoints": len(self.api_schema.endpoints),
            "total_models": len(self.api_schema.models),
            "validator_methods": len(self.get_validator_methods()),
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


def generate_validators(
    api_schema: APISchema,
    output_dir: Path,
    template_dir: Optional[Path] = None,
) -> Path:
    """
    Convenience function to generate validators.py.
    
    Args:
        api_schema: Normalized API schema
        output_dir: Directory to write validators.py
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        Path to generated file
    """
    generator = ValidatorsGenerator(api_schema, output_dir, template_dir)
    output_file = generator.generate()
    generator.validate_generation(output_file)
    return output_file

# Made with Bob

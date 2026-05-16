"""
Documentation generator for DataSentinel.

Generates data_dict.md with comprehensive API documentation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.api_schema import APISchema, AuthConfig, Endpoint, Parameter
from schemas.field_schema import FieldSchema, FieldType


class DocsGenerator:
    """
    Generates data_dict.md from APISchema.
    
    Creates:
    - Comprehensive data dictionary in Markdown
    - Model documentation with field details
    - Endpoint documentation with examples
    - Authentication documentation
    - Field type reference
    - Validation rules reference
    - Error response documentation
    """
    
    def __init__(
        self,
        api_schema: APISchema,
        output_dir: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the docs generator.
        
        Args:
            api_schema: Normalized API schema
            output_dir: Directory to write data_dict.md
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
        self.env.filters["tojson"] = lambda x: json.dumps(x, indent=2)
        self.env.globals["_get_endpoint_anchor"] = self._get_endpoint_anchor
        self.env.globals["_count_total_fields"] = self._count_total_fields
        self.env.globals["_get_field_type_display"] = self._get_field_type_display
        self.env.globals["_get_field_constraints"] = self._get_field_constraints
        self.env.globals["_get_field_example"] = self._get_field_example
        self.env.globals["_get_param_type_display"] = self._get_param_type_display
        self.env.globals["_get_param_constraints"] = self._get_param_constraints
        self.env.globals["_get_auth_header"] = self._get_auth_header
        self.env.globals["_get_example_request_body"] = self._get_example_request_body
        
        logger.info(f"Initialized DocsGenerator for {api_schema.title}")
    
    def _get_endpoint_anchor(self, endpoint: Endpoint) -> str:
        """
        Get anchor link for an endpoint.
        
        Args:
            endpoint: Endpoint schema
        
        Returns:
            Anchor string
        """
        return f"{endpoint.method.lower()}-{endpoint.path.replace('/', '-').replace('{', '').replace('}', '').strip('-')}"
    
    def _count_total_fields(self) -> int:
        """
        Count total fields across all models.
        
        Returns:
            Total field count
        """
        return sum(len(model.fields) for model in self.api_schema.models.values())
    
    def _get_field_type_display(self, field: FieldSchema) -> str:
        """
        Get display string for field type.
        
        Args:
            field: Field schema
        
        Returns:
            Type display string
        """
        if field.type == FieldType.ARRAY and field.item_type:
            return f"array[{field.item_type.value}]"
        elif field.type == FieldType.OBJECT and field.nested_model:
            return f"[{field.nested_model}](#{ field.nested_model.lower()})"
        return field.type.value
    
    def _get_field_constraints(self, field: FieldSchema) -> str:
        """
        Get constraints string for a field.
        
        Args:
            field: Field schema
        
        Returns:
            Constraints string
        """
        constraints = []
        
        if field.min_length is not None:
            constraints.append(f"min_length: {field.min_length}")
        if field.max_length is not None:
            constraints.append(f"max_length: {field.max_length}")
        if field.pattern:
            constraints.append(f"pattern: `{field.pattern}`")
        if field.min_value is not None:
            constraints.append(f"min: {field.min_value}")
        if field.max_value is not None:
            constraints.append(f"max: {field.max_value}")
        if field.multiple_of is not None:
            constraints.append(f"multiple_of: {field.multiple_of}")
        if field.enum_values:
            constraints.append(f"enum: {', '.join(str(v) for v in field.enum_values[:3])}{'...' if len(field.enum_values) > 3 else ''}")
        if field.min_items is not None:
            constraints.append(f"min_items: {field.min_items}")
        if field.max_items is not None:
            constraints.append(f"max_items: {field.max_items}")
        if field.unique_items:
            constraints.append("unique_items")
        
        return ", ".join(constraints) if constraints else "None"
    
    def _get_field_example(self, field: FieldSchema) -> str:
        """
        Get example value for a field.
        
        Args:
            field: Field schema
        
        Returns:
            Example string
        """
        if field.example is not None:
            if isinstance(field.example, str):
                return f'`"{field.example}"`'
            return f"`{field.example}`"
        
        if field.enum_values:
            return f'`"{field.enum_values[0]}"`' if isinstance(field.enum_values[0], str) else f"`{field.enum_values[0]}`"
        
        return "N/A"
    
    def _get_param_type_display(self, param: Parameter) -> str:
        """
        Get display string for parameter type.
        
        Args:
            param: Parameter schema
        
        Returns:
            Type display string
        """
        return param.field_schema.type.value
    
    def _get_param_constraints(self, param: Parameter) -> str:
        """
        Get constraints string for a parameter.
        
        Args:
            param: Parameter schema
        
        Returns:
            Constraints string
        """
        return self._get_field_constraints(param.field_schema)
    
    def _get_auth_header(self, auth_config: AuthConfig) -> str:
        """
        Get authentication header example.
        
        Args:
            auth_config: Auth configuration
        
        Returns:
            Header string
        """
        if auth_config.type == "bearer":
            return "Authorization: Bearer YOUR_TOKEN"
        elif auth_config.type == "api_key" and auth_config.location == "header":
            return f"{auth_config.name}: YOUR_API_KEY"
        return "Authorization: YOUR_CREDENTIALS"
    
    def _get_example_request_body(self, endpoint: Endpoint) -> Dict[str, Any]:
        """
        Get example request body for an endpoint.
        
        Args:
            endpoint: Endpoint schema
        
        Returns:
            Example body dictionary
        """
        if endpoint.request_model and endpoint.request_model.example:
            return endpoint.request_model.example
        
        # Generate simple example
        if endpoint.request_model:
            example = {}
            for field in endpoint.request_model.fields:
                if field.example is not None:
                    example[field.name] = field.example
                elif field.type == FieldType.STRING:
                    example[field.name] = "string"
                elif field.type == FieldType.INTEGER:
                    example[field.name] = 0
                elif field.type == FieldType.FLOAT:
                    example[field.name] = 0.0
                elif field.type == FieldType.BOOLEAN:
                    example[field.name] = True
                elif field.type == FieldType.ARRAY:
                    example[field.name] = []
                elif field.type == FieldType.OBJECT:
                    example[field.name] = {}
            return example
        
        return {}
    
    def _get_model_names(self) -> List[str]:
        """
        Get list of all model names.
        
        Returns:
            List of model names
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
        Generate data_dict.md file.
        
        Returns:
            Path to generated file
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating data_dict.md...")
        
        try:
            # Load template
            template = self.env.get_template("data_dict.md.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / "data_dict.md"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated data_dict.md at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate data_dict.md: {e}")
            raise
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what will be generated.
        
        Returns:
            Dictionary with generation statistics
        """
        return {
            "api_title": self.api_schema.title,
            "api_version": self.api_schema.version,
            "total_models": len(self.api_schema.models),
            "total_endpoints": len(self.api_schema.endpoints),
            "total_fields": self._count_total_fields(),
            "has_authentication": self.api_schema.auth_config is not None,
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


def generate_docs(
    api_schema: APISchema,
    output_dir: Path,
    template_dir: Optional[Path] = None,
) -> Path:
    """
    Convenience function to generate data_dict.md.
    
    Args:
        api_schema: Normalized API schema
        output_dir: Directory to write data_dict.md
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        Path to generated file
    """
    generator = DocsGenerator(api_schema, output_dir, template_dir)
    return generator.generate()

# Made with Bob

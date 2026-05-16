"""
Pydantic models generator.

This module generates Pydantic v2 BaseModel classes from APISchema.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from core.exceptions import GeneratorError
from schemas import APISchema, FieldSchema, FieldType


class ModelsGenerator:
    """
    Generator for Pydantic models.
    
    This generator creates a models.py file containing Pydantic BaseModel
    classes for all models in the APISchema.
    """
    
    def __init__(self, api_schema: APISchema, output_dir: Path):
        """
        Initialize models generator.
        
        Args:
            api_schema: APISchema to generate models from
            output_dir: Directory to write generated files
        """
        self.api_schema = api_schema
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters and functions
        self.env.filters['repr'] = repr
        self.env.globals['_get_field_type_annotation'] = self._get_field_type_annotation
        self.env.globals['_has_field_args'] = self._has_field_args
        self.env.globals['_has_validators'] = self._has_validators
    
    def generate(self) -> Path:
        """
        Generate models.py file.
        
        Returns:
            Path to generated file
            
        Raises:
            GeneratorError: If generation fails
        """
        logger.info(f"Generating Pydantic models for {self.api_schema.title}")
        
        try:
            # Load template
            template = self.env.get_template("models.py.jinja2")
            
            # Render template
            content = template.render(
                api_schema=self.api_schema,
                generation_timestamp=datetime.utcnow().isoformat() + "Z"
            )
            
            # Write to file
            output_file = self.output_dir / "models.py"
            output_file.write_text(content, encoding="utf-8")
            
            logger.info(f"Generated models.py with {len(self.api_schema.models)} models")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate models: {e}")
            raise GeneratorError(
                f"Failed to generate Pydantic models: {e}",
                details={"api_schema": self.api_schema.title}
            )
    
    def _get_field_type_annotation(self, field: FieldSchema) -> str:
        """
        Get Python type annotation for a field.
        
        Args:
            field: FieldSchema to get type for
            
        Returns:
            Python type annotation string
        """
        # Map FieldType to Python type
        type_map = {
            FieldType.STRING: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATE: "date",
            FieldType.DATETIME: "datetime",
            FieldType.UUID: "UUID",
            FieldType.EMAIL: "EmailStr",
            FieldType.URL: "HttpUrl",
            FieldType.ANY: "Any",
        }
        
        # Handle array type
        if field.type == FieldType.ARRAY:
            if field.item_type:
                item_type = type_map.get(field.item_type, "Any")
            else:
                item_type = "Any"
            base_type = f"List[{item_type}]"
        
        # Handle object type
        elif field.type == FieldType.OBJECT:
            if field.nested_model and field.nested_model in self.api_schema.models:
                base_type = field.nested_model
            else:
                if field.nested_model:
                    logger.warning(
                        f"Field '{field.name}' references unknown model "
                        f"'{field.nested_model}'; falling back to dict[str, Any]"
                    )
                base_type = "dict[str, Any]"
        
        # Handle scalar types
        else:
            base_type = type_map.get(field.type, "Any")
        
        # Make optional if not required
        if not field.required:
            return f"Optional[{base_type}]"
        
        return base_type
    
    def _has_field_args(self, field: FieldSchema) -> bool:
        """
        Check if field needs Field() arguments.
        
        Args:
            field: FieldSchema to check
            
        Returns:
            True if field needs Field() call
        """
        return (
            field.default is not None or
            not field.required or
            field.description is not None or
            field.min_length is not None or
            field.max_length is not None or
            field.pattern is not None or
            field.min_value is not None or
            field.max_value is not None or
            field.multiple_of is not None or
            field.example is not None or
            field.deprecated
        )
    
    def _has_validators(self, model: Any) -> bool:
        """
        Check if model needs custom validators.
        
        Args:
            model: ModelSchema to check
            
        Returns:
            True if model needs validators
        """
        for field in model.fields:
            if field.enum_values:
                return True
        return False
    
    def get_imports(self) -> set[str]:
        """
        Get required imports for generated models.
        
        Returns:
            Set of import statements
        """
        imports = {
            "from pydantic import BaseModel, Field",
        }
        
        # Check which types are used
        uses_email = any(
            f.type == FieldType.EMAIL
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_email:
            imports.add("from pydantic import EmailStr")
        
        uses_url = any(
            f.type == FieldType.URL
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_url:
            imports.add("from pydantic import HttpUrl")
        
        uses_uuid = any(
            f.type == FieldType.UUID
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_uuid:
            imports.add("from uuid import UUID")
        
        uses_date = any(
            f.type == FieldType.DATE
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_date:
            imports.add("from datetime import date")
        
        uses_datetime = any(
            f.type == FieldType.DATETIME
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_datetime:
            imports.add("from datetime import datetime")
        
        uses_list = any(
            f.type == FieldType.ARRAY
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_list:
            imports.add("from typing import List")
        
        uses_optional = any(
            not f.required
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_optional:
            imports.add("from typing import Optional")
        
        uses_any = any(
            f.type == FieldType.ANY
            for model in self.api_schema.models.values()
            for f in model.fields
        )
        if uses_any:
            imports.add("from typing import Any")
        
        return imports

# Made with Bob

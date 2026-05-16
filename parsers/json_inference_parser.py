"""
JSON type inference parser.

This module implements a type inference engine that analyzes JSON data
and automatically infers Pydantic model schemas with validation rules.
"""

import re
from pathlib import Path
from typing import Any

from loguru import logger

from core.exceptions import ParserError
from core.utils import is_url
from parsers.base_parser import BaseParser
from schemas import (
    APISchema,
    Endpoint,
    FieldSchema,
    FieldType,
    ModelSchema,
    PYTHON_TYPE_MAP,
)


class JSONInferenceParser(BaseParser):
    """
    Type inference engine for raw JSON data.
    
    This parser analyzes JSON structure and automatically infers:
    - Field types from values
    - Validation patterns (email, URL, UUID, dates)
    - Nested object structures
    - Array item types
    - Optional vs required fields (with multiple samples)
    """
    
    def __init__(self, source: str | Path, auth_handler=None):
        """
        Initialize JSON inference parser.

        Args:
            source: Path to JSON file or REST endpoint URL
            auth_handler: Optional AuthHandler (forwarded to BaseParser).
        """
        super().__init__(source, auth_handler=auth_handler)
        self.infer_patterns = True  # Detect patterns in strings
    
    async def parse(self) -> APISchema:
        """
        Parse JSON and infer schema.
        
        Returns:
            APISchema with inferred models and endpoint
            
        Raises:
            ParserError: If JSON cannot be parsed or inferred
        """
        logger.info(f"Inferring schema from JSON source: {self.source}")
        
        # Validate source
        if not self.validate_source():
            raise ParserError(f"Invalid source: {self.source}")
        
        # Load JSON data
        json_data = await self._load_json_data()
        
        # Determine base URL
        if is_url(self.source):
            from core.utils import extract_base_url
            base_url = extract_base_url(self.source)
        else:
            base_url = "http://localhost"
        
        # Infer model from JSON structure
        inferred_model = self._infer_model_from_json(json_data, "InferredModel")
        
        # Collect all models (including nested ones)
        all_models = self._collect_all_models(inferred_model, json_data)
        
        # Create endpoint
        endpoint = Endpoint(
            path="/data",
            method="GET",
            summary="Inferred endpoint",
            description="Auto-generated from JSON sample",
            operation_id="get_data",
            request_model=None,
            response_model=inferred_model,  # Keep as ModelSchema object
            auth_required=False,
            deprecated=False
        )
        
        # Create API schema
        api_schema = APISchema(
            title="Inferred API",
            version="1.0.0",
            base_url=base_url,
            description="Auto-generated schema from JSON inference",
            endpoints=[endpoint],
            models=all_models,
            auth_config=None
        )
        
        # Validate
        self._validate_parsed_schema(api_schema)
        
        logger.info(
            f"Successfully inferred schema: "
            f"{len(api_schema.models)} models, "
            f"{len(api_schema.endpoints)} endpoints"
        )
        
        return api_schema
    
    async def _load_json_data(self) -> Any:
        """
        Load JSON data from source.
        
        Returns:
            Parsed JSON data
            
        Raises:
            ParserError: If JSON cannot be loaded
        """
        if is_url(self.source):
            # Fetch from URL
            return await self._fetch_url(self.source)
        else:
            # Load from file
            path = Path(self.source)
            return self._load_file(path)
    
    def _infer_model_from_json(
        self,
        data: Any,
        model_name: str = "InferredModel"
    ) -> ModelSchema:
        """
        Recursively infer Pydantic model from JSON structure.
        
        Args:
            data: JSON data to analyze
            model_name: Name for the model
            
        Returns:
            ModelSchema with inferred fields
            
        Raises:
            ParserError: If data cannot be inferred
        """
        if isinstance(data, dict):
            fields: list[FieldSchema] = []
            
            for key, value in data.items():
                field = self._infer_field_from_value(key, value)
                fields.append(field)
            
            return ModelSchema(
                name=self._normalize_model_name(model_name),
                fields=fields,
                description=f"Inferred from JSON data",
                example=data if isinstance(data, dict) else None
            )
        
        elif isinstance(data, list) and len(data) > 0:
            # Infer from first item (could be enhanced with multi-sample analysis)
            return self._infer_model_from_json(data[0], f"{model_name}Item")
        
        else:
            raise ParserError(
                "Cannot infer model from non-dict, non-list data",
                details={"data_type": type(data).__name__}
            )
    
    def _infer_field_from_value(self, name: str, value: Any) -> FieldSchema:
        """
        Infer field schema from a value.
        
        Args:
            name: Field name
            value: Field value
            
        Returns:
            FieldSchema with inferred type and constraints
        """
        # Normalize field name
        field_name = self._normalize_field_name(name)
        
        # Infer type
        field_type = self._infer_field_type(value)
        
        # Create base field
        field = FieldSchema(
            name=field_name,
            type=field_type,
            required=True,  # Assume required unless we have multiple samples
            description=f"Inferred from sample data",
            default=None,
            pattern=None,
            min_length=None,
            max_length=None,
            min_value=None,
            max_value=None,
            multiple_of=None,
            enum_values=None,
            item_type=None,
            min_items=None,
            max_items=None,
            unique_items=False,
            nested_model=None,
            additional_properties=False,
            example=None,
            deprecated=False,
            read_only=False,
            write_only=False
        )
        
        # Add type-specific constraints
        if field_type == FieldType.STRING and isinstance(value, str):
            # Detect patterns
            if self.infer_patterns:
                pattern_result = self._detect_string_pattern(value)
                if pattern_result:
                    pattern_name, pattern_regex = pattern_result
                    field.pattern = pattern_regex
                    
                    # Update type based on detected pattern
                    if pattern_name == "email":
                        field.type = FieldType.EMAIL
                    elif pattern_name == "url":
                        field.type = FieldType.URL
                    elif pattern_name == "uuid":
                        field.type = FieldType.UUID
                    elif pattern_name in ("iso_date", "iso_datetime"):
                        field.type = FieldType.DATE
            
            # Add length constraints
            if value:
                field.min_length = 1
                field.max_length = max(len(value) * 2, 255)  # Reasonable max
        
        elif field_type == FieldType.INTEGER and isinstance(value, int):
            # Add range constraints based on value
            field.min_value = 0 if value >= 0 else value - 1000
            field.max_value = value + 1000
        
        elif field_type == FieldType.FLOAT and isinstance(value, float):
            # Add range constraints
            field.min_value = 0.0 if value >= 0 else value - 1000.0
            field.max_value = value + 1000.0
        
        elif field_type == FieldType.ARRAY and isinstance(value, list):
            # Infer item type
            if len(value) > 0:
                first_item = value[0]
                field.item_type = self._infer_field_type(first_item)
                
                # If items are objects, create nested model
                if isinstance(first_item, dict):
                    nested_model_name = f"{field_name.title().replace('_', '')}Item"
                    field.nested_model = nested_model_name
            
            # Add array constraints
            field.min_items = 0
            field.max_items = max(len(value) * 2, 100)
        
        elif field_type == FieldType.OBJECT and isinstance(value, dict):
            # Create nested model
            nested_model_name = f"{field_name.title().replace('_', '')}"
            field.nested_model = self._normalize_model_name(nested_model_name)
        
        # Add example
        field.example = value
        
        return field
    
    def _collect_all_models(self, root_model: ModelSchema, json_data: Any) -> dict[str, ModelSchema]:
        """
        Collect all models including nested ones.
        
        Args:
            root_model: The root model
            json_data: Original JSON data
            
        Returns:
            Dictionary of all models
        """
        models = {root_model.name: root_model}
        
        # Recursively collect nested models
        def collect_nested(model: ModelSchema, data: Any):
            for field in model.fields:
                if field.nested_model:
                    # Find the corresponding data
                    field_data = None
                    if isinstance(data, dict) and field.name in data:
                        field_data = data[field.name]
                        
                        # Handle arrays
                        if field.type == FieldType.ARRAY and isinstance(field_data, list) and len(field_data) > 0:
                            field_data = field_data[0]
                        
                        # Create nested model if not already exists
                        if field.nested_model not in models and field_data:
                            nested_model = self._infer_model_from_json(field_data, field.nested_model)
                            models[nested_model.name] = nested_model
                            collect_nested(nested_model, field_data)
        
        collect_nested(root_model, json_data)
        return models
        return field
    
    def _infer_field_type(self, value: Any) -> FieldType:
        """
        Infer field type from value.
        
        Args:
            value: Value to analyze
            
        Returns:
            Inferred FieldType
        """
        # Handle None
        if value is None:
            return FieldType.ANY
        
        # Get Python type
        python_type = type(value)
        
        # Map to FieldType
        if python_type in PYTHON_TYPE_MAP:
            return PYTHON_TYPE_MAP[python_type]
        
        # Default to ANY for unknown types
        logger.warning(f"Unknown type {python_type}, defaulting to ANY")
        return FieldType.ANY
    
    def _detect_string_pattern(self, value: str) -> tuple[str, str] | None:
        """
        Detect common patterns in string values.
        
        Args:
            value: String value to analyze
            
        Returns:
            Tuple of (pattern_name, regex_pattern) if detected, None otherwise
        """
        patterns = {
            'email': r'^[\w\.-]+@[\w\.-]+\.\w+$',
            'url': r'^https?://[^\s]+$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            'iso_date': r'^\d{4}-\d{2}-\d{2}$',
            'iso_datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        }
        
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, value, re.IGNORECASE):
                logger.debug(f"Detected {pattern_name} pattern in value: {value[:50]}")
                return (pattern_name, pattern)
        
        return None
    
    def extract_endpoints(self, spec: Any) -> list[Endpoint]:
        """
        Extract endpoints from JSON data.
        
        For JSON inference, we create a single GET endpoint.
        
        Args:
            spec: JSON data (not used, endpoint is synthetic)
            
        Returns:
            List with single endpoint
        """
        # This is handled in parse() method
        return []
    
    def extract_models(self, spec: Any) -> dict[str, ModelSchema]:
        """
        Extract models from JSON data.
        
        Args:
            spec: JSON data
            
        Returns:
            Dictionary of inferred models
        """
        # This is handled in parse() method
        return {}
    
    def analyze_multiple_samples(self, samples: list[dict[str, Any]]) -> ModelSchema:
        """
        Analyze multiple JSON samples to detect optional fields.
        
        This method compares multiple samples to determine which fields
        are consistently present (required) vs sometimes missing (optional).
        
        Args:
            samples: List of JSON objects to analyze
            
        Returns:
            ModelSchema with accurate required/optional field detection
        """
        if not samples:
            raise ParserError("No samples provided for analysis")
        
        # Collect all field names across samples
        all_fields: dict[str, list[Any]] = {}
        
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            
            for key, value in sample.items():
                if key not in all_fields:
                    all_fields[key] = []
                all_fields[key].append(value)
        
        # Infer fields
        fields: list[FieldSchema] = []
        
        for field_name, values in all_fields.items():
            # Determine if field is required (present in all samples)
            is_required = len(values) == len(samples)
            
            # Infer type from first non-None value
            non_none_values = [v for v in values if v is not None]
            if non_none_values:
                representative_value = non_none_values[0]
            else:
                representative_value = None
            
            # Create field
            field = self._infer_field_from_value(field_name, representative_value)
            field.required = is_required
            
            fields.append(field)
        
        return ModelSchema(
            name="InferredModel",
            fields=fields,
            description=f"Inferred from {len(samples)} samples",
            example=None
        )

# Made with Bob

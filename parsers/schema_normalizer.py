"""
Schema normalization and validation.

This module provides final validation and normalization of APISchema objects
to ensure consistency and correctness before code generation.
"""

from typing import Any

from loguru import logger

from core.exceptions import ParserError
from schemas import APISchema, Endpoint, FieldSchema, FieldType, ModelSchema


class SchemaNormalizer:
    """
    Schema normalizer and validator.
    
    This class performs final validation and normalization on APISchema objects:
    - Validates schema consistency
    - Resolves model references
    - Normalizes field names and types
    - Detects circular dependencies
    - Ensures all required models exist
    """
    
    def __init__(self, api_schema: APISchema):
        """
        Initialize schema normalizer.
        
        Args:
            api_schema: APISchema to normalize and validate
        """
        self.api_schema = api_schema
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def normalize(self) -> APISchema:
        """
        Normalize and validate the API schema.
        
        Returns:
            Normalized APISchema
            
        Raises:
            ParserError: If validation fails
        """
        logger.info("Normalizing and validating API schema")
        
        # Run validation checks
        self._validate_basic_info()
        self._validate_endpoints()
        self._validate_models()
        self._validate_model_references()
        self._detect_circular_dependencies()
        self._normalize_field_names()
        self._validate_field_types()
        
        # Log warnings
        for warning in self.warnings:
            logger.warning(warning)
        
        # Check for errors
        if self.errors:
            error_msg = "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in self.errors)
            logger.error(error_msg)
            raise ParserError(
                "Schema normalization failed",
                details={"errors": self.errors, "warnings": self.warnings}
            )
        
        logger.info(
            f"Schema normalized successfully: "
            f"{len(self.api_schema.endpoints)} endpoints, "
            f"{len(self.api_schema.models)} models, "
            f"{len(self.warnings)} warnings"
        )
        
        return self.api_schema
    
    def _validate_basic_info(self) -> None:
        """Validate basic API information."""
        if not self.api_schema.title:
            self.errors.append("API title is required")
        
        if not self.api_schema.version:
            self.errors.append("API version is required")
        
        if not self.api_schema.base_url:
            self.errors.append("Base URL is required")
        
        # Validate base URL format
        if self.api_schema.base_url and not (
            self.api_schema.base_url.startswith("http://") or
            self.api_schema.base_url.startswith("https://")
        ):
            self.warnings.append(f"Base URL should start with http:// or https://: {self.api_schema.base_url}")
    
    def _validate_endpoints(self) -> None:
        """Validate all endpoints."""
        if not self.api_schema.endpoints:
            self.warnings.append("No endpoints defined in API schema")
            return
        
        # Check for duplicate endpoints
        endpoint_signatures = set()
        for endpoint in self.api_schema.endpoints:
            signature = (endpoint.path, endpoint.method)
            if signature in endpoint_signatures:
                self.errors.append(f"Duplicate endpoint: {endpoint.method} {endpoint.path}")
            endpoint_signatures.add(signature)
            
            # Validate individual endpoint
            self._validate_endpoint(endpoint)
    
    def _validate_endpoint(self, endpoint: Endpoint) -> None:
        """
        Validate a single endpoint.
        
        Args:
            endpoint: Endpoint to validate
        """
        # Validate path
        if not endpoint.path:
            self.errors.append("Endpoint path is required")
        elif not endpoint.path.startswith("/"):
            self.warnings.append(f"Endpoint path should start with /: {endpoint.path}")
        
        # Validate method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
        if endpoint.method not in valid_methods:
            self.errors.append(f"Invalid HTTP method: {endpoint.method}")
        
        # Validate response model exists
        if endpoint.response_model:
            self._validate_model_exists(endpoint.response_model, f"endpoint {endpoint.path}")
        
        # Validate request model exists (if present)
        if endpoint.request_model:
            self._validate_model_exists(endpoint.request_model, f"endpoint {endpoint.path}")
        
        # Validate parameters
        for param in endpoint.parameters:
            if param.location not in ["path", "query", "header", "cookie"]:
                self.errors.append(
                    f"Invalid parameter location '{param.location}' in {endpoint.path}"
                )
    
    def _validate_models(self) -> None:
        """Validate all models."""
        if not self.api_schema.models:
            self.warnings.append("No models defined in API schema")
            return
        
        for model_name, model in self.api_schema.models.items():
            self._validate_model(model_name, model)
    
    def _validate_model(self, model_name: str, model: ModelSchema) -> None:
        """
        Validate a single model.
        
        Args:
            model_name: Model name (key in models dict)
            model: ModelSchema to validate
        """
        # Validate model name matches
        if model.name != model_name:
            self.warnings.append(
                f"Model name mismatch: key='{model_name}', name='{model.name}'"
            )
        
        # Validate fields
        if not model.fields:
            self.warnings.append(f"Model '{model_name}' has no fields")
            return
        
        # Check for duplicate field names
        field_names = set()
        for field in model.fields:
            if field.name in field_names:
                self.errors.append(f"Duplicate field '{field.name}' in model '{model_name}'")
            field_names.add(field.name)
            
            # Validate individual field
            self._validate_field(field, model_name)
    
    def _validate_field(self, field: FieldSchema, model_name: str) -> None:
        """
        Validate a single field.
        
        Args:
            field: FieldSchema to validate
            model_name: Name of containing model
        """
        # Validate field name
        if not field.name:
            self.errors.append(f"Field name is required in model '{model_name}'")
        
        # Validate field type
        if not isinstance(field.type, FieldType):
            self.errors.append(
                f"Invalid field type for '{field.name}' in model '{model_name}': {field.type}"
            )
        
        # Validate array fields
        if field.type == FieldType.ARRAY:
            if field.item_type is None:
                self.warnings.append(
                    f"Array field '{field.name}' in model '{model_name}' has no item_type"
                )
            
            # Validate min/max items
            if field.min_items is not None and field.max_items is not None:
                if field.min_items > field.max_items:
                    self.errors.append(
                        f"Field '{field.name}' in model '{model_name}': "
                        f"min_items ({field.min_items}) > max_items ({field.max_items})"
                    )
        
        # Validate object fields
        if field.type == FieldType.OBJECT:
            if field.nested_model is None:
                self.warnings.append(
                    f"Object field '{field.name}' in model '{model_name}' has no nested_model"
                )
        
        # Validate string constraints
        if field.type == FieldType.STRING:
            if field.min_length is not None and field.max_length is not None:
                if field.min_length > field.max_length:
                    self.errors.append(
                        f"Field '{field.name}' in model '{model_name}': "
                        f"min_length ({field.min_length}) > max_length ({field.max_length})"
                    )
        
        # Validate numeric constraints
        if field.type in [FieldType.INTEGER, FieldType.FLOAT]:
            if field.min_value is not None and field.max_value is not None:
                if field.min_value > field.max_value:
                    self.errors.append(
                        f"Field '{field.name}' in model '{model_name}': "
                        f"min_value ({field.min_value}) > max_value ({field.max_value})"
                    )
    
    def _validate_model_references(self) -> None:
        """Validate that all model references exist."""
        # Collect all referenced models
        referenced_models = set()
        
        # From endpoints
        for endpoint in self.api_schema.endpoints:
            if endpoint.response_model:
                referenced_models.add(endpoint.response_model.name)
            if endpoint.request_model:
                referenced_models.add(endpoint.request_model.name)
        
        # From nested fields
        for model in self.api_schema.models.values():
            for field in model.fields:
                if field.nested_model:
                    referenced_models.add(field.nested_model)
        
        # Check if all referenced models exist
        for ref_model in referenced_models:
            if ref_model not in self.api_schema.models:
                self.errors.append(f"Referenced model '{ref_model}' does not exist")
    
    def _validate_model_exists(self, model: ModelSchema, context: str) -> None:
        """
        Validate that a model exists in the schema.
        
        Args:
            model: ModelSchema to check
            context: Context for error message
        """
        if model.name not in self.api_schema.models:
            # Check if it's an inline model (not in models dict)
            if not model.fields:
                self.warnings.append(
                    f"Model '{model.name}' referenced in {context} has no fields"
                )
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies in model references."""
        for model_name, model in self.api_schema.models.items():
            visited = set()
            if self._has_circular_dependency(model_name, visited):
                self.errors.append(f"Circular dependency detected in model '{model_name}'")
    
    def _has_circular_dependency(
        self,
        model_name: str,
        visited: set[str],
        path: list[str] | None = None
    ) -> bool:
        """
        Check if a model has circular dependencies.
        
        Args:
            model_name: Model to check
            visited: Set of visited models
            path: Current path (for error reporting)
            
        Returns:
            True if circular dependency detected
        """
        if path is None:
            path = []
        
        if model_name in visited:
            # Circular dependency found
            cycle = " -> ".join(path + [model_name])
            logger.debug(f"Circular dependency: {cycle}")
            return True
        
        if model_name not in self.api_schema.models:
            return False
        
        visited.add(model_name)
        path.append(model_name)
        
        model = self.api_schema.models[model_name]
        for field in model.fields:
            if field.nested_model:
                if self._has_circular_dependency(field.nested_model, visited.copy(), path.copy()):
                    return True
        
        return False
    
    def _normalize_field_names(self) -> None:
        """Normalize field names to snake_case."""
        from core.utils import normalize_field_name
        
        for model in self.api_schema.models.values():
            for field in model.fields:
                normalized = normalize_field_name(field.name)
                if normalized != field.name:
                    logger.debug(f"Normalized field name: {field.name} -> {normalized}")
                    field.name = normalized
    
    def _validate_field_types(self) -> None:
        """Validate field type consistency."""
        for model_name, model in self.api_schema.models.items():
            for field in model.fields:
                # Validate enum values match field type
                if field.enum_values:
                    self._validate_enum_values(field, model_name)
                
                # Validate default value matches field type
                if field.default is not None:
                    self._validate_default_value(field, model_name)
    
    def _validate_enum_values(self, field: FieldSchema, model_name: str) -> None:
        """
        Validate enum values match field type.
        
        Args:
            field: Field with enum values
            model_name: Name of containing model
        """
        if not field.enum_values:
            return
        
        expected_type = self._get_python_type(field.type)
        if expected_type is None:
            return
        
        for value in field.enum_values:
            if not isinstance(value, expected_type):
                self.warnings.append(
                    f"Enum value {value} in field '{field.name}' of model '{model_name}' "
                    f"does not match field type {field.type}"
                )
    
    def _validate_default_value(self, field: FieldSchema, model_name: str) -> None:
        """
        Validate default value matches field type.
        
        Args:
            field: Field with default value
            model_name: Name of containing model
        """
        if field.default is None:
            return
        
        expected_type = self._get_python_type(field.type)
        if expected_type is None:
            return
        
        if not isinstance(field.default, expected_type):
            self.warnings.append(
                f"Default value {field.default} in field '{field.name}' of model '{model_name}' "
                f"does not match field type {field.type}"
            )
    
    def _get_python_type(self, field_type: FieldType) -> type | None:
        """
        Get Python type for FieldType.
        
        Args:
            field_type: FieldType to convert
            
        Returns:
            Python type or None if not applicable
        """
        type_map = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: float,
            FieldType.BOOLEAN: bool,
            FieldType.ARRAY: list,
            FieldType.OBJECT: dict,
            FieldType.EMAIL: str,
            FieldType.URL: str,
            FieldType.UUID: str,
            FieldType.DATE: str,
            FieldType.DATETIME: str,
        }
        return type_map.get(field_type)
    
    def get_validation_report(self) -> dict[str, Any]:
        """
        Get validation report.
        
        Returns:
            Dictionary with validation results
        """
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": {
                "endpoints": len(self.api_schema.endpoints),
                "models": len(self.api_schema.models),
                "total_fields": sum(len(m.fields) for m in self.api_schema.models.values())
            }
        }

# Made with Bob

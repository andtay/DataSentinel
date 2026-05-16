"""
Abstract base parser for API specifications.

This module defines the interface that all parsers must implement,
ensuring consistent behavior across different input formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from core.auth_manager import AuthHandler
from core.exceptions import ParserError
from schemas import APISchema, Endpoint, ModelSchema


class BaseParser(ABC):
    """
    Abstract base class for all API specification parsers.

    All parsers (OpenAPI, GraphQL, JSON) must implement this interface
    to ensure they produce consistent APISchema output.

    Contract:
    1. Accept source (file path or URL) in __init__
    2. Implement async parse() returning APISchema
    3. Handle errors gracefully with ParserError
    4. Provide helper methods for common operations
    """

    def __init__(self, source: str | Path, auth_handler: AuthHandler | None = None):
        """
        Initialize parser with source.

        Args:
            source: File path or URL to API specification
            auth_handler: Optional authentication handler used by parsers that
                fetch the spec over HTTP (e.g. GraphQL introspection). Parsers
                that read from local files can ignore it.
        """
        self.source = str(source)
        self.auth_handler = auth_handler
        logger.debug(f"Initialized {self.__class__.__name__} with source: {self.source}")
    
    @abstractmethod
    async def parse(self) -> APISchema:
        """
        Parse input and return normalized APISchema.
        
        This is the main entry point for all parsers. It should:
        1. Load/fetch the specification
        2. Parse the specification format
        3. Extract endpoints and models
        4. Return normalized APISchema
        
        Returns:
            APISchema: Normalized API specification
            
        Raises:
            ParserError: If parsing fails
        """
        pass
    
    @abstractmethod
    def extract_endpoints(self, spec: Any) -> list[Endpoint]:
        """
        Extract all endpoints from specification.
        
        Args:
            spec: Parsed specification (format depends on parser)
            
        Returns:
            List of Endpoint objects
            
        Raises:
            ParserError: If endpoint extraction fails
        """
        pass
    
    @abstractmethod
    def extract_models(self, spec: Any) -> dict[str, ModelSchema]:
        """
        Extract all data models from specification.
        
        Args:
            spec: Parsed specification (format depends on parser)
            
        Returns:
            Dictionary mapping model names to ModelSchema objects
            
        Raises:
            ParserError: If model extraction fails
        """
        pass
    
    def validate_source(self) -> bool:
        """
        Validate that source is accessible and valid.
        
        This method checks if the source exists (for files) or is reachable
        (for URLs) before attempting to parse.
        
        Returns:
            True if source is valid, False otherwise
        """
        from core.utils import is_url
        
        if is_url(self.source):
            # For URLs, we'll validate during fetch
            return True
        
        # For files, check if they exist
        path = Path(self.source)
        if not path.exists():
            logger.error(f"Source file does not exist: {self.source}")
            return False
        
        if not path.is_file():
            logger.error(f"Source is not a file: {self.source}")
            return False
        
        return True
    
    def _load_file(self, path: Path) -> dict[str, Any]:
        """
        Load specification from file.
        
        Supports JSON and YAML formats based on file extension.
        
        Args:
            path: Path to specification file
            
        Returns:
            Parsed specification as dictionary
            
        Raises:
            ParserError: If file cannot be loaded or parsed
        """
        from core.utils import load_json_file, load_yaml_file
        
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                logger.debug(f"Loading YAML file: {path}")
                return load_yaml_file(path)
            elif path.suffix.lower() == '.json':
                logger.debug(f"Loading JSON file: {path}")
                return load_json_file(path)
            else:
                raise ParserError(
                    f"Unsupported file format: {path.suffix}",
                    details={"path": str(path), "suffix": path.suffix}
                )
        except Exception as e:
            logger.error(f"Failed to load file {path}: {e}")
            raise ParserError(
                f"Failed to load specification file: {e}",
                details={"path": str(path)}
            )
    
    async def _fetch_url(self, url: str) -> dict[str, Any]:
        """
        Fetch specification from URL.
        
        Args:
            url: URL to specification
            
        Returns:
            Parsed specification as dictionary
            
        Raises:
            ParserError: If URL cannot be fetched or parsed
        """
        from core.base_provider import SimpleProvider
        
        try:
            logger.debug(f"Fetching specification from URL: {url}")
            
            # Extract base URL and path
            from core.utils import extract_base_url
            base_url = extract_base_url(url)
            path = url[len(base_url):]
            
            # Fetch using SimpleProvider
            async with SimpleProvider(base_url) as provider:
                data = await provider.fetch(path)
                return data
                
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise ParserError(
                f"Failed to fetch specification from URL: {e}",
                details={"url": url}
            )
    
    def _normalize_model_name(self, name: str) -> str:
        """
        Normalize model name to PascalCase.
        
        Args:
            name: Original model name
            
        Returns:
            Normalized model name in PascalCase
        """
        import re
        # First, handle camelCase by inserting underscores before capitals
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        
        # Replace hyphens and spaces with underscores
        name = name.replace('-', '_').replace(' ', '_')
        
        # Remove other special characters
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        
        # Convert to PascalCase
        parts = name.split('_')
        return ''.join(word.capitalize() for word in parts if word)
    
    def _normalize_field_name(self, name: str) -> str:
        """
        Normalize field name to snake_case.
        
        Args:
            name: Original field name
            
        Returns:
            Normalized field name in snake_case
        """
        from core.utils import normalize_field_name
        return normalize_field_name(name)
    
    def _generate_model_name(self, endpoint_path: str, suffix: str = "Response") -> str:
        """
        Generate a model name from endpoint path.
        
        Args:
            endpoint_path: API endpoint path (e.g., /users/{id})
            suffix: Suffix to add to model name
            
        Returns:
            Generated model name in PascalCase
        """
        # Extract path parts (excluding parameters)
        parts = [p for p in endpoint_path.split('/') if p and not p.startswith('{')]
        
        if not parts:
            return f"Default{suffix}"
        
        # Convert to PascalCase
        name = ''.join(word.capitalize() for word in parts)
        return f"{name}{suffix}"
    
    def _deduplicate_models(self, models: dict[str, ModelSchema]) -> dict[str, ModelSchema]:
        """
        Remove duplicate models with identical structures.
        
        Args:
            models: Dictionary of models
            
        Returns:
            Dictionary with duplicates removed
        """
        # Create a mapping of field signatures to model names
        signature_to_name: dict[tuple[tuple[str, str, bool], ...], str] = {}
        deduplicated: dict[str, ModelSchema] = {}
        
        for name, model in models.items():
            # Create signature from field names and types
            field_sig = tuple(
                (f.name, f.type.value, f.required)
                for f in sorted(model.fields, key=lambda x: x.name)
            )
            
            if field_sig in signature_to_name:
                # Duplicate found, use existing model
                logger.debug(
                    f"Model {name} is duplicate of {signature_to_name[field_sig]}"
                )
            else:
                # New unique model
                signature_to_name[field_sig] = name
                deduplicated[name] = model
        
        if len(deduplicated) < len(models):
            logger.info(
                f"Deduplicated {len(models) - len(deduplicated)} models "
                f"({len(models)} -> {len(deduplicated)})"
            )
        
        return deduplicated
    
    def _validate_parsed_schema(self, api_schema: APISchema) -> None:
        """
        Validate parsed schema for consistency.
        
        Args:
            api_schema: Parsed API schema
            
        Raises:
            ParserError: If schema validation fails
        """
        errors = api_schema.validate_schema()
        
        if errors:
            error_msg = "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ParserError(
                "Parsed schema has validation errors",
                details={"errors": errors}
            )
        
        logger.debug("Schema validation passed")

# Made with Bob

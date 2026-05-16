"""
OpenAPI/Swagger specification parser.

This module implements a deterministic parser for OpenAPI 3.x and Swagger 2.x
specifications. It uses prance for $ref resolution and provides complete
schema extraction with validation rules.
"""

from pathlib import Path
from typing import Any

from loguru import logger
from prance import ResolvingParser

from core.exceptions import ParserError
from core.utils import is_url
from parsers.base_parser import BaseParser
from schemas import (
    APISchema,
    AuthConfig,
    Endpoint,
    FieldSchema,
    FieldType,
    ModelSchema,
    Parameter,
    OPENAPI_TYPE_MAP,
)


class OpenAPIParser(BaseParser):
    """
    OpenAPI/Swagger specification parser.
    
    This parser handles:
    - OpenAPI 3.x specifications
    - Swagger 2.x specifications
    - $ref resolution (via prance)
    - Complete schema extraction with validation rules
    - Authentication configuration
    """
    
    def __init__(self, source: str | Path, auth_handler=None):
        """
        Initialize OpenAPI parser.

        Args:
            source: Path to OpenAPI file or URL to specification
            auth_handler: Optional AuthHandler (forwarded to BaseParser).
        """
        super().__init__(source, auth_handler=auth_handler)
        self.spec: dict[str, Any] = {}
        self.openapi_version: str = ""
    
    async def parse(self) -> APISchema:
        """
        Parse OpenAPI specification.
        
        Returns:
            APISchema with extracted endpoints and models
            
        Raises:
            ParserError: If specification cannot be parsed
        """
        logger.info(f"Parsing OpenAPI specification from: {self.source}")
        
        # Validate source
        if not self.validate_source():
            raise ParserError(f"Invalid source: {self.source}")
        
        # Load and resolve specification
        self.spec = await self._load_and_resolve_spec()
        
        # Detect OpenAPI version
        self.openapi_version = self._detect_version()
        logger.info(f"Detected OpenAPI version: {self.openapi_version}")
        
        # Extract base information
        title = self.spec.get("info", {}).get("title", "API")
        version = self.spec.get("info", {}).get("version", "1.0.0")
        description = self.spec.get("info", {}).get("description")
        
        # Extract base URL
        base_url = self._extract_base_url()
        
        # Extract authentication configuration
        auth_config = self._extract_auth_config()
        
        # Extract endpoints
        endpoints = self.extract_endpoints(self.spec)
        
        # Extract models from components/definitions
        models = self.extract_models(self.spec)
        
        # Deduplicate models
        models = self._deduplicate_models(models)
        
        # Create API schema
        api_schema = APISchema(
            title=title,
            version=version,
            base_url=base_url,
            description=description,
            endpoints=endpoints,
            models=models,
            auth_config=auth_config
        )
        
        # Validate
        self._validate_parsed_schema(api_schema)
        
        logger.info(
            f"Successfully parsed OpenAPI spec: "
            f"{len(api_schema.endpoints)} endpoints, "
            f"{len(api_schema.models)} models"
        )
        
        return api_schema
    
    async def _load_and_resolve_spec(self) -> dict[str, Any]:
        """
        Load and resolve OpenAPI specification with $ref resolution.
        
        Returns:
            Resolved specification dictionary
            
        Raises:
            ParserError: If specification cannot be loaded or resolved
        """
        try:
            # Convert source to string for prance
            source_str = str(self.source)
            
            # Use prance to load and resolve $refs
            parser = ResolvingParser(source_str, backend="openapi-spec-validator")
            
            return parser.specification
            
        except Exception as e:
            logger.error(f"Failed to load/resolve OpenAPI spec: {e}")
            raise ParserError(
                f"Failed to parse OpenAPI specification: {e}",
                details={"source": str(self.source)}
            )
    
    def _detect_version(self) -> str:
        """
        Detect OpenAPI/Swagger version.
        
        Returns:
            Version string (e.g., "3.0.0", "2.0")
        """
        if "openapi" in self.spec:
            return self.spec["openapi"]
        elif "swagger" in self.spec:
            return self.spec["swagger"]
        else:
            logger.warning("Could not detect OpenAPI version, assuming 3.0.0")
            return "3.0.0"
    
    def _extract_base_url(self) -> str:
        """
        Extract base URL from specification.
        
        Returns:
            Base URL for API
        """
        # OpenAPI 3.x uses servers array
        if "servers" in self.spec and self.spec["servers"]:
            return self.spec["servers"][0].get("url", "http://localhost")
        
        # Swagger 2.x uses host + basePath + schemes
        if "host" in self.spec:
            scheme = self.spec.get("schemes", ["https"])[0]
            host = self.spec["host"]
            base_path = self.spec.get("basePath", "")
            return f"{scheme}://{host}{base_path}"
        
        # If source is URL, extract base
        if is_url(self.source):
            from core.utils import extract_base_url
            return extract_base_url(self.source)
        
        return "http://localhost"
    
    def _extract_auth_config(self) -> AuthConfig | None:
        """
        Extract authentication configuration.
        
        Returns:
            AuthConfig if authentication is defined, None otherwise
        """
        # OpenAPI 3.x security schemes
        if "components" in self.spec and "securitySchemes" in self.spec["components"]:
            schemes = self.spec["components"]["securitySchemes"]
            # Use first scheme for simplicity
            if schemes:
                scheme_name, scheme_def = next(iter(schemes.items()))
                return self._parse_security_scheme(scheme_def)
        
        # Swagger 2.x security definitions
        if "securityDefinitions" in self.spec:
            defs = self.spec["securityDefinitions"]
            if defs:
                scheme_name, scheme_def = next(iter(defs.items()))
                return self._parse_security_scheme(scheme_def)
        
        return None
    
    def _parse_security_scheme(self, scheme: dict[str, Any]) -> AuthConfig:
        """
        Parse a security scheme definition.
        
        Args:
            scheme: Security scheme definition
            
        Returns:
            AuthConfig object
        """
        scheme_type = scheme.get("type", "").lower()
        
        if scheme_type == "apikey":
            return AuthConfig(
                type="api_key",
                location=scheme.get("in", "header"),
                name=scheme.get("name", "X-API-Key"),
                scheme=None,
                token_url=None,
                authorization_url=None,
                scopes=None
            )
        
        elif scheme_type == "http":
            http_scheme = scheme.get("scheme", "bearer").lower()
            return AuthConfig(
                type="bearer" if http_scheme == "bearer" else "api_key",
                location="header",
                name="Authorization",
                scheme=http_scheme.capitalize(),
                token_url=None,
                authorization_url=None,
                scopes=None
            )
        
        elif scheme_type == "oauth2":
            flows = scheme.get("flows", {})
            # Get first flow
            flow_type = next(iter(flows.keys()), None)
            if flow_type:
                flow = flows[flow_type]
                return AuthConfig(
                    type="oauth2",
                    location="header",
                    name="Authorization",
                    scheme="Bearer",
                    token_url=flow.get("tokenUrl"),
                    authorization_url=flow.get("authorizationUrl"),
                    scopes=flow.get("scopes", {})
                )
        
        # Default to no auth
        return AuthConfig(
            type="none",
            location=None,
            name=None,
            scheme=None,
            token_url=None,
            authorization_url=None,
            scopes=None
        )
    
    def extract_endpoints(self, spec: dict[str, Any]) -> list[Endpoint]:
        """
        Extract endpoints from OpenAPI paths.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            List of Endpoint objects
        """
        endpoints: list[Endpoint] = []
        paths = spec.get("paths", {})
        
        for path, path_item in paths.items():
            # Skip $ref and other special keys
            if path.startswith("$"):
                continue
            
            # Extract operations (GET, POST, etc.)
            for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if method not in path_item:
                    continue
                
                operation = path_item[method]
                
                # Extract endpoint details
                endpoint = self._parse_operation(path, method.upper(), operation)
                endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_operation(
        self,
        path: str,
        method: str,
        operation: dict[str, Any]
    ) -> Endpoint:
        """
        Parse a single operation into an Endpoint.
        
        Args:
            path: Endpoint path
            method: HTTP method
            operation: Operation definition
            
        Returns:
            Endpoint object
        """
        # Basic info
        summary = operation.get("summary")
        description = operation.get("description")
        operation_id = operation.get("operationId")
        tags = operation.get("tags", [])
        deprecated = operation.get("deprecated", False)
        
        # Parameters
        parameters = self._parse_parameters(operation.get("parameters", []))
        
        # Request body (OpenAPI 3.x)
        request_model = None
        if "requestBody" in operation:
            request_model = self._parse_request_body(operation["requestBody"])
        
        # Response (use 200/201 response)
        response_model = self._parse_response(operation.get("responses", {}))
        
        # Auth required (check if security is defined)
        auth_required = "security" in operation or "security" in self.spec
        
        return Endpoint(
            path=path,
            method=method,
            summary=summary,
            description=description,
            operation_id=operation_id,
            request_model=request_model,
            response_model=response_model,
            parameters=parameters,
            auth_required=auth_required,
            tags=tags,
            deprecated=deprecated
        )
    
    def _parse_parameters(self, params: list[dict[str, Any]]) -> list[Parameter]:
        """
        Parse operation parameters.
        
        Args:
            params: List of parameter definitions
            
        Returns:
            List of Parameter objects
        """
        parameters: list[Parameter] = []
        
        for param in params:
            # Get parameter schema
            if "schema" in param:
                # OpenAPI 3.x
                param_schema = param["schema"]
            else:
                # Swagger 2.x - parameter IS the schema
                param_schema = param
            
            # Create field schema
            field_schema = self._schema_to_field(
                param.get("name", "param"),
                param_schema
            )
            
            # Create parameter
            parameter = Parameter(
                name=param.get("name", "param"),
                location=param.get("in", "query"),
                required=param.get("required", False),
                field_schema=field_schema,
                description=param.get("description"),
                deprecated=param.get("deprecated", False)
            )
            
            parameters.append(parameter)
        
        return parameters
    
    def _parse_request_body(self, request_body: dict[str, Any]) -> ModelSchema | None:
        """
        Parse request body into a model.
        
        Args:
            request_body: Request body definition
            
        Returns:
            ModelSchema if body is defined, None otherwise
        """
        content = request_body.get("content", {})
        
        # Try JSON content type first
        for content_type in ["application/json", "application/*", "*/*"]:
            if content_type in content:
                media_type = content[content_type]
                if "schema" in media_type:
                    return self._schema_to_model(
                        "RequestBody",
                        media_type["schema"]
                    )
        
        return None
    
    def _parse_response(self, responses: dict[str, Any]) -> ModelSchema:
        """
        Parse response into a model.
        
        Args:
            responses: Responses definition
            
        Returns:
            ModelSchema for successful response
        """
        # Try success status codes in order
        for status in ["200", "201", "202", "204", "default"]:
            if status not in responses:
                continue
            
            response = responses[status]
            
            # OpenAPI 3.x
            if "content" in response:
                content = response["content"]
                for content_type in ["application/json", "application/*", "*/*"]:
                    if content_type in content:
                        media_type = content[content_type]
                        if "schema" in media_type:
                            return self._schema_to_model(
                                "Response",
                                media_type["schema"]
                            )
            
            # Swagger 2.x
            if "schema" in response:
                return self._schema_to_model("Response", response["schema"])
        
        # Default empty response
        return ModelSchema(
            name="EmptyResponse",
            fields=[],
            description="Empty response",
            example=None
        )
    
    def extract_models(self, spec: dict[str, Any]) -> dict[str, ModelSchema]:
        """
        Extract models from components/definitions.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            Dictionary of model name to ModelSchema
        """
        models: dict[str, ModelSchema] = {}
        
        # OpenAPI 3.x components/schemas
        if "components" in spec and "schemas" in spec["components"]:
            schemas = spec["components"]["schemas"]
            for name, schema in schemas.items():
                model = self._schema_to_model(name, schema)
                models[model.name] = model
        
        # Swagger 2.x definitions
        if "definitions" in spec:
            definitions = spec["definitions"]
            for name, schema in definitions.items():
                model = self._schema_to_model(name, schema)
                models[model.name] = model
        
        return models
    
    def _schema_to_model(self, name: str, schema: dict[str, Any]) -> ModelSchema:
        """
        Convert OpenAPI schema to ModelSchema.
        
        Args:
            name: Model name
            schema: OpenAPI schema definition
            
        Returns:
            ModelSchema object
        """
        # Normalize name
        model_name = self._normalize_model_name(name)
        
        # Get properties
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        
        # Convert properties to fields
        fields: list[FieldSchema] = []
        for field_name, field_schema in properties.items():
            field = self._schema_to_field(field_name, field_schema)
            field.required = field_name in required_fields
            fields.append(field)
        
        # Get description and example
        description = schema.get("description")
        example = schema.get("example")
        
        return ModelSchema(
            name=model_name,
            fields=fields,
            description=description,
            example=example
        )
    
    def _schema_to_field(self, name: str, schema: dict[str, Any]) -> FieldSchema:
        """
        Convert OpenAPI schema to FieldSchema.
        
        Args:
            name: Field name
            schema: OpenAPI schema definition
            
        Returns:
            FieldSchema object
        """
        # Normalize field name
        field_name = self._normalize_field_name(name)
        
        # Get type
        openapi_type = schema.get("type", "string")
        openapi_format = schema.get("format")
        
        # Map to FieldType
        field_type = self._map_openapi_type(openapi_type, openapi_format)
        
        # Create field
        field = FieldSchema(
            name=field_name,
            type=field_type,
            required=True,  # Will be set by caller
            description=schema.get("description"),
            default=schema.get("default"),
            pattern=schema.get("pattern"),
            min_length=schema.get("minLength"),
            max_length=schema.get("maxLength"),
            min_value=schema.get("minimum"),
            max_value=schema.get("maximum"),
            multiple_of=schema.get("multipleOf"),
            enum_values=schema.get("enum"),
            item_type=None,
            min_items=schema.get("minItems"),
            max_items=schema.get("maxItems"),
            unique_items=schema.get("uniqueItems", False),
            nested_model=None,
            additional_properties=schema.get("additionalProperties", False) if isinstance(schema.get("additionalProperties"), bool) else False,
            example=schema.get("example"),
            deprecated=schema.get("deprecated", False),
            read_only=schema.get("readOnly", False),
            write_only=schema.get("writeOnly", False)
        )
        
        # Handle array items
        if field_type == FieldType.ARRAY and "items" in schema:
            items_schema = schema["items"]
            items_type = items_schema.get("type", "string")
            items_format = items_schema.get("format")
            field.item_type = self._map_openapi_type(items_type, items_format)
            
            # If items are objects, set nested model
            if items_type == "object":
                field.nested_model = self._normalize_model_name(f"{name}Item")
        
        # Handle nested objects
        if field_type == FieldType.OBJECT:
            field.nested_model = self._normalize_model_name(name)
        
        return field
    
    def _map_openapi_type(self, openapi_type: str, openapi_format: str | None = None) -> FieldType:
        """
        Map OpenAPI type and format to FieldType.
        
        Args:
            openapi_type: OpenAPI type (string, integer, etc.)
            openapi_format: OpenAPI format (email, uuid, etc.)
            
        Returns:
            Corresponding FieldType
        """
        # Create lookup key as tuple
        lookup_key = (openapi_type, openapi_format)
        
        # Try exact match first (type + format)
        if lookup_key in OPENAPI_TYPE_MAP:
            return OPENAPI_TYPE_MAP[lookup_key]
        
        # Fall back to type only (type, None)
        fallback_key = (openapi_type, None)
        if fallback_key in OPENAPI_TYPE_MAP:
            return OPENAPI_TYPE_MAP[fallback_key]
        
        # Default to STRING
        logger.warning(f"Unknown OpenAPI type: {openapi_type}:{openapi_format}, defaulting to STRING")
        return FieldType.STRING

# Made with Bob

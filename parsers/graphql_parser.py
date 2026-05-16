"""
GraphQL introspection-based parser.

This module implements a parser that uses GraphQL introspection queries
to extract schema information from GraphQL APIs.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from core.exceptions import ParserError
from core.utils import is_url
from core.base_provider import SimpleProvider
from parsers.base_parser import BaseParser
from schemas import (
    APISchema,
    AuthConfig,
    Endpoint,
    FieldSchema,
    FieldType,
    ModelSchema,
    Parameter,
    GRAPHQL_TYPE_MAP,
)


# GraphQL introspection query
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type {
    ...TypeRef
  }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


class GraphQLParser(BaseParser):
    """
    GraphQL introspection-based parser.
    
    This parser:
    - Executes introspection query against GraphQL endpoint
    - Extracts types, queries, mutations from schema
    - Converts GraphQL types to normalized APISchema
    - Handles nested types and custom scalars
    """
    
    def __init__(self, source: str | Path, auth_handler=None):
        """
        Initialize GraphQL parser.

        Args:
            source: GraphQL endpoint URL
            auth_handler: Optional AuthHandler used to authenticate the
                introspection request (e.g. Bearer or X-API-Key). Endpoints
                like Bitquery require this; public ones (Rick & Morty) do not.
        """
        super().__init__(source, auth_handler=auth_handler)
        self.schema_data: dict[str, Any] = {}
        self.type_map: dict[str, dict[str, Any]] = {}
    
    async def parse(self) -> APISchema:
        """
        Parse GraphQL schema via introspection.
        
        Returns:
            APISchema with extracted queries, mutations, and types
            
        Raises:
            ParserError: If introspection fails or schema cannot be parsed
        """
        logger.info(f"Parsing GraphQL schema from: {self.source}")
        
        # Validate source (must be URL for GraphQL)
        if not is_url(self.source):
            raise ParserError(
                "GraphQL parser requires a URL endpoint",
                details={"source": str(self.source)}
            )
        
        # Execute introspection query
        self.schema_data = await self._execute_introspection()
        
        # Build type map for easy lookup
        self._build_type_map()
        
        # Extract base information
        title = self._extract_title()
        version = "1.0.0"  # GraphQL doesn't have version in schema
        description = "GraphQL API"
        base_url = str(self.source)
        
        # Extract endpoints (queries and mutations)
        endpoints = self.extract_endpoints(self.schema_data)
        
        # Extract models (types)
        models = self.extract_models(self.schema_data)
        
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
            auth_config=None  # GraphQL auth is typically handled via headers
        )
        
        # Validate
        self._validate_parsed_schema(api_schema)
        
        logger.info(
            f"Successfully parsed GraphQL schema: "
            f"{len(api_schema.endpoints)} endpoints, "
            f"{len(api_schema.models)} models"
        )
        
        return api_schema
    
    async def _execute_introspection(self) -> dict[str, Any]:
        """
        Execute GraphQL introspection query.
        
        Returns:
            Introspection result data
            
        Raises:
            ParserError: If introspection fails
        """
        try:
            # Extract base URL for provider
            from core.utils import extract_base_url
            base_url = extract_base_url(self.source)
            
            # Get path from source
            from urllib.parse import urlparse
            parsed = urlparse(self.source)
            path = parsed.path or "/"
            
            # Execute introspection query (auth header injected by the handler)
            async with SimpleProvider(base_url, auth_handler=self.auth_handler) as provider:
                response = await provider.fetch(
                    path,
                    method="POST",
                    json={"query": INTROSPECTION_QUERY}
                )
                
                # Check for errors
                if "errors" in response:
                    errors = response["errors"]
                    raise ParserError(
                        "GraphQL introspection returned errors",
                        details={"errors": errors}
                    )
                
                # Extract schema data
                if "data" not in response or "__schema" not in response["data"]:
                    raise ParserError(
                        "Invalid introspection response",
                        details={"response": response}
                    )
                
                return response["data"]["__schema"]
                
        except Exception as e:
            logger.error(f"Failed to execute GraphQL introspection: {e}")
            raise ParserError(
                f"GraphQL introspection failed: {e}",
                details={"endpoint": str(self.source)}
            )
    
    def _build_type_map(self) -> None:
        """Build a map of type names to type definitions for easy lookup."""
        self.type_map = {}
        
        for type_def in self.schema_data.get("types", []):
            type_name = type_def.get("name")
            if type_name:
                self.type_map[type_name] = type_def
    
    def _extract_title(self) -> str:
        """
        Extract API title from schema.
        
        Returns:
            API title
        """
        # Try to get from query type name
        query_type = self.schema_data.get("queryType", {})
        if query_type:
            return f"{query_type.get('name', 'GraphQL')} API"
        
        return "GraphQL API"
    
    def extract_endpoints(self, spec: dict[str, Any]) -> list[Endpoint]:
        """
        Extract endpoints from GraphQL queries and mutations.
        
        Args:
            spec: GraphQL schema data
            
        Returns:
            List of Endpoint objects
        """
        endpoints: list[Endpoint] = []
        
        # Extract queries
        query_type_name = spec.get("queryType", {}).get("name")
        if query_type_name and query_type_name in self.type_map:
            query_type = self.type_map[query_type_name]
            for field in query_type.get("fields", []):
                endpoint = self._field_to_endpoint(field, "query")
                endpoints.append(endpoint)
        
        # Extract mutations
        mutation_type = spec.get("mutationType")
        mutation_type_name = mutation_type.get("name") if mutation_type else None
        if mutation_type_name and mutation_type_name in self.type_map:
            mutation_type = self.type_map[mutation_type_name]
            for field in mutation_type.get("fields", []):
                endpoint = self._field_to_endpoint(field, "mutation")
                endpoints.append(endpoint)
        
        return endpoints
    
    def _field_to_endpoint(self, field: dict[str, Any], operation_type: str) -> Endpoint:
        """
        Convert GraphQL field to Endpoint.
        
        Args:
            field: GraphQL field definition
            operation_type: "query" or "mutation"
            
        Returns:
            Endpoint object
        """
        name = field.get("name", "unknown")
        description = field.get("description")
        deprecated = field.get("isDeprecated", False)
        
        # Extract arguments as parameters
        parameters = []
        for arg in field.get("args", []):
            param = self._arg_to_parameter(arg)
            parameters.append(param)
        
        # Extract return type as response model
        return_type = field.get("type", {})
        response_model = self._type_to_model(return_type, f"{name}Response")
        
        # Determine HTTP method (queries are GET-like, mutations are POST-like)
        method = "GET" if operation_type == "query" else "POST"
        
        return Endpoint(
            path=f"/{operation_type}/{name}",
            method=method,
            summary=name,
            description=description,
            operation_id=name,
            request_model=None,  # GraphQL uses parameters, not request body
            response_model=response_model,
            parameters=parameters,
            auth_required=True,  # Assume auth required
            tags=[operation_type],
            deprecated=deprecated
        )
    
    def _arg_to_parameter(self, arg: dict[str, Any]) -> Parameter:
        """
        Convert GraphQL argument to Parameter.
        
        Args:
            arg: GraphQL argument definition
            
        Returns:
            Parameter object
        """
        name = arg.get("name", "param")
        description = arg.get("description")
        arg_type = arg.get("type", {})
        
        # Determine if required (NON_NULL type)
        required = arg_type.get("kind") == "NON_NULL"
        
        # Get the actual type (unwrap NON_NULL if present)
        actual_type = arg_type
        if required:
            actual_type = arg_type.get("ofType", {})
        
        # Create field schema
        field_schema = self._graphql_type_to_field(name, actual_type)
        
        return Parameter(
            name=name,
            location="query",  # GraphQL args are like query params
            required=required,
            field_schema=field_schema,
            description=description,
            deprecated=False
        )
    
    def extract_models(self, spec: dict[str, Any]) -> dict[str, ModelSchema]:
        """
        Extract models from GraphQL types.
        
        Args:
            spec: GraphQL schema data
            
        Returns:
            Dictionary of model name to ModelSchema
        """
        models: dict[str, ModelSchema] = {}
        
        for type_def in spec.get("types", []):
            # Skip built-in types and non-object types
            type_name = type_def.get("name", "")
            type_kind = type_def.get("kind", "")
            
            if type_name.startswith("__"):
                continue  # Skip introspection types
            
            if type_kind not in ["OBJECT", "INPUT_OBJECT"]:
                continue  # Only process object types
            
            # Convert to model
            model = self._type_def_to_model(type_def)
            if model:
                models[model.name] = model
        
        return models
    
    def _type_def_to_model(self, type_def: dict[str, Any]) -> ModelSchema | None:
        """
        Convert GraphQL type definition to ModelSchema.
        
        Args:
            type_def: GraphQL type definition
            
        Returns:
            ModelSchema or None if type should be skipped
        """
        name = type_def.get("name", "Unknown")
        description = type_def.get("description")
        kind = type_def.get("kind", "")
        
        # Get fields
        fields: list[FieldSchema] = []
        
        if kind == "OBJECT":
            for field in type_def.get("fields", []):
                field_schema = self._graphql_field_to_field_schema(field)
                fields.append(field_schema)
        elif kind == "INPUT_OBJECT":
            for input_field in type_def.get("inputFields", []):
                field_schema = self._graphql_input_to_field_schema(input_field)
                fields.append(field_schema)
        
        if not fields:
            return None
        
        return ModelSchema(
            name=self._normalize_model_name(name),
            fields=fields,
            description=description,
            example=None
        )
    
    def _graphql_field_to_field_schema(self, field: dict[str, Any]) -> FieldSchema:
        """
        Convert GraphQL field to FieldSchema.
        
        Args:
            field: GraphQL field definition
            
        Returns:
            FieldSchema object
        """
        name = field.get("name", "field")
        description = field.get("description")
        deprecated = field.get("isDeprecated", False)
        field_type = field.get("type", {})
        
        # Determine if required
        required = field_type.get("kind") == "NON_NULL"
        
        # Get actual type
        actual_type = field_type
        if required:
            actual_type = field_type.get("ofType", {})
        
        # Create field schema
        field_schema = self._graphql_type_to_field(name, actual_type)
        field_schema.required = required
        field_schema.description = description
        field_schema.deprecated = deprecated
        
        return field_schema
    
    def _graphql_input_to_field_schema(self, input_field: dict[str, Any]) -> FieldSchema:
        """
        Convert GraphQL input field to FieldSchema.
        
        Args:
            input_field: GraphQL input field definition
            
        Returns:
            FieldSchema object
        """
        name = input_field.get("name", "field")
        description = input_field.get("description")
        field_type = input_field.get("type", {})
        default_value = input_field.get("defaultValue")
        
        # Determine if required
        required = field_type.get("kind") == "NON_NULL"
        
        # Get actual type
        actual_type = field_type
        if required:
            actual_type = field_type.get("ofType", {})
        
        # Create field schema
        field_schema = self._graphql_type_to_field(name, actual_type)
        field_schema.required = required
        field_schema.description = description
        field_schema.default = default_value
        
        return field_schema
    
    def _graphql_type_to_field(self, name: str, gql_type: dict[str, Any]) -> FieldSchema:
        """
        Convert GraphQL type to FieldSchema.
        
        Args:
            name: Field name
            gql_type: GraphQL type definition
            
        Returns:
            FieldSchema object
        """
        field_name = self._normalize_field_name(name)
        kind = gql_type.get("kind", "")
        type_name = gql_type.get("name", "")
        
        # Handle LIST type
        if kind == "LIST":
            item_type_def = gql_type.get("ofType", {})
            item_type = self._map_graphql_type(item_type_def.get("name", "String"))
            
            return FieldSchema(
                name=field_name,
                type=FieldType.ARRAY,
                required=True,
                description=None,
                default=None,
                pattern=None,
                min_length=None,
                max_length=None,
                min_value=None,
                max_value=None,
                multiple_of=None,
                enum_values=None,
                item_type=item_type,
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
        
        # Handle OBJECT type
        if kind == "OBJECT":
            return FieldSchema(
                name=field_name,
                type=FieldType.OBJECT,
                required=True,
                description=None,
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
                nested_model=self._normalize_model_name(type_name),
                additional_properties=False,
                example=None,
                deprecated=False,
                read_only=False,
                write_only=False
            )
        
        # Handle SCALAR and ENUM types
        field_type = self._map_graphql_type(type_name)
        
        return FieldSchema(
            name=field_name,
            type=field_type,
            required=True,
            description=None,
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
    
    def _type_to_model(self, gql_type: dict[str, Any], model_name: str) -> ModelSchema:
        """
        Convert GraphQL type to ModelSchema for response.
        
        Args:
            gql_type: GraphQL type definition
            model_name: Name for the model
            
        Returns:
            ModelSchema object
        """
        # Unwrap NON_NULL and LIST wrappers
        actual_type = self._unwrap_type(gql_type)
        type_name = actual_type.get("name", "")
        
        # If it's a known type, return reference
        if type_name in self.type_map:
            type_def = self.type_map[type_name]
            model = self._type_def_to_model(type_def)
            if model:
                return model
        
        # Create simple model
        return ModelSchema(
            name=self._normalize_model_name(model_name),
            fields=[],
            description=f"Response for {model_name}",
            example=None
        )
    
    def _unwrap_type(self, gql_type: dict[str, Any]) -> dict[str, Any]:
        """
        Unwrap NON_NULL and LIST wrappers to get actual type.
        
        Args:
            gql_type: GraphQL type definition
            
        Returns:
            Unwrapped type definition
        """
        kind = gql_type.get("kind", "")
        
        if kind in ["NON_NULL", "LIST"]:
            of_type = gql_type.get("ofType", {})
            return self._unwrap_type(of_type)
        
        return gql_type
    
    def _map_graphql_type(self, type_name: str) -> FieldType:
        """
        Map GraphQL type name to FieldType.
        
        Args:
            type_name: GraphQL type name
            
        Returns:
            Corresponding FieldType
        """
        if type_name in GRAPHQL_TYPE_MAP:
            return GRAPHQL_TYPE_MAP[type_name]
        
        # Default to STRING for unknown types
        logger.warning(f"Unknown GraphQL type: {type_name}, defaulting to STRING")
        return FieldType.STRING

# Made with Bob

"""
Auto-generated GraphQL API validators for Query API.

Generated: 2026-05-17T11:16:29.381912Z
API Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Union
import json
import httpx
from loguru import logger
from pydantic import ValidationError

from models import Query, Character, Location, Episode, FilterCharacter, Characters, Info, FilterLocation, FilterEpisode
from exceptions import (
    ValidationException,
    APIException,
    SchemaException,
)
from retry_handler import with_retry


class APIValidator:
    """
    Validates GraphQL API responses against Pydantic models.

    All operations POST to /graphql with a GraphQL query body.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_cache: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.graphql_path = "/graphql"
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._cache: Dict[str, Any] = {}
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(
            f"Initialized GraphQL APIValidator for {base_url}{self.graphql_path} "
            f"(timeout={timeout}s, max_retries={max_retries})"
        )

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    def _get_cache_key(self, query: str) -> str:
        return query

    def _check_cache(self, cache_key: str) -> Optional[Any]:
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]
        return None

    def _update_cache(self, cache_key: str, data: Any) -> None:
        if self.enable_cache:
            self._cache[cache_key] = data

    def _detect_schema_drift(
        self,
        expected_fields: set,
        actual_fields: set,
    ) -> Dict[str, List[str]]:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        drift: Dict[str, List[str]] = {}
        if missing:
            drift["missing"] = sorted(missing)
        if extra:
            drift["extra"] = sorted(extra)
        return drift

    @with_retry(max_attempts=3, base_delay=1.0)
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        if not self._client:
            raise APIException("Client not initialized. Use async context manager.")

        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            raise APIException(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {e}")
            raise APIException(f"Request failed: {str(e)}")

    def _coerce_list_ids(self, value: Any) -> Any:
        """Coerce GraphQL object lists to ID strings when models expect scalars."""
        if not isinstance(value, list):
            return value
        coerced = []
        for item in value:
            if isinstance(item, dict) and "id" in item:
                coerced.append(str(item["id"]))
            else:
                coerced.append(item)
        return coerced

    def _coerce_payload(self, payload: Any) -> Any:
        """Normalize common GraphQL list shapes before Pydantic validation."""
        if not isinstance(payload, dict):
            return payload
        data = dict(payload)
        for key in ("episode", "episodes", "characters", "residents"):
            if key in data:
                data[key] = self._coerce_list_ids(data[key])
        for loc_key in ("origin", "location"):
            if isinstance(data.get(loc_key), dict):
                nested = dict(data[loc_key])
                if "residents" in nested:
                    nested["residents"] = self._coerce_list_ids(nested["residents"])
                data[loc_key] = nested
        if isinstance(data.get("results"), list):
            data["results"] = [
                self._coerce_payload(item) if isinstance(item, dict) else item
                for item in data["results"]
            ]
        return data

    async def _execute_graphql(
        self,
        operation_type: str,
        operation_name: str,
        selection: str,
        args_clause: str,
    ) -> Dict[str, Any]:
        """Execute a GraphQL operation and return the data payload."""
        keyword = "mutation" if operation_type == "mutation" else "query"
        query = (
            keyword
            + " { "
            + operation_name
            + args_clause
            + " { "
            + selection
            + " } }"
        )

        cache_key = self._get_cache_key(query)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        logger.info(f"GraphQL {keyword} {operation_name}{args_clause}")
        response = await self._make_request(
            "POST",
            self.graphql_path,
            json={"query": query},
        )

        try:
            body = response.json()
        except Exception as e:
            raise ValidationException(f"Invalid JSON response: {str(e)}")

        if body.get("errors"):
            messages = [err.get("message", str(err)) for err in body["errors"]]
            raise APIException(f"GraphQL errors: {'; '.join(messages)}")

        data = body.get("data") or {}
        payload = data.get(operation_name)
        if payload is None:
            raise ValidationException(
                f"GraphQL response missing '{operation_name}' in data"
            )

        self._update_cache(cache_key, payload)
        return payload

    async def validate_character(
        self,
        id: str,
    ) -> Character:
        """
        Validate GraphQL query character.
        """
        arg_parts: List[str] = []
        if id is not None:
            arg_parts.append('id: "' + str(id) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="character",
            selection="id name status species type gender origin { id name type dimension residents { id } created } location { id name type dimension residents { id } created } image episode { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Character.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for character: {drift}")

        try:
            return Character.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_characters(
        self,
        page: Optional[int] = None,
        filter: Optional[str] = None,
    ) -> Characters:
        """
        Validate GraphQL query characters.
        """
        arg_parts: List[str] = []
        if page is not None:
            arg_parts.append("page: " + str(page))
        if filter is not None:
            arg_parts.append('filter: "' + str(filter) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="characters",
            selection="info { count pages next prev } results { id }",
            args_clause=args_clause,
        )

        expected_fields = set(Characters.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for characters: {drift}")

        try:
            return Characters.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_characters_by_ids(
        self,
        ids: List[Any],
    ) -> Character:
        """
        Validate GraphQL query charactersByIds.
        """
        arg_parts: List[str] = []
        if ids is not None:
            arg_parts.append("ids: " + json.dumps(ids))
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="charactersByIds",
            selection="id name status species type gender origin { id name type dimension residents { id } created } location { id name type dimension residents { id } created } image episode { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Character.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for charactersByIds: {drift}")

        try:
            return Character.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_location(
        self,
        id: str,
    ) -> Location:
        """
        Validate GraphQL query location.
        """
        arg_parts: List[str] = []
        if id is not None:
            arg_parts.append('id: "' + str(id) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="location",
            selection="id name type dimension residents { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Location.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for location: {drift}")

        try:
            return Location.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_locations(
        self,
        page: Optional[int] = None,
        filter: Optional[str] = None,
    ) -> Any:
        """
        Validate GraphQL query locations.
        """
        arg_parts: List[str] = []
        if page is not None:
            arg_parts.append("page: " + str(page))
        if filter is not None:
            arg_parts.append('filter: "' + str(filter) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="locations",
            selection="id",
            args_clause=args_clause,
        )

        return payload

    async def validate_locations_by_ids(
        self,
        ids: List[Any],
    ) -> Location:
        """
        Validate GraphQL query locationsByIds.
        """
        arg_parts: List[str] = []
        if ids is not None:
            arg_parts.append("ids: " + json.dumps(ids))
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="locationsByIds",
            selection="id name type dimension residents { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Location.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for locationsByIds: {drift}")

        try:
            return Location.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_episode(
        self,
        id: str,
    ) -> Episode:
        """
        Validate GraphQL query episode.
        """
        arg_parts: List[str] = []
        if id is not None:
            arg_parts.append('id: "' + str(id) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="episode",
            selection="id name air_date episode characters { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Episode.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for episode: {drift}")

        try:
            return Episode.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_episodes(
        self,
        page: Optional[int] = None,
        filter: Optional[str] = None,
    ) -> Any:
        """
        Validate GraphQL query episodes.
        """
        arg_parts: List[str] = []
        if page is not None:
            arg_parts.append("page: " + str(page))
        if filter is not None:
            arg_parts.append('filter: "' + str(filter) + '"')
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="episodes",
            selection="id",
            args_clause=args_clause,
        )

        return payload

    async def validate_episodes_by_ids(
        self,
        ids: List[Any],
    ) -> Episode:
        """
        Validate GraphQL query episodesByIds.
        """
        arg_parts: List[str] = []
        if ids is not None:
            arg_parts.append("ids: " + json.dumps(ids))
        args_clause = f"({', '.join(arg_parts)})" if arg_parts else ""

        payload = await self._execute_graphql(
            operation_type="query",
            operation_name="episodesByIds",
            selection="id name air_date episode characters { id } created",
            args_clause=args_clause,
        )

        expected_fields = set(Episode.model_fields.keys())
        actual_fields = set(payload.keys()) if isinstance(payload, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        if drift:
            logger.warning(f"Schema drift for episodesByIds: {drift}")

        try:
            return Episode.model_validate(
                self._coerce_payload(payload)
            )
        except ValidationError as e:
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )



class ValidationReport:
    """Generates validation reports for API endpoints."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def add_result(
        self,
        endpoint: str,
        success: bool,
        error: Optional[str] = None,
        drift: Optional[Dict] = None,
    ) -> None:
        self.results.append({
            "endpoint": endpoint,
            "success": success,
            "error": error,
            "drift": drift,
        })

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        drift_detected = sum(1 for r in self.results if r.get("drift"))
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "drift_detected": drift_detected,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }

    def get_failed_endpoints(self) -> List[Dict[str, Any]]:
        return [r for r in self.results if not r["success"]]

    def get_drift_endpoints(self) -> List[Dict[str, Any]]:
        return [r for r in self.results if r.get("drift")]
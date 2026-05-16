"""
Auto-generated API validators for Query API.

Generated: 2026-05-16T15:20:09.460077Z
API Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Union
import httpx
from loguru import logger
from pydantic import ValidationError

from models import Query, Character, Location, Episode, FilterCharacter, Characters, Info, FilterLocation, FilterEpisode
from core.exceptions import (
    ValidationException,
    APIException,
    SchemaException,
)
from core.retry_handler import with_retry


class APIValidator:
    """
    Validates API responses against Pydantic models.
    
    Features:
    - Automatic retry with exponential backoff
    - Schema drift detection
    - Detailed error reporting
    - Response caching (optional)
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_cache: bool = False,
    ):
        """
        Initialize the API validator.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_cache: Enable response caching
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._cache: Dict[str, Any] = {}
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(
            f"Initialized APIValidator for {base_url} "
            f"(timeout={timeout}s, max_retries={max_retries})"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from endpoint and parameters."""
        param_str = str(sorted(params.items())) if params else ""
        return f"{endpoint}:{param_str}"
    
    def _check_cache(self, cache_key: str) -> Optional[Any]:
        """Check if response is cached."""
        if self.enable_cache and cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]
        return None
    
    def _update_cache(self, cache_key: str, data: Any) -> None:
        """Update cache with response data."""
        if self.enable_cache:
            self._cache[cache_key] = data
            logger.debug(f"Cached response for {cache_key}")
    
    def _detect_schema_drift(
        self,
        expected_fields: set,
        actual_fields: set,
    ) -> Dict[str, List[str]]:
        """
        Detect schema drift between expected and actual fields.
        
        Returns:
            Dict with 'missing' and 'extra' field lists
        """
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        
        drift = {}
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
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
        
        Returns:
            HTTP response
        
        Raises:
            APIException: If request fails after retries
        """
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

    async def validate_character(
        self,
        id: str,
    ) -> Character:
        """
        Validate GET /query/character.
        
        Get a specific character by ID
        
        Args:
            id: No description
        
        Returns:
            Validated Character instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/character"
        
        # Build query parameters
        params = {}
        if id is not None:
            params["id"] = id
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Character.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/character: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Character.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/character")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/character: {e}")
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
        Validate GET /query/characters.
        
        Get the list of all characters
        
        Args:
            page: No description
            filter: No description
        
        Returns:
            Validated Characters instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/characters"
        
        # Build query parameters
        params = {}
        if page is not None:
            params["page"] = page
        if filter is not None:
            params["filter"] = filter
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Characters.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/characters: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Characters.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/characters")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/characters: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_characters_by_ids(
        self,
        ids: List[Any],
    ) -> Character:
        """
        Validate GET /query/charactersByIds.
        
        Get a list of characters selected by ids
        
        Args:
            ids: No description
        
        Returns:
            Validated Character instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/charactersByIds"
        
        # Build query parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Character.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/charactersByIds: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Character.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/charactersByIds")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/charactersByIds: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_location(
        self,
        id: str,
    ) -> Location:
        """
        Validate GET /query/location.
        
        Get a specific locations by ID
        
        Args:
            id: No description
        
        Returns:
            Validated Location instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/location"
        
        # Build query parameters
        params = {}
        if id is not None:
            params["id"] = id
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Location.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/location: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Location.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/location")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/location: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_locations(
        self,
        page: Optional[int] = None,
        filter: Optional[str] = None,
    ) -> Locations:
        """
        Validate GET /query/locations.
        
        Get the list of all locations
        
        Args:
            page: No description
            filter: No description
        
        Returns:
            Validated Locations instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/locations"
        
        # Build query parameters
        params = {}
        if page is not None:
            params["page"] = page
        if filter is not None:
            params["filter"] = filter
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Locations.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/locations: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Locations.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/locations")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/locations: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_locations_by_ids(
        self,
        ids: List[Any],
    ) -> Location:
        """
        Validate GET /query/locationsByIds.
        
        Get a list of locations selected by ids
        
        Args:
            ids: No description
        
        Returns:
            Validated Location instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/locationsByIds"
        
        # Build query parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Location.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/locationsByIds: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Location.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/locationsByIds")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/locationsByIds: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_episode(
        self,
        id: str,
    ) -> Episode:
        """
        Validate GET /query/episode.
        
        Get a specific episode by ID
        
        Args:
            id: No description
        
        Returns:
            Validated Episode instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/episode"
        
        # Build query parameters
        params = {}
        if id is not None:
            params["id"] = id
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Episode.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/episode: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Episode.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/episode")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/episode: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_episodes(
        self,
        page: Optional[int] = None,
        filter: Optional[str] = None,
    ) -> Episodes:
        """
        Validate GET /query/episodes.
        
        Get the list of all episodes
        
        Args:
            page: No description
            filter: No description
        
        Returns:
            Validated Episodes instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/episodes"
        
        # Build query parameters
        params = {}
        if page is not None:
            params["page"] = page
        if filter is not None:
            params["filter"] = filter
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Episodes.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/episodes: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Episodes.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/episodes")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/episodes: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )

    async def validate_episodes_by_ids(
        self,
        ids: List[Any],
    ) -> Episode:
        """
        Validate GET /query/episodesByIds.
        
        Get a list of episodes selected by ids
        
        Args:
            ids: No description
        
        Returns:
            Validated Episode instance
        
        Raises:
            ValidationException: If response validation fails
            SchemaException: If schema drift detected
            APIException: If API request fails
        """
        # Build endpoint URL with path parameters
        endpoint_path = "/query/episodesByIds"
        
        # Build query parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_path, params)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        # Make request
        logger.info(f"Validating GET {endpoint_path}")
        response = await self._make_request(
            "GET",
            endpoint_path,
            params=params,
        )
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValidationException(f"Invalid JSON response: {str(e)}")
        
        # Detect schema drift
        expected_fields = set(Episode.model_fields.keys())
        actual_fields = set(data.keys()) if isinstance(data, dict) else set()
        drift = self._detect_schema_drift(expected_fields, actual_fields)
        
        if drift:
            logger.warning(f"Schema drift detected for /query/episodesByIds: {drift}")
            # Optionally raise exception for strict validation
            # raise SchemaException(f"Schema drift: {drift}")
        
        # Validate response
        try:
            validated = Episode.model_validate(data)
            
            # Update cache
            self._update_cache(cache_key, validated)
            
            logger.success(f"Successfully validated GET /query/episodesByIds")
            return validated
            
        except ValidationError as e:
            logger.error(f"Validation failed for /query/episodesByIds: {e}")
            raise ValidationException(
                f"Response validation failed: {e.error_count()} errors",
                errors=e.errors(),
            )


class ValidationReport:
    """
    Generates validation reports for API endpoints.
    """
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
    
    def add_result(
        self,
        endpoint: str,
        success: bool,
        error: Optional[str] = None,
        drift: Optional[Dict] = None,
    ) -> None:
        """Add validation result."""
        self.results.append({
            "endpoint": endpoint,
            "success": success,
            "error": error,
            "drift": drift,
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
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
        """Get list of failed endpoints."""
        return [r for r in self.results if not r["success"]]
    
    def get_drift_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of endpoints with schema drift."""
        return [r for r in self.results if r.get("drift")]
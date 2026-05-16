"""
Abstract base provider for API interactions.

This module provides the foundation for all API communication with:
- Retry logic integration
- Authentication injection
- Error handling
- Endpoint introspection
"""

from abc import ABC, abstractmethod
from typing import Any

import httpx
from loguru import logger

from core.auth_manager import AuthHandler, NoAuth
from core.exceptions import NetworkError
from core.retry_handler import retry_with_backoff
from config.settings import get_settings


class BaseProvider(ABC):
    """
    Abstract base class for API providers.
    
    This class provides common functionality for all API interactions:
    - HTTP client management
    - Authentication injection
    - Retry logic
    - Error handling
    - Endpoint introspection
    
    Subclasses should implement specific API interaction patterns.
    """
    
    def __init__(
        self,
        base_url: str,
        auth_handler: AuthHandler | None = None,
        timeout: float | None = None
    ):
        """
        Initialize base provider.
        
        Args:
            base_url: Base URL for API endpoints
            auth_handler: Authentication handler (default: NoAuth)
            timeout: Request timeout in seconds (default: from settings)
        """
        self.base_url = base_url.rstrip('/')
        self.auth_handler = auth_handler or NoAuth()
        
        settings = get_settings()
        self.timeout = timeout or settings.default_timeout
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "DataSentinel/1.0.0",
                "Accept": "application/json"
            }
        )
        
        logger.debug(
            f"Initialized {self.__class__.__name__}: "
            f"base_url={base_url}, timeout={self.timeout}s"
        )
    
    async def close(self) -> None:
        """
        Close HTTP client connection.
        
        This should be called when the provider is no longer needed
        to properly clean up resources.
        """
        await self.client.aclose()
        logger.debug(f"Closed {self.__class__.__name__} HTTP client")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _build_url(self, path: str) -> str:
        """
        Build full URL from base URL and path.
        
        Args:
            path: API endpoint path
            
        Returns:
            Full URL
        """
        # Remove leading slash from path if present
        path = path.lstrip('/')
        return f"{self.base_url}/{path}"
    
    def _inject_auth(self, request: httpx.Request) -> httpx.Request:
        """
        Inject authentication into request.
        
        Args:
            request: HTTP request
            
        Returns:
            Authenticated request
        """
        return self.auth_handler.inject_auth(request)
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def fetch(
        self,
        path: str,
        method: str = "GET",
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Fetch data from API endpoint with retry logic.
        
        This method automatically:
        - Builds full URL
        - Injects authentication
        - Retries on transient failures
        - Handles errors
        
        Args:
            path: API endpoint path (relative to base_url)
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            **kwargs: Additional arguments passed to httpx.request()
            
        Returns:
            Response data as dictionary
            
        Raises:
            NetworkError: If request fails after retries
            
        Example:
            ```python
            provider = MyProvider("https://api.example.com")
            data = await provider.fetch("/users/1")
            ```
        """
        url = self._build_url(path)
        
        try:
            # Create request
            request = self.client.build_request(
                method=method.upper(),
                url=url,
                **kwargs
            )
            
            # Inject authentication
            request = self._inject_auth(request)
            
            # Send request
            logger.debug(f"{method.upper()} {url}")
            response = await self.client.send(request)
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            logger.debug(f"Successfully fetched {url}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {method} {url}: {e}"
            )
            raise NetworkError(
                f"HTTP {e.response.status_code}: {e}",
                details={
                    "url": url,
                    "method": method,
                    "status_code": e.response.status_code
                }
            )
        
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise NetworkError(
                f"Request failed: {e}",
                details={"url": url, "method": method}
            )
        
        except ValueError as e:
            logger.error(f"Invalid JSON response from {url}: {e}")
            raise NetworkError(
                f"Invalid JSON response: {e}",
                details={"url": url, "method": method}
            )
    
    async def fetch_raw(
        self,
        path: str,
        method: str = "GET",
        **kwargs: Any
    ) -> httpx.Response:
        """
        Fetch raw response from API endpoint.
        
        Similar to fetch() but returns the raw httpx.Response object
        instead of parsing JSON. Useful for non-JSON responses or
        when you need access to headers, status code, etc.
        
        Args:
            path: API endpoint path
            method: HTTP method
            **kwargs: Additional arguments passed to httpx.request()
            
        Returns:
            Raw httpx.Response object
            
        Raises:
            NetworkError: If request fails
        """
        url = self._build_url(path)
        
        try:
            request = self.client.build_request(
                method=method.upper(),
                url=url,
                **kwargs
            )
            
            request = self._inject_auth(request)
            
            logger.debug(f"{method.upper()} {url} (raw)")
            response = await self.client.send(request)
            response.raise_for_status()
            
            return response
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {method} {url}: {e}")
            raise NetworkError(
                f"Request failed: {e}",
                details={"url": url, "method": method}
            )
    
    async def introspect_endpoint(
        self,
        path: str
    ) -> dict[str, Any]:
        """
        Introspect API endpoint to discover schema.
        
        This method attempts to discover the endpoint's schema by:
        1. Trying OPTIONS request (if supported)
        2. Making a sample GET request and inferring from response
        
        Args:
            path: API endpoint path
            
        Returns:
            Dictionary with endpoint information:
            - methods: List of supported HTTP methods
            - sample_response: Sample response data (if available)
            - content_type: Response content type
            
        Example:
            ```python
            info = await provider.introspect_endpoint("/users")
            print(info["methods"])  # ['GET', 'POST']
            ```
        """
        url = self._build_url(path)
        endpoint_info: dict[str, Any] = {
            "url": url,
            "methods": [],
            "sample_response": None,
            "content_type": None
        }
        
        # Try OPTIONS request
        try:
            response = await self.fetch_raw(path, method="OPTIONS")
            
            # Extract allowed methods from Allow header
            allow_header = response.headers.get("Allow", "")
            if allow_header:
                endpoint_info["methods"] = [
                    m.strip() for m in allow_header.split(",")
                ]
                logger.debug(f"Discovered methods for {url}: {endpoint_info['methods']}")
        
        except NetworkError:
            logger.debug(f"OPTIONS not supported for {url}")
        
        # Try sample GET request
        try:
            response = await self.fetch_raw(path, method="GET")
            endpoint_info["content_type"] = response.headers.get("Content-Type")
            
            # Try to parse JSON response
            try:
                endpoint_info["sample_response"] = response.json()
                logger.debug(f"Got sample response from {url}")
            except ValueError:
                logger.debug(f"Non-JSON response from {url}")
            
            # Add GET to methods if not already present
            if "GET" not in endpoint_info["methods"]:
                endpoint_info["methods"].append("GET")
        
        except NetworkError:
            logger.debug(f"GET request failed for {url}")
        
        return endpoint_info
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that connection to API is working.
        
        Subclasses should implement this to check API connectivity.
        This might involve hitting a health check endpoint or
        making a simple request.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass


class SimpleProvider(BaseProvider):
    """
    Simple concrete implementation of BaseProvider.
    
    This is a basic provider that can be used for simple REST APIs
    without special requirements.
    """
    
    async def validate_connection(self) -> bool:
        """
        Validate connection by attempting to fetch base URL.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.fetch_raw("/")
            return True
        except NetworkError:
            return False

# Made with Bob

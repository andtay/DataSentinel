"""
Authentication management for API interactions.

This module provides a unified interface for different authentication strategies:
- API Key (header or query parameter)
- Bearer Token
- OAuth2 (with automatic token refresh)
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from loguru import logger

from core.exceptions import AuthenticationError


class AuthType(str, Enum):
    """Supported authentication types."""
    
    API_KEY = "api_key"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    NONE = "none"


class AuthHandler(ABC):
    """
    Abstract base class for authentication handlers.
    
    All authentication strategies must implement this interface.
    """
    
    @abstractmethod
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """
        Inject authentication into HTTP request.
        
        Args:
            request: HTTP request to authenticate
            
        Returns:
            Authenticated request with credentials injected
        """
        pass


class NoAuth(AuthHandler):
    """
    No authentication handler.
    
    This handler does nothing and is used when no authentication is required.
    """
    
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """Return request unchanged."""
        return request


class APIKeyAuth(AuthHandler):
    """
    API Key authentication handler.
    
    Supports both header-based and query parameter-based API key authentication.
    """
    
    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
        query_param: str | None = None
    ):
        """
        Initialize API Key authentication.
        
        Args:
            api_key: The API key value
            header_name: Header name for API key (default: X-API-Key)
            query_param: Query parameter name (if using query param instead of header)
        """
        self.api_key = api_key
        self.header_name = header_name
        self.query_param = query_param
        
        logger.debug(
            f"Initialized API Key auth: "
            f"header={header_name if not query_param else None}, "
            f"query_param={query_param}"
        )
    
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """
        Inject API key into request.
        
        If query_param is set, adds API key as query parameter.
        Otherwise, adds API key as header.
        """
        if self.query_param:
            # Add as query parameter
            url = request.url.copy_with(
                params={**dict(request.url.params), self.query_param: self.api_key}
            )
            return httpx.Request(
                method=request.method,
                url=url,
                headers=request.headers,
                content=request.content
            )
        else:
            # Add as header
            request.headers[self.header_name] = self.api_key
            return request


class BearerAuth(AuthHandler):
    """
    Bearer token authentication handler.
    
    Adds Authorization header with Bearer token.
    """
    
    def __init__(self, token: str):
        """
        Initialize Bearer token authentication.
        
        Args:
            token: Bearer token value
        """
        self.token = token
        logger.debug("Initialized Bearer token auth")
    
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """Inject Bearer token into Authorization header."""
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


class OAuth2Auth(AuthHandler):
    """
    OAuth2 authentication handler with automatic token refresh.
    
    This handler manages OAuth2 client credentials flow with automatic
    token refresh when the access token expires.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scopes: list[str] | None = None
    ):
        """
        Initialize OAuth2 authentication.
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: Token endpoint URL
            scopes: Optional list of scopes to request
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scopes = scopes or []
        
        self.access_token: str | None = None
        self.expires_at: datetime | None = None
        
        logger.debug(f"Initialized OAuth2 auth: token_url={token_url}")
    
    async def refresh_token(self) -> None:
        """
        Refresh OAuth2 access token.
        
        This method fetches a new access token from the token endpoint
        using the client credentials flow.
        
        Raises:
            AuthenticationError: If token refresh fails
        """
        logger.info("Refreshing OAuth2 access token...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": " ".join(self.scopes) if self.scopes else None
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                
                # Set expiration with 5-minute buffer
                self.expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                logger.info(f"OAuth2 token refreshed, expires at {self.expires_at}")
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to refresh OAuth2 token: {e}")
            raise AuthenticationError(
                f"OAuth2 token refresh failed: {e}",
                details={"token_url": self.token_url}
            )
        except KeyError as e:
            logger.error(f"Invalid token response: missing {e}")
            raise AuthenticationError(
                f"Invalid OAuth2 token response: missing {e}",
                details={"token_url": self.token_url}
            )
    
    def _is_token_expired(self) -> bool:
        """Check if current token is expired or about to expire."""
        if not self.access_token or not self.expires_at:
            return True
        
        # Consider token expired if it expires in less than 1 minute
        return datetime.now() >= (self.expires_at - timedelta(minutes=1))
    
    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """
        Inject OAuth2 token into request.
        
        Note: For OAuth2, you should call ensure_token() before making requests
        to handle token refresh asynchronously.
        """
        # Inject token if available
        if self.access_token:
            request.headers["Authorization"] = f"Bearer {self.access_token}"
        
        return request
    
    async def ensure_token(self) -> None:
        """
        Ensure we have a valid token, refreshing if necessary.
        
        Call this method before making requests to handle token refresh.
        """
        if self._is_token_expired():
            await self.refresh_token()


class AuthManager:
    """
    Factory for creating authentication handlers.
    
    This class provides a convenient way to create the appropriate
    authentication handler based on the authentication type.
    """
    
    @staticmethod
    def get_auth_handler(
        auth_type: AuthType | str,
        **kwargs: Any
    ) -> AuthHandler:
        """
        Create appropriate authentication handler.
        
        Args:
            auth_type: Type of authentication
            **kwargs: Authentication-specific parameters
            
        Returns:
            Configured authentication handler
            
        Raises:
            ValueError: If auth_type is not supported
            AuthenticationError: If required parameters are missing
            
        Examples:
            >>> # API Key authentication
            >>> auth = AuthManager.get_auth_handler(
            ...     AuthType.API_KEY,
            ...     api_key="my_key",
            ...     header_name="X-API-Key"
            ... )
            
            >>> # Bearer token authentication
            >>> auth = AuthManager.get_auth_handler(
            ...     AuthType.BEARER,
            ...     token="my_token"
            ... )
            
            >>> # OAuth2 authentication
            >>> auth = AuthManager.get_auth_handler(
            ...     AuthType.OAUTH2,
            ...     client_id="my_client",
            ...     client_secret="my_secret",
            ...     token_url="https://auth.example.com/token"
            ... )
        """
        # Convert string to enum if necessary
        if isinstance(auth_type, str):
            try:
                auth_type = AuthType(auth_type.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported auth type: {auth_type}. "
                    f"Supported types: {[t.value for t in AuthType]}"
                )
        
        # Create appropriate handler
        if auth_type == AuthType.NONE:
            return NoAuth()
        
        elif auth_type == AuthType.API_KEY:
            api_key = kwargs.get("api_key")
            if not api_key:
                raise AuthenticationError(
                    "API key is required for API_KEY authentication",
                    details={"auth_type": auth_type.value}
                )
            
            return APIKeyAuth(
                api_key=api_key,
                header_name=kwargs.get("header_name", "X-API-Key"),
                query_param=kwargs.get("query_param")
            )
        
        elif auth_type == AuthType.BEARER:
            token = kwargs.get("token")
            if not token:
                raise AuthenticationError(
                    "Token is required for BEARER authentication",
                    details={"auth_type": auth_type.value}
                )
            
            return BearerAuth(token=token)
        
        elif auth_type == AuthType.OAUTH2:
            client_id = kwargs.get("client_id")
            client_secret = kwargs.get("client_secret")
            token_url = kwargs.get("token_url")
            
            if not all([client_id, client_secret, token_url]):
                raise AuthenticationError(
                    "client_id, client_secret, and token_url are required for OAuth2 authentication",
                    details={"auth_type": auth_type.value}
                )
            
            return OAuth2Auth(
                client_id=str(client_id),
                client_secret=str(client_secret),
                token_url=str(token_url),
                scopes=kwargs.get("scopes")
            )
        
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

# Made with Bob

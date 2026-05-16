"""
Comprehensive tests for core/auth_manager.py

Tests authentication handlers and the AuthManager factory.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx

from core.auth_manager import (
    AuthType,
    AuthHandler,
    NoAuth,
    APIKeyAuth,
    BearerAuth,
    OAuth2Auth,
    AuthManager
)
from core.exceptions import AuthenticationError


# ============================================================================
# AuthType Enum Tests
# ============================================================================

class TestAuthType:
    """Test AuthType enum."""
    
    def test_auth_type_values(self):
        """Test AuthType enum values."""
        assert AuthType.API_KEY.value == "api_key"
        assert AuthType.BEARER.value == "bearer"
        assert AuthType.OAUTH2.value == "oauth2"
        assert AuthType.NONE.value == "none"
    
    def test_auth_type_from_string(self):
        """Test creating AuthType from string."""
        assert AuthType("api_key") == AuthType.API_KEY
        assert AuthType("bearer") == AuthType.BEARER
        assert AuthType("oauth2") == AuthType.OAUTH2
        assert AuthType("none") == AuthType.NONE
    
    def test_auth_type_invalid_string(self):
        """Test invalid AuthType string raises ValueError."""
        with pytest.raises(ValueError):
            AuthType("invalid")


# ============================================================================
# NoAuth Tests
# ============================================================================

class TestNoAuth:
    """Test NoAuth handler."""
    
    def test_no_auth_initialization(self):
        """Test NoAuth can be initialized."""
        auth = NoAuth()
        assert isinstance(auth, AuthHandler)
    
    def test_no_auth_inject_unchanged(self):
        """Test NoAuth returns request unchanged."""
        auth = NoAuth()
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = auth.inject_auth(request)
        
        assert result is request
        assert result.url == request.url
        assert result.headers == request.headers


# ============================================================================
# APIKeyAuth Tests
# ============================================================================

class TestAPIKeyAuth:
    """Test APIKeyAuth handler."""
    
    def test_api_key_auth_initialization_header(self):
        """Test APIKeyAuth initialization with header."""
        auth = APIKeyAuth(api_key="test_key", header_name="X-Custom-Key")
        
        assert auth.api_key == "test_key"
        assert auth.header_name == "X-Custom-Key"
        assert auth.query_param is None
    
    def test_api_key_auth_initialization_query(self):
        """Test APIKeyAuth initialization with query param."""
        auth = APIKeyAuth(api_key="test_key", query_param="api_key")
        
        assert auth.api_key == "test_key"
        assert auth.query_param == "api_key"
    
    def test_api_key_auth_default_header_name(self):
        """Test APIKeyAuth uses default header name."""
        auth = APIKeyAuth(api_key="test_key")
        
        assert auth.header_name == "X-API-Key"
    
    def test_api_key_inject_as_header(self):
        """Test API key injection as header."""
        auth = APIKeyAuth(api_key="secret_key", header_name="X-API-Key")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = auth.inject_auth(request)
        
        assert result.headers["X-API-Key"] == "secret_key"
    
    def test_api_key_inject_as_query_param(self):
        """Test API key injection as query parameter."""
        auth = APIKeyAuth(api_key="secret_key", query_param="key")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = auth.inject_auth(request)
        
        assert "key=secret_key" in str(result.url)
        assert result.url.params["key"] == "secret_key"
    
    def test_api_key_inject_preserves_existing_params(self):
        """Test API key injection preserves existing query params."""
        auth = APIKeyAuth(api_key="secret_key", query_param="key")
        request = httpx.Request(
            "GET",
            "https://api.example.com/data?existing=value"
        )
        
        result = auth.inject_auth(request)
        
        assert result.url.params["key"] == "secret_key"
        assert result.url.params["existing"] == "value"
    
    def test_api_key_inject_preserves_request_properties(self):
        """Test API key injection preserves request properties."""
        auth = APIKeyAuth(api_key="secret_key", query_param="key")
        request = httpx.Request(
            "POST",
            "https://api.example.com/data",
            headers={"Content-Type": "application/json"},
            content=b'{"test": "data"}'
        )
        
        result = auth.inject_auth(request)
        
        assert result.method == "POST"
        assert result.headers["Content-Type"] == "application/json"
        assert result.content == b'{"test": "data"}'


# ============================================================================
# BearerAuth Tests
# ============================================================================

class TestBearerAuth:
    """Test BearerAuth handler."""
    
    def test_bearer_auth_initialization(self):
        """Test BearerAuth initialization."""
        auth = BearerAuth(token="test_token")
        
        assert auth.token == "test_token"
    
    def test_bearer_inject_auth_header(self):
        """Test Bearer token injection."""
        auth = BearerAuth(token="my_token")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = auth.inject_auth(request)
        
        assert result.headers["Authorization"] == "Bearer my_token"
    
    def test_bearer_inject_overwrites_existing_auth(self):
        """Test Bearer token overwrites existing Authorization header."""
        auth = BearerAuth(token="new_token")
        request = httpx.Request(
            "GET",
            "https://api.example.com/data",
            headers={"Authorization": "Bearer old_token"}
        )
        
        result = auth.inject_auth(request)
        
        assert result.headers["Authorization"] == "Bearer new_token"


# ============================================================================
# OAuth2Auth Tests
# ============================================================================

class TestOAuth2Auth:
    """Test OAuth2Auth handler."""
    
    def test_oauth2_initialization(self):
        """Test OAuth2Auth initialization."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        assert auth.client_id == "client123"
        assert auth.client_secret == "secret456"
        assert auth.token_url == "https://auth.example.com/token"
        assert auth.scopes == []
        assert auth.access_token is None
        assert auth.expires_at is None
    
    def test_oauth2_initialization_with_scopes(self):
        """Test OAuth2Auth initialization with scopes."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"]
        )
        
        assert auth.scopes == ["read", "write"]
    
    @pytest.mark.asyncio
    async def test_oauth2_refresh_token_success(self):
        """Test successful OAuth2 token refresh."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await auth.refresh_token()
        
        assert auth.access_token == "new_access_token"
        assert auth.expires_at is not None
        assert auth.expires_at > datetime.now()
    
    @pytest.mark.asyncio
    async def test_oauth2_refresh_token_with_scopes(self):
        """Test OAuth2 token refresh includes scopes."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"]
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await auth.refresh_token()
            
            # Verify scopes were included in request
            call_args = mock_post.call_args
            assert call_args[1]["data"]["scope"] == "read write"
    
    @pytest.mark.asyncio
    async def test_oauth2_refresh_token_http_error(self):
        """Test OAuth2 token refresh handles HTTP errors."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPError("Connection failed")
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                await auth.refresh_token()
            
            assert "OAuth2 token refresh failed" in str(exc_info.value)
            assert "token_url" in exc_info.value.details
    
    @pytest.mark.asyncio
    async def test_oauth2_refresh_token_missing_access_token(self):
        """Test OAuth2 token refresh handles missing access_token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"expires_in": 3600}  # Missing access_token
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                await auth.refresh_token()
            
            assert "Invalid OAuth2 token response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_oauth2_refresh_token_default_expiry(self):
        """Test OAuth2 token refresh uses default expiry."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token"
            # No expires_in field
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            before = datetime.now()
            await auth.refresh_token()
            after = datetime.now()
        
        # Should use default 3600 seconds minus 300 second buffer
        expected_min = before + timedelta(seconds=3300)
        expected_max = after + timedelta(seconds=3300)
        
        assert auth.expires_at is not None
        assert expected_min <= auth.expires_at <= expected_max
    
    def test_oauth2_is_token_expired_no_token(self):
        """Test _is_token_expired returns True when no token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        assert auth._is_token_expired() is True
    
    def test_oauth2_is_token_expired_no_expiry(self):
        """Test _is_token_expired returns True when no expiry."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "token"
        
        assert auth._is_token_expired() is True
    
    def test_oauth2_is_token_expired_expired(self):
        """Test _is_token_expired returns True for expired token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "token"
        auth.expires_at = datetime.now() - timedelta(minutes=5)
        
        assert auth._is_token_expired() is True
    
    def test_oauth2_is_token_expired_about_to_expire(self):
        """Test _is_token_expired returns True for token expiring soon."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "token"
        auth.expires_at = datetime.now() + timedelta(seconds=30)
        
        assert auth._is_token_expired() is True
    
    def test_oauth2_is_token_expired_valid(self):
        """Test _is_token_expired returns False for valid token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "token"
        auth.expires_at = datetime.now() + timedelta(hours=1)
        
        assert auth._is_token_expired() is False
    
    def test_oauth2_inject_auth_with_token(self):
        """Test OAuth2 inject_auth with valid token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "my_oauth_token"
        
        request = httpx.Request("GET", "https://api.example.com/data")
        result = auth.inject_auth(request)
        
        assert result.headers["Authorization"] == "Bearer my_oauth_token"
    
    def test_oauth2_inject_auth_without_token(self):
        """Test OAuth2 inject_auth without token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        request = httpx.Request("GET", "https://api.example.com/data")
        result = auth.inject_auth(request)
        
        assert "Authorization" not in result.headers
    
    @pytest.mark.asyncio
    async def test_oauth2_ensure_token_refreshes_expired(self):
        """Test ensure_token refreshes expired token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "refreshed_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await auth.ensure_token()
        
        assert auth.access_token == "refreshed_token"
    
    @pytest.mark.asyncio
    async def test_oauth2_ensure_token_skips_valid(self):
        """Test ensure_token skips refresh for valid token."""
        auth = OAuth2Auth(
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        auth.access_token = "valid_token"
        auth.expires_at = datetime.now() + timedelta(hours=1)
        
        with patch.object(auth, "refresh_token") as mock_refresh:
            await auth.ensure_token()
            
            mock_refresh.assert_not_called()


# ============================================================================
# AuthManager Tests
# ============================================================================

class TestAuthManager:
    """Test AuthManager factory."""
    
    def test_get_auth_handler_none(self):
        """Test creating NoAuth handler."""
        auth = AuthManager.get_auth_handler(AuthType.NONE)
        
        assert isinstance(auth, NoAuth)
    
    def test_get_auth_handler_none_from_string(self):
        """Test creating NoAuth handler from string."""
        auth = AuthManager.get_auth_handler("none")
        
        assert isinstance(auth, NoAuth)
    
    def test_get_auth_handler_api_key(self):
        """Test creating APIKeyAuth handler."""
        auth = AuthManager.get_auth_handler(
            AuthType.API_KEY,
            api_key="test_key"
        )
        
        assert isinstance(auth, APIKeyAuth)
        assert auth.api_key == "test_key"
    
    def test_get_auth_handler_api_key_with_header(self):
        """Test creating APIKeyAuth handler with custom header."""
        auth = AuthManager.get_auth_handler(
            AuthType.API_KEY,
            api_key="test_key",
            header_name="X-Custom-Key"
        )
        
        assert isinstance(auth, APIKeyAuth)
        assert auth.header_name == "X-Custom-Key"
    
    def test_get_auth_handler_api_key_with_query_param(self):
        """Test creating APIKeyAuth handler with query param."""
        auth = AuthManager.get_auth_handler(
            AuthType.API_KEY,
            api_key="test_key",
            query_param="key"
        )
        
        assert isinstance(auth, APIKeyAuth)
        assert auth.query_param == "key"
    
    def test_get_auth_handler_api_key_missing_key(self):
        """Test APIKeyAuth creation fails without api_key."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthManager.get_auth_handler(AuthType.API_KEY)
        
        assert "API key is required" in str(exc_info.value)
    
    def test_get_auth_handler_bearer(self):
        """Test creating BearerAuth handler."""
        auth = AuthManager.get_auth_handler(
            AuthType.BEARER,
            token="test_token"
        )
        
        assert isinstance(auth, BearerAuth)
        assert auth.token == "test_token"
    
    def test_get_auth_handler_bearer_missing_token(self):
        """Test BearerAuth creation fails without token."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthManager.get_auth_handler(AuthType.BEARER)
        
        assert "Token is required" in str(exc_info.value)
    
    def test_get_auth_handler_oauth2(self):
        """Test creating OAuth2Auth handler."""
        auth = AuthManager.get_auth_handler(
            AuthType.OAUTH2,
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token"
        )
        
        assert isinstance(auth, OAuth2Auth)
        assert auth.client_id == "client123"
        assert auth.client_secret == "secret456"
        assert auth.token_url == "https://auth.example.com/token"
    
    def test_get_auth_handler_oauth2_with_scopes(self):
        """Test creating OAuth2Auth handler with scopes."""
        auth = AuthManager.get_auth_handler(
            AuthType.OAUTH2,
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"]
        )
        
        assert isinstance(auth, OAuth2Auth)
        assert auth.scopes == ["read", "write"]
    
    def test_get_auth_handler_oauth2_missing_client_id(self):
        """Test OAuth2Auth creation fails without client_id."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthManager.get_auth_handler(
                AuthType.OAUTH2,
                client_secret="secret456",
                token_url="https://auth.example.com/token"
            )
        
        assert "client_id, client_secret, and token_url are required" in str(exc_info.value)
    
    def test_get_auth_handler_oauth2_missing_client_secret(self):
        """Test OAuth2Auth creation fails without client_secret."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthManager.get_auth_handler(
                AuthType.OAUTH2,
                client_id="client123",
                token_url="https://auth.example.com/token"
            )
        
        assert "client_id, client_secret, and token_url are required" in str(exc_info.value)
    
    def test_get_auth_handler_oauth2_missing_token_url(self):
        """Test OAuth2Auth creation fails without token_url."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthManager.get_auth_handler(
                AuthType.OAUTH2,
                client_id="client123",
                client_secret="secret456"
            )
        
        assert "client_id, client_secret, and token_url are required" in str(exc_info.value)
    
    def test_get_auth_handler_string_auth_type(self):
        """Test creating handler from string auth type."""
        auth = AuthManager.get_auth_handler(
            "api_key",
            api_key="test_key"
        )
        
        assert isinstance(auth, APIKeyAuth)
    
    def test_get_auth_handler_string_case_insensitive(self):
        """Test string auth type is case insensitive."""
        auth = AuthManager.get_auth_handler(
            "API_KEY",
            api_key="test_key"
        )
        
        assert isinstance(auth, APIKeyAuth)
    
    def test_get_auth_handler_invalid_string(self):
        """Test invalid string auth type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AuthManager.get_auth_handler("invalid_type")
        
        assert "Unsupported auth type: invalid_type" in str(exc_info.value)
    
    def test_get_auth_handler_invalid_enum(self):
        """Test invalid enum value raises ValueError."""
        # This shouldn't happen in practice, but test defensive code
        with pytest.raises(ValueError):
            AuthManager.get_auth_handler("not_an_auth_type")


# ============================================================================
# Integration Tests
# ============================================================================

class TestAuthIntegration:
    """Integration tests for authentication handlers."""
    
    def test_api_key_header_full_flow(self):
        """Test complete API key header authentication flow."""
        # Create auth handler
        auth = AuthManager.get_auth_handler(
            AuthType.API_KEY,
            api_key="secret123",
            header_name="X-API-Key"
        )
        
        # Create request
        request = httpx.Request(
            "GET",
            "https://api.example.com/users",
            headers={"Accept": "application/json"}
        )
        
        # Inject auth
        authenticated_request = auth.inject_auth(request)
        
        # Verify
        assert authenticated_request.headers["X-API-Key"] == "secret123"
        assert authenticated_request.headers["Accept"] == "application/json"
    
    def test_api_key_query_full_flow(self):
        """Test complete API key query param authentication flow."""
        # Create auth handler
        auth = AuthManager.get_auth_handler(
            AuthType.API_KEY,
            api_key="secret123",
            query_param="apikey"
        )
        
        # Create request
        request = httpx.Request(
            "GET",
            "https://api.example.com/users?page=1"
        )
        
        # Inject auth
        authenticated_request = auth.inject_auth(request)
        
        # Verify
        assert authenticated_request.url.params["apikey"] == "secret123"
        assert authenticated_request.url.params["page"] == "1"
    
    def test_bearer_full_flow(self):
        """Test complete Bearer token authentication flow."""
        # Create auth handler
        auth = AuthManager.get_auth_handler(
            AuthType.BEARER,
            token="jwt_token_here"
        )
        
        # Create request
        request = httpx.Request(
            "POST",
            "https://api.example.com/data",
            json={"key": "value"}
        )
        
        # Inject auth
        authenticated_request = auth.inject_auth(request)
        
        # Verify
        assert authenticated_request.headers["Authorization"] == "Bearer jwt_token_here"
    
    @pytest.mark.asyncio
    async def test_oauth2_full_flow(self):
        """Test complete OAuth2 authentication flow."""
        # Create auth handler
        auth = AuthManager.get_auth_handler(
            AuthType.OAUTH2,
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=["read"]
        )
        
        # Verify it's OAuth2Auth
        assert isinstance(auth, OAuth2Auth)
        
        # Mock token refresh
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "oauth_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            # Ensure token (now type checker knows it's OAuth2Auth)
            await auth.ensure_token()
        
        # Create request
        request = httpx.Request("GET", "https://api.example.com/data")
        
        # Inject auth
        authenticated_request = auth.inject_auth(request)
        
        # Verify
        assert authenticated_request.headers["Authorization"] == "Bearer oauth_token"


# Made with Bob
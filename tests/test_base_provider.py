"""
Comprehensive tests for core/base_provider.py

Tests BaseProvider abstract class and SimpleProvider implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import httpx

from core.base_provider import BaseProvider, SimpleProvider
from core.auth_manager import NoAuth, BearerAuth
from core.exceptions import NetworkError


# ============================================================================
# Test Provider Implementation
# ============================================================================

class TestProvider(BaseProvider):
    """Concrete test implementation of BaseProvider."""
    
    async def validate_connection(self) -> bool:
        """Test implementation of validate_connection."""
        try:
            await self.fetch("/health")
            return True
        except NetworkError:
            return False


# ============================================================================
# BaseProvider Initialization Tests
# ============================================================================

class TestBaseProviderInitialization:
    """Test BaseProvider initialization."""
    
    @pytest.mark.asyncio
    async def test_initialization_with_defaults(self):
        """Test BaseProvider initialization with default values."""
        provider = TestProvider("https://api.example.com")
        
        assert provider.base_url == "https://api.example.com"
        assert isinstance(provider.auth_handler, NoAuth)
        assert provider.timeout > 0
        assert provider.client is not None
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_initialization_strips_trailing_slash(self):
        """Test base_url trailing slash is stripped."""
        provider = TestProvider("https://api.example.com/")
        
        assert provider.base_url == "https://api.example.com"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_initialization_with_auth_handler(self):
        """Test initialization with custom auth handler."""
        auth = BearerAuth("test_token")
        provider = TestProvider("https://api.example.com", auth_handler=auth)
        
        assert provider.auth_handler is auth
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_initialization_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        provider = TestProvider("https://api.example.com", timeout=60.0)
        
        assert provider.timeout == 60.0
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_client_has_correct_headers(self):
        """Test HTTP client has correct default headers."""
        provider = TestProvider("https://api.example.com")
        
        assert "User-Agent" in provider.client.headers
        assert "DataSentinel" in provider.client.headers["User-Agent"]
        assert provider.client.headers["Accept"] == "application/json"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_client_follows_redirects(self):
        """Test HTTP client is configured to follow redirects."""
        provider = TestProvider("https://api.example.com")
        
        assert provider.client.follow_redirects is True
        
        await provider.close()


# ============================================================================
# Context Manager Tests
# ============================================================================

class TestBaseProviderContextManager:
    """Test BaseProvider async context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager_enter(self):
        """Test async context manager __aenter__."""
        async with TestProvider("https://api.example.com") as provider:
            assert provider is not None
            assert provider.client is not None
    
    @pytest.mark.asyncio
    async def test_context_manager_exit_closes_client(self):
        """Test async context manager __aexit__ closes client."""
        provider = TestProvider("https://api.example.com")
        
        async with provider:
            pass
        
        # Client should be closed after exiting context
        assert provider.client.is_closed


# ============================================================================
# URL Building Tests
# ============================================================================

class TestBaseProviderURLBuilding:
    """Test BaseProvider URL building."""
    
    @pytest.mark.asyncio
    async def test_build_url_simple_path(self):
        """Test building URL with simple path."""
        provider = TestProvider("https://api.example.com")
        
        url = provider._build_url("users")
        
        assert url == "https://api.example.com/users"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_build_url_with_leading_slash(self):
        """Test building URL strips leading slash from path."""
        provider = TestProvider("https://api.example.com")
        
        url = provider._build_url("/users")
        
        assert url == "https://api.example.com/users"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_build_url_nested_path(self):
        """Test building URL with nested path."""
        provider = TestProvider("https://api.example.com")
        
        url = provider._build_url("users/123/posts")
        
        assert url == "https://api.example.com/users/123/posts"
        
        await provider.close()


# ============================================================================
# Authentication Injection Tests
# ============================================================================

class TestBaseProviderAuthInjection:
    """Test BaseProvider authentication injection."""
    
    @pytest.mark.asyncio
    async def test_inject_auth_with_no_auth(self):
        """Test auth injection with NoAuth handler."""
        provider = TestProvider("https://api.example.com")
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = provider._inject_auth(request)
        
        assert result is request  # NoAuth returns unchanged
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_inject_auth_with_bearer(self):
        """Test auth injection with Bearer token."""
        auth = BearerAuth("test_token")
        provider = TestProvider("https://api.example.com", auth_handler=auth)
        request = httpx.Request("GET", "https://api.example.com/data")
        
        result = provider._inject_auth(request)
        
        assert result.headers["Authorization"] == "Bearer test_token"
        
        await provider.close()


# ============================================================================
# Fetch Method Tests
# ============================================================================

class TestBaseProviderFetch:
    """Test BaseProvider fetch method."""
    
    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful fetch request."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "name": "Test"}
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            result = await provider.fetch("/users/1")
        
        assert result == {"id": 1, "name": "Test"}
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_with_post_method(self):
        """Test fetch with POST method."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            result = await provider.fetch("/users", method="POST", json={"name": "New User"})
        
        assert result == {"created": True}
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self):
        """Test fetch builds correct URL."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "build_request") as mock_build:
            mock_build.return_value = httpx.Request("GET", "https://api.example.com/users")
            
            with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                await provider.fetch("/users")
            
            # Verify URL was built correctly
            call_args = mock_build.call_args
            assert "https://api.example.com/users" in str(call_args)
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_injects_auth(self):
        """Test fetch injects authentication."""
        auth = BearerAuth("test_token")
        provider = TestProvider("https://api.example.com", auth_handler=auth)
        
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        
        captured_request = None
        
        async def capture_request(request):
            nonlocal captured_request
            captured_request = request
            return mock_response
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = capture_request
            
            await provider.fetch("/users")
        
        assert captured_request is not None
        assert captured_request.headers["Authorization"] == "Bearer test_token"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_http_status_error(self):
        """Test fetch handles HTTP status errors."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            with pytest.raises(NetworkError) as exc_info:
                await provider.fetch("/users/999")
        
        assert "HTTP 404" in str(exc_info.value)
        assert exc_info.value.details["status_code"] == 404
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_request_error(self):
        """Test fetch handles request errors."""
        provider = TestProvider("https://api.example.com")
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = httpx.RequestError("Connection failed")
            
            with pytest.raises(NetworkError) as exc_info:
                await provider.fetch("/users")
        
        assert "Request failed" in str(exc_info.value)
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_json(self):
        """Test fetch handles invalid JSON response."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            with pytest.raises(NetworkError) as exc_info:
                await provider.fetch("/users")
        
        assert "Invalid JSON response" in str(exc_info.value)
        
        await provider.close()


# ============================================================================
# Fetch Raw Method Tests
# ============================================================================

class TestBaseProviderFetchRaw:
    """Test BaseProvider fetch_raw method."""
    
    @pytest.mark.asyncio
    async def test_fetch_raw_success(self):
        """Test successful fetch_raw request."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            result = await provider.fetch_raw("/users")
        
        assert result is mock_response
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_raw_with_method(self):
        """Test fetch_raw with custom method."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "build_request") as mock_build:
            mock_build.return_value = httpx.Request("POST", "https://api.example.com/users")
            
            with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                await provider.fetch_raw("/users", method="POST")
            
            # Verify POST method was used
            call_args = mock_build.call_args
            assert call_args[1]["method"] == "POST"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_fetch_raw_http_error(self):
        """Test fetch_raw handles HTTP errors."""
        provider = TestProvider("https://api.example.com")
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(NetworkError) as exc_info:
                await provider.fetch_raw("/users")
        
        assert "Request failed" in str(exc_info.value)
        
        await provider.close()


# ============================================================================
# Introspect Endpoint Tests
# ============================================================================

class TestBaseProviderIntrospectEndpoint:
    """Test BaseProvider introspect_endpoint method."""
    
    @pytest.mark.asyncio
    async def test_introspect_endpoint_with_options(self):
        """Test introspect_endpoint with OPTIONS support."""
        provider = TestProvider("https://api.example.com")
        
        mock_options_response = Mock(spec=httpx.Response)
        mock_options_response.headers = {"Allow": "GET, POST, PUT, DELETE"}
        mock_options_response.raise_for_status = Mock()
        
        mock_get_response = Mock(spec=httpx.Response)
        mock_get_response.headers = {"Content-Type": "application/json"}
        mock_get_response.json.return_value = {"sample": "data"}
        mock_get_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = [mock_options_response, mock_get_response]
            
            result = await provider.introspect_endpoint("/users")
        
        assert "GET" in result["methods"]
        assert "POST" in result["methods"]
        assert result["sample_response"] == {"sample": "data"}
        assert result["content_type"] == "application/json"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_introspect_endpoint_without_options(self):
        """Test introspect_endpoint when OPTIONS not supported."""
        provider = TestProvider("https://api.example.com")
        
        mock_get_response = Mock(spec=httpx.Response)
        mock_get_response.headers = {"Content-Type": "application/json"}
        mock_get_response.json.return_value = {"sample": "data"}
        mock_get_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            # First call (OPTIONS) fails, second (GET) succeeds
            mock_send.side_effect = [
                httpx.HTTPError("OPTIONS not supported"),
                mock_get_response
            ]
            
            result = await provider.introspect_endpoint("/users")
        
        assert result["methods"] == ["GET"]
        assert result["sample_response"] == {"sample": "data"}
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_introspect_endpoint_non_json_response(self):
        """Test introspect_endpoint with non-JSON response."""
        provider = TestProvider("https://api.example.com")
        
        mock_get_response = Mock(spec=httpx.Response)
        mock_get_response.headers = {"Content-Type": "text/html"}
        mock_get_response.json.side_effect = ValueError("Not JSON")
        mock_get_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = [
                httpx.HTTPError("OPTIONS not supported"),
                mock_get_response
            ]
            
            result = await provider.introspect_endpoint("/users")
        
        assert result["methods"] == ["GET"]
        assert result["sample_response"] is None
        assert result["content_type"] == "text/html"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_introspect_endpoint_all_requests_fail(self):
        """Test introspect_endpoint when all requests fail."""
        provider = TestProvider("https://api.example.com")
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = httpx.HTTPError("Connection failed")
            
            result = await provider.introspect_endpoint("/users")
        
        assert result["methods"] == []
        assert result["sample_response"] is None
        
        await provider.close()


# ============================================================================
# Close Method Tests
# ============================================================================

class TestBaseProviderClose:
    """Test BaseProvider close method."""
    
    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Test close method closes HTTP client."""
        provider = TestProvider("https://api.example.com")
        
        await provider.close()
        
        assert provider.client.is_closed


# ============================================================================
# SimpleProvider Tests
# ============================================================================

class TestSimpleProvider:
    """Test SimpleProvider implementation."""
    
    @pytest.mark.asyncio
    async def test_simple_provider_initialization(self):
        """Test SimpleProvider can be initialized."""
        provider = SimpleProvider("https://api.example.com")
        
        assert provider.base_url == "https://api.example.com"
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self):
        """Test validate_connection returns True on success."""
        provider = SimpleProvider("https://api.example.com")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            result = await provider.validate_connection()
        
        assert result is True
        
        await provider.close()
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self):
        """Test validate_connection returns False on failure."""
        provider = SimpleProvider("https://api.example.com")
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = httpx.HTTPError("Connection failed")
            
            result = await provider.validate_connection()
        
        assert result is False
        
        await provider.close()


# ============================================================================
# Integration Tests
# ============================================================================

class TestBaseProviderIntegration:
    """Integration tests for BaseProvider."""
    
    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test complete request flow from initialization to response."""
        auth = BearerAuth("test_token")
        
        async with TestProvider("https://api.example.com", auth_handler=auth) as provider:
            mock_response = Mock()
            mock_response.json.return_value = {"id": 1, "name": "Test User"}
            mock_response.raise_for_status = Mock()
            
            captured_request = None
            
            async def capture_request(request):
                nonlocal captured_request
                captured_request = request
                return mock_response
            
            with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = capture_request
                
                result = await provider.fetch("/users/1")
            
            # Verify result
            assert result == {"id": 1, "name": "Test User"}
            
            
            # Verify auth was injected
            assert captured_request is not None
            # Verify auth was injected
            assert captured_request.headers["Authorization"] == "Bearer test_token"
            
            # Verify URL was built correctly
            assert str(captured_request.url) == "https://api.example.com/users/1"
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Test that fetch retries on transient failures."""
        provider = TestProvider("https://api.example.com")
        
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        
        call_count = 0
        
        async def fail_then_succeed(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.RequestError("Temporary failure")
            return mock_response
        
        with patch.object(provider.client, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = fail_then_succeed
            
            result = await provider.fetch("/users")
        
        assert result == {"success": True}
        assert call_count == 2  # Failed once, then succeeded
        
        await provider.close()


# Made with Bob
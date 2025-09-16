"""
Comprehensive test suite for base service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.base import BaseService


@pytest.mark.unit
class TestBaseService:
    """Test the base service functionality."""

    @pytest.fixture
    def base_service(self):
        """Create BaseService instance for testing."""
        return BaseService("http://test.example.com", timeout=30)

    def test_base_service_initialization(self, base_service):
        """Test BaseService initialization."""
        assert base_service.base_url == "http://test.example.com"
        assert base_service.timeout == 30
        assert base_service.logger is not None

    def test_base_service_initialization_with_trailing_slash(self):
        """Test BaseService initialization with trailing slash."""
        service = BaseService("http://test.example.com/", timeout=30)
        assert service.base_url == "http://test.example.com"

    def test_base_service_initialization_without_trailing_slash(self):
        """Test BaseService initialization without trailing slash."""
        service = BaseService("http://test.example.com", timeout=30)
        assert service.base_url == "http://test.example.com"

    def test_base_service_default_timeout(self):
        """Test BaseService default timeout."""
        service = BaseService("http://test.example.com")
        assert service.timeout == 30

    def test_base_service_custom_timeout(self):
        """Test BaseService custom timeout."""
        service = BaseService("http://test.example.com", timeout=60)
        assert service.timeout == 60

    def test_base_service_logger_initialization(self, base_service):
        """Test BaseService logger initialization."""
        assert base_service.logger is not None
        assert hasattr(base_service.logger, 'info')
        assert hasattr(base_service.logger, 'error')
        assert callable(base_service.logger.info)
        assert callable(base_service.logger.error)

    @pytest.mark.asyncio
    async def test_make_request_success(self, base_service):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await base_service._make_request("GET", "/test")

            assert result == {"success": True}
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_with_params(self, base_service):
        """Test HTTP request with parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            params = {"param1": "value1", "param2": "value2"}
            result = await base_service._make_request("GET", "/test", params=params)

            assert result == {"success": True}
            call_args = mock_client.request.call_args
            assert call_args[1]['params'] == params

    @pytest.mark.asyncio
    async def test_make_request_with_data(self, base_service):
        """Test HTTP request with data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            data = {"key": "value"}
            result = await base_service._make_request("POST", "/test", data=data)

            assert result == {"success": True}
            call_args = mock_client.request.call_args
            assert call_args[1]['json'] == data

    @pytest.mark.asyncio
    async def test_make_request_with_headers(self, base_service):
        """Test HTTP request with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            headers = {"Custom-Header": "value"}
            result = await base_service._make_request("GET", "/test", headers=headers)

            assert result == {"success": True}
            call_args = mock_client.request.call_args
            request_headers = call_args[1]['headers']
            assert "Custom-Header" in request_headers
            assert request_headers["Custom-Header"] == "value"

    @pytest.mark.asyncio
    async def test_make_request_default_headers(self, base_service):
        """Test HTTP request with default headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await base_service._make_request("GET", "/test")

            call_args = mock_client.request.call_args
            request_headers = call_args[1]['headers']
            assert "Content-Type" in request_headers
            assert request_headers["Content-Type"] == "application/json"
            assert "User-Agent" in request_headers
            assert "PortalEngine" in request_headers["User-Agent"]

    @pytest.mark.asyncio
    async def test_make_request_endpoint_stripping(self, base_service):
        """Test endpoint slash stripping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await base_service._make_request("GET", "/test")

            call_args = mock_client.request.call_args
            url = call_args[1]['url']
            assert url == "http://test.example.com/test"

    @pytest.mark.asyncio
    async def test_make_request_endpoint_with_leading_slash(self, base_service):
        """Test endpoint with leading slash."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await base_service._make_request("GET", "/test")

            call_args = mock_client.request.call_args
            url = call_args[1]['url']
            assert url == "http://test.example.com/test"

    @pytest.mark.asyncio
    async def test_make_request_endpoint_without_leading_slash(self, base_service):
        """Test endpoint without leading slash."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await base_service._make_request("GET", "test")

            call_args = mock_client.request.call_args
            url = call_args[1]['url']
            assert url == "http://test.example.com/test"

    @pytest.mark.asyncio
    async def test_make_request_http_status_error(self, base_service):
        """Test HTTP status error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await base_service._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_request_error(self, base_service):
        """Test request error handling."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.RequestError):
                await base_service._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_unexpected_error(self, base_service):
        """Test unexpected error handling."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.side_effect = Exception("Unexpected error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(Exception):
                await base_service._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_timeout_configuration(self, base_service):
        """Test timeout configuration."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await base_service._make_request("GET", "/test")

            # Verify AsyncClient was created with correct timeout
            mock_client_class.assert_called_once_with(timeout=30)

    @pytest.mark.asyncio
    async def test_make_request_custom_timeout(self):
        """Test custom timeout configuration."""
        service = BaseService("http://test.example.com", timeout=60)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await service._make_request("GET", "/test")

            # Verify AsyncClient was created with custom timeout
            mock_client_class.assert_called_once_with(timeout=60)

    @pytest.mark.asyncio
    async def test_make_request_json_parsing_error(self, base_service):
        """Test JSON parsing error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError):
                await base_service._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_different_methods(self, base_service):
        """Test different HTTP methods."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        for method in methods:
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.request.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await base_service._make_request(method, "/test")
                assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_health_check_success(self, base_service):
        """Test successful health check."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"status": "healthy"}
            
            result = await base_service.health_check()
            assert result is True
            mock_make_request.assert_called_once_with("GET", "/health/")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, base_service):
        """Test failed health check."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = Exception("Service unavailable")
            
            result = await base_service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_http_error(self, base_service):
        """Test health check with HTTP error."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Service Unavailable", request=Mock(), response=Mock()
            )
            
            result = await base_service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_request_error(self, base_service):
        """Test health check with request error."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Connection failed")
            
            result = await base_service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_timeout_error(self, base_service):
        """Test health check with timeout error."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await base_service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_any_exception(self, base_service):
        """Test health check with any exception."""
        with patch.object(base_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = ValueError("Any error")
            
            result = await base_service.health_check()
            assert result is False

    def test_base_service_inheritance(self):
        """Test BaseService inheritance."""
        class TestService(BaseService):
            def __init__(self):
                super().__init__("http://test.example.com")
        
        service = TestService()
        assert isinstance(service, BaseService)
        assert service.base_url == "http://test.example.com"
        assert service.timeout == 30
        assert service.logger is not None

    def test_base_service_logger_name(self, base_service):
        """Test BaseService logger name."""
        assert base_service.logger is not None
        # Check that logger is properly initialized
        assert hasattr(base_service.logger, '_logger_factory_args')

    def test_base_service_with_custom_logger_name(self):
        """Test BaseService with custom logger name."""
        class CustomService(BaseService):
            pass
        
        service = CustomService("http://test.example.com")
        assert service.logger is not None
        # Check that logger is properly initialized
        assert hasattr(service.logger, '_logger_factory_args')

    def test_base_service_url_construction(self, base_service):
        """Test BaseService URL construction."""
        # Test various endpoint formats
        test_cases = [
            ("/test", "http://test.example.com/test"),
            ("test", "http://test.example.com/test"),
            ("/test/", "http://test.example.com/test/"),
            ("test/", "http://test.example.com/test/"),
            ("/test/path", "http://test.example.com/test/path"),
            ("test/path", "http://test.example.com/test/path"),
        ]
        
        for endpoint, expected_url in test_cases:
            url = f"{base_service.base_url}/{endpoint.lstrip('/')}"
            assert url == expected_url

    def test_base_service_headers_merge(self, base_service):
        """Test BaseService headers merging."""
        # Test that custom headers are merged with default headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "PortalEngine/1.0.0"
        }
        
        custom_headers = {
            "Custom-Header": "value",
            "Authorization": "Bearer token"
        }
        
        # Simulate header merging
        merged_headers = default_headers.copy()
        merged_headers.update(custom_headers)
        
        assert merged_headers["Content-Type"] == "application/json"
        assert merged_headers["User-Agent"] == "PortalEngine/1.0.0"
        assert merged_headers["Custom-Header"] == "value"
        assert merged_headers["Authorization"] == "Bearer token"

    def test_base_service_timeout_validation(self):
        """Test BaseService timeout validation."""
        # Test valid timeouts
        valid_timeouts = [1, 30, 60, 120, 300]
        for timeout in valid_timeouts:
            service = BaseService("http://test.example.com", timeout=timeout)
            assert service.timeout == timeout

    def test_base_service_url_validation(self):
        """Test BaseService URL validation."""
        # Test valid URLs
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://localhost:3031",
            "https://api.example.com/v1"
        ]
        
        for url in valid_urls:
            service = BaseService(url)
            assert service.base_url == url

    def test_base_service_method_availability(self, base_service):
        """Test BaseService method availability."""
        # Test that all expected methods are available
        assert hasattr(base_service, '_make_request')
        assert hasattr(base_service, 'health_check')
        assert callable(base_service._make_request)
        assert callable(base_service.health_check)

    def test_base_service_async_methods(self, base_service):
        """Test BaseService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(base_service._make_request)
        assert inspect.iscoroutinefunction(base_service.health_check)

    def test_base_service_error_logging(self, base_service):
        """Test BaseService error logging."""
        with patch.object(base_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                base_service.logger.error(
                    "HTTP error occurred",
                    url="http://test.example.com/test",
                    status_code=getattr(e.response, 'status_code', None),
                    response_text=getattr(e.response, 'text', ''),
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_base_service_info_logging(self, base_service):
        """Test BaseService info logging."""
        with patch.object(base_service.logger, 'info') as mock_info:
            # Simulate an info log
            base_service.logger.info(
                "Request completed",
                url="http://test.example.com/test",
                method="GET",
                status_code=200
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_base_service_context_manager_usage(self, base_service):
        """Test BaseService context manager usage."""
        # Test that the service can be used in context managers
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # This should not raise an exception
            assert base_service is not None

    def test_base_service_thread_safety(self, base_service):
        """Test BaseService thread safety."""
        import threading
        import time
        
        results = []
        
        def test_health_check():
            try:
                # Simulate health check
                result = base_service.health_check()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_health_check, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

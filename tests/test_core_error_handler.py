"""
Tests for app/core/error_handler.py
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.error_handler import (
    create_error_response,
    handle_exception,
    log_service_error,
    safe_execute
)
from app.core.exceptions import PortalEngineException, ServiceUnavailableError
from app.models.responses import APIResponse


class TestCreateErrorResponse:
    """Test cases for create_error_response function"""
    
    def test_create_error_response_basic(self):
        """Test basic error response creation"""
        response = create_error_response(
            status_code=400,
            message="Bad request",
            error_details={"field": "value"}
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        data = response.body.decode()
        assert "Bad request" in data
        assert "field" in data
    
    def test_create_error_response_with_correlation_id(self):
        """Test error response with correlation ID"""
        response = create_error_response(
            status_code=500,
            message="Internal error",
            correlation_id="test-correlation-123"
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        data = response.body.decode()
        assert "test-correlation-123" in data
    
    def test_create_error_response_with_traceback(self):
        """Test error response with traceback"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            response = create_error_response(
                status_code=500,
                message="Internal error",
                include_traceback=True,
                exc=e
            )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        data = response.body.decode()
        assert "ValueError" in data
        assert "Test error" in data
    
    def test_create_error_response_minimal(self):
        """Test minimal error response"""
        response = create_error_response(
            status_code=404,
            message="Not found"
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        data = response.body.decode()
        assert "Not found" in data


class TestHandleException:
    """Test cases for handle_exception function"""
    
    @pytest.mark.asyncio
    async def test_handle_exception_validation_error(self):
        """Test handling ValidationError"""
        from pydantic import ValidationError
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "POST"
        request.headers = {}
        
        validation_error = ValidationError.from_exception_data(
            "ValidationError", 
            [{"type": "missing", "loc": ("field",), "msg": "Field required"}]
        )
        
        response = await handle_exception(request, validation_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        data = response.body.decode()
        assert "validation" in data.lower()
    
    @pytest.mark.asyncio
    async def test_handle_exception_http_exception(self):
        """Test handling HTTPException"""
        from fastapi import HTTPException
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        
        http_error = HTTPException(status_code=404, detail="Not found")
        
        response = await handle_exception(request, http_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        data = response.body.decode()
        assert "Not found" in data
    
    @pytest.mark.asyncio
    async def test_handle_exception_portal_engine_exception(self):
        """Test handling PortalEngineException"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "POST"
        request.headers = {}
        
        portal_error = ServiceUnavailableError("test_service", "Service down")
        
        response = await handle_exception(request, portal_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
        data = response.body.decode()
        assert "Service down" in data
    
    @pytest.mark.asyncio
    async def test_handle_exception_generic_exception(self):
        """Test handling generic Exception"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "POST"
        request.headers = {}
        
        generic_error = Exception("Generic error")
        
        response = await handle_exception(request, generic_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        data = response.body.decode()
        assert "Generic error" in data
    
    @pytest.mark.asyncio
    async def test_handle_exception_with_correlation_id(self):
        """Test handling exception with correlation ID"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "POST"
        request.headers = {"X-Correlation-ID": "test-123"}
        
        generic_error = Exception("Test error")
        
        response = await handle_exception(request, generic_error)
        
        assert isinstance(response, JSONResponse)
        data = response.body.decode()
        assert "test-123" in data


class TestLogServiceError:
    """Test cases for log_service_error function"""
    
    @patch('app.core.error_handler.logger')
    def test_log_service_error_basic(self, mock_logger):
        """Test basic service error logging"""
        error = Exception("Service error")
        
        log_service_error("test_service", "test_operation", error)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "test_service" in str(call_args)
        assert "test_operation" in str(call_args)
        assert "Service error" in str(call_args)
    
    @patch('app.core.error_handler.logger')
    def test_log_service_error_with_context(self, mock_logger):
        """Test service error logging with additional context"""
        error = Exception("Service error")
        context = {"user_id": "123", "request_id": "req-456"}
        
        log_service_error("test_service", "test_operation", error, context)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "test_service" in str(call_args)
        assert "test_operation" in str(call_args)
        assert "123" in str(call_args)
        assert "req-456" in str(call_args)
    
    @patch('app.core.error_handler.logger')
    def test_log_service_error_none_context(self, mock_logger):
        """Test service error logging with None context"""
        error = Exception("Service error")
        
        log_service_error("test_service", "test_operation", error, None)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "test_service" in str(call_args)
        assert "test_operation" in str(call_args)


class TestSafeExecute:
    """Test cases for safe_execute decorator"""
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function"""
        @safe_execute
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        assert result == 5
    
    @patch('app.core.error_handler.logger')
    def test_safe_execute_exception(self, mock_logger):
        """Test safe_execute with exception"""
        @safe_execute
        def test_function(x, y):
            raise ValueError("Test error")
        
        result = test_function(2, 3)
        
        # Should return None on exception
        assert result is None
        # Should log the error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Test error" in str(call_args)
    
    @patch('app.core.error_handler.logger')
    def test_safe_execute_with_args_kwargs(self, mock_logger):
        """Test safe_execute with various argument types"""
        @safe_execute
        def test_function(a, b, c=None, d=None):
            if a == "error":
                raise ValueError("Test error")
            return f"{a}-{b}-{c}-{d}"
        
        # Success case
        result = test_function("test", "value", c="optional", d="keyword")
        assert result == "test-value-optional-keyword"
        
        # Error case
        result = test_function("error", "value", c="optional")
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('app.core.error_handler.logger')
    def test_safe_execute_async_function(self, mock_logger):
        """Test safe_execute with async function"""
        import asyncio
        
        @safe_execute
        async def async_test_function(x):
            if x == "error":
                raise ValueError("Async error")
            return x * 2
        
        # Success case
        result = asyncio.run(async_test_function("test"))
        assert result == "testtest"
        
        # Error case
        result = asyncio.run(async_test_function("error"))
        assert result is None
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Async error" in str(call_args)
    
    def test_safe_execute_preserves_function_metadata(self):
        """Test that safe_execute preserves function metadata"""
        @safe_execute
        def test_function(x):
            """Test function docstring"""
            return x
        
        assert test_function.__name__ == "test_function"
        assert "Test function docstring" in test_function.__doc__
    
    @patch('app.core.error_handler.logger')
    def test_safe_execute_multiple_exceptions(self, mock_logger):
        """Test safe_execute with multiple different exceptions"""
        @safe_execute
        def test_function(exception_type):
            if exception_type == "ValueError":
                raise ValueError("Value error")
            elif exception_type == "TypeError":
                raise TypeError("Type error")
            elif exception_type == "RuntimeError":
                raise RuntimeError("Runtime error")
            return "success"
        
        # Test different exception types
        test_function("ValueError")
        test_function("TypeError")
        test_function("RuntimeError")
        
        # Should have logged 3 errors
        assert mock_logger.error.call_count == 3
        
        # Test success case
        result = test_function("success")
        assert result == "success"

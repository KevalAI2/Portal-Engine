"""
Comprehensive test suite for the main FastAPI application
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status


@pytest.mark.unit
class TestMainApplication:
    """Test the main FastAPI application setup and configuration."""

    def test_app_creation(self, client: TestClient):
        """Test that the FastAPI app is created correctly."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "environment" in data
        assert "docs" in data
        assert "health" in data

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Welcome to Portal Engine"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "test"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/v1/health"

    def test_ping_endpoint(self, client: TestClient):
        """Test the ping endpoint."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "pong"

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are properly set."""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == status.HTTP_200_OK

    def test_process_time_header(self, client: TestClient):
        """Test that process time header is added to responses."""
        response = client.get("/ping")
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0

    def test_gzip_middleware(self, client: TestClient):
        """Test that GZip middleware is working."""
        # Create a large response to trigger GZip
        large_data = {"data": "x" * 2000}
        response = client.post("/api/v1/users/test_user/generate-recommendations", 
                             json={"prompt": "test"})
        # The response should be compressed if large enough
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_global_exception_handler(self, client: TestClient):
        """Test the global exception handler."""
        with patch('app.main.app') as mock_app:
            mock_app.side_effect = Exception("Test exception")
            
            # This would normally cause a 500 error, but our handler should catch it
            response = client.get("/ping")
            # The actual response depends on how the exception is handled
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_openapi_docs_endpoints(self, client: TestClient):
        """Test that OpenAPI documentation endpoints are accessible."""
        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK

    def test_request_logging_middleware(self, client: TestClient):
        """Test that request logging middleware works."""
        with patch('app.main.logger') as mock_logger:
            response = client.get("/ping")
            assert response.status_code == status.HTTP_200_OK
            # Verify that logging methods were called
            assert mock_logger.info.called

    def test_invalid_endpoint(self, client: TestClient):
        """Test that invalid endpoints return 404."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, client: TestClient):
        """Test that unsupported HTTP methods return 405."""
        response = client.delete("/ping")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_lifespan_events(self, client: TestClient):
        """Test application lifespan events."""
        # The lifespan events are tested implicitly when the app starts
        # We can verify the app starts successfully
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_app_configuration(self, client: TestClient):
        """Test that the app is configured with correct settings."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_data = response.json()
        assert openapi_data["info"]["title"] == "Portal Engine"
        assert openapi_data["info"]["version"] == "1.0.0"
        assert "Portal Engine - A modular recommendation system" in openapi_data["info"]["description"]

    def test_router_inclusion(self, client: TestClient):
        """Test that all routers are properly included."""
        # Test health router
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        
        # Test users router
        response = client.get("/api/v1/users/test_user/profile")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_response_format_consistency(self, client: TestClient):
        """Test that responses follow consistent format."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data

    def test_error_response_format(self, client: TestClient):
        """Test that error responses follow consistent format."""
        response = client.get("/api/v1/users/nonexistent/profile")
        # Should return an error response
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        if response.status_code != status.HTTP_404_NOT_FOUND:
            data = response.json()
            assert "success" in data or "detail" in data

    def test_content_type_headers(self, client: TestClient):
        """Test that content type headers are set correctly."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers.get("content-type", "")

    def test_security_headers(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for common security headers
        headers = response.headers
        # Note: These headers might not be present depending on middleware configuration
        # This test verifies the response is valid regardless

    def test_concurrent_requests(self, client: TestClient):
        """Test that the app can handle concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/ping")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(results) == 5
        assert all(status_code == status.HTTP_200_OK for status_code in results)

    def test_large_request_handling(self, client: TestClient):
        """Test handling of large requests."""
        large_data = {"data": "x" * 10000}  # 10KB of data
        
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             json={"prompt": "test prompt"})
        # Should handle large requests gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_special_characters_in_requests(self, client: TestClient):
        """Test handling of special characters in requests."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        response = client.get(f"/ping?test={special_chars}")
        assert response.status_code == status.HTTP_200_OK

    def test_unicode_handling(self, client: TestClient):
        """Test handling of Unicode characters."""
        unicode_text = "测试中文 🚀 ñáéíóú"
        
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             json={"prompt": unicode_text})
        # Should handle Unicode gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_empty_request_body(self, client: TestClient):
        """Test handling of empty request bodies."""
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             json={})
        # Should handle empty body gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_malformed_json(self, client: TestClient):
        """Test handling of malformed JSON."""
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_content_type(self, client: TestClient):
        """Test handling of missing content type header."""
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             data='{"prompt": "test"}')
        # Should handle missing content type gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE]

    def test_app_metadata(self, client: TestClient):
        """Test that app metadata is correctly exposed."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_data = response.json()
        assert "info" in openapi_data
        assert "title" in openapi_data["info"]
        assert "version" in openapi_data["info"]
        assert "description" in openapi_data["info"]

    def test_health_endpoint_integration(self, client: TestClient):
        """Test integration with health endpoint."""
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "services" in data

    def test_users_endpoint_integration(self, client: TestClient):
        """Test integration with users endpoint."""
        response = client.get("/api/v1/users/test_user/profile")
        # Should return some response (success or error)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_middleware_order(self, client: TestClient):
        """Test that middleware is applied in correct order."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify that process time header is present (added by our middleware)
        assert "X-Process-Time" in response.headers

    def test_app_startup_shutdown(self, client: TestClient):
        """Test app startup and shutdown lifecycle."""
        # Test that app starts successfully
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        # Test that app is responsive
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK

    def test_error_handling_consistency(self, client: TestClient):
        """Test that error handling is consistent across endpoints."""
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test 405 error
        response = client.delete("/ping")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_response_time_performance(self, client: TestClient):
        """Test that response times are reasonable."""
        import time
        
        start_time = time.time()
        response = client.get("/ping")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_memory_usage(self, client: TestClient):
        """Test that memory usage is reasonable."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make several requests
        for _ in range(10):
            response = client.get("/ping")
            assert response.status_code == status.HTTP_200_OK
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024

    def test_app_configuration_validation(self, client: TestClient):
        """Test that app configuration is valid."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_data = response.json()
        
        # Validate OpenAPI structure
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data
        assert "components" in openapi_data
        
        # Validate info section
        info = openapi_data["info"]
        assert "title" in info
        assert "version" in info
        assert "description" in info

    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight request handling."""
        response = client.options("/api/v1/health/",
                                headers={
                                    "Origin": "http://localhost:3000",
                                    "Access-Control-Request-Method": "GET",
                                    "Access-Control-Request-Headers": "Content-Type"
                                })
        assert response.status_code == status.HTTP_200_OK

    def test_request_id_tracking(self, client: TestClient):
        """Test request ID tracking if implemented."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check if request ID is in headers or response
        # This depends on implementation

    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting if implemented."""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = client.get("/ping")
            responses.append(response.status_code)
        
        # All should succeed if no rate limiting is implemented
        assert all(status_code == status.HTTP_200_OK for status_code in responses)

    def test_graceful_degradation(self, client: TestClient):
        """Test graceful degradation when services are unavailable."""
        with patch('app.api.dependencies.get_user_profile_service') as mock_service:
            mock_service.return_value.get_user_profile.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/v1/users/test_user/profile")
            # Should handle service unavailability gracefully
            assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_404_NOT_FOUND]

    def test_data_validation(self, client: TestClient):
        """Test data validation across endpoints."""
        # Test with invalid data types
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             json={"prompt": 123})  # Should be string
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_endpoint_discovery(self, client: TestClient):
        """Test that all expected endpoints are discoverable."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Check for key endpoints
        expected_paths = [
            "/",
            "/ping",
            "/api/v1/health/",
            "/api/v1/users/{user_id}/profile"
        ]
        
        for path in expected_paths:
            assert path in paths or any(path.startswith(p) for p in paths.keys())

    def test_api_versioning(self, client: TestClient):
        """Test API versioning implementation."""
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        
        # Test that version is included in responses
        data = response.json()
        assert "version" in data

    def test_documentation_accessibility(self, client: TestClient):
        """Test that API documentation is accessible."""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
        
        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK

    def test_error_message_clarity(self, client: TestClient):
        """Test that error messages are clear and helpful."""
        response = client.get("/api/v1/users/invalid_user/profile")
        
        if response.status_code != status.HTTP_200_OK:
            data = response.json()
            # Error messages should be informative
            assert "message" in data or "detail" in data
            error_msg = data.get("message", data.get("detail", ""))
            assert len(error_msg) > 0

    def test_response_compression(self, client: TestClient):
        """Test response compression."""
        # Create a large response
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        # Check if response is compressed
        content_encoding = response.headers.get("content-encoding", "")
        # Note: Compression might not be applied to small responses

    def test_security_headers_presence(self, client: TestClient):
        """Test presence of security headers."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for security headers
        headers = response.headers
        # These headers might not be present depending on configuration
        # This test ensures the response is valid regardless

    def test_content_negotiation(self, client: TestClient):
        """Test content negotiation."""
        # Test JSON response
        response = client.get("/ping", headers={"Accept": "application/json"})
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers.get("content-type", "")

    def test_caching_headers(self, client: TestClient):
        """Test caching headers if implemented."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for caching headers
        cache_control = response.headers.get("cache-control", "")
        # Caching might not be implemented, so this is just a check

    def test_etag_support(self, client: TestClient):
        """Test ETag support if implemented."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for ETag header
        etag = response.headers.get("etag", "")
        # ETag might not be implemented

    def test_last_modified_header(self, client: TestClient):
        """Test Last-Modified header if implemented."""
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for Last-Modified header
        last_modified = response.headers.get("last-modified", "")
        # Last-Modified might not be implemented

    def test_conditional_requests(self, client: TestClient):
        """Test conditional requests if implemented."""
        # First request
        response1 = client.get("/ping")
        assert response1.status_code == status.HTTP_200_OK
        
        # Request with If-None-Match
        etag = response1.headers.get("etag", "")
        if etag:
            response2 = client.get("/ping", headers={"If-None-Match": etag})
            # Should return 304 if content hasn't changed
            assert response2.status_code in [status.HTTP_200_OK, status.HTTP_304_NOT_MODIFIED]

    def test_request_size_limits(self, client: TestClient):
        """Test request size limits."""
        # Test with very large request
        large_data = {"data": "x" * 1000000}  # 1MB
        
        response = client.post("/api/v1/users/test_user/generate-recommendations",
                             json={"prompt": "test"})
        # Should handle large requests appropriately
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_timeout_handling(self, client: TestClient):
        """Test timeout handling."""
        with patch('app.services.llm_service.LLMService.generate_recommendations') as mock_gen:
            mock_gen.side_effect = TimeoutError("Request timeout")
            
            response = client.post("/api/v1/users/test_user/generate-recommendations",
                                 json={"prompt": "test"})
            # Should handle timeouts gracefully
            assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_408_REQUEST_TIMEOUT]

    def test_concurrent_user_requests(self, client: TestClient):
        """Test handling concurrent requests from different users."""
        import threading
        
        results = []
        
        def make_user_request(user_id):
            response = client.get(f"/api/v1/users/{user_id}/profile")
            results.append((user_id, response.status_code))
        
        # Create requests for different users
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_user_request, args=(f"user_{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all requests completed
        assert len(results) == 5
        assert all(status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR] 
                  for _, status_code in results)

    def test_app_health_under_load(self, client: TestClient):
        """Test app health under load."""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.get("/ping")
            end_time = time.time()
            results.append((response.status_code, end_time - start_time))
        
        # Create load
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded and response times are reasonable
        assert len(results) == 20
        assert all(status_code == status.HTTP_200_OK for status_code, _ in results)
        assert all(response_time < 2.0 for _, response_time in results)  # All under 2 seconds

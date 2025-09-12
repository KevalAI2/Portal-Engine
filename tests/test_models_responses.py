"""
Tests for app/models/responses.py
"""
import pytest
from pydantic import ValidationError
from app.models.responses import APIResponse, HealthCheckResponse


class TestAPIResponse:
    """Test cases for APIResponse model"""
    
    def test_success_response_default(self):
        """Test success response with default values"""
        response = APIResponse.success_response()
        assert response.success is True
        assert response.data is None
        assert response.message == "Success"
        assert response.status_code == 200
        assert response.error is None
    
    def test_success_response_with_data(self):
        """Test success response with custom data"""
        data = {"key": "value", "count": 42}
        response = APIResponse.success_response(data=data)
        assert response.success is True
        assert response.data == data
        assert response.message == "Success"
        assert response.status_code == 200
        assert response.error is None
    
    def test_success_response_with_custom_message(self):
        """Test success response with custom message"""
        response = APIResponse.success_response(message="Operation completed")
        assert response.success is True
        assert response.data is None
        assert response.message == "Operation completed"
        assert response.status_code == 200
        assert response.error is None
    
    def test_success_response_with_custom_status_code(self):
        """Test success response with custom status code"""
        response = APIResponse.success_response(status_code=201)
        assert response.success is True
        assert response.data is None
        assert response.message == "Success"
        assert response.status_code == 201
        assert response.error is None
    
    def test_success_response_with_all_params(self):
        """Test success response with all custom parameters"""
        data = {"result": "created"}
        response = APIResponse.success_response(
            data=data,
            message="Resource created",
            status_code=201
        )
        assert response.success is True
        assert response.data == data
        assert response.message == "Resource created"
        assert response.status_code == 201
        assert response.error is None
    
    def test_error_response_default(self):
        """Test error response with default values"""
        response = APIResponse.error_response()
        assert response.success is False
        assert response.data is None
        assert response.message == "Error"
        assert response.status_code == 400
        assert response.error is None
    
    def test_error_response_with_message(self):
        """Test error response with custom message"""
        response = APIResponse.error_response(message="Validation failed")
        assert response.success is False
        assert response.data is None
        assert response.message == "Validation failed"
        assert response.status_code == 400
        assert response.error is None
    
    def test_error_response_with_data(self):
        """Test error response with data"""
        data = {"field": "value"}
        response = APIResponse.error_response(data=data)
        assert response.success is False
        assert response.data == data
        assert response.message == "Error"
        assert response.status_code == 400
        assert response.error is None
    
    def test_error_response_with_status_code(self):
        """Test error response with custom status code"""
        response = APIResponse.error_response(status_code=404)
        assert response.success is False
        assert response.data is None
        assert response.message == "Error"
        assert response.status_code == 404
        assert response.error is None
    
    def test_error_response_with_error_details(self):
        """Test error response with error details"""
        error_details = {"code": "VALIDATION_ERROR", "field": "email"}
        response = APIResponse.error_response(error=error_details)
        assert response.success is False
        assert response.data is None
        assert response.message == "Error"
        assert response.status_code == 400
        assert response.error == error_details
    
    def test_error_response_with_all_params(self):
        """Test error response with all custom parameters"""
        data = {"input": "invalid"}
        error_details = {"code": "INVALID_INPUT"}
        response = APIResponse.error_response(
            message="Invalid input provided",
            data=data,
            status_code=422,
            error=error_details
        )
        assert response.success is False
        assert response.data == data
        assert response.message == "Invalid input provided"
        assert response.status_code == 422
        assert response.error == error_details
    
    def test_validation_error_response_default(self):
        """Test validation error response with default values"""
        response = APIResponse.validation_error_response()
        assert response.success is False
        assert response.message == "Validation error"
        assert response.status_code == 422
        assert response.error == {"validation_errors": []}
    
    def test_validation_error_response_with_message(self):
        """Test validation error response with custom message"""
        response = APIResponse.validation_error_response(message="Field validation failed")
        assert response.success is False
        assert response.message == "Field validation failed"
        assert response.status_code == 422
        assert response.error == {"validation_errors": []}
    
    def test_validation_error_response_with_errors(self):
        """Test validation error response with validation errors"""
        errors = [{"field": "email", "message": "Invalid email format"}]
        response = APIResponse.validation_error_response(errors=errors)
        assert response.success is False
        assert response.message == "Validation error"
        assert response.status_code == 422
        assert response.error == {"validation_errors": errors}
    
    def test_validation_error_response_with_all_params(self):
        """Test validation error response with all custom parameters"""
        errors = [{"field": "password", "message": "Password too short"}]
        response = APIResponse.validation_error_response(
            message="Password validation failed",
            errors=errors
        )
        assert response.success is False
        assert response.message == "Password validation failed"
        assert response.status_code == 422
        assert response.error == {"validation_errors": errors}
    
    def test_service_unavailable_response_default(self):
        """Test service unavailable response with default values"""
        response = APIResponse.service_unavailable_response()
        assert response.success is False
        assert response.message == "Service temporarily unavailable"
        assert response.status_code == 503
        assert response.error is None
    
    def test_service_unavailable_response_with_message(self):
        """Test service unavailable response with custom message"""
        response = APIResponse.service_unavailable_response(message="Database connection failed")
        assert response.success is False
        assert response.message == "Database connection failed"
        assert response.status_code == 503
        assert response.error is None
    
    def test_service_unavailable_response_with_service(self):
        """Test service unavailable response with service name"""
        response = APIResponse.service_unavailable_response(service="database")
        assert response.success is False
        assert response.message == "Service temporarily unavailable"
        assert response.status_code == 503
        assert response.error == {"service": "database"}
    
    def test_service_unavailable_response_with_all_params(self):
        """Test service unavailable response with all custom parameters"""
        response = APIResponse.service_unavailable_response(
            message="Redis connection timeout",
            service="redis"
        )
        assert response.success is False
        assert response.message == "Redis connection timeout"
        assert response.status_code == 503
        assert response.error == {"service": "redis"}
    
    def test_direct_instantiation_success(self):
        """Test direct instantiation of successful response"""
        response = APIResponse(
            success=True,
            data={"result": "ok"},
            message="Operation successful",
            status_code=200
        )
        assert response.success is True
        assert response.data == {"result": "ok"}
        assert response.message == "Operation successful"
        assert response.status_code == 200
        assert response.error is None
    
    def test_direct_instantiation_error(self):
        """Test direct instantiation of error response"""
        response = APIResponse(
            success=False,
            data=None,
            message="Operation failed",
            status_code=500,
            error={"code": "INTERNAL_ERROR"}
        )
        assert response.success is False
        assert response.data is None
        assert response.message == "Operation failed"
        assert response.status_code == 500
        assert response.error == {"code": "INTERNAL_ERROR"}
    
    def test_model_validation_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            APIResponse()  # Missing required fields
    
    def test_model_validation_success_field(self):
        """Test that success field is required"""
        with pytest.raises(ValidationError):
            APIResponse(message="test")  # Missing success field
    
    def test_model_validation_message_field(self):
        """Test that message field is required"""
        with pytest.raises(ValidationError):
            APIResponse(success=True)  # Missing message field


class TestHealthCheckResponse:
    """Test cases for HealthCheckResponse model"""
    
    def test_valid_health_check_response(self):
        """Test valid health check response"""
        response = HealthCheckResponse(
            status="healthy",
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="development",
            services={
                "database": "healthy",
                "redis": "healthy",
                "celery": "degraded"
            }
        )
        assert response.status == "healthy"
        assert response.timestamp == "2023-01-01T00:00:00Z"
        assert response.version == "1.0.0"
        assert response.environment == "development"
        assert response.services == {
            "database": "healthy",
            "redis": "healthy",
            "celery": "degraded"
        }
    
    def test_health_check_response_with_empty_services(self):
        """Test health check response with empty services dict"""
        response = HealthCheckResponse(
            status="unhealthy",
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="production",
            services={}
        )
        assert response.status == "unhealthy"
        assert response.services == {}
    
    def test_health_check_response_missing_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            HealthCheckResponse()  # Missing all required fields
    
    def test_health_check_response_missing_status(self):
        """Test missing status field raises ValidationError"""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                timestamp="2023-01-01T00:00:00Z",
                version="1.0.0",
                environment="development",
                services={}
            )
    
    def test_health_check_response_missing_timestamp(self):
        """Test missing timestamp field raises ValidationError"""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                status="healthy",
                version="1.0.0",
                environment="development",
                services={}
            )
    
    def test_health_check_response_missing_version(self):
        """Test missing version field raises ValidationError"""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                status="healthy",
                timestamp="2023-01-01T00:00:00Z",
                environment="development",
                services={}
            )
    
    def test_health_check_response_missing_environment(self):
        """Test missing environment field raises ValidationError"""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                status="healthy",
                timestamp="2023-01-01T00:00:00Z",
                version="1.0.0",
                services={}
            )
    
    def test_health_check_response_missing_services(self):
        """Test missing services field raises ValidationError"""
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                status="healthy",
                timestamp="2023-01-01T00:00:00Z",
                version="1.0.0",
                environment="development"
            )
    
    def test_health_check_response_with_various_statuses(self):
        """Test health check response with various status values"""
        statuses = ["healthy", "unhealthy", "degraded", "unknown"]
        for status in statuses:
            response = HealthCheckResponse(
                status=status,
                timestamp="2023-01-01T00:00:00Z",
                version="1.0.0",
                environment="development",
                services={"test": "ok"}
            )
            assert response.status == status
    
    def test_health_check_response_with_various_environments(self):
        """Test health check response with various environment values"""
        environments = ["development", "staging", "production", "test"]
        for env in environments:
            response = HealthCheckResponse(
                status="healthy",
                timestamp="2023-01-01T00:00:00Z",
                version="1.0.0",
                environment=env,
                services={"test": "ok"}
            )
            assert response.environment == env
    
    def test_health_check_response_with_complex_services(self):
        """Test health check response with complex services dict"""
        services = {
            "database": "healthy",
            "redis": "degraded",
            "celery": "unhealthy",
            "external_api": "unknown",
            "queue": "healthy"
        }
        response = HealthCheckResponse(
            status="degraded",
            timestamp="2023-01-01T00:00:00Z",
            version="2.1.0",
            environment="production",
            services=services
        )
        assert response.services == services

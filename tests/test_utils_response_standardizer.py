"""
Tests for API response standardization utilities
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.utils.response_standardizer import (
    StandardResponse, create_json_response, handle_exception,
    standardize_pagination, standardize_list_response,
    standardize_single_response, standardize_created_response,
    standardize_updated_response, standardize_deleted_response
)


class TestStandardResponse:
    """Test StandardResponse class"""
    
    def test_success_response_basic(self):
        """Test basic success response"""
        response = StandardResponse.success()
        
        assert response["success"] is True
        assert response["message"] == "Success"
        assert response["status_code"] == 200
        assert response["data"] is None
        assert "metadata" not in response
    
    def test_success_response_with_data(self):
        """Test success response with data"""
        data = {"key": "value"}
        response = StandardResponse.success(data=data, message="Custom success")
        
        assert response["success"] is True
        assert response["message"] == "Custom success"
        assert response["status_code"] == 200
        assert response["data"] == data
    
    def test_success_response_with_metadata(self):
        """Test success response with metadata"""
        data = {"key": "value"}
        metadata = {"timestamp": "2023-01-01T00:00:00Z"}
        response = StandardResponse.success(data=data, metadata=metadata)
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["metadata"] == metadata
    
    def test_success_response_custom_status_code(self):
        """Test success response with custom status code"""
        response = StandardResponse.success(status_code=201)
        
        assert response["success"] is True
        assert response["status_code"] == 201
    
    def test_error_response_basic(self):
        """Test basic error response"""
        response = StandardResponse.error()
        
        assert response["success"] is False
        assert response["message"] == "An error occurred"
        assert response["status_code"] == 500
        assert "error_code" not in response
        assert "details" not in response
    
    def test_error_response_with_details(self):
        """Test error response with details"""
        response = StandardResponse.error(
            message="Custom error",
            status_code=400,
            error_code="CUSTOM_ERROR",
            details={"field": "value"}
        )
        
        assert response["success"] is False
        assert response["message"] == "Custom error"
        assert response["status_code"] == 400
        assert response["error_code"] == "CUSTOM_ERROR"
        assert response["details"] == {"field": "value"}
    
    def test_validation_error_response(self):
        """Test validation error response"""
        errors = {"field1": ["Required"], "field2": ["Invalid format"]}
        response = StandardResponse.validation_error("Validation failed", errors)
        
        assert response["success"] is False
        assert response["message"] == "Validation failed"
        assert response["status_code"] == 422
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["details"]["validation_errors"] == errors
    
    def test_validation_error_response_no_errors(self):
        """Test validation error response without errors"""
        response = StandardResponse.validation_error("Validation failed")
        
        assert response["success"] is False
        assert response["message"] == "Validation failed"
        assert response["status_code"] == 422
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["details"] is None
    
    def test_not_found_response_basic(self):
        """Test basic not found response"""
        response = StandardResponse.not_found()
        
        assert response["success"] is False
        assert response["message"] == "Resource not found"
        assert response["status_code"] == 404
        assert response["error_code"] == "NOT_FOUND"
        assert response["details"] is None
    
    def test_not_found_response_with_resource_type(self):
        """Test not found response with resource type"""
        response = StandardResponse.not_found("User not found", "user")
        
        assert response["success"] is False
        assert response["message"] == "User not found"
        assert response["status_code"] == 404
        assert response["error_code"] == "NOT_FOUND"
        assert response["details"]["resource_type"] == "user"
    
    def test_unauthorized_response_basic(self):
        """Test basic unauthorized response"""
        response = StandardResponse.unauthorized()
        
        assert response["success"] is False
        assert response["message"] == "Unauthorized access"
        assert response["status_code"] == 401
        assert response["error_code"] == "UNAUTHORIZED"
        assert response["details"] is None
    
    def test_unauthorized_response_with_details(self):
        """Test unauthorized response with details"""
        details = {"reason": "Invalid token"}
        response = StandardResponse.unauthorized("Invalid credentials", details)
        
        assert response["success"] is False
        assert response["message"] == "Invalid credentials"
        assert response["status_code"] == 401
        assert response["error_code"] == "UNAUTHORIZED"
        assert response["details"] == details
    
    def test_forbidden_response_basic(self):
        """Test basic forbidden response"""
        response = StandardResponse.forbidden()
        
        assert response["success"] is False
        assert response["message"] == "Access forbidden"
        assert response["status_code"] == 403
        assert response["error_code"] == "FORBIDDEN"
        assert response["details"] is None
    
    def test_forbidden_response_with_details(self):
        """Test forbidden response with details"""
        details = {"required_permission": "admin"}
        response = StandardResponse.forbidden("Insufficient permissions", details)
        
        assert response["success"] is False
        assert response["message"] == "Insufficient permissions"
        assert response["status_code"] == 403
        assert response["error_code"] == "FORBIDDEN"
        assert response["details"] == details
    
    def test_rate_limited_response_basic(self):
        """Test basic rate limited response"""
        response = StandardResponse.rate_limited()
        
        assert response["success"] is False
        assert response["message"] == "Rate limit exceeded"
        assert response["status_code"] == 429
        assert response["error_code"] == "RATE_LIMITED"
        assert response["details"] is None
    
    def test_rate_limited_response_with_retry_after(self):
        """Test rate limited response with retry after"""
        response = StandardResponse.rate_limited("Too many requests", 60)
        
        assert response["success"] is False
        assert response["message"] == "Too many requests"
        assert response["status_code"] == 429
        assert response["error_code"] == "RATE_LIMITED"
        assert response["details"]["retry_after"] == 60
    
    def test_server_error_response_basic(self):
        """Test basic server error response"""
        response = StandardResponse.server_error()
        
        assert response["success"] is False
        assert response["message"] == "Internal server error"
        assert response["status_code"] == 500
        assert response["error_code"] == "SERVER_ERROR"
        assert response["details"] is None
    
    def test_server_error_response_with_details(self):
        """Test server error response with details"""
        details = {"error_id": "err_123"}
        response = StandardResponse.server_error("Database error", details)
        
        assert response["success"] is False
        assert response["message"] == "Database error"
        assert response["status_code"] == 500
        assert response["error_code"] == "SERVER_ERROR"
        assert response["details"] == details
    
    def test_service_unavailable_response_basic(self):
        """Test basic service unavailable response"""
        response = StandardResponse.service_unavailable()
        
        assert response["success"] is False
        assert response["message"] == "Service temporarily unavailable"
        assert response["status_code"] == 503
        assert response["error_code"] == "SERVICE_UNAVAILABLE"
        assert response["details"] is None
    
    def test_service_unavailable_response_with_retry_after(self):
        """Test service unavailable response with retry after"""
        response = StandardResponse.service_unavailable("Maintenance mode", 300)
        
        assert response["success"] is False
        assert response["message"] == "Maintenance mode"
        assert response["status_code"] == 503
        assert response["error_code"] == "SERVICE_UNAVAILABLE"
        assert response["details"]["retry_after"] == 300


class TestCreateJsonResponse:
    """Test create_json_response function"""
    
    def test_create_json_response_basic(self):
        """Test creating basic JSON response"""
        response_data = {"success": True, "message": "Success", "status_code": 200}
        response = create_json_response(response_data)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        assert response.body == b'{"success":true,"message":"Success","status_code":200}'
    
    def test_create_json_response_custom_status_code(self):
        """Test creating JSON response with custom status code"""
        response_data = {"success": True, "message": "Created", "status_code": 201}
        response = create_json_response(response_data, status_code=201)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 201
    
    def test_create_json_response_uses_data_status_code(self):
        """Test that JSON response uses status code from data when not provided"""
        response_data = {"success": True, "message": "Created", "status_code": 201}
        response = create_json_response(response_data)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 201


class TestHandleException:
    """Test handle_exception function"""
    
    def test_handle_http_exception(self):
        """Test handling HTTPException"""
        exc = HTTPException(status_code=404, detail="Not found")
        response = handle_exception(exc)
        
        assert response["success"] is False
        assert response["message"] == "Not found"
        assert response["status_code"] == 404
        assert response["error_code"] == "HTTP_404"
    
    def test_handle_generic_exception(self):
        """Test handling generic exception"""
        exc = ValueError("Invalid value")
        
        with patch('app.utils.response_standardizer.logger') as mock_logger:
            response = handle_exception(exc)
        
        assert response["success"] is False
        assert response["message"] == "An unexpected error occurred"
        assert response["status_code"] == 500
        assert response["error_code"] == "SERVER_ERROR"
        assert response["details"]["error_type"] == "ValueError"
        mock_logger.error.assert_called_once()


class TestStandardizePagination:
    """Test standardize_pagination function"""
    
    def test_standardize_pagination_basic(self):
        """Test basic pagination standardization"""
        data = [1, 2, 3, 4, 5]
        pagination = standardize_pagination(data, page=1, page_size=5)
        
        assert pagination["page"] == 1
        assert pagination["page_size"] == 5
        assert pagination["total_items"] == 5
        assert pagination["has_next"] is False
    
    def test_standardize_pagination_with_total_count(self):
        """Test pagination with total count"""
        data = [1, 2, 3, 4, 5]
        pagination = standardize_pagination(data, page=1, page_size=5, total_count=10)
        
        assert pagination["page"] == 1
        assert pagination["page_size"] == 5
        assert pagination["total_items"] == 5
        assert pagination["total_count"] == 10
        assert pagination["total_pages"] == 2
        assert pagination["has_next"] is True
    
    def test_standardize_pagination_has_next_page(self):
        """Test pagination with next page available"""
        data = [1, 2, 3, 4, 5]
        pagination = standardize_pagination(data, page=1, page_size=5, total_count=15)
        
        assert pagination["has_next"] is True
        assert pagination["total_pages"] == 3
    
    def test_standardize_pagination_no_next_page(self):
        """Test pagination without next page"""
        data = [1, 2, 3, 4, 5]
        pagination = standardize_pagination(data, page=2, page_size=5, total_count=10)
        
        assert pagination["has_next"] is False
        assert pagination["total_pages"] == 2


class TestStandardizeListResponse:
    """Test standardize_list_response function"""
    
    def test_standardize_list_response_basic(self):
        """Test basic list response standardization"""
        items = [{"id": 1}, {"id": 2}]
        response = standardize_list_response(items)
        
        assert response["success"] is True
        assert response["message"] == "Items retrieved successfully"
        assert response["data"]["items"] == items
        assert response["data"]["count"] == 2
        assert "pagination" not in response["data"]
    
    def test_standardize_list_response_with_pagination(self):
        """Test list response with pagination"""
        items = [{"id": 1}, {"id": 2}]
        response = standardize_list_response(items, page=1, page_size=2, total_count=5)
        
        assert response["success"] is True
        assert response["data"]["items"] == items
        assert response["data"]["count"] == 2
        assert "pagination" in response["data"]
        assert response["data"]["pagination"]["page"] == 1
        assert response["data"]["pagination"]["page_size"] == 2
        assert response["data"]["pagination"]["total_count"] == 5
    
    def test_standardize_list_response_custom_message(self):
        """Test list response with custom message"""
        items = [{"id": 1}]
        response = standardize_list_response(items, message="Custom message")
        
        assert response["success"] is True
        assert response["message"] == "Custom message"


class TestStandardizeSingleResponse:
    """Test standardize_single_response function"""
    
    def test_standardize_single_response_basic(self):
        """Test basic single response standardization"""
        item = {"id": 1, "name": "test"}
        response = standardize_single_response(item)
        
        assert response["success"] is True
        assert response["message"] == "Item retrieved successfully"
        assert response["data"] == item
    
    def test_standardize_single_response_custom_message(self):
        """Test single response with custom message"""
        item = {"id": 1}
        response = standardize_single_response(item, "Custom message")
        
        assert response["success"] is True
        assert response["message"] == "Custom message"
        assert response["data"] == item


class TestStandardizeCreatedResponse:
    """Test standardize_created_response function"""
    
    def test_standardize_created_response_basic(self):
        """Test basic created response standardization"""
        item = {"id": 1, "name": "test"}
        response = standardize_created_response(item)
        
        assert response["success"] is True
        assert response["message"] == "Item created successfully"
        assert response["status_code"] == 201
        assert response["data"] == item
    
    def test_standardize_created_response_custom_message(self):
        """Test created response with custom message"""
        item = {"id": 1}
        response = standardize_created_response(item, "User created")
        
        assert response["success"] is True
        assert response["message"] == "User created"
        assert response["status_code"] == 201
        assert response["data"] == item


class TestStandardizeUpdatedResponse:
    """Test standardize_updated_response function"""
    
    def test_standardize_updated_response_basic(self):
        """Test basic updated response standardization"""
        item = {"id": 1, "name": "updated"}
        response = standardize_updated_response(item)
        
        assert response["success"] is True
        assert response["message"] == "Item updated successfully"
        assert response["status_code"] == 200
        assert response["data"] == item
    
    def test_standardize_updated_response_custom_message(self):
        """Test updated response with custom message"""
        item = {"id": 1}
        response = standardize_updated_response(item, "User updated")
        
        assert response["success"] is True
        assert response["message"] == "User updated"
        assert response["status_code"] == 200
        assert response["data"] == item


class TestStandardizeDeletedResponse:
    """Test standardize_deleted_response function"""
    
    def test_standardize_deleted_response_basic(self):
        """Test basic deleted response standardization"""
        response = standardize_deleted_response()
        
        assert response["success"] is True
        assert response["message"] == "Item deleted successfully"
        assert response["status_code"] == 204
        assert response["data"] is None
    
    def test_standardize_deleted_response_custom_message(self):
        """Test deleted response with custom message"""
        response = standardize_deleted_response("User deleted")
        
        assert response["success"] is True
        assert response["message"] == "User deleted"
        assert response["status_code"] == 204
        assert response["data"] is None

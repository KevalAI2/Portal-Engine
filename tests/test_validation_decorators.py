"""
Comprehensive test suite for validation decorators
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from app.core.validation_decorators import (
    validate_request_body,
    validate_query_params,
    sanitize_input,
    validate_user_authentication,
    validate_rate_limit,
    validate_cors_origin,
    validate_content_type,
    validate_request_size
)
from app.core.exceptions import ValidationError as CustomValidationError
from app.models.responses import APIResponse


class TestValidationDecorators:
    """Test cases for validation decorators"""

    def test_validate_request_body_success(self):
        """Test successful request body validation"""
        class TestModel(BaseModel):
            name: str
            age: int

        @validate_request_body(TestModel)
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success", "data": validated_data}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"name": "John", "age": 30})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_request_body_validation_error(self):
        """Test request body validation error"""
        class TestModel(BaseModel):
            name: str
            age: int

        @validate_request_body(TestModel)
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"name": "John"})  # Missing age
            assert response.status_code == 400
            data = response.json()
            assert "validation_errors" in data["error"]

    def test_validate_request_body_with_required_fields(self):
        """Test request body validation with required fields"""
        @validate_request_body(None, required_fields=["name", "age"])
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success", "data": validated_data}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"name": "John", "age": 30})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_request_body_missing_required_field(self):
        """Test request body validation with missing required field"""
        @validate_request_body(None, required_fields=["name"])
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={})  # Missing name
            assert response.status_code == 400
            data = response.json()
            assert "Missing required fields" in data["message"]

    def test_validate_query_params_success(self):
        """Test successful query parameter validation"""
        @validate_query_params(required_params=["page", "limit"])
        async def test_endpoint(request: Request, validated_params=None):
            return {"status": "success", "params": validated_params}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test?page=1&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_query_params_missing_required(self):
        """Test query parameter validation with missing required param"""
        @validate_query_params(required_params=["page", "limit"])
        async def test_endpoint(request: Request, validated_params=None):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test?page=1")  # Missing limit
            assert response.status_code == 400
            data = response.json()
            assert "Missing required query parameters" in data["message"]

    def test_sanitize_input_success(self):
        """Test successful input sanitization"""
        @sanitize_input
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_user_authentication_success(self):
        """Test successful user authentication validation"""
        @validate_user_authentication
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_user_authentication_missing_header(self):
        """Test user authentication validation with missing header"""
        @validate_user_authentication
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test")  # No Authorization header
            assert response.status_code == 401
            data = response.json()
            assert "Authorization header required" in data["message"]

    def test_validate_rate_limit_success(self):
        """Test successful rate limiting"""
        @validate_rate_limit(requests_per_minute=60)
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_cors_origin_success(self):
        """Test successful CORS origin validation"""
        @validate_cors_origin
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["GET"])

        with TestClient(app) as client:
            response = client.get("/test", headers={"Origin": "https://example.com"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_content_type_success(self):
        """Test successful content type validation"""
        @validate_content_type(allowed_types=["application/json"])
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"data": "test"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_content_type_invalid(self):
        """Test content type validation with invalid type"""
        @validate_content_type(allowed_types=["application/json"])
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", data="test", headers={"content-type": "text/plain"})
            assert response.status_code == 415
            data = response.json()
            assert "Content type must be one of" in data["message"]

    def test_validate_request_size_success(self):
        """Test successful request size validation"""
        @validate_request_size(max_size=1024)
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"data": "small"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_request_size_too_large(self):
        """Test request size validation with oversized request"""
        @validate_request_size(max_size=10)
        async def test_endpoint(request: Request):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"data": "this is a very long string that exceeds the limit"})
            assert response.status_code == 413
            data = response.json()
            assert "Request size exceeds maximum allowed size" in data["message"]

    def test_validation_error_handling(self):
        """Test validation error handling"""
        @validate_request_body(None, required_fields=["name"])
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={})  # Missing name
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["error_code"] == "VALIDATION_ERROR"

    def test_validation_with_custom_error_handler(self):
        """Test validation with custom error handler"""
        @validate_request_body(None, required_fields=["name"])
        async def test_endpoint(request: Request, validated_data=None):
            return {"status": "success"}

        app = FastAPI()
        app.add_api_route("/test", test_endpoint, methods=["POST"])

        with TestClient(app) as client:
            response = client.post("/test", json={"name": "test"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
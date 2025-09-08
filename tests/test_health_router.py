"""
Simplified test suite for the health check API router
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime


@pytest.mark.unit
class TestHealthRouter:
    """Test the health check router functionality."""

    def test_health_check_success(self, client: TestClient, mock_user_profile_service, 
                                 mock_lie_service, mock_cis_service):
        """Test successful health check with all services healthy."""
        # Ensure mocks return healthy status
        mock_user_profile_service.health_check.return_value.__aenter__ = AsyncMock(return_value=True)
        mock_lie_service.health_check.return_value.__aenter__ = AsyncMock(return_value=True)
        mock_cis_service.health_check.return_value.__aenter__ = AsyncMock(return_value=True)
        
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["environment"] == "test"
        assert "services" in data
        
        services = data["services"]
        assert services["user_profile_service"] == "healthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    def test_health_check_degraded(self, client: TestClient, mock_user_profile_service,
                                  mock_lie_service, mock_cis_service):
        """Test health check with some services unhealthy."""
        mock_user_profile_service.health_check.return_value.__aenter__ = AsyncMock(return_value=False)
        mock_lie_service.health_check.return_value.__aenter__ = AsyncMock(return_value=True)
        mock_cis_service.health_check.return_value.__aenter__ = AsyncMock(return_value=True)
        
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "degraded"
        
        services = data["services"]
        assert services["user_profile_service"] == "unhealthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    def test_readiness_check_success(self, client: TestClient):
        """Test readiness check endpoint."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check_success(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "alive"

"""
Simplified test suite for the health check API router
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import status


@pytest.mark.unit
class TestHealthRouter:
    """Test the health check router functionality."""

    def test_health_check_success(self, client: TestClient, mock_user_profile_service,
                                 mock_lie_service, mock_cis_service):
        """Test successful health check with all services healthy."""
        mock_user_profile_service.health_check = AsyncMock(return_value=True)
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Check new APIResponse format
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]
        assert data["data"]["version"] == "1.0.0"
        assert data["data"]["environment"] == "test"
        assert "services" in data["data"]

        services = data["data"]["services"]
        assert services["user_profile_service"] == "healthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    def test_health_check_degraded(self, client: TestClient, mock_user_profile_service,
                                  mock_lie_service, mock_cis_service):
        """Test health check with some services unhealthy."""
        mock_user_profile_service.health_check = AsyncMock(return_value=False)
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Check new APIResponse format
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "degraded"

        services = data["data"]["services"]
        assert services["user_profile_service"] == "unhealthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    def test_readiness_check_success(self, client: TestClient):
        """Test readiness check endpoint."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Check new APIResponse format
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "ready"

    def test_liveness_check_success(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Check new APIResponse format
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "alive"

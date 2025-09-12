import pytest
import threading
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from app.api.routers.health import router
from app.core.config import settings
from app.models.responses import HealthCheckResponse, APIResponse

@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthRouter:
    """Test the health check router functionality."""

    async def test_health_check_success(self, client: TestClient, mock_user_profile_service,
                                       mock_lie_service, mock_cis_service):
        """Test successful health check with all services healthy."""
        mock_user_profile_service.health_check = AsyncMock(return_value=True)
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]
        assert data["data"]["version"] == settings.app_version
        assert data["data"]["environment"] == settings.environment
        assert "services" in data["data"]

        services = data["data"]["services"]
        assert services["user_profile_service"] == "healthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    async def test_health_check_degraded(self, client: TestClient, mock_user_profile_service,
                                        mock_lie_service, mock_cis_service):
        """Test health check with some services unhealthy (degraded state)."""
        mock_user_profile_service.health_check = AsyncMock(return_value=False)
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "degraded"
        assert "services" in data["data"]
        services = data["data"]["services"]
        assert services["user_profile_service"] == "unhealthy"
        assert services["lie_service"] == "healthy"
        assert services["cis_service"] == "healthy"

    async def test_health_check_all_unhealthy(self, client: TestClient, mock_user_profile_service,
                                             mock_lie_service, mock_cis_service):
        """Test health check when all services are unhealthy."""
        mock_user_profile_service.health_check = AsyncMock(return_value=False)
        mock_lie_service.health_check = AsyncMock(return_value=False)
        mock_cis_service.health_check = AsyncMock(return_value=False)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "unhealthy"
        assert "services" in data["data"]
        services = data["data"]["services"]
        assert services["user_profile_service"] == "unhealthy"
        assert services["lie_service"] == "unhealthy"
        assert services["cis_service"] == "unhealthy"

    async def test_health_check_dependency_error(self, client: TestClient, mock_user_profile_service,
                                                mock_lie_service, mock_cis_service):
        """Test health check when a dependency raises an exception."""
        mock_user_profile_service.health_check = AsyncMock(side_effect=Exception("User profile service down"))
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "degraded"
        assert data["data"]["services"]["user_profile_service"] == "unavailable"
        assert data["data"]["services"]["lie_service"] == "healthy"
        assert data["data"]["services"]["cis_service"] == "healthy"

    async def test_health_check_general_error(self, client: TestClient):
        """Test health check when the entire endpoint fails."""
        with patch("app.api.routers.health.APIResponse.success_response", side_effect=Exception("General failure")):
            response = client.get("/api/v1/health/")
            # The health router catches the exception and returns a proper error response with 200 status
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Health check failed"
            assert data["status_code"] == 503
            assert data["data"]["status"] == "unhealthy"
            assert "error" in data["data"]["services"]

    async def test_readiness_check_success(self, client: TestClient):
        """Test readiness check endpoint success."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "ready"
        assert "timestamp" in data["data"]
        assert data["data"]["message"] == "Service is ready to accept requests"

    async def test_readiness_check_failure(self, client: TestClient):
        """Test readiness check endpoint failure."""
        with patch("app.api.routers.health.APIResponse.success_response", side_effect=Exception("Readiness failure")):
            response = client.get("/api/v1/health/ready")
            # The readiness router catches the exception and returns a proper error response with 200 status
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Service not ready"
            assert data["status_code"] == 503
            assert data["data"]["status"] == "not_ready"
            assert "error" in data["data"]

    async def test_liveness_check_success(self, client: TestClient):
        """Test liveness check endpoint success."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "alive"
        assert "timestamp" in data["data"]
        assert data["data"]["message"] == "Service is alive"

    async def test_liveness_check_failure(self, client: TestClient):
        """Test liveness check endpoint failure."""
        with patch("app.api.routers.health.APIResponse.success_response", side_effect=Exception("Liveness failure")):
            response = client.get("/api/v1/health/live")
            # The liveness router catches the exception and returns a proper error response with 200 status
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Service is not alive"
            assert data["status_code"] == 503
            assert data["data"]["status"] == "dead"
            assert "error" in data["data"]

    async def test_health_check_concurrent_requests(self, client: TestClient, mock_user_profile_service,
                                                   mock_lie_service, mock_cis_service):
        """Test concurrent health check requests."""
        mock_user_profile_service.health_check = AsyncMock(return_value=True)
        mock_lie_service.health_check = AsyncMock(return_value=True)
        mock_cis_service.health_check = AsyncMock(return_value=True)

        results = []

        def make_health_request():
            response = client.get("/api/v1/health/")
            assert response.status_code == status.HTTP_200_OK
            results.append(response.json())

        threads = [threading.Thread(target=make_health_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r["success"] is True and r["data"]["status"] == "healthy" for r in results)
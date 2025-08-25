"""
Tests for recommendations API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


class TestRecommendationsAPI:
    """Test class for recommendations API endpoints"""
    
    def test_get_recommendation_types(self, client: TestClient):
        """Test getting supported recommendation types"""
        response = client.get("/api/v1/recommendations/types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "music" in data
        assert "movie" in data
        assert "place" in data
        assert "event" in data
    
    def test_get_recommendations_not_found(self, client: TestClient):
        """Test getting recommendations when none exist"""
        with patch('app.api.routers.recommendations.get_cache_service') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get_recommendations.return_value = None
            mock_get_cache.return_value = mock_cache
            
            response = client.get("/api/v1/recommendations/music?user_id=test_user")
            
            assert response.status_code == 404
            data = response.json()
            assert "No recommendations found" in data["detail"]
    
    def test_get_recommendations_success(self, client: TestClient, sample_recommendation_response):
        """Test getting recommendations successfully"""
        with patch('app.api.routers.recommendations.get_cache_service') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get_recommendations.return_value = sample_recommendation_response
            mock_get_cache.return_value = mock_cache
            
            response = client.get("/api/v1/recommendations/music?user_id=test_user_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "test_user_123"
            assert data["type"] == "music"
            assert len(data["recommendations"]) == 1
            assert data["recommendations"][0]["title"] == "Test Music"
    
    def test_get_recommendations_invalid_type(self, client: TestClient):
        """Test getting recommendations with invalid type"""
        response = client.get("/api/v1/recommendations/invalid_type?user_id=test_user")
        
        assert response.status_code == 422  # Validation error
    
    def test_refresh_recommendations_success(self, client: TestClient):
        """Test refreshing recommendations successfully"""
        with patch('app.api.routers.recommendations.generate_recommendations') as mock_task:
            mock_task.delay.return_value.id = "test_task_id"
            
            response = client.post(
                "/api/v1/recommendations/refresh/test_user_123",
                json={"user_id": "test_user_123", "force": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "task_triggered" in data["message"]
            assert data["data"]["user_id"] == "test_user_123"
            assert len(data["data"]["tasks"]) == 4  # 4 recommendation types
    
    def test_refresh_recommendations_force(self, client: TestClient):
        """Test refreshing recommendations with force flag"""
        with patch('app.api.routers.recommendations.generate_recommendations') as mock_task:
            mock_task.delay.return_value.id = "test_task_id"
            
            response = client.post(
                "/api/v1/recommendations/refresh/test_user_123",
                json={"user_id": "test_user_123", "force": True}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["force_refresh"] is True
    
    def test_delete_recommendations_success(self, client: TestClient):
        """Test deleting recommendations successfully"""
        with patch('app.api.routers.recommendations.get_cache_service') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.delete_recommendations.return_value = True
            mock_get_cache.return_value = mock_cache
            
            response = client.delete("/api/v1/recommendations/music?user_id=test_user_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "deleted successfully" in data["message"]
    
    def test_delete_recommendations_failure(self, client: TestClient):
        """Test deleting recommendations when it fails"""
        with patch('app.api.routers.recommendations.get_cache_service') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.delete_recommendations.return_value = False
            mock_get_cache.return_value = mock_cache
            
            response = client.delete("/api/v1/recommendations/music?user_id=test_user_123")
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to delete" in data["detail"]
    
    def test_get_task_status_pending(self, client: TestClient):
        """Test getting task status for pending task"""
        with patch('app.api.routers.recommendations.celery_app') as mock_celery:
            mock_result = AsyncMock()
            mock_result.status = "PENDING"
            mock_result.date_done = None
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/api/v1/recommendations/status/test_task_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test_task_id"
            assert data["status"] == "PENDING"
    
    def test_get_task_status_completed(self, client: TestClient):
        """Test getting task status for completed task"""
        from datetime import datetime
        
        with patch('app.api.routers.recommendations.celery_app') as mock_celery:
            mock_result = AsyncMock()
            mock_result.status = "SUCCESS"
            mock_result.date_done = datetime.utcnow()
            mock_result.successful.return_value = True
            mock_result.result = {"success": True, "message": "Task completed"}
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/api/v1/recommendations/status/test_task_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"
            assert data["result"]["success"] is True
    
    def test_get_task_status_failed(self, client: TestClient):
        """Test getting task status for failed task"""
        from datetime import datetime
        
        with patch('app.api.routers.recommendations.celery_app') as mock_celery:
            mock_result = AsyncMock()
            mock_result.status = "FAILURE"
            mock_result.date_done = datetime.utcnow()
            mock_result.successful.return_value = False
            mock_result.failed.return_value = True
            mock_result.info = "Task failed due to error"
            mock_celery.AsyncResult.return_value = mock_result
            
            response = client.get("/api/v1/recommendations/status/test_task_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "FAILURE"
            assert "Task failed due to error" in data["error"]


class TestRecommendationsIntegration:
    """Integration tests for recommendations workflow"""
    
    def test_full_recommendation_workflow(self, client: TestClient):
        """Test the complete recommendation workflow"""
        # Step 1: Refresh recommendations
        with patch('app.api.routers.recommendations.generate_recommendations') as mock_task:
            mock_task.delay.return_value.id = "workflow_task_id"
            
            refresh_response = client.post(
                "/api/v1/recommendations/refresh/test_user_123",
                json={"user_id": "test_user_123", "force": True}
            )
            
            assert refresh_response.status_code == 200
        
        # Step 2: Check task status
        with patch('app.api.routers.recommendations.celery_app') as mock_celery:
            mock_result = AsyncMock()
            mock_result.status = "SUCCESS"
            mock_result.date_done = "2024-01-01T12:00:00Z"
            mock_result.successful.return_value = True
            mock_result.result = {"success": True, "message": "Workflow completed"}
            mock_celery.AsyncResult.return_value = mock_result
            
            status_response = client.get("/api/v1/recommendations/status/workflow_task_id")
            
            assert status_response.status_code == 200
            data = status_response.json()
            assert data["status"] == "SUCCESS"
        
        # Step 3: Get recommendations (after they're generated)
        with patch('app.api.routers.recommendations.get_cache_service') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get_recommendations.return_value = sample_recommendation_response
            mock_get_cache.return_value = mock_cache
            
            get_response = client.get("/api/v1/recommendations/music?user_id=test_user_123")
            
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["user_id"] == "test_user_123"
            assert data["type"] == "music"
    
    def test_error_handling(self, client: TestClient):
        """Test error handling in recommendations API"""
        # Test with missing user_id parameter
        response = client.get("/api/v1/recommendations/music")
        
        assert response.status_code == 422  # Validation error
        
        # Test with invalid recommendation type
        response = client.get("/api/v1/recommendations/invalid?user_id=test_user")
        
        assert response.status_code == 422  # Validation error
        
        # Test with malformed refresh request
        response = client.post(
            "/api/v1/recommendations/refresh/test_user_123",
            json={"invalid_field": "value"}
        )
        
        assert response.status_code == 422  # Validation error

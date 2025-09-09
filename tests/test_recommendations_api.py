"""
Test suite for user recommendations API endpoints using existing user routes
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestUserRecommendationsAPI:
    """Test class for user recommendations API endpoints using existing user routes"""
    
    def test_get_user_recommendations_success(self, client: TestClient, sample_recommendation_response, mock_external_services):
        """Test getting user recommendations successfully"""
        # Configure the global mock to return our test data
        mock_external_services['llm_service'].return_value.get_recommendations_from_redis.return_value = sample_recommendation_response
        print(f"DEBUG: Mock configured with: {sample_recommendation_response}")

        response = client.get("/api/v1/users/test_user_123/recommendations")
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response data: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # The actual response structure has recommendations nested under data.data
        assert "data" in data
        assert "recommendations" in data["data"]
    
    def test_get_user_recommendations_not_found(self, client: TestClient, mock_external_services):
        """Test getting user recommendations when none exist"""
        # Configure the global mock to return None (no recommendations)
        mock_external_services['llm_service'].return_value.get_recommendations_from_redis.return_value = None
        
        response = client.get("/api/v1/users/test_user_123/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No recommendations found" in data["message"]
    
    def test_generate_recommendations_success(self, client: TestClient, mock_external_services):
        """Test generating recommendations successfully"""
        # Configure the global mock to return success
        mock_external_services['llm_service'].return_value.generate_recommendations.return_value = {"success": True, "recommendations": []}
        
        response = client.post(
            "/api/v1/users/test_user_123/generate-recommendations",
            json={"prompt": "I like jazz music"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Recommendations generated successfully" in data["message"]
    
    def test_generate_recommendations_direct_success(self, client: TestClient, mock_external_services):
        """Test generating recommendations directly (without storing)"""
        # Configure the global mock to return success
        mock_external_services['llm_service'].return_value.generate_recommendations.return_value = {"success": True, "recommendations": []}
        
        response = client.post(
            "/api/v1/users/generate-recommendations",
            json={"prompt": "I like jazz music"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Recommendations generated successfully" in data["message"]
    
    def test_clear_user_recommendations_success(self, client: TestClient, mock_external_services):
        """Test clearing user recommendations successfully"""
        # Configure the global mock to return None (successful clear)
        mock_external_services['llm_service'].return_value.clear_recommendations.return_value = None
        
        response = client.delete("/api/v1/users/test_user_123/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Recommendations cleared successfully" in data["message"]
    
    def test_get_ranked_results_success(self, client: TestClient, mock_external_services):
        """Test getting ranked results successfully"""
        # Configure the global mock to return success
        mock_external_services['results_service'].return_value.get_ranked_results.return_value = {"success": True, "results": []}
        
        response = client.get("/api/v1/users/test_user_123/results")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Ranked results retrieved successfully" in data["message"]
    
    def test_get_ranked_results_with_filters(self, client: TestClient, mock_external_services):
        """Test getting ranked results with filters"""
        # Configure the global mock to return success
        mock_external_services['results_service'].return_value.get_ranked_results.return_value = {"success": True, "results": []}
        
        response = client.get(
            "/api/v1/users/test_user_123/results?category=music&limit=10&min_score=0.5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Verify the service was called with correct filters
        mock_external_services['results_service'].return_value.get_ranked_results.assert_called_once()
        call_args = mock_external_services['results_service'].return_value.get_ranked_results.call_args
        assert call_args[0][0] == "test_user_123"  # user_id
        filters = call_args[0][1]  # filters dict
        assert filters["category"] == "music"
        assert filters["limit"] == 10
        assert filters["min_score"] == 0.5


class TestUserRecommendationsIntegration:
    """Integration tests for user recommendations workflow"""
    
    def test_full_recommendation_workflow(self, client: TestClient, sample_recommendation_response, mock_external_services):
        """Test the complete user recommendation workflow"""
        # Configure all the global mocks
        mock_external_services['llm_service'].return_value.generate_recommendations.return_value = {"success": True, "recommendations": []}
        mock_external_services['llm_service'].return_value.get_recommendations_from_redis.return_value = sample_recommendation_response
        mock_external_services['results_service'].return_value.get_ranked_results.return_value = {"success": True, "results": []}
        
        # Step 1: Generate recommendations
        generate_response = client.post(
            "/api/v1/users/test_user_123/generate-recommendations",
            json={"prompt": "I like jazz music"}
        )
        
        assert generate_response.status_code == 200
        data = generate_response.json()
        assert data["success"] is True
        
        # Step 2: Get recommendations
        get_response = client.get("/api/v1/users/test_user_123/recommendations")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Step 3: Get ranked results
        ranked_response = client.get("/api/v1/users/test_user_123/results")
        
        assert ranked_response.status_code == 200
        data = ranked_response.json()
        assert data["success"] is True
    
    def test_error_handling(self, client: TestClient):
        """Test error handling in user recommendations API"""
        # Test with missing prompt in generate recommendations
        response = client.post(
            "/api/v1/users/test_user_123/generate-recommendations",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test with invalid user ID format
        response = client.get("/api/v1/users/invalid_user_id/recommendations")
        assert response.status_code == 200  # Should still return 200 with error message
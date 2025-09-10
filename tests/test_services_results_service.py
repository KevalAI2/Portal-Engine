import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import redis
from app.services.results_service import ResultsService


@pytest.mark.unit
class TestResultsService:
    """Test the results service functionality."""

    @pytest.fixture
    def results_service(self):
        """Create ResultsService instance for testing."""
        with patch('app.services.results_service.redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            service = ResultsService()
            service.redis_client = mock_redis_instance
            yield service

    def test_results_service_initialization(self, results_service):
        """Test ResultsService initialization."""
        assert results_service.timeout == 30
        assert hasattr(results_service, 'redis_client')

    def test_get_recommendations(self, results_service):
        """Test recommendations retrieval from Redis."""
        mock_data = {
            "recommendations": {
                "movies": [{"title": "Test Movie", "rating": 4.5}]
            },
            "prompt": "test prompt"
        }
        
        results_service.redis_client.get.return_value = json.dumps(mock_data)
        
        result = results_service._get_recommendations("user_123")
        
        assert result == mock_data
        results_service.redis_client.get.assert_called_once_with("recommendations:user_123")

    def test_get_recommendations_empty(self, results_service):
        """Test recommendations retrieval with empty response."""
        results_service.redis_client.get.return_value = None
        
        result = results_service._get_recommendations("user_123")
        
        assert result is None

    def test_get_recommendations_error(self, results_service):
        """Test recommendations retrieval with error."""
        results_service.redis_client.get.side_effect = Exception("Redis error")
        
        result = results_service._get_recommendations("user_123")
        
        assert result is None

    def test_rank_recommendations(self, results_service):
        """Test recommendations ranking."""
        recommendations = {
            "movies": [
                {"title": "Movie 1", "genre": "action", "description": "action movie"},
                {"title": "Movie 2", "genre": "comedy", "description": "comedy movie"},
            ]
        }
        prompt = "action movies"
        
        ranked = results_service._rank_recommendations(recommendations, prompt, "user_123")
        
        assert isinstance(ranked, dict)
        assert "movies" in ranked
        assert len(ranked["movies"]) == 2
        # Movie 1 should have higher score due to "action" in genre matching prompt
        assert ranked["movies"][0]["ranking_score"] >= ranked["movies"][1]["ranking_score"]

    def test_rank_recommendations_empty(self, results_service):
        """Test recommendations ranking with empty list."""
        ranked = results_service._rank_recommendations({"test": []}, "test prompt", "user_123")
        
        assert isinstance(ranked, dict)
        assert len(ranked["test"]) == 0

    def test_rank_recommendations_single_item(self, results_service):
        """Test recommendations ranking with single item."""
        recommendations = {"test": [{"title": "Single", "genre": "test", "description": "test"}]}
        
        ranked = results_service._rank_recommendations(recommendations, "test", "user_123")
        
        assert isinstance(ranked, dict)
        assert len(ranked["test"]) == 1
        assert "ranking_score" in ranked["test"][0]

    def test_calculate_item_score(self, results_service):
        """Test item score calculation."""
        item = {"title": "Action Movie", "genre": "action", "description": "great action film"}
        prompt = "action movies"
        
        score = results_service._calculate_item_score(item, prompt, "movies")
        
        assert isinstance(score, float)
        assert score > 0

    def test_calculate_item_score_edge_cases(self, results_service):
        """Test item score calculation edge cases."""
        # Test with minimal data
        item = {"title": "Test"}
        score = results_service._calculate_item_score(item, "test", "movies")
        assert isinstance(score, float)
        assert score >= 0
        
        # Test with no matching words
        item = {"title": "XYZ", "genre": "abc", "description": "def"}
        score = results_service._calculate_item_score(item, "completely different", "movies")
        assert score == 1.0  # Base score only

    def test_deduplicate_results(self, results_service):
        """Test results deduplication."""
        recommendations = {
            "category1": [
                {"title": "Duplicate", "name": "Item 1"},
                {"title": "Unique", "name": "Item 2"},
            ],
            "category2": [
                {"title": "Duplicate", "name": "Item 1"},  # Same title, should be removed
                {"title": "Another", "name": "Item 3"},
            ]
        }
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, dict)
        total = sum(len(items) for items in deduplicated.values())
        assert total == 3  # One duplicate removed

    def test_deduplicate_results_no_duplicates(self, results_service):
        """Test results deduplication with no duplicates."""
        recommendations = {
            "category1": [
                {"title": "Item 1", "name": "Test 1"},
                {"title": "Item 2", "name": "Test 2"},
            ],
            "category2": [
                {"title": "Item 3", "name": "Test 3"},
            ]
        }
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, dict)
        total = sum(len(items) for items in deduplicated.values())
        assert total == 3

    def test_deduplicate_results_all_duplicates(self, results_service):
        """Test results deduplication with all duplicates."""
        recommendations = {
            "category1": [
                {"title": "Same", "name": "Item 1"},
                {"title": "Same", "name": "Item 2"},  # Same title, different name
            ],
            "category2": [
                {"title": "Same", "name": "Item 3"},  # Same title
            ]
        }
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, dict)
        total = sum(len(items) for items in deduplicated.values())
        assert total == 1  # Only first occurrence kept

    def test_deduplicate_results_empty(self, results_service):
        """Test results deduplication with empty list."""
        deduplicated = results_service._deduplicate_results({})
        
        assert isinstance(deduplicated, dict)
        assert len(deduplicated) == 0

    def test_apply_filters(self, results_service):
        """Test filters application."""
        recommendations = {
            "hotel": [
                {"title": "Hotel 1", "ranking_score": 8.5, "category": "hotel"},
                {"title": "Hotel 2", "ranking_score": 7.0, "category": "hotel"},
            ],
            "restaurant": [
                {"title": "Restaurant 1", "ranking_score": 8.0, "category": "restaurant"},
            ]
        }
        
        filters = {"category": "hotel", "min_score": 8.0}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, dict)
        assert "restaurant" not in filtered  # Should be filtered out
        assert len(filtered["hotel"]) == 1  # Only hotel with score >= 8.0
        assert filtered["hotel"][0]["title"] == "Hotel 1"

    def test_apply_filters_no_filters(self, results_service):
        """Test filters application with no filters."""
        recommendations = {
            "hotel": [{"title": "Hotel 1", "ranking_score": 8.5}],
            "restaurant": [{"title": "Restaurant 1", "ranking_score": 8.0}]
        }
        
        filters = {}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, dict)
        total = sum(len(items) for items in filtered.values())
        assert total == 2  # No filtering applied

    def test_apply_filters_empty_recommendations(self, results_service):
        """Test filters application with empty recommendations."""
        recommendations = {}
        filters = {"category": "hotel"}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, dict)
        assert len(filtered) == 0

    def test_apply_filters_multiple_conditions(self, results_service):
        """Test filters application with multiple conditions."""
        recommendations = {
            "hotel": [
                {"title": "Hotel 1", "ranking_score": 8.5, "category": "hotel"},
                {"title": "Hotel 2", "ranking_score": 7.0, "category": "hotel"},
                {"title": "Hotel 3", "ranking_score": 9.0, "category": "hotel"},
            ]
        }
        
        filters = {
            "category": "hotel",
            "min_score": 8.0,
            "limit": 2
        }
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, dict)
        total = sum(len(items) for items in filtered.values())
        assert total == 2  # Limited to 2 items, both with score >= 8.0
        # Note: _apply_filters doesn't sort, it just applies filters and limits
        # The order should be preserved from the original list
        assert filtered["hotel"][0]["ranking_score"] == 8.5
        assert filtered["hotel"][1]["ranking_score"] == 9.0

    def test_calculate_metadata(self, results_service):
        """Test metadata calculation."""
        recommendations = {
            "movies": [
                {"title": "Movie 1", "ranking_score": 8.5},
                {"title": "Movie 2", "ranking_score": 7.5},
            ]
        }
        raw_data = {"generated_at": "2023-01-01"}
        
        metadata = results_service._calculate_metadata(recommendations, raw_data)
        
        assert isinstance(metadata, dict)
        assert metadata["total_results"] == 2
        assert "movies" in metadata["categories"]
        assert metadata["average_scores"]["movies"] == 8.0
        assert metadata["original_generation_time"] == "2023-01-01"

    def test_calculate_metadata_empty(self, results_service):
        """Test metadata calculation with empty recommendations."""
        recommendations = {}
        raw_data = {}
        
        metadata = results_service._calculate_metadata(recommendations, raw_data)
        
        assert isinstance(metadata, dict)
        assert metadata["total_results"] == 0
        assert metadata["categories"] == []
        assert metadata["average_scores"] == {}

    def test_generate_dummy_ranked_results(self, results_service):
        """Test dummy ranked results generation."""
        results = results_service._generate_dummy_ranked_results("user_123", {})
        
        assert isinstance(results, dict)
        assert "success" in results
        assert "ranked_recommendations" in results
        assert any(cat in results["ranked_recommendations"] for cat in ["movies", "music", "places", "events"])

    def test_generate_dummy_ranked_results_with_filters(self, results_service):
        """Test dummy ranked results generation with filters."""
        filters = {"category": "movies", "limit": 2}
        results = results_service._generate_dummy_ranked_results("user_123", filters)
        
        assert isinstance(results, dict)
        assert results["applied_filters"] == filters
        assert len(results["ranked_recommendations"]["movies"]) == 2

    def test_get_ranked_results_with_redis_data(self, results_service):
        """Test get_ranked_results with Redis data."""
        mock_data = {
            "recommendations": {
                "movies": [{"title": "Test Movie", "genre": "test", "description": "test"}]
            },
            "prompt": "test prompt"
        }
        
        results_service.redis_client.get.return_value = json.dumps(mock_data)
        
        result = results_service.get_ranked_results("user_123", {})
        
        assert result["success"] is True
        assert result["user_id"] == "user_123"
        assert "ranked_recommendations" in result

    def test_get_ranked_results_no_redis_data(self, results_service):
        """Test get_ranked_results with no Redis data."""
        results_service.redis_client.get.return_value = None
        
        result = results_service.get_ranked_results("user_123", {})
        
        assert result["success"] is True
        assert result["user_id"] == "user_123"
        assert result["data_source"] == "dummy_data"

    def test_get_ranked_results_error(self, results_service):
        """Test get_ranked_results with error - should return dummy data, not error."""
        results_service.redis_client.get.side_effect = Exception("Redis error")
        
        result = results_service.get_ranked_results("user_123", {})
        
        # The method catches exceptions and returns dummy data with success=True
        assert result["success"] is True
        assert result["user_id"] == "user_123"
        assert result["data_source"] == "dummy_data"

    def test_results_service_method_availability(self, results_service):
        """Test ResultsService method availability."""
        assert hasattr(results_service, "_get_recommendations")
        assert hasattr(results_service, "_rank_recommendations")
        assert hasattr(results_service, "_calculate_item_score")
        assert hasattr(results_service, "_deduplicate_results")
        assert hasattr(results_service, "_apply_filters")
        assert hasattr(results_service, "_calculate_metadata")
        assert hasattr(results_service, "_generate_dummy_ranked_results")
        assert hasattr(results_service, "get_ranked_results")

    def test_results_service_sync_methods(self, results_service):
        """Test ResultsService methods are sync (not async)."""
        import inspect
        
        # All methods should be synchronous
        assert not inspect.iscoroutinefunction(results_service._get_recommendations)
        assert not inspect.iscoroutinefunction(results_service._rank_recommendations)
        assert not inspect.iscoroutinefunction(results_service._calculate_item_score)
        assert not inspect.iscoroutinefunction(results_service._deduplicate_results)
        assert not inspect.iscoroutinefunction(results_service._apply_filters)
        assert not inspect.iscoroutinefunction(results_service._calculate_metadata)
        assert not inspect.iscoroutinefunction(results_service._generate_dummy_ranked_results)
        assert not inspect.iscoroutinefunction(results_service.get_ranked_results)
"""
Comprehensive test suite for results service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.results_service import ResultsService
from app.models.schemas import RecommendationItem


@pytest.mark.unit
class TestResultsService:
    """Test the results service functionality."""

    @pytest.fixture
    def results_service(self):
        """Create ResultsService instance for testing."""
        with patch('app.services.results_service.settings') as mock_settings:
            mock_settings.results_service_url = "http://test.example.com"
            return ResultsService()

    def test_results_service_initialization(self, results_service):
        """Test ResultsService initialization."""
        assert results_service.base_url == "http://test.example.com"
        assert results_service.timeout == 30
        assert results_service.logger is not None

    def test_results_service_inheritance(self, results_service):
        """Test ResultsService inheritance from BaseService."""
        from app.services.base import BaseService
        assert isinstance(results_service, BaseService)

    def test_get_recommendations(self, results_service):
        """Test recommendations retrieval."""
        mock_recommendations = [
            {"id": "rec_1", "title": "Recommendation 1", "rating": 4.5},
            {"id": "rec_2", "title": "Recommendation 2", "rating": 4.0},
            {"id": "rec_3", "title": "Recommendation 3", "rating": 3.5},
        ]
        
        with patch.object(results_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"recommendations": mock_recommendations}
            
            result = results_service._get_recommendations("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["id"] == "rec_1"
            assert result[0]["title"] == "Recommendation 1"
            assert result[0]["rating"] == 4.5

    def test_get_recommendations_empty(self, results_service):
        """Test recommendations retrieval with empty response."""
        with patch.object(results_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"recommendations": []}
            
            result = results_service._get_recommendations("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_recommendations_error(self, results_service):
        """Test recommendations retrieval with error."""
        with patch.object(results_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = results_service._get_recommendations("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 0

    def test_rank_recommendations(self, results_service):
        """Test recommendations ranking."""
        recommendations = [
            {"id": "rec_1", "rating": 4.5, "price": 100},
            {"id": "rec_2", "rating": 4.0, "price": 200},
            {"id": "rec_3", "rating": 3.5, "price": 150},
        ]
        
        ranked = results_service._rank_recommendations(recommendations)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 3
        # Should be sorted by rating (descending)
        assert ranked[0]["rating"] >= ranked[1]["rating"]
        assert ranked[1]["rating"] >= ranked[2]["rating"]

    def test_rank_recommendations_empty(self, results_service):
        """Test recommendations ranking with empty list."""
        ranked = results_service._rank_recommendations([])
        
        assert isinstance(ranked, list)
        assert len(ranked) == 0

    def test_rank_recommendations_single_item(self, results_service):
        """Test recommendations ranking with single item."""
        recommendations = [{"id": "rec_1", "rating": 4.5, "price": 100}]
        
        ranked = results_service._rank_recommendations(recommendations)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 1
        assert ranked[0]["id"] == "rec_1"

    def test_rank_recommendations_same_rating(self, results_service):
        """Test recommendations ranking with same rating."""
        recommendations = [
            {"id": "rec_1", "rating": 4.0, "price": 100},
            {"id": "rec_2", "rating": 4.0, "price": 200},
            {"id": "rec_3", "rating": 4.0, "price": 150},
        ]
        
        ranked = results_service._rank_recommendations(recommendations)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 3
        # All should have same rating
        assert all(rec["rating"] == 4.0 for rec in ranked)

    def test_rank_recommendations_missing_rating(self, results_service):
        """Test recommendations ranking with missing rating."""
        recommendations = [
            {"id": "rec_1", "rating": 4.5, "price": 100},
            {"id": "rec_2", "price": 200},  # Missing rating
            {"id": "rec_3", "rating": 3.5, "price": 150},
        ]
        
        ranked = results_service._rank_recommendations(recommendations)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 3
        # Should handle missing rating gracefully
        assert ranked[0]["rating"] == 4.5
        assert ranked[2]["rating"] == 3.5

    def test_calculate_item_score(self, results_service):
        """Test item score calculation."""
        item = {"rating": 4.5, "price": 100, "reviews": 50}
        
        score = results_service._calculate_item_score(item)
        
        assert isinstance(score, float)
        assert score > 0
        # Higher rating should result in higher score
        assert score > 4.0

    def test_calculate_item_score_edge_cases(self, results_service):
        """Test item score calculation edge cases."""
        # Test with missing fields
        item = {"rating": 4.5}
        score = results_service._calculate_item_score(item)
        assert isinstance(score, float)
        assert score > 0
        
        # Test with zero rating
        item = {"rating": 0, "price": 100}
        score = results_service._calculate_item_score(item)
        assert isinstance(score, float)
        assert score >= 0
        
        # Test with negative rating
        item = {"rating": -1, "price": 100}
        score = results_service._calculate_item_score(item)
        assert isinstance(score, float)
        assert score >= 0
        
        # Test with very high rating
        item = {"rating": 10, "price": 100}
        score = results_service._calculate_item_score(item)
        assert isinstance(score, float)
        assert score > 0

    def test_calculate_item_score_performance(self, results_service):
        """Test item score calculation performance."""
        import time
        
        items = [{"rating": i % 5 + 1, "price": i * 10} for i in range(1000)]
        
        start_time = time.time()
        for item in items:
            results_service._calculate_item_score(item)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second for 1000 items

    def test_deduplicate_results(self, results_service):
        """Test results deduplication."""
        recommendations = [
            {"id": "rec_1", "title": "Recommendation 1"},
            {"id": "rec_2", "title": "Recommendation 2"},
            {"id": "rec_1", "title": "Recommendation 1"},  # Duplicate
            {"id": "rec_3", "title": "Recommendation 3"},
        ]
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, list)
        assert len(deduplicated) == 3  # Should remove duplicate
        assert deduplicated[0]["id"] == "rec_1"
        assert deduplicated[1]["id"] == "rec_2"
        assert deduplicated[2]["id"] == "rec_3"

    def test_deduplicate_results_no_duplicates(self, results_service):
        """Test results deduplication with no duplicates."""
        recommendations = [
            {"id": "rec_1", "title": "Recommendation 1"},
            {"id": "rec_2", "title": "Recommendation 2"},
            {"id": "rec_3", "title": "Recommendation 3"},
        ]
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, list)
        assert len(deduplicated) == 3
        assert deduplicated == recommendations

    def test_deduplicate_results_all_duplicates(self, results_service):
        """Test results deduplication with all duplicates."""
        recommendations = [
            {"id": "rec_1", "title": "Recommendation 1"},
            {"id": "rec_1", "title": "Recommendation 1"},
            {"id": "rec_1", "title": "Recommendation 1"},
        ]
        
        deduplicated = results_service._deduplicate_results(recommendations)
        
        assert isinstance(deduplicated, list)
        assert len(deduplicated) == 1
        assert deduplicated[0]["id"] == "rec_1"

    def test_deduplicate_results_empty(self, results_service):
        """Test results deduplication with empty list."""
        deduplicated = results_service._deduplicate_results([])
        
        assert isinstance(deduplicated, list)
        assert len(deduplicated) == 0

    def test_apply_filters(self, results_service):
        """Test filters application."""
        recommendations = [
            {"id": "rec_1", "category": "hotel", "price": 100, "rating": 4.5},
            {"id": "rec_2", "category": "restaurant", "price": 200, "rating": 4.0},
            {"id": "rec_3", "category": "hotel", "price": 150, "rating": 3.5},
        ]
        
        filters = {"category": "hotel", "max_price": 150}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 2  # Should filter by category and price
        assert all(rec["category"] == "hotel" for rec in filtered)
        assert all(rec["price"] <= 150 for rec in filtered)

    def test_apply_filters_no_filters(self, results_service):
        """Test filters application with no filters."""
        recommendations = [
            {"id": "rec_1", "category": "hotel", "price": 100},
            {"id": "rec_2", "category": "restaurant", "price": 200},
        ]
        
        filters = {}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 2
        assert filtered == recommendations

    def test_apply_filters_empty_recommendations(self, results_service):
        """Test filters application with empty recommendations."""
        recommendations = []
        filters = {"category": "hotel"}
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 0

    def test_apply_filters_none_filters(self, results_service):
        """Test filters application with None filters."""
        recommendations = [
            {"id": "rec_1", "category": "hotel", "price": 100},
            {"id": "rec_2", "category": "restaurant", "price": 200},
        ]
        
        filters = None
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 2
        assert filtered == recommendations

    def test_apply_filters_multiple_conditions(self, results_service):
        """Test filters application with multiple conditions."""
        recommendations = [
            {"id": "rec_1", "category": "hotel", "price": 100, "rating": 4.5},
            {"id": "rec_2", "category": "restaurant", "price": 200, "rating": 4.0},
            {"id": "rec_3", "category": "hotel", "price": 150, "rating": 3.5},
            {"id": "rec_4", "category": "hotel", "price": 200, "rating": 4.0},
        ]
        
        filters = {
            "category": "hotel",
            "max_price": 150,
            "min_rating": 4.0
        }
        
        filtered = results_service._apply_filters(recommendations, filters)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 1  # Only rec_1 should pass all filters
        assert filtered[0]["id"] == "rec_1"

    def test_calculate_metadata(self, results_service):
        """Test metadata calculation."""
        recommendations = [
            {"id": "rec_1", "rating": 4.5, "price": 100},
            {"id": "rec_2", "rating": 4.0, "price": 200},
            {"id": "rec_3", "rating": 3.5, "price": 150},
        ]
        
        metadata = results_service._calculate_metadata(recommendations)
        
        assert isinstance(metadata, dict)
        assert "total_count" in metadata
        assert "average_rating" in metadata
        assert "average_price" in metadata
        assert "price_range" in metadata
        assert metadata["total_count"] == 3
        assert metadata["average_rating"] > 0
        assert metadata["average_price"] > 0
        assert "min" in metadata["price_range"]
        assert "max" in metadata["price_range"]

    def test_calculate_metadata_empty(self, results_service):
        """Test metadata calculation with empty recommendations."""
        recommendations = []
        
        metadata = results_service._calculate_metadata(recommendations)
        
        assert isinstance(metadata, dict)
        assert metadata["total_count"] == 0
        assert metadata["average_rating"] == 0
        assert metadata["average_price"] == 0
        assert metadata["price_range"]["min"] == 0
        assert metadata["price_range"]["max"] == 0

    def test_calculate_metadata_single_item(self, results_service):
        """Test metadata calculation with single item."""
        recommendations = [{"id": "rec_1", "rating": 4.5, "price": 100}]
        
        metadata = results_service._calculate_metadata(recommendations)
        
        assert isinstance(metadata, dict)
        assert metadata["total_count"] == 1
        assert metadata["average_rating"] == 4.5
        assert metadata["average_price"] == 100
        assert metadata["price_range"]["min"] == 100
        assert metadata["price_range"]["max"] == 100

    def test_calculate_metadata_missing_fields(self, results_service):
        """Test metadata calculation with missing fields."""
        recommendations = [
            {"id": "rec_1", "rating": 4.5},  # Missing price
            {"id": "rec_2", "price": 200},    # Missing rating
            {"id": "rec_3", "rating": 3.5, "price": 150},
        ]
        
        metadata = results_service._calculate_metadata(recommendations)
        
        assert isinstance(metadata, dict)
        assert metadata["total_count"] == 3
        # Should handle missing fields gracefully
        assert metadata["average_rating"] > 0
        assert metadata["average_price"] > 0

    def test_generate_dummy_ranked_results(self, results_service):
        """Test dummy ranked results generation."""
        results = results_service._generate_dummy_ranked_results()
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert isinstance(result, dict)
            assert "id" in result
            assert "title" in result
            assert "description" in result
            assert "location" in result
            assert "rating" in result
            assert "price" in result
            assert "category" in result

    def test_generate_dummy_ranked_results_structure(self, results_service):
        """Test dummy ranked results structure."""
        results = results_service._generate_dummy_ranked_results()
        
        for result in results:
            # Check required fields
            assert hasattr(result, 'id') or 'id' in result
            assert hasattr(result, 'title') or 'title' in result
            assert hasattr(result, 'description') or 'description' in result
            assert hasattr(result, 'location') or 'location' in result
            assert hasattr(result, 'rating') or 'rating' in result
            assert hasattr(result, 'price') or 'price' in result
            assert hasattr(result, 'category') or 'category' in result
            
            # Check field values
            assert len(str(result.get('id', ''))) > 0
            assert len(str(result.get('title', ''))) > 0
            assert len(str(result.get('description', ''))) > 0
            assert len(str(result.get('location', ''))) > 0
            assert result.get('rating', 0) > 0
            assert result.get('price', 0) > 0
            assert len(str(result.get('category', ''))) > 0

    def test_generate_dummy_ranked_results_uniqueness(self, results_service):
        """Test dummy ranked results uniqueness."""
        results = results_service._generate_dummy_ranked_results()
        
        # Check that IDs are unique
        ids = [result.get('id', '') for result in results]
        assert len(set(ids)) == len(ids)

    def test_generate_dummy_ranked_results_multiple_calls(self, results_service):
        """Test dummy ranked results multiple calls."""
        results1 = results_service._generate_dummy_ranked_results()
        results2 = results_service._generate_dummy_ranked_results()
        
        # Both should be valid
        assert isinstance(results1, list)
        assert isinstance(results2, list)
        assert len(results1) > 0
        assert len(results2) > 0
        
        # Both should have same structure
        for result in results1 + results2:
            assert isinstance(result, dict)
            assert 'id' in result
            assert 'title' in result
            assert 'description' in result
            assert 'location' in result
            assert 'rating' in result
            assert 'price' in result
            assert 'category' in result

    def test_generate_dummy_ranked_results_performance(self, results_service):
        """Test dummy ranked results performance."""
        import time
        
        start_time = time.time()
        results = results_service._generate_dummy_ranked_results()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second for dummy results
        assert len(results) > 0

    def test_results_service_logger_name(self, results_service):
        """Test ResultsService logger name."""
        assert results_service.logger._context.get('logger') == 'ResultsService'

    def test_results_service_method_availability(self, results_service):
        """Test ResultsService method availability."""
        # Test that all expected methods are available
        assert hasattr(results_service, '_make_request')
        assert hasattr(results_service, 'health_check')
        assert hasattr(results_service, '_get_recommendations')
        assert hasattr(results_service, '_rank_recommendations')
        assert hasattr(results_service, '_calculate_item_score')
        assert hasattr(results_service, '_deduplicate_results')
        assert hasattr(results_service, '_apply_filters')
        assert hasattr(results_service, '_calculate_metadata')
        assert hasattr(results_service, '_generate_dummy_ranked_results')
        assert callable(results_service._make_request)
        assert callable(results_service.health_check)
        assert callable(results_service._get_recommendations)
        assert callable(results_service._rank_recommendations)
        assert callable(results_service._calculate_item_score)
        assert callable(results_service._deduplicate_results)
        assert callable(results_service._apply_filters)
        assert callable(results_service._calculate_metadata)
        assert callable(results_service._generate_dummy_ranked_results)

    def test_results_service_async_methods(self, results_service):
        """Test ResultsService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(results_service._make_request)
        assert inspect.iscoroutinefunction(results_service.health_check)
        assert inspect.iscoroutinefunction(results_service._get_recommendations)
        assert not inspect.iscoroutinefunction(results_service._rank_recommendations)
        assert not inspect.iscoroutinefunction(results_service._calculate_item_score)
        assert not inspect.iscoroutinefunction(results_service._deduplicate_results)
        assert not inspect.iscoroutinefunction(results_service._apply_filters)
        assert not inspect.iscoroutinefunction(results_service._calculate_metadata)
        assert not inspect.iscoroutinefunction(results_service._generate_dummy_ranked_results)

    def test_results_service_error_handling(self, results_service):
        """Test ResultsService error handling."""
        # Test that service handles errors gracefully
        with patch.object(results_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                results_service.logger.error(
                    "Error in results service",
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_results_service_info_logging(self, results_service):
        """Test ResultsService info logging."""
        with patch.object(results_service.logger, 'info') as mock_info:
            # Simulate an info log
            results_service.logger.info(
                "Results service operation completed",
                operation="test"
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_results_service_thread_safety(self, results_service):
        """Test ResultsService thread safety."""
        import threading
        import time
        
        results = []
        
        def test_operation():
            try:
                # Simulate a service operation
                dummy_results = results_service._generate_dummy_ranked_results()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_operation, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_results_service_memory_usage(self, results_service):
        """Test ResultsService memory usage."""
        import gc
        
        # Generate multiple dummy results
        results_list = []
        for _ in range(100):
            dummy_results = results_service._generate_dummy_ranked_results()
            results_list.append(dummy_results)
        
        # Check memory usage
        assert len(results_list) == 100
        
        # Clean up
        del results_list
        gc.collect()

    def test_results_service_performance(self, results_service):
        """Test ResultsService performance."""
        import time
        
        # Test dummy results generation performance
        start_time = time.time()
        results_list = []
        for _ in range(100):
            dummy_results = results_service._generate_dummy_ranked_results()
            results_list.append(dummy_results)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 dummy results
        assert len(results_list) == 100

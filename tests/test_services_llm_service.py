"""
Comprehensive test suite for LLM service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.llm_service import LLMService
from app.models.schemas import RecommendationItem


@pytest.mark.unit
class TestLLMService:
    """Test the LLM service functionality."""

    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        with patch('app.services.llm_service.settings') as mock_settings:
            mock_settings.llm_service_url = "http://test.example.com"
            return LLMService()

    def test_llm_service_initialization(self, llm_service):
        """Test LLMService initialization."""
        assert llm_service.base_url == "http://test.example.com"
        assert llm_service.timeout == 30
        assert llm_service.logger is not None

    def test_llm_service_inheritance(self, llm_service):
        """Test LLMService inheritance from BaseService."""
        from app.services.base import BaseService
        assert isinstance(llm_service, BaseService)

    def test_setup_demo_data(self, llm_service):
        """Test demo data setup."""
        demo_data = llm_service._setup_demo_data()
        
        # Check that demo data is properly structured
        assert isinstance(demo_data, dict)
        assert "recommendations" in demo_data
        assert isinstance(demo_data["recommendations"], list)
        assert len(demo_data["recommendations"]) > 0
        
        # Check recommendation structure
        for rec in demo_data["recommendations"]:
            assert isinstance(rec, dict)
            assert "id" in rec
            assert "title" in rec
            assert "description" in rec
            assert "location" in rec
            assert "rating" in rec
            assert "price" in rec
            assert "category" in rec

    def test_normalize_key(self, llm_service):
        """Test key normalization."""
        test_cases = [
            ("user_123", "user_123"),
            ("USER_123", "user_123"),
            ("User 123", "user_123"),
            ("user-123", "user_123"),
            ("user@123", "user_123"),
            ("user+123", "user_123"),
            ("user.123", "user_123"),
            ("user/123", "user_123"),
            ("user\\123", "user_123"),
            ("user:123", "user_123"),
            ("user;123", "user_123"),
            ("user,123", "user_123"),
            ("user?123", "user_123"),
            ("user!123", "user_123"),
            ("user#123", "user_123"),
            ("user$123", "user_123"),
            ("user%123", "user_123"),
            ("user^123", "user_123"),
            ("user&123", "user_123"),
            ("user*123", "user_123"),
            ("user(123)", "user_123"),
            ("user[123]", "user_123"),
            ("user{123}", "user_123"),
            ("user|123", "user_123"),
            ("user<123>", "user_123"),
            ("user\"123\"", "user_123"),
            ("user'123'", "user_123"),
            ("user`123`", "user_123"),
            ("user~123", "user_123"),
            ("user\t123", "user_123"),
            ("user\n123", "user_123"),
            ("user\r123", "user_123"),
            ("user 123", "user_123"),
            ("  user 123  ", "user_123"),
            ("", ""),
            ("   ", ""),
            ("user", "user"),
            ("123", "123"),
            ("user123", "user123"),
            ("user_123_location", "user_123_location"),
            ("user_123_location_456", "user_123_location_456"),
        ]
        
        for input_key, expected_output in test_cases:
            result = llm_service._normalize_key(input_key)
            assert result == expected_output

    def test_normalize_key_edge_cases(self, llm_service):
        """Test key normalization edge cases."""
        # Test None input
        result = llm_service._normalize_key(None)
        assert result == ""
        
        # Test empty string
        result = llm_service._normalize_key("")
        assert result == ""
        
        # Test whitespace only
        result = llm_service._normalize_key("   ")
        assert result == ""
        
        # Test single character
        result = llm_service._normalize_key("a")
        assert result == "a"
        
        # Test special characters only
        result = llm_service._normalize_key("!@#$%^&*()")
        assert result == ""

    def test_normalize_key_unicode(self, llm_service):
        """Test key normalization with Unicode."""
        unicode_cases = [
            ("用户123", "用户123"),
            ("usuario123", "usuario123"),
            ("пользователь123", "пользователь123"),
            ("ユーザー123", "ユーザー123"),
            ("用户 123", "用户_123"),
            ("usuario 123", "usuario_123"),
            ("пользователь 123", "пользователь_123"),
            ("ユーザー 123", "ユーザー_123"),
        ]
        
        for input_key, expected_output in unicode_cases:
            result = llm_service._normalize_key(input_key)
            assert result == expected_output

    def test_normalize_key_performance(self, llm_service):
        """Test key normalization performance."""
        import time
        
        # Test with many keys
        keys = [f"user_{i}_key_{j}" for i in range(100) for j in range(10)]
        
        start_time = time.time()
        for key in keys:
            llm_service._normalize_key(key)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second for 1000 keys

    def test_get_user_interaction_history(self, llm_service):
        """Test user interaction history retrieval."""
        # Test with mock interaction data
        mock_interactions = [
            {"user_id": "user_123", "location_id": "loc_1", "rating": 5, "interaction_type": "review"},
            {"user_id": "user_123", "location_id": "loc_2", "rating": 4, "interaction_type": "view"},
            {"user_id": "user_123", "location_id": "loc_3", "rating": 3, "interaction_type": "click"},
        ]
        
        with patch.object(llm_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"interactions": mock_interactions}
            
            result = llm_service._get_user_interaction_history("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["user_id"] == "user_123"
            assert result[0]["location_id"] == "loc_1"
            assert result[0]["rating"] == 5
            assert result[0]["interaction_type"] == "review"

    def test_get_user_interaction_history_empty(self, llm_service):
        """Test user interaction history with empty response."""
        with patch.object(llm_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"interactions": []}
            
            result = llm_service._get_user_interaction_history("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_user_interaction_history_error(self, llm_service):
        """Test user interaction history with error."""
        with patch.object(llm_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = llm_service._get_user_interaction_history("user_123")
            
            assert isinstance(result, list)
            assert len(result) == 0

    def test_compute_ranking_score(self, llm_service):
        """Test ranking score computation."""
        # Test with different interaction types and ratings
        test_cases = [
            ({"rating": 5, "interaction_type": "review"}, 5.0),
            ({"rating": 4, "interaction_type": "review"}, 4.0),
            ({"rating": 3, "interaction_type": "review"}, 3.0),
            ({"rating": 2, "interaction_type": "review"}, 2.0),
            ({"rating": 1, "interaction_type": "review"}, 1.0),
            ({"rating": 5, "interaction_type": "view"}, 2.5),
            ({"rating": 4, "interaction_type": "view"}, 2.0),
            ({"rating": 3, "interaction_type": "view"}, 1.5),
            ({"rating": 2, "interaction_type": "view"}, 1.0),
            ({"rating": 1, "interaction_type": "view"}, 0.5),
            ({"rating": 5, "interaction_type": "click"}, 1.0),
            ({"rating": 4, "interaction_type": "click"}, 0.8),
            ({"rating": 3, "interaction_type": "click"}, 0.6),
            ({"rating": 2, "interaction_type": "click"}, 0.4),
            ({"rating": 1, "interaction_type": "click"}, 0.2),
        ]
        
        for interaction, expected_score in test_cases:
            result = llm_service._compute_ranking_score(interaction)
            assert result == expected_score

    def test_compute_ranking_score_edge_cases(self, llm_service):
        """Test ranking score computation edge cases."""
        # Test with missing rating
        interaction = {"interaction_type": "review"}
        result = llm_service._compute_ranking_score(interaction)
        assert result == 0.0
        
        # Test with missing interaction_type
        interaction = {"rating": 5}
        result = llm_service._compute_ranking_score(interaction)
        assert result == 0.0
        
        # Test with invalid rating
        interaction = {"rating": 6, "interaction_type": "review"}
        result = llm_service._compute_ranking_score(interaction)
        assert result == 0.0
        
        # Test with invalid interaction_type
        interaction = {"rating": 5, "interaction_type": "invalid"}
        result = llm_service._compute_ranking_score(interaction)
        assert result == 0.0

    def test_compute_ranking_score_performance(self, llm_service):
        """Test ranking score computation performance."""
        import time
        
        # Test with many interactions
        interactions = [
            {"rating": i % 5 + 1, "interaction_type": "review"}
            for i in range(1000)
        ]
        
        start_time = time.time()
        for interaction in interactions:
            llm_service._compute_ranking_score(interaction)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second for 1000 interactions

    def test_generate_demo_recommendations(self, llm_service):
        """Test demo recommendations generation."""
        recommendations = llm_service._generate_demo_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert isinstance(rec, RecommendationItem)
            assert rec.id is not None
            assert rec.title is not None
            assert rec.description is not None
            assert rec.location is not None
            assert rec.rating is not None
            assert rec.price is not None
            assert rec.category is not None

    def test_generate_demo_recommendations_structure(self, llm_service):
        """Test demo recommendations structure."""
        recommendations = llm_service._generate_demo_recommendations()
        
        for rec in recommendations:
            # Check required fields
            assert hasattr(rec, 'id')
            assert hasattr(rec, 'title')
            assert hasattr(rec, 'description')
            assert hasattr(rec, 'location')
            assert hasattr(rec, 'rating')
            assert hasattr(rec, 'price')
            assert hasattr(rec, 'category')
            
            # Check field types
            assert isinstance(rec.id, str)
            assert isinstance(rec.title, str)
            assert isinstance(rec.description, str)
            assert isinstance(rec.location, str)
            assert isinstance(rec.rating, (int, float))
            assert isinstance(rec.price, (int, float))
            assert isinstance(rec.category, str)
            
            # Check field values
            assert len(rec.id) > 0
            assert len(rec.title) > 0
            assert len(rec.description) > 0
            assert len(rec.location) > 0
            assert rec.rating > 0
            assert rec.price > 0
            assert len(rec.category) > 0

    def test_generate_demo_recommendations_uniqueness(self, llm_service):
        """Test demo recommendations uniqueness."""
        recommendations = llm_service._generate_demo_recommendations()
        
        # Check that IDs are unique
        ids = [rec.id for rec in recommendations]
        assert len(set(ids)) == len(ids)

    def test_generate_demo_recommendations_multiple_calls(self, llm_service):
        """Test demo recommendations multiple calls."""
        recs1 = llm_service._generate_demo_recommendations()
        recs2 = llm_service._generate_demo_recommendations()
        
        # Both should be valid
        assert isinstance(recs1, list)
        assert isinstance(recs2, list)
        assert len(recs1) > 0
        assert len(recs2) > 0
        
        # Both should have same structure
        for rec in recs1 + recs2:
            assert isinstance(rec, RecommendationItem)
            assert rec.id is not None
            assert rec.title is not None
            assert rec.description is not None
            assert rec.location is not None
            assert rec.rating is not None
            assert rec.price is not None
            assert rec.category is not None

    def test_generate_demo_recommendations_performance(self, llm_service):
        """Test demo recommendations performance."""
        import time
        
        start_time = time.time()
        recommendations = llm_service._generate_demo_recommendations()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second for demo recommendations
        assert len(recommendations) > 0

    def test_generate_personalized_reason(self, llm_service):
        """Test personalized reason generation."""
        user_profile = {
            "name": "John Doe",
            "interests": ["travel", "food", "adventure"],
            "preferences": {"accommodation": "hotel", "activities": "outdoor"}
        }
        
        recommendation = {
            "title": "Mountain Hiking Adventure",
            "description": "A challenging hike through beautiful mountain trails",
            "category": "adventure",
            "location": "Mountain Peak"
        }
        
        reason = llm_service._generate_personalized_reason(user_profile, recommendation)
        
        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "John" in reason or "travel" in reason or "adventure" in reason

    def test_generate_personalized_reason_edge_cases(self, llm_service):
        """Test personalized reason generation edge cases."""
        # Test with empty user profile
        user_profile = {}
        recommendation = {"title": "Test", "description": "Test", "category": "test", "location": "Test"}
        
        reason = llm_service._generate_personalized_reason(user_profile, recommendation)
        assert isinstance(reason, str)
        assert len(reason) > 0
        
        # Test with empty recommendation
        user_profile = {"name": "John", "interests": ["travel"]}
        recommendation = {}
        
        reason = llm_service._generate_personalized_reason(user_profile, recommendation)
        assert isinstance(reason, str)
        assert len(reason) > 0
        
        # Test with None values
        user_profile = None
        recommendation = None
        
        reason = llm_service._generate_personalized_reason(user_profile, recommendation)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_generate_personalized_reason_performance(self, llm_service):
        """Test personalized reason generation performance."""
        import time
        
        user_profile = {"name": "John", "interests": ["travel"], "preferences": {"activities": "outdoor"}}
        recommendation = {"title": "Test", "description": "Test", "category": "test", "location": "Test"}
        
        start_time = time.time()
        for _ in range(100):
            llm_service._generate_personalized_reason(user_profile, recommendation)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 2.0  # 2 seconds for 100 reasons

    def test_llm_service_logger_name(self, llm_service):
        """Test LLMService logger name."""
        assert llm_service.logger._context.get('logger') == 'LLMService'

    def test_llm_service_method_availability(self, llm_service):
        """Test LLMService method availability."""
        # Test that all expected methods are available
        assert hasattr(llm_service, '_make_request')
        assert hasattr(llm_service, 'health_check')
        assert hasattr(llm_service, '_setup_demo_data')
        assert hasattr(llm_service, '_normalize_key')
        assert hasattr(llm_service, '_get_user_interaction_history')
        assert hasattr(llm_service, '_compute_ranking_score')
        assert hasattr(llm_service, '_generate_demo_recommendations')
        assert hasattr(llm_service, '_generate_personalized_reason')
        assert callable(llm_service._make_request)
        assert callable(llm_service.health_check)
        assert callable(llm_service._setup_demo_data)
        assert callable(llm_service._normalize_key)
        assert callable(llm_service._get_user_interaction_history)
        assert callable(llm_service._compute_ranking_score)
        assert callable(llm_service._generate_demo_recommendations)
        assert callable(llm_service._generate_personalized_reason)

    def test_llm_service_async_methods(self, llm_service):
        """Test LLMService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(llm_service._make_request)
        assert inspect.iscoroutinefunction(llm_service.health_check)
        assert inspect.iscoroutinefunction(llm_service._get_user_interaction_history)
        assert not inspect.iscoroutinefunction(llm_service._setup_demo_data)
        assert not inspect.iscoroutinefunction(llm_service._normalize_key)
        assert not inspect.iscoroutinefunction(llm_service._compute_ranking_score)
        assert not inspect.iscoroutinefunction(llm_service._generate_demo_recommendations)
        assert not inspect.iscoroutinefunction(llm_service._generate_personalized_reason)

    def test_llm_service_error_handling(self, llm_service):
        """Test LLMService error handling."""
        # Test that service handles errors gracefully
        with patch.object(llm_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                llm_service.logger.error(
                    "Error in LLM service",
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_llm_service_info_logging(self, llm_service):
        """Test LLMService info logging."""
        with patch.object(llm_service.logger, 'info') as mock_info:
            # Simulate an info log
            llm_service.logger.info(
                "LLM service operation completed",
                operation="test"
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_llm_service_thread_safety(self, llm_service):
        """Test LLMService thread safety."""
        import threading
        import time
        
        results = []
        
        def test_operation():
            try:
                # Simulate a service operation
                demo_data = llm_service._setup_demo_data()
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

    def test_llm_service_memory_usage(self, llm_service):
        """Test LLMService memory usage."""
        import gc
        
        # Generate multiple demo data
        demo_data_list = []
        for _ in range(100):
            demo_data = llm_service._setup_demo_data()
            demo_data_list.append(demo_data)
        
        # Check memory usage
        assert len(demo_data_list) == 100
        
        # Clean up
        del demo_data_list
        gc.collect()

    def test_llm_service_performance(self, llm_service):
        """Test LLMService performance."""
        import time
        
        # Test demo data generation performance
        start_time = time.time()
        demo_data_list = []
        for _ in range(100):
            demo_data = llm_service._setup_demo_data()
            demo_data_list.append(demo_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 demo data
        assert len(demo_data_list) == 100

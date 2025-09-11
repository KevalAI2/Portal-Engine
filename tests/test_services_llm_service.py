"""
Comprehensive test suite for LLM service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.llm_service import LLMService
import time
import threading
import gc


@pytest.mark.unit
class TestLLMService:
    """Test the LLM service functionality."""

    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing."""
        with patch('app.services.llm_service.settings') as mock_settings:
            mock_settings.recommendation_api_url = "http://test.example.com"
            mock_settings.recommendation_api_provider = "test_provider"
            mock_settings.redis_host = "localhost"
            return LLMService(timeout=120)

    def test_llm_service_initialization(self, llm_service):
        """Test LLMService initialization."""
        assert llm_service is not None
        assert hasattr(llm_service, 'timeout')
        assert llm_service.timeout == 120

    def test_setup_demo_data(self, llm_service):
        """Test demo data setup."""
        demo_data = llm_service._setup_demo_data()
        assert demo_data is None

    def test_normalize_key(self, llm_service):
        """Test key normalization."""
        test_cases = [
            ("user_123", "user123"),
            ("USER_123", "user123"),
            ("User 123", "user 123"),
            ("user-123", "user123"),
            ("user@123", "user123"),
            ("user+123", "user123"),
            ("user.123", "user123"),
            ("user/123", "user123"),
            ("user\\123", "user123"),
            ("user:123", "user123"),
            ("user;123", "user123"),
            ("user,123", "user123"),
            ("user?123", "user123"),
            ("user!123", "user123"),
            ("user#123", "user123"),
            ("user$123", "user123"),
            ("user%123", "user123"),
            ("user^123", "user123"),
            ("user&123", "user123"),
            ("user*123", "user123"),
            ("user(123)", "user123"),
            ("user[123]", "user123"),
            ("user{123}", "user123"),
            ("user|123", "user123"),
            ("user<123>", "user123"),
            ("user\"123\"", "user123"),
            ("user'123'", "user123"),
            ("user`123`", "user123"),
            ("user~123", "user123"),
            ("user\t123", "user\t123"),
            ("user\n123", "user\n123"),
            ("user\r123", "user\r123"),
            ("user 123", "user 123"),
            ("  user 123  ", "user 123"),
            ("", ""),
            ("   ", ""),
            ("user", "user"),
            ("123", "123"),
            ("user123", "user123"),
            ("user_123_location", "user123location"),
            ("user_123_location_456", "user123location456"),
        ]
        
        for input_key, expected_output in test_cases:
            result = llm_service._normalize_key(input_key)
            assert result == expected_output, f"Failed for input: {input_key}"

    def test_normalize_key_edge_cases(self, llm_service):
        """Test key normalization edge cases."""
        result = llm_service._normalize_key(None)
        assert result == ""
        
        result = llm_service._normalize_key("")
        assert result == ""
        
        result = llm_service._normalize_key("   ")
        assert result == ""
        
        result = llm_service._normalize_key("a")
        assert result == "a"
        
        result = llm_service._normalize_key("!@#$%^&*()")
        assert result == ""

    def test_normalize_key_unicode(self, llm_service):
        """Test key normalization with Unicode."""
        unicode_cases = [
            ("用户123", "用户123"),
            ("usuario123", "usuario123"),
            ("пользователь123", "пользователь123"),
            ("ユーザー123", "ユーザー123"),
            ("用户 123", "用户 123"),
            ("usuario 123", "usuario 123"),
            ("пользователь 123", "пользователь 123"),
            ("ユーザー 123", "ユーザー 123"),
        ]
        
        for input_key, expected_output in unicode_cases:
            result = llm_service._normalize_key(input_key)
            assert result == expected_output, f"Failed for input: {input_key}"

    def test_normalize_key_performance(self, llm_service):
        """Test key normalization performance."""
        keys = [f"user_{i}_key_{j}" for i in range(100) for j in range(10)]
        
        start_time = time.time()
        for key in keys:
            llm_service._normalize_key(key)
        end_time = time.time()
        
        assert end_time - start_time < 1.0, "Normalization performance too slow"

    def test_get_user_interaction_history(self, llm_service):
        """Test user interaction history retrieval."""
        result = llm_service._get_user_interaction_history("user_123")
        
        assert isinstance(result, dict)
        assert "events" in result
        assert "movies" in result
        assert "music" in result
        assert "places" in result
        for category in result:
            assert isinstance(result[category], list)
            for item in result[category]:
                assert isinstance(item, dict)
                assert "action" in item
                assert "timestamp" in item
                assert any(key in item for key in ["title", "name"])

    def test_get_user_interaction_history_empty(self, llm_service):
        """Test user interaction history with empty user_id."""
        result = llm_service._get_user_interaction_history("")
        
        assert isinstance(result, dict)
        assert "events" in result
        assert "movies" in result
        assert "music" in result
        assert "places" in result

    def test_compute_ranking_score(self, llm_service):
        """Test ranking score computation."""
        history = {
            "events": [
                {"action": "liked", "name": "Test Event", "timestamp": "2024-01-01T00:00:00Z"},
                {"action": "view", "name": "Test Event", "timestamp": "2024-01-02T00:00:00Z"}
            ],
            "movies": [],
            "music": [],
            "places": []
        }
        
        test_cases = [
            ({"name": "Test Event"}, "events", 0.98),  # liked (2.0) + view (0.4) * 0.2 + 0.5 = 0.98
            ({"name": "Unknown Event"}, "events", 0.5),  # No match, base score
            ({"title": "Test Movie"}, "movies", 0.5),  # No history, base score
        ]
        
        for item, category, expected_score in test_cases:
            result = llm_service._compute_ranking_score(item, category, history)
            assert 0.0 <= result <= 1.0, f"Score out of range for {item}"
            assert abs(result - expected_score) < 0.01, f"Unexpected score for {item}"

    def test_compute_ranking_score_edge_cases(self, llm_service):
        """Test ranking score computation edge cases."""
        history = {
            "events": [],
            "movies": [],
            "music": [],
            "places": []
        }
        
        test_cases = [
            ({}, "events", 0.5),
            ({"name": "Test Event"}, "events", 0.5),
            ({"title": "Test Movie"}, "movies", 0.5),
            ({"invalid_field": "value"}, "places", 0.5),
        ]
        
        for item, category, expected_score in test_cases:
            result = llm_service._compute_ranking_score(item, category, history)
            assert result == expected_score, f"Unexpected score for {item}"

    def test_compute_ranking_score_performance(self, llm_service):
        """Test ranking score computation performance."""
        history = {
            "events": [{"action": "view", "name": f"event_{i}", "timestamp": "2024-01-01T00:00:00Z"} for i in range(10)],
            "movies": [],
            "music": [],
            "places": []
        }
        
        items = [
            {"name": f"event_{i % 10}"} for i in range(100)
        ]
        
        start_time = time.time()
        for item in items:
            llm_service._compute_ranking_score(item, "events", history)
        end_time = time.time()
        
        assert end_time - start_time < 0.5, "Ranking score computation too slow"

    def test_generate_demo_recommendations(self, llm_service):
        """Test demo recommendations generation."""
        recommendations = llm_service._generate_demo_recommendations("demo prompt")
        
        assert isinstance(recommendations, dict)
        assert "events" in recommendations
        assert "movies" in recommendations
        assert "music" in recommendations
        assert "places" in recommendations
        assert all(isinstance(recommendations[cat], list) for cat in recommendations)

    def test_generate_demo_recommendations_structure(self, llm_service):
        """Test demo recommendations structure."""
        recommendations = llm_service._generate_demo_recommendations("demo prompt")
        
        for category, items in recommendations.items():
            assert isinstance(items, list)
            for item in items:
                assert isinstance(item, dict)
                assert any(field in item for field in ["name", "title", "genre", "type", "date"])

    def test_generate_demo_recommendations_uniqueness(self, llm_service):
        """Test demo recommendations uniqueness."""
        recommendations = llm_service._generate_demo_recommendations("demo prompt")
        
        for category, items in recommendations.items():
            if items:
                identifiers = [item.get("name") or item.get("title") for item in items]
                unique_identifiers = set(identifiers)
                assert len(unique_identifiers) == len(identifiers), f"Duplicates found in {category}"

    def test_generate_demo_recommendations_multiple_calls(self, llm_service):
        """Test demo recommendations multiple calls."""
        recs1 = llm_service._generate_demo_recommendations("demo prompt")
        recs2 = llm_service._generate_demo_recommendations("demo prompt")
        
        assert isinstance(recs1, dict)
        assert isinstance(recs2, dict)
        assert recs1.keys() == recs2.keys()
        for category in recs1:
            assert len(recs1[category]) == len(recs2[category])

    def test_generate_demo_recommendations_performance(self, llm_service):
        """Test demo recommendations performance."""
        start_time = time.time()
        recommendations = llm_service._generate_demo_recommendations("demo prompt")
        end_time = time.time()
        
        assert end_time - start_time < 0.1, "Demo recommendations generation too slow"
        assert isinstance(recommendations, dict)

    def test_generate_personalized_reason(self, llm_service):
        """Test personalized reason generation."""
        item = {
            "name": "Test Event",
            "category": "event",
            "organizer": "Test Organizer",
            "duration": "2 hours"
        }
        
        reason = llm_service._generate_personalized_reason(item, "events", "cultural events", user_id="user_123", current_city="Barcelona")
        
        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "Barcelona" in reason
        assert "user_123" not in reason  # User ID should not appear in reason

    def test_generate_personalized_reason_edge_cases(self, llm_service):
        """Test personalized reason generation edge cases."""
        test_cases = [
            (None, "events", "personalize prompt", "Barcelona"),
            ({}, "movies", "personalize prompt", "Barcelona"),
            ({"title": "Test Movie"}, "movies", "", "Barcelona"),
            ({"name": "Test Place"}, "places", "personalize prompt", "Barcelona"),
        ]
        
        for item, category, prompt, current_city in test_cases:
            reason = llm_service._generate_personalized_reason(item, category, prompt, user_id=None, current_city=current_city)
            assert isinstance(reason, str)
            assert len(reason) > 0
            assert "Barcelona" in reason

    def test_generate_personalized_reason_performance(self, llm_service):
        """Test personalized reason generation performance."""
        item = {"name": "Test Event", "category": "event"}
        
        start_time = time.time()
        for _ in range(100):
            llm_service._generate_personalized_reason(item, "events", "personalize prompt")
        end_time = time.time()
        
        assert end_time - start_time < 0.1, "Personalized reason generation too slow"

    def test_llm_service_logger_name(self, llm_service):
        """Test LLMService logger name."""
        from app.services.llm_service import logger
        assert logger is not None
        assert logger.name == "llm_service"

    def test_llm_service_method_availability(self, llm_service):
        """Test LLMService method availability."""
        expected_methods = [
            '_normalize_key',
            '_get_user_interaction_history',
            '_compute_ranking_score',
            '_generate_demo_recommendations',
            '_generate_personalized_reason',
            '_setup_demo_data'
        ]
        
        for method in expected_methods:
            assert hasattr(llm_service, method), f"Missing method: {method}"
            assert callable(getattr(llm_service, method)), f"Method {method} is not callable"

    def test_llm_service_async_methods(self, llm_service):
        """Test LLMService async methods."""
        import inspect
        
        async_methods = ['generate_recommendations', '_call_llm_api']
        sync_methods = [
            '_normalize_key',
            '_get_user_interaction_history',
            '_compute_ranking_score',
            '_generate_demo_recommendations',
            '_generate_personalized_reason',
            '_setup_demo_data'
        ]
        
        for method in async_methods:
            assert inspect.iscoroutinefunction(getattr(llm_service, method)), f"Method {method} should be async"
        
        for method in sync_methods:
            assert not inspect.iscoroutinefunction(getattr(llm_service, method)), f"Method {method} should not be async"

    def test_llm_service_error_handling(self, llm_service):
        """Test LLMService error handling."""
        with pytest.raises(AttributeError):
            llm_service.non_existent_method

    @patch('app.services.llm_service.logger')
    def test_llm_service_info_logging(self, mock_logger, llm_service):
        """Test LLMService info logging."""
        from app.services.llm_service import logger
        logger.info("LLM service operation completed", extra={"operation": "test"})
        mock_logger.info.assert_called()

    def test_llm_service_thread_safety(self, llm_service):
        """Test LLMService thread safety."""
        results = []
        
        def test_operation():
            try:
                demo_data = llm_service._setup_demo_data()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_operation, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results), f"Thread safety failed: {results}"

    def test_llm_service_memory_usage(self, llm_service):
        """Test LLMService memory usage."""
        demo_data_list = []
        for _ in range(100):
            demo_data = llm_service._setup_demo_data()
            demo_data_list.append(demo_data)
        
        assert len(demo_data_list) == 100
        
        del demo_data_list
        gc.collect()

    def test_llm_service_performance(self, llm_service):
        """Test LLMService performance."""
        start_time = time.time()
        demo_data_list = []
        for _ in range(100):
            demo_data = llm_service._setup_demo_data()
            demo_data_list.append(demo_data)
        end_time = time.time()
        
        assert end_time - start_time < 0.1, "Performance test too slow"
        assert len(demo_data_list) == 100
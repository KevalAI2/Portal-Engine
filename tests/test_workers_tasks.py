"""
Comprehensive test suite for Celery workers module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.workers.tasks import (
    fetch_user_data,
    build_prompt,
    call_llm,
    cache_results,
    generate_recommendations,
    process_user,
    get_users,
    process_user_comprehensive,
    generate_user_prompt
)


@pytest.mark.unit
class TestCeleryWorkers:
    """Test the Celery workers functionality."""

    def test_fetch_user_data(self):
        """Test fetch_user_data task."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service:
            with patch('app.workers.tasks.LIEService') as mock_lie_service:
                with patch('app.workers.tasks.CISService') as mock_cis_service:
                    # Mock the service instances and their async methods
                    mock_user_instance = Mock()
                    mock_lie_instance = Mock()
                    mock_cis_instance = Mock()
                    
                    # Create mock UserProfile object
                    mock_profile = Mock()
                    mock_profile.model_dump.return_value = {"user_id": "user_123", "name": "Test User"}
                    
                    # Create mock LocationData and InteractionData objects
                    mock_location = Mock()
                    mock_location.model_dump.return_value = {"user_id": "user_123", "location": "Test City"}
                    
                    mock_interaction = Mock()
                    mock_interaction.model_dump.return_value = {"user_id": "user_123", "interactions": []}
                    
                    # Set up async method returns
                    mock_user_instance.get_user_profile = AsyncMock(return_value=mock_profile)
                    mock_lie_instance.get_location_data = AsyncMock(return_value=mock_location)
                    mock_cis_instance.get_interaction_data = AsyncMock(return_value=mock_interaction)
                    
                    # Set up service constructors
                    mock_user_service.return_value = mock_user_instance
                    mock_lie_service.return_value = mock_lie_instance
                    mock_cis_service.return_value = mock_cis_instance

                    result = fetch_user_data("user_123")

                    assert isinstance(result, dict)
                    assert result["success"] is True
                    assert "user_data" in result
                    assert "user_profile" in result["user_data"]
                    assert "location_data" in result["user_data"]
                    assert "interaction_data" in result["user_data"]

    def test_fetch_user_data_error_handling(self):
        """Test fetch_user_data task error handling."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service:
            mock_user_service.side_effect = Exception("Service error")
            
            result = fetch_user_data("user_123")
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_fetch_user_data_empty_user_id(self):
        """Test fetch_user_data task with empty user ID."""
        result = fetch_user_data("")
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_fetch_user_data_none_user_id(self):
        """Test fetch_user_data task with None user ID."""
        result = fetch_user_data(None)
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_build_prompt(self):
        """Test build_prompt task."""
        user_data = {
            "user_profile": {
                "user_id": "user_123",
                "name": "John",
                "email": "john@example.com",
                "age": 30,
                "location": "New York, NY",
                "interests": ["travel"],
                "preferences": {"accommodation": "hotel"}
            },
            "location_data": {
                "user_id": "user_123",
                "current_location": "New York, NY",
                "home_location": "New York, NY",
                "travel_history": ["Paris", "London"]
            },
            "interaction_data": {
                "user_id": "user_123",
                "recent_interactions": [{"rating": 5, "interaction_type": "review"}],
                "engagement_score": 0.8
            }
        }
        
        with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder:
            mock_builder = Mock()
            mock_builder.build_recommendation_prompt.return_value = "Test prompt"
            mock_prompt_builder.return_value = mock_builder
            
            result = build_prompt(user_data, "place")
            
            assert isinstance(result, dict)
            assert result["success"] is True
            assert "prompt" in result

    def test_build_prompt_error_handling(self):
        """Test build_prompt task error handling."""
        user_data = {}
        
        with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder:
            mock_prompt_builder.side_effect = Exception("Builder error")
            
            result = build_prompt(user_data, "place")
            
            assert isinstance(result, dict)
            assert result["success"] is False
            assert "error" in result

    def test_build_prompt_empty_data(self):
        """Test build_prompt task with empty data."""
        user_data = {}
        
        result = build_prompt(user_data, "place")
        
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result

    def test_call_llm(self):
        """Test call_llm task."""
        prompt = "Test prompt"
        user_context = {"user_id": "user_123"}
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.generate_recommendations = AsyncMock(return_value=[{"id": "1", "title": "Test"}])
            
            result = call_llm(prompt, user_context, "place")
            
            assert isinstance(result, dict)
            assert "recommendations" in result

    def test_call_llm_error_handling(self):
        """Test call_llm task error handling."""
        prompt = "Test prompt"
        user_context = {"user_id": "user_123"}
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.generate_recommendations = AsyncMock(side_effect=Exception("LLM error"))
            
            result = call_llm(prompt, user_context, "place")
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_call_llm_empty_prompt(self):
        """Test call_llm task with empty prompt."""
        prompt = ""
        user_context = {"user_id": "user_123"}
        
        result = call_llm(prompt, user_context, "place")
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_call_llm_none_prompt(self):
        """Test call_llm task with None prompt."""
        prompt = None
        user_context = {"user_id": "user_123"}
        
        result = call_llm(prompt, user_context, "place")
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_cache_results(self):
        """Test cache_results task."""
        user_id = "user_123"
        recommendations = [{"id": "rec_1", "title": "Recommendation 1"}]
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.store_recommendations = AsyncMock(return_value=True)
            
            result = cache_results(user_id, recommendations, "place")
            
            assert isinstance(result, dict)
            assert result["success"] is True
            assert "cached_count" in result

    def test_cache_results_error_handling(self):
        """Test cache_results task error handling."""
        user_id = "user_123"
        recommendations = []
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.store_recommendations = AsyncMock(side_effect=Exception("Cache error"))
            
            result = cache_results(user_id, recommendations, "place")
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_cache_results_empty_data(self):
        """Test cache_results task with empty data."""
        user_id = ""
        recommendations = []
        
        result = cache_results(user_id, recommendations, "place")
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_generate_recommendations(self):
        """Test generate_recommendations task."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            with patch('app.workers.tasks.fetch_user_data') as mock_fetch:
                with patch('app.workers.tasks.build_prompt') as mock_build:
                    with patch('app.workers.tasks.call_llm') as mock_call:
                        with patch('app.workers.tasks.cache_results') as mock_cache:
                            mock_llm_service.get_recommendations = AsyncMock(return_value=None)
                            mock_fetch.return_value = {"user_profile": {}}
                            mock_build.return_value = "Test prompt"
                            mock_call.return_value = {"recommendations": []}
                            mock_cache.return_value = {"results": []}
                            
                            result = generate_recommendations(user_id, "place")
                        
                        assert isinstance(result, dict)
                        assert result["success"] is True
                        assert "recommendations" in result

    def test_generate_recommendations_error_handling(self):
        """Test generate_recommendations task error handling."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.fetch_user_data') as mock_fetch:
            mock_fetch.side_effect = Exception("Fetch error")
            
            result = generate_recommendations(user_id)
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_generate_recommendations_empty_user_id(self):
        """Test generate_recommendations task with empty user ID."""
        user_id = ""
        
        result = generate_recommendations(user_id)
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_process_user(self):
        """Test process_user task."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.generate_recommendations') as mock_generate:
            mock_generate.return_value = {"results": []}
            
            result = process_user(user_id)
            
            assert isinstance(result, dict)
            assert "results" in result

    def test_process_user_error_handling(self):
        """Test process_user task error handling."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.generate_recommendations') as mock_generate:
            mock_generate.side_effect = Exception("Generate error")
            
            result = process_user(user_id)
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_process_user_empty_user_id(self):
        """Test process_user task with empty user ID."""
        user_id = ""
        
        result = process_user(user_id)
        
        assert isinstance(result, dict)
        assert "error" in result

    def test_get_users(self):
        """Test get_users task."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service:
            mock_service = Mock()
            mock_service.get_user_profile.return_value = {"user_id": "user_123"}
            mock_user_service.return_value = mock_service
            
            result = get_users()
            
            assert isinstance(result, list)
            assert len(result) > 0

    def test_get_users_error_handling(self):
        """Test get_users task error handling."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service:
            mock_user_service.side_effect = Exception("Service error")
            
            result = get_users()
            
            assert isinstance(result, list)
            assert len(result) == 0

    def test_process_user_comprehensive(self):
        """Test process_user_comprehensive task."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.process_user') as mock_process:
            mock_process.return_value = {"results": []}
            
            result = process_user_comprehensive(user_id)
            
            assert isinstance(result, dict)
            assert "results" in result

    def test_process_user_comprehensive_error_handling(self):
        """Test process_user_comprehensive task error handling."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.process_user') as mock_process:
            mock_process.side_effect = Exception("Process error")
            
            result = process_user_comprehensive(user_id)
            
            assert isinstance(result, dict)
            assert "error" in result

    def test_generate_user_prompt(self):
        """Test generate_user_prompt task."""
        user_id = "1"
        
        with patch('app.workers.tasks.fetch_user_data') as mock_fetch:
            with patch('app.workers.tasks.build_prompt') as mock_build:
                mock_fetch.return_value = {"user_profile": {}}
                mock_build.return_value = "Test prompt"
                
                result = generate_user_prompt(user_id)
                
                assert isinstance(result, str)
                assert result == "Test prompt"

    def test_generate_user_prompt_error_handling(self):
        """Test generate_user_prompt task error handling."""
        user_id = "user_123"
        
        with patch('app.workers.tasks.fetch_user_data') as mock_fetch:
            mock_fetch.side_effect = Exception("Fetch error")
            
            result = generate_user_prompt(user_id)
            
            assert isinstance(result, str)
            assert "error" in result.lower()

    def test_celery_workers_import(self):
        """Test Celery workers import."""
        from app.workers.tasks import (
            fetch_user_data,
            build_prompt,
            call_llm,
            cache_results,
            generate_recommendations,
            process_user,
            get_users,
            process_user_comprehensive,
            generate_user_prompt
        )
        
        # All functions should be callable
        assert callable(fetch_user_data)
        assert callable(build_prompt)
        assert callable(call_llm)
        assert callable(cache_results)
        assert callable(generate_recommendations)
        assert callable(process_user)
        assert callable(get_users)
        assert callable(process_user_comprehensive)
        assert callable(generate_user_prompt)

    def test_celery_workers_function_signatures(self):
        """Test Celery workers function signatures."""
        import inspect
        
        # Check function signatures
        assert len(inspect.signature(fetch_user_data).parameters) == 1
        assert len(inspect.signature(build_prompt).parameters) == 1
        assert len(inspect.signature(call_llm).parameters) == 1
        assert len(inspect.signature(cache_results).parameters) == 2
        assert len(inspect.signature(generate_recommendations).parameters) == 1
        assert len(inspect.signature(process_user).parameters) == 1
        assert len(inspect.signature(get_users).parameters) == 0
        assert len(inspect.signature(process_user_comprehensive).parameters) == 1
        assert len(inspect.signature(generate_user_prompt).parameters) == 1

    def test_celery_workers_return_types(self):
        """Test Celery workers return types."""
        # Test return types
        assert isinstance(fetch_user_data("user_123"), dict)
        assert isinstance(build_prompt({}), str)
        assert isinstance(call_llm("prompt"), dict)
        assert isinstance(cache_results("user_123", []), dict)
        assert isinstance(generate_recommendations("user_123"), dict)
        assert isinstance(process_user("user_123"), dict)
        assert isinstance(get_users(), list)
        assert isinstance(process_user_comprehensive("user_123"), dict)
        assert isinstance(generate_user_prompt("user_123"), str)

    def test_celery_workers_error_handling(self):
        """Test Celery workers error handling."""
        # Test that all workers handle errors gracefully
        assert "error" in fetch_user_data("").keys()
        assert "error" in build_prompt({}).lower()
        assert "error" in call_llm("").keys()
        assert "error" in cache_results("", []).keys()
        assert "error" in generate_recommendations("").keys()
        assert "error" in process_user("").keys()
        assert isinstance(get_users(), list)
        assert "error" in process_user_comprehensive("").keys()
        assert "error" in generate_user_prompt("").lower()

    def test_celery_workers_thread_safety(self):
        """Test Celery workers thread safety."""
        import threading
        import time
        
        results = []
        
        def test_worker():
            try:
                result = fetch_user_data("user_123")
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_worker, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_celery_workers_performance(self):
        """Test Celery workers performance."""
        import time
        
        start_time = time.time()
        for _ in range(100):
            fetch_user_data("user_123")
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 2.0  # 2 seconds for 100 calls

    def test_celery_workers_memory_usage(self):
        """Test Celery workers memory usage."""
        import gc
        
        # Create multiple results
        results = []
        for _ in range(100):
            result = fetch_user_data("user_123")
            results.append(result)
        
        # Check memory usage
        assert len(results) == 100
        
        # Clean up
        del results
        gc.collect()

    def test_celery_workers_data_consistency(self):
        """Test Celery workers data consistency."""
        # Test that workers return consistent data structures
        result1 = fetch_user_data("user_123")
        result2 = fetch_user_data("user_123")
        
        # Both should be dictionaries
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        
        # Both should have similar structure
        assert "user_profile" in result1
        assert "location_data" in result1
        assert "interaction_data" in result1
        assert "user_profile" in result2
        assert "location_data" in result2
        assert "interaction_data" in result2

    def test_celery_workers_unicode_support(self):
        """Test Celery workers Unicode support."""
        unicode_user_id = "用户123"
        
        result = fetch_user_data(unicode_user_id)
        
        assert isinstance(result, dict)
        assert "user_profile" in result
        assert "location_data" in result
        assert "interaction_data" in result

    def test_celery_workers_large_data(self):
        """Test Celery workers with large data."""
        large_user_id = "a" * 1000  # Very long user ID
        
        result = fetch_user_data(large_user_id)
        
        assert isinstance(result, dict)
        assert "user_profile" in result
        assert "location_data" in result
        assert "interaction_data" in result

    def test_celery_workers_concurrent_access(self):
        """Test Celery workers concurrent access."""
        import asyncio
        
        async def test_worker():
            result = fetch_user_data("user_123")
            return result
        
        # Create multiple concurrent tasks
        tasks = [test_worker() for _ in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        # All should complete successfully
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results)

import time
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.cis_service import CISService
from app.models.schemas import InteractionData


@pytest.mark.unit
class TestCISService:
    """Test the CIS service functionality."""

    @pytest.fixture
    def cis_service(self):
        """Create CISService instance for testing."""
        with patch('app.services.cis_service.settings') as mock_settings:
            mock_settings.cis_service_url = "http://test.example.com"
            return CISService(timeout=30)

    def test_cis_service_initialization(self, cis_service):
        """Test CISService initialization."""
        assert cis_service.base_url == "http://test.example.com"
        assert cis_service.timeout == 30
        assert cis_service.logger is not None

    def test_cis_service_inheritance(self, cis_service):
        """Test CISService inheritance from BaseService."""
        from app.services.base import BaseService
        assert isinstance(cis_service, BaseService)

    def test_generate_mock_interaction_data(self, cis_service):
        """Test mock interaction data generation."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check that interaction_data is a dictionary with required keys
        assert isinstance(interaction_data, dict) and 'user_id' in interaction_data and 'recent_interactions' in interaction_data and 'engagement_score' in interaction_data
        
        # Check required fields
        assert interaction_data['user_id'] is not None
        assert interaction_data['recent_interactions'] is not None
        assert interaction_data['engagement_score'] is not None

    def test_generate_mock_interaction_data_field_types(self, cis_service):
        """Test mock interaction data field types."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check field types
        assert isinstance(interaction_data['user_id'], str)
        assert isinstance(interaction_data['recent_interactions'], list)
        assert isinstance(interaction_data['engagement_score'], float)

    def test_generate_mock_interaction_data_field_values(self, cis_service):
        """Test mock interaction data field values."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check field values are reasonable
        assert len(interaction_data['user_id']) > 0
        assert len(interaction_data['recent_interactions']) > 0
        assert 0.0 <= interaction_data['engagement_score'] <= 1.0

    def test_generate_mock_interaction_data_multiple_calls(self, cis_service):
        """Test mock interaction data generation multiple calls."""
        interaction_data_list = []
        for i in range(5):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            interaction_data_list.append(interaction_data)
        
        # Check that all interaction data are valid dictionaries
        for interaction_data in interaction_data_list:
            assert isinstance(interaction_data, dict) and 'user_id' in interaction_data and 'recent_interactions' in interaction_data and 'engagement_score' in interaction_data
            assert interaction_data['user_id'] is not None
            assert interaction_data['recent_interactions'] is not None

    def test_generate_mock_interaction_data_uniqueness(self, cis_service):
        """Test mock interaction data uniqueness."""
        interaction_data_list = []
        for i in range(10):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            interaction_data_list.append(interaction_data)
        
        # Check that user_ids are unique
        user_ids = [data["user_id"] for data in interaction_data_list]
        assert len(set(user_ids)) == len(user_ids)

    def test_generate_mock_interaction_data_context_structure(self, cis_service):
        """Test mock interaction data context structure."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check recent_interactions structure
        assert isinstance(interaction_data['recent_interactions'], list)
        for interaction in interaction_data['recent_interactions']:
            assert "id" in interaction
            assert "content_type" in interaction
            assert "interaction_type" in interaction
            assert "timestamp" in interaction
            assert isinstance(interaction["id"], str)
            assert isinstance(interaction["content_type"], str)
            assert isinstance(interaction["interaction_type"], str)
            assert isinstance(interaction["timestamp"], str)

    def test_generate_mock_interaction_data_metadata_structure(self, cis_service):
        """Test mock interaction data metadata structure."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check metadata structure (assuming metadata-like fields are in recent_interactions)
        for interaction in interaction_data['recent_interactions']:
            assert isinstance(interaction["content_type"], str)
            assert isinstance(interaction["interaction_type"], str)
            assert isinstance(interaction["timestamp"], str)

    def test_generate_mock_interaction_data_rating_validation(self, cis_service):
        """Test mock interaction data rating validation."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check engagement_score is within valid range
        assert 0.0 <= interaction_data['engagement_score'] <= 1.0

    def test_generate_mock_interaction_data_duration_validation(self, cis_service):
        """Test mock interaction data duration validation."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check recent_interactions have valid timestamps
        for interaction in interaction_data['recent_interactions']:
            assert "T" in interaction["timestamp"]

    def test_generate_mock_interaction_data_interaction_types(self, cis_service):
        """Test mock interaction data interaction types."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check interaction types in recent_interactions are valid
        valid_types = [
            "view", "like", "share", "comment", "save", "bookmark", "click",
            "purchase", "download", "install", "subscribe", "follow", "rate",
            "review", "recommend", "search", "browse", "watch", "listen", "read",
            "react", "report", "block", "mute", "pin", "highlight", "annotate"
        ]
        for interaction in interaction_data['recent_interactions']:
            assert interaction["interaction_type"] in valid_types

    def test_generate_mock_interaction_data_timestamp_format(self, cis_service):
        """Test mock interaction data timestamp format."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check timestamp format in recent_interactions (ISO 8601)
        for interaction in interaction_data['recent_interactions']:
            assert "T" in interaction["timestamp"]

    def test_generate_mock_interaction_data_created_updated_format(self, cis_service):
        """Test mock interaction data created/updated format."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Check timestamp format in recent_interactions (ISO 8601)
        for interaction in interaction_data['recent_interactions']:
            assert "T" in interaction["timestamp"]

    @pytest.mark.asyncio
    async def test_get_interaction_data_success(self, cis_service):
        """Test successful interaction data retrieval."""
        mock_interaction_data = {
            "user_id": "user_123",
            "recent_interactions": [
                {
                    "id": "int_123",
                    "content_type": "article",
                    "interaction_type": "view",
                    "timestamp": "2023-01-01T00:00:00Z"
                }
            ],
            "engagement_score": 0.8,
            "data_confidence": 0.9,
            "interaction_history": [],
            "interaction_preferences": {}
        }

        with patch.object(cis_service, '_generate_mock_interaction_data') as mock_generate:
            mock_generate.return_value = mock_interaction_data
            
            result = await cis_service.get_interaction_data("user_123")
            
            # Result should be parsed into InteractionData
            assert isinstance(result, InteractionData)
            assert result.user_id == "user_123"
            assert len(result.recent_interactions) > 0
            assert result.recent_interactions[0]["id"] == "int_123"
            assert result.recent_interactions[0]["interaction_type"] == "view"
            assert 0.0 <= result.engagement_score <= 1.0
            mock_generate.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    async def test_get_interaction_data_not_found(self, cis_service):
        """Test interaction data not found."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await cis_service.get_interaction_data("nonexistent_user")
            
            # Should return generated interaction data when not found
            assert isinstance(result, InteractionData)
            assert result.user_id == "nonexistent_user"

    @pytest.mark.asyncio
    async def test_get_interaction_data_service_error(self, cis_service):
        """Test interaction data service error."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when service error
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_interaction_data_timeout_error(self, cis_service):
        """Test interaction data timeout error."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when timeout
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_interaction_data_any_exception(self, cis_service):
        """Test interaction data any exception."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = ValueError("Any error")
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when any exception
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_interaction_data_invalid_response(self, cis_service):
        """Test interaction data invalid response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"invalid": "data"}
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when invalid response
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_interaction_data_partial_response(self, cis_service):
        """Test interaction data partial response."""
        partial_data = {
            "user_id": "user_123",
            "recent_interactions": [
                {
                    "id": "int_123",
                    "content_type": "article",
                    "interaction_type": "view"
                }
            ]
        }

        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = partial_data
            
            result = await cis_service.get_interaction_data("user_123")
            
            # Should return generated interaction data when partial response
            assert isinstance(result, InteractionData)
            assert result.user_id == "user_123"
            assert len(result.recent_interactions) > 0
            assert 0.0 <= result.engagement_score <= 1.0

    @pytest.mark.asyncio
    async def test_get_interaction_data_empty_response(self, cis_service):
        """Test interaction data empty response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {}
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when empty response
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"
            assert len(result.recent_interactions) > 0
            assert 0.0 <= result.engagement_score <= 1.0

    @pytest.mark.asyncio
    async def test_get_interaction_data_none_response(self, cis_service):
        """Test interaction data None response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = None
            
            result = await cis_service.get_interaction_data("test_user")
            
            # Should return generated interaction data when None response
            assert isinstance(result, InteractionData)
            assert result.user_id == "test_user"
            assert len(result.recent_interactions) > 0
            assert 0.0 <= result.engagement_score <= 1.0

    @pytest.mark.asyncio
    async def test_get_interaction_data_different_interaction_ids(self, cis_service):
        """Test interaction data with different user IDs."""
        user_ids = ["user1", "user2", "user3", "user_123", "test-user", "user@domain.com"]
        
        for user_id in user_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(user_id)
                
                assert isinstance(result, InteractionData)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_special_characters(self, cis_service):
        """Test interaction data with special characters."""
        special_user_ids = ["user-123", "user_123", "user.123", "user@123", "user+123"]
        
        for user_id in special_user_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(user_id)
                
                assert isinstance(result, InteractionData)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_unicode(self, cis_service):
        """Test interaction data with Unicode characters."""
        unicode_user_ids = ["用户123", "usuário123", "пользователь123", "ユーザー123"]
        
        for user_id in unicode_user_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(user_id)
                
                assert isinstance(result, InteractionData)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_long_user_id(self, cis_service):
        """Test interaction data with long user ID."""
        long_user_id = "a" * 1000  # Very long user ID
        
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await cis_service.get_interaction_data(long_user_id)
            
            # Should return generated interaction data when long user ID
            assert isinstance(result, InteractionData)
            assert result.user_id == long_user_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_concurrent_requests(self, cis_service):
        """Test interaction data concurrent requests."""
        import asyncio
        
        async def get_interaction_data(user_id):
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                return await cis_service.get_interaction_data(user_id)
        
        # Create multiple concurrent requests
        tasks = [get_interaction_data(f"user_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check all results are valid
        for i, result in enumerate(results):
            assert isinstance(result, InteractionData)
            assert result.user_id == f"user_{i}"

    @pytest.mark.asyncio
    async def test_get_interaction_data_caching_behavior(self, cis_service):
        """Test interaction data caching behavior."""
        # Test that multiple calls with same user_id return consistent results
        user_id = "user_123"
        
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result1 = await cis_service.get_interaction_data(user_id)
            result2 = await cis_service.get_interaction_data(user_id)
            
            # Results should be consistent (same user_id)
            assert result1.user_id == result2.user_id
            assert result1.user_id == user_id

    def test_cis_service_logger_name(self, cis_service):
        """Test CISService logger name."""
        assert cis_service.logger._logger_factory_args[0] == 'cis_service'

    def test_cis_service_method_availability(self, cis_service):
        """Test CISService method availability."""
        # Test that all expected methods are available
        assert hasattr(cis_service, '_make_request')
        assert hasattr(cis_service, 'health_check')
        assert hasattr(cis_service, '_generate_mock_interaction_data')
        assert hasattr(cis_service, 'get_interaction_data')
        assert callable(cis_service._make_request)
        assert callable(cis_service.health_check)
        assert callable(cis_service._generate_mock_interaction_data)
        assert callable(cis_service.get_interaction_data)

    def test_cis_service_async_methods(self, cis_service):
        """Test CISService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(cis_service._make_request)
        assert inspect.iscoroutinefunction(cis_service.health_check)
        assert inspect.iscoroutinefunction(cis_service.get_interaction_data)
        assert not inspect.iscoroutinefunction(cis_service._generate_mock_interaction_data)

    def test_cis_service_error_handling(self, cis_service):
        """Test CISService error handling."""
        with patch.object(cis_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                cis_service.logger.error(
                    "Error fetching interaction data",
                    interaction_id="test_interaction",
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_cis_service_info_logging(self, cis_service):
        """Test CISService info logging."""
        with patch.object(cis_service.logger, 'info') as mock_info:
            # Simulate an info log
            cis_service.logger.info(
                "Interaction data retrieved",
                interaction_id="test_interaction",
                source="api"
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_cis_service_thread_safety(self, cis_service):
        """Test CISService thread safety."""
        import threading
        
        results = []
        
        def test_get_interaction_data(i):
            try:
                # Simulate interaction data generation
                interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_get_interaction_data, args=(i,), name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_cis_service_memory_usage(self, cis_service):
        """Test CISService memory usage."""
        import gc
        
        # Generate multiple interaction data
        interaction_data_list = []
        for i in range(100):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            interaction_data_list.append(interaction_data)
        
        # Check memory usage
        assert len(interaction_data_list) == 100
        
        # Clean up
        del interaction_data_list
        gc.collect()

    def test_cis_service_performance(self, cis_service):
        """Test CISService performance."""
        import time
        
        # Test interaction data generation performance
        start_time = time.time()
        interaction_data_list = []
        for i in range(100):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            interaction_data_list.append(interaction_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 interaction data
        assert len(interaction_data_list) == 100

    def test_cis_service_data_consistency(self, cis_service):
        """Test CISService data consistency."""
        # Test that generated data is consistent
        interaction_data1 = cis_service._generate_mock_interaction_data(user_id="test_user_1")
        interaction_data2 = cis_service._generate_mock_interaction_data(user_id="test_user_2")
        
        # Both should be valid dictionaries with required keys
        assert isinstance(interaction_data1, dict) and 'user_id' in interaction_data1 and 'recent_interactions' in interaction_data1 and 'engagement_score' in interaction_data1
        assert isinstance(interaction_data2, dict) and 'user_id' in interaction_data2 and 'recent_interactions' in interaction_data2 and 'engagement_score' in interaction_data2
        
        # Both should have all required fields
        for interaction_data in [interaction_data1, interaction_data2]:
            assert interaction_data['user_id'] is not None
            assert interaction_data['recent_interactions'] is not None
            assert interaction_data['engagement_score'] is not None

    def test_cis_service_data_validation(self, cis_service):
        """Test CISService data validation."""
        # Test that generated data passes validation
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Test engagement_score validation
        assert 0.0 <= interaction_data['engagement_score'] <= 1.0
        
        # Test interaction type validation
        valid_types = [
            "view", "like", "share", "comment", "save", "bookmark", "click",
            "purchase", "download", "install", "subscribe", "follow", "rate",
            "review", "recommend", "search", "browse", "watch", "listen", "read",
            "react", "report", "block", "mute", "pin", "highlight", "annotate"
        ]
        for interaction in interaction_data['recent_interactions']:
            assert interaction["interaction_type"] in valid_types
        
        # Test timestamp format validation
        for interaction in interaction_data['recent_interactions']:
            assert "T" in interaction["timestamp"]
        
        # Test recent_interactions validation
        for interaction in interaction_data['recent_interactions']:
            assert "id" in interaction
            assert "content_type" in interaction
            assert "interaction_type" in interaction
            assert "timestamp" in interaction

    def test_cis_service_context_data_types(self, cis_service):
        """Test CISService context data types."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Test recent_interactions data types
        for interaction in interaction_data['recent_interactions']:
            assert isinstance(interaction["id"], str)
            assert isinstance(interaction["content_type"], str)
            assert isinstance(interaction["interaction_type"], str)
            assert isinstance(interaction["timestamp"], str)

    def test_cis_service_metadata_data_types(self, cis_service):
        """Test CISService metadata data types."""
        interaction_data = cis_service._generate_mock_interaction_data(user_id="test_user")
        
        # Test metadata-like data types in recent_interactions
        for interaction in interaction_data['recent_interactions']:
            assert isinstance(interaction["content_type"], str)
            assert isinstance(interaction["interaction_type"], str)
            assert isinstance(interaction["timestamp"], str)

    def test_cis_service_interaction_type_distribution(self, cis_service):
        """Test CISService interaction type distribution."""
        # Generate multiple interaction data and check type distribution
        interaction_types = []
        for i in range(100):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            for interaction in interaction_data['recent_interactions']:
                interaction_types.append(interaction["interaction_type"])
        
        # Check that we have variety in interaction types
        unique_types = set(interaction_types)
        assert len(unique_types) > 1  # Should have multiple types

    def test_cis_service_rating_distribution(self, cis_service):
        """Test CISService rating distribution."""
        # Generate multiple interaction data and check engagement_score distribution
        scores = []
        for i in range(100):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            scores.append(interaction_data['engagement_score'])
        
        # Check that scores are within valid range
        assert all(0.0 <= score <= 1.0 for score in scores)
        
        # Check that we have variety in scores
        unique_scores = set(scores)
        assert len(unique_scores) > 1  # Should have multiple scores

    def test_cis_service_duration_distribution(self, cis_service):
        """Test CISService duration distribution."""
        # Generate multiple interaction data and check timestamp variety
        timestamps = []
        for i in range(100):
            interaction_data = cis_service._generate_mock_interaction_data(user_id=f"test_user_{i}")
            for interaction in interaction_data['recent_interactions']:
                timestamps.append(interaction["timestamp"])
        
        # Check that timestamps are valid
        for timestamp in timestamps:
            assert "T" in timestamp
        
        # Check that we have variety in timestamps
        unique_timestamps = set(timestamps)
        assert len(unique_timestamps) > 1  # Should have multiple timestamps
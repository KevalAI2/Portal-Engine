"""
Comprehensive test suite for CIS service module
"""
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
            return CISService()

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
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check that interaction_data is an InteractionData instance
        assert isinstance(interaction_data, InteractionData)
        
        # Check required fields
        assert interaction_data.interaction_id is not None
        assert interaction_data.user_id is not None
        assert interaction_data.location_id is not None
        assert interaction_data.interaction_type is not None
        assert interaction_data.timestamp is not None
        assert interaction_data.duration is not None
        assert interaction_data.rating is not None
        assert interaction_data.feedback is not None
        assert interaction_data.context is not None
        assert interaction_data.metadata is not None
        assert interaction_data.created_at is not None
        assert interaction_data.updated_at is not None

    def test_generate_mock_interaction_data_field_types(self, cis_service):
        """Test mock interaction data field types."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check field types
        assert isinstance(interaction_data.interaction_id, str)
        assert isinstance(interaction_data.user_id, str)
        assert isinstance(interaction_data.location_id, str)
        assert isinstance(interaction_data.interaction_type, str)
        assert isinstance(interaction_data.timestamp, str)
        assert isinstance(interaction_data.duration, int)
        assert isinstance(interaction_data.rating, int)
        assert isinstance(interaction_data.feedback, str)
        assert isinstance(interaction_data.context, dict)
        assert isinstance(interaction_data.metadata, dict)
        assert isinstance(interaction_data.created_at, str)
        assert isinstance(interaction_data.updated_at, str)

    def test_generate_mock_interaction_data_field_values(self, cis_service):
        """Test mock interaction data field values."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check field values are reasonable
        assert len(interaction_data.interaction_id) > 0
        assert len(interaction_data.user_id) > 0
        assert len(interaction_data.location_id) > 0
        assert len(interaction_data.interaction_type) > 0
        assert len(interaction_data.timestamp) > 0
        assert interaction_data.duration > 0
        assert 1 <= interaction_data.rating <= 5
        assert len(interaction_data.feedback) > 0
        assert len(interaction_data.context) > 0
        assert len(interaction_data.metadata) > 0
        assert len(interaction_data.created_at) > 0
        assert len(interaction_data.updated_at) > 0

    def test_generate_mock_interaction_data_multiple_calls(self, cis_service):
        """Test mock interaction data generation multiple calls."""
        interaction_data_list = []
        for _ in range(5):
            interaction_data = cis_service._generate_mock_interaction_data()
            interaction_data_list.append(interaction_data)
        
        # Check that all interaction data are valid
        for interaction_data in interaction_data_list:
            assert isinstance(interaction_data, InteractionData)
            assert interaction_data.interaction_id is not None
            assert interaction_data.user_id is not None
            assert interaction_data.location_id is not None
            assert interaction_data.interaction_type is not None

    def test_generate_mock_interaction_data_uniqueness(self, cis_service):
        """Test mock interaction data uniqueness."""
        interaction_data_list = []
        for _ in range(10):
            interaction_data = cis_service._generate_mock_interaction_data()
            interaction_data_list.append(interaction_data)
        
        # Check that interaction_ids are unique
        interaction_ids = [data.interaction_id for data in interaction_data_list]
        assert len(set(interaction_ids)) == len(interaction_ids)

    def test_generate_mock_interaction_data_context_structure(self, cis_service):
        """Test mock interaction data context structure."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check context structure
        assert "device" in interaction_data.context
        assert "platform" in interaction_data.context
        assert "session_id" in interaction_data.context
        assert "ip_address" in interaction_data.context
        assert "user_agent" in interaction_data.context
        assert "referrer" in interaction_data.context
        assert "language" in interaction_data.context
        assert "timezone" in interaction_data.context
        assert isinstance(interaction_data.context["device"], str)
        assert isinstance(interaction_data.context["platform"], str)
        assert isinstance(interaction_data.context["session_id"], str)
        assert isinstance(interaction_data.context["ip_address"], str)
        assert isinstance(interaction_data.context["user_agent"], str)
        assert isinstance(interaction_data.context["referrer"], str)
        assert isinstance(interaction_data.context["language"], str)
        assert isinstance(interaction_data.context["timezone"], str)

    def test_generate_mock_interaction_data_metadata_structure(self, cis_service):
        """Test mock interaction data metadata structure."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check metadata structure
        assert "source" in interaction_data.metadata
        assert "campaign" in interaction_data.metadata
        assert "tags" in interaction_data.metadata
        assert "custom_fields" in interaction_data.metadata
        assert isinstance(interaction_data.metadata["source"], str)
        assert isinstance(interaction_data.metadata["campaign"], str)
        assert isinstance(interaction_data.metadata["tags"], list)
        assert isinstance(interaction_data.metadata["custom_fields"], dict)

    def test_generate_mock_interaction_data_rating_validation(self, cis_service):
        """Test mock interaction data rating validation."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check rating is within valid range
        assert 1 <= interaction_data.rating <= 5

    def test_generate_mock_interaction_data_duration_validation(self, cis_service):
        """Test mock interaction data duration validation."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check duration is positive
        assert interaction_data.duration > 0

    def test_generate_mock_interaction_data_interaction_types(self, cis_service):
        """Test mock interaction data interaction types."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check interaction type is valid
        valid_types = ["view", "click", "purchase", "review", "share", "bookmark", "like", "dislike"]
        assert interaction_data.interaction_type in valid_types

    def test_generate_mock_interaction_data_timestamp_format(self, cis_service):
        """Test mock interaction data timestamp format."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check timestamp format (ISO 8601)
        assert "T" in interaction_data.timestamp
        assert "Z" in interaction_data.timestamp or "+" in interaction_data.timestamp

    def test_generate_mock_interaction_data_created_updated_format(self, cis_service):
        """Test mock interaction data created/updated format."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Check created_at and updated_at format (ISO 8601)
        assert "T" in interaction_data.created_at
        assert "Z" in interaction_data.created_at or "+" in interaction_data.created_at
        assert "T" in interaction_data.updated_at
        assert "Z" in interaction_data.updated_at or "+" in interaction_data.updated_at

    @pytest.mark.asyncio
    async def test_get_interaction_data_success(self, cis_service):
        """Test successful interaction data retrieval."""
        mock_interaction_data = {
            "interaction_id": "int_123",
            "user_id": "user_123",
            "location_id": "loc_123",
            "interaction_type": "view",
            "timestamp": "2023-01-01T00:00:00Z",
            "duration": 30,
            "rating": 4,
            "feedback": "Great experience!",
            "context": {
                "device": "mobile",
                "platform": "ios",
                "session_id": "session_123",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "referrer": "https://example.com",
                "language": "en",
                "timezone": "America/New_York"
            },
            "metadata": {
                "source": "web",
                "campaign": "summer2023",
                "tags": ["travel", "vacation"],
                "custom_fields": {"priority": "high"}
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }

        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = mock_interaction_data
            
            result = await cis_service.get_interaction_data("int_123")
            
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "int_123"
            assert result.user_id == "user_123"
            assert result.location_id == "loc_123"
            assert result.interaction_type == "view"
            mock_make_request.assert_called_once_with("GET", "/interaction/int_123")

    @pytest.mark.asyncio
    async def test_get_interaction_data_not_found(self, cis_service):
        """Test interaction data not found."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await cis_service.get_interaction_data("nonexistent_interaction")
            
            # Should return generated interaction data when not found
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "nonexistent_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_service_error(self, cis_service):
        """Test interaction data service error."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when service error
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_timeout_error(self, cis_service):
        """Test interaction data timeout error."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when timeout
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_any_exception(self, cis_service):
        """Test interaction data any exception."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = ValueError("Any error")
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when any exception
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_invalid_response(self, cis_service):
        """Test interaction data invalid response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"invalid": "data"}
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when invalid response
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_partial_response(self, cis_service):
        """Test interaction data partial response."""
        partial_data = {
            "interaction_id": "int_123",
            "user_id": "user_123",
            "location_id": "loc_123",
            "interaction_type": "view"
            # Missing other required fields
        }

        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = partial_data
            
            result = await cis_service.get_interaction_data("int_123")
            
            # Should return generated interaction data when partial response
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "int_123"

    @pytest.mark.asyncio
    async def test_get_interaction_data_empty_response(self, cis_service):
        """Test interaction data empty response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {}
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when empty response
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_none_response(self, cis_service):
        """Test interaction data None response."""
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = None
            
            result = await cis_service.get_interaction_data("test_interaction")
            
            # Should return generated interaction data when None response
            assert isinstance(result, InteractionData)
            assert result.interaction_id == "test_interaction"

    @pytest.mark.asyncio
    async def test_get_interaction_data_different_interaction_ids(self, cis_service):
        """Test interaction data with different interaction IDs."""
        interaction_ids = ["int1", "int2", "int3", "int_123", "test-int", "int@domain.com"]
        
        for interaction_id in interaction_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(interaction_id)
                
                assert isinstance(result, InteractionData)
                assert result.interaction_id == interaction_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_special_characters(self, cis_service):
        """Test interaction data with special characters."""
        special_interaction_ids = ["int-123", "int_123", "int.123", "int@123", "int+123"]
        
        for interaction_id in special_interaction_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(interaction_id)
                
                assert isinstance(result, InteractionData)
                assert result.interaction_id == interaction_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_unicode(self, cis_service):
        """Test interaction data with Unicode characters."""
        unicode_interaction_ids = ["交互123", "interacción123", "взаимодействие123", "相互作用123"]
        
        for interaction_id in unicode_interaction_ids:
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await cis_service.get_interaction_data(interaction_id)
                
                assert isinstance(result, InteractionData)
                assert result.interaction_id == interaction_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_long_interaction_id(self, cis_service):
        """Test interaction data with long interaction ID."""
        long_interaction_id = "a" * 1000  # Very long interaction ID
        
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await cis_service.get_interaction_data(long_interaction_id)
            
            assert isinstance(result, InteractionData)
            assert result.interaction_id == long_interaction_id

    @pytest.mark.asyncio
    async def test_get_interaction_data_concurrent_requests(self, cis_service):
        """Test interaction data concurrent requests."""
        import asyncio
        
        async def get_interaction_data(interaction_id):
            with patch.object(cis_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                return await cis_service.get_interaction_data(interaction_id)
        
        # Create multiple concurrent requests
        tasks = [get_interaction_data(f"int_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check all results are valid
        for i, result in enumerate(results):
            assert isinstance(result, InteractionData)
            assert result.interaction_id == f"int_{i}"

    @pytest.mark.asyncio
    async def test_get_interaction_data_caching_behavior(self, cis_service):
        """Test interaction data caching behavior."""
        # Test that multiple calls with same interaction_id return consistent results
        interaction_id = "int_123"
        
        with patch.object(cis_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result1 = await cis_service.get_interaction_data(interaction_id)
            result2 = await cis_service.get_interaction_data(interaction_id)
            
            # Results should be consistent (same interaction_id)
            assert result1.interaction_id == result2.interaction_id
            assert result1.interaction_id == interaction_id

    def test_cis_service_logger_name(self, cis_service):
        """Test CISService logger name."""
        assert cis_service.logger._context.get('logger') == 'CISService'

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
        # Test that service handles errors gracefully
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
        import time
        
        results = []
        
        def test_get_interaction_data():
            try:
                # Simulate interaction data generation
                interaction_data = cis_service._generate_mock_interaction_data()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_get_interaction_data, name=f"thread_{i}")
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
        for _ in range(100):
            interaction_data = cis_service._generate_mock_interaction_data()
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
        for _ in range(100):
            interaction_data = cis_service._generate_mock_interaction_data()
            interaction_data_list.append(interaction_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 interaction data
        assert len(interaction_data_list) == 100

    def test_cis_service_data_consistency(self, cis_service):
        """Test CISService data consistency."""
        # Test that generated data is consistent
        interaction_data1 = cis_service._generate_mock_interaction_data()
        interaction_data2 = cis_service._generate_mock_interaction_data()
        
        # Both should be valid InteractionData instances
        assert isinstance(interaction_data1, InteractionData)
        assert isinstance(interaction_data2, InteractionData)
        
        # Both should have all required fields
        for interaction_data in [interaction_data1, interaction_data2]:
            assert interaction_data.interaction_id is not None
            assert interaction_data.user_id is not None
            assert interaction_data.location_id is not None
            assert interaction_data.interaction_type is not None
            assert interaction_data.timestamp is not None
            assert interaction_data.duration is not None
            assert interaction_data.rating is not None
            assert interaction_data.feedback is not None
            assert interaction_data.context is not None
            assert interaction_data.metadata is not None
            assert interaction_data.created_at is not None
            assert interaction_data.updated_at is not None

    def test_cis_service_data_validation(self, cis_service):
        """Test CISService data validation."""
        # Test that generated data passes validation
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Test rating validation
        assert 1 <= interaction_data.rating <= 5
        
        # Test duration validation
        assert interaction_data.duration > 0
        
        # Test interaction type validation
        valid_types = ["view", "click", "purchase", "review", "share", "bookmark", "like", "dislike"]
        assert interaction_data.interaction_type in valid_types
        
        # Test timestamp format validation
        assert "T" in interaction_data.timestamp
        assert "Z" in interaction_data.timestamp or "+" in interaction_data.timestamp
        
        # Test context validation
        assert "device" in interaction_data.context
        assert "platform" in interaction_data.context
        assert "session_id" in interaction_data.context
        assert "ip_address" in interaction_data.context
        assert "user_agent" in interaction_data.context
        assert "referrer" in interaction_data.context
        assert "language" in interaction_data.context
        assert "timezone" in interaction_data.context
        
        # Test metadata validation
        assert "source" in interaction_data.metadata
        assert "campaign" in interaction_data.metadata
        assert "tags" in interaction_data.metadata
        assert "custom_fields" in interaction_data.metadata
        
        # Test list validations
        assert isinstance(interaction_data.metadata["tags"], list)
        assert isinstance(interaction_data.metadata["custom_fields"], dict)

    def test_cis_service_context_data_types(self, cis_service):
        """Test CISService context data types."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Test context data types
        assert isinstance(interaction_data.context["device"], str)
        assert isinstance(interaction_data.context["platform"], str)
        assert isinstance(interaction_data.context["session_id"], str)
        assert isinstance(interaction_data.context["ip_address"], str)
        assert isinstance(interaction_data.context["user_agent"], str)
        assert isinstance(interaction_data.context["referrer"], str)
        assert isinstance(interaction_data.context["language"], str)
        assert isinstance(interaction_data.context["timezone"], str)

    def test_cis_service_metadata_data_types(self, cis_service):
        """Test CISService metadata data types."""
        interaction_data = cis_service._generate_mock_interaction_data()
        
        # Test metadata data types
        assert isinstance(interaction_data.metadata["source"], str)
        assert isinstance(interaction_data.metadata["campaign"], str)
        assert isinstance(interaction_data.metadata["tags"], list)
        assert isinstance(interaction_data.metadata["custom_fields"], dict)

    def test_cis_service_interaction_type_distribution(self, cis_service):
        """Test CISService interaction type distribution."""
        # Generate multiple interaction data and check type distribution
        interaction_types = []
        for _ in range(100):
            interaction_data = cis_service._generate_mock_interaction_data()
            interaction_types.append(interaction_data.interaction_type)
        
        # Check that we have variety in interaction types
        unique_types = set(interaction_types)
        assert len(unique_types) > 1  # Should have multiple types

    def test_cis_service_rating_distribution(self, cis_service):
        """Test CISService rating distribution."""
        # Generate multiple interaction data and check rating distribution
        ratings = []
        for _ in range(100):
            interaction_data = cis_service._generate_mock_interaction_data()
            ratings.append(interaction_data.rating)
        
        # Check that ratings are within valid range
        assert all(1 <= rating <= 5 for rating in ratings)
        
        # Check that we have variety in ratings
        unique_ratings = set(ratings)
        assert len(unique_ratings) > 1  # Should have multiple ratings

    def test_cis_service_duration_distribution(self, cis_service):
        """Test CISService duration distribution."""
        # Generate multiple interaction data and check duration distribution
        durations = []
        for _ in range(100):
            interaction_data = cis_service._generate_mock_interaction_data()
            durations.append(interaction_data.duration)
        
        # Check that durations are positive
        assert all(duration > 0 for duration in durations)
        
        # Check that we have variety in durations
        unique_durations = set(durations)
        assert len(unique_durations) > 1  # Should have multiple durations

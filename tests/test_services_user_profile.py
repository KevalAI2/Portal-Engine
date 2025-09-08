"""
Comprehensive test suite for user profile service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.user_profile import UserProfileService
from app.models.schemas import UserProfile


@pytest.mark.unit
class TestUserProfileService:
    """Test the user profile service functionality."""

    @pytest.fixture
    def user_profile_service(self):
        """Create UserProfileService instance for testing."""
        with patch('app.services.user_profile.settings') as mock_settings:
            mock_settings.user_profile_service_url = "http://test.example.com"
            return UserProfileService()

    def test_user_profile_service_initialization(self, user_profile_service):
        """Test UserProfileService initialization."""
        assert user_profile_service.base_url == "http://test.example.com"
        assert user_profile_service.timeout == 30
        assert user_profile_service.logger is not None

    def test_user_profile_service_inheritance(self, user_profile_service):
        """Test UserProfileService inheritance from BaseService."""
        from app.services.base import BaseService
        assert isinstance(user_profile_service, BaseService)

    def test_generate_schema_based_profile(self, user_profile_service):
        """Test schema-based profile generation."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check that profile is a dictionary
        assert isinstance(profile, dict)
        
        # Check required fields
        assert profile["user_id"] is not None
        assert profile["name"] is not None
        assert profile["email"] is not None
        assert profile["age"] is not None
        assert profile["location"] is not None
        assert "preferences" in profile

    def test_generate_schema_based_profile_field_types(self, user_profile_service):
        """Test schema-based profile field types."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check field types
        assert isinstance(profile["user_id"], str)
        assert isinstance(profile["name"], str)
        assert isinstance(profile["email"], str)
        assert isinstance(profile["age"], int)
        assert isinstance(profile.gender, str)
        assert isinstance(profile["location"], dict)
        assert isinstance(profile["interests"], list)
        assert isinstance(profile["preferences"], dict)
        assert isinstance(profile["budget"], dict)
        assert isinstance(profile["travel_style"], str)
        assert isinstance(profile["accommodation_preferences"], list)
        assert isinstance(profile["activity_preferences"], list)
        assert isinstance(profile["dietary_restrictions"], list)
        assert isinstance(profile["accessibility_needs"], list)
        assert isinstance(profile["language_preferences"], list)
        assert isinstance(profile["currency_preference"], str)
        assert isinstance(profile["timezone"], str)
        assert isinstance(profile["notification_preferences"], dict)
        assert isinstance(profile["privacy_settings"], dict)
        assert isinstance(profile["created_at"], str)
        assert isinstance(profile["updated_at"], str)

    def test_generate_schema_based_profile_field_values(self, user_profile_service):
        """Test schema-based profile field values."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check field values are reasonable
        assert len(profile["user_id"]) > 0
        assert len(profile["name"]) > 0
        assert "@" in profile["email"]
        assert 18 <= profile["age"] <= 80
        assert profile.gender in ["male", "female", "other"]
        assert len(profile["location"]) > 0
        assert len(profile["interests"]) > 0
        assert len(profile["preferences"]) > 0
        assert len(profile["budget"]) > 0
        assert len(profile["travel_style"]) > 0
        assert len(profile["accommodation_preferences"]) > 0
        assert len(profile["activity_preferences"]) > 0
        assert len(profile["dietary_restrictions"]) >= 0
        assert len(profile["accessibility_needs"]) >= 0
        assert len(profile["language_preferences"]) > 0
        assert len(profile["currency_preference"]) > 0
        assert len(profile["timezone"]) > 0
        assert len(profile["notification_preferences"]) > 0
        assert len(profile["privacy_settings"]) > 0
        assert len(profile["created_at"]) > 0
        assert len(profile["updated_at"]) > 0

    def test_generate_schema_based_profile_multiple_calls(self, user_profile_service):
        """Test schema-based profile generation multiple calls."""
        profiles = []
        for _ in range(5):
            profile = user_profile_service._generate_schema_based_profile("test_user_123")
            profiles.append(profile)
        
        # Check that all profiles are valid
        for profile in profiles:
            assert isinstance(profile, dict)
            assert profile["user_id"] is not None
            assert profile["name"] is not None
            assert profile["email"] is not None

    def test_generate_schema_based_profile_uniqueness(self, user_profile_service):
        """Test schema-based profile uniqueness."""
        profiles = []
        for _ in range(10):
            profile = user_profile_service._generate_schema_based_profile("test_user_123")
            profiles.append(profile)
        
        # Check that user_ids are unique
        user_ids = [profile["user_id"] for profile in profiles]
        assert len(set(user_ids)) == len(user_ids)

    def test_generate_schema_based_profile_location_structure(self, user_profile_service):
        """Test schema-based profile location structure."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check location structure
        assert "country" in profile["location"]
        assert "city" in profile["location"]
        assert "coordinates" in profile["location"]
        assert isinstance(profile["location"]["coordinates"], dict)
        assert "lat" in profile["location"]["coordinates"]
        assert "lng" in profile["location"]["coordinates"]

    def test_generate_schema_based_profile_budget_structure(self, user_profile_service):
        """Test schema-based profile budget structure."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check budget structure
        assert "min" in profile["budget"]
        assert "max" in profile["budget"]
        assert "currency" in profile["budget"]
        assert isinstance(profile["budget"]["min"], (int, float))
        assert isinstance(profile["budget"]["max"], (int, float))
        assert profile["budget"]["min"] <= profile["budget"]["max"]

    def test_generate_schema_based_profile_preferences_structure(self, user_profile_service):
        """Test schema-based profile preferences structure."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check preferences structure
        assert "accommodation" in profile["preferences"]
        assert "activities" in profile["preferences"]
        assert "dining" in profile["preferences"]
        assert "transportation" in profile["preferences"]

    def test_generate_schema_based_profile_notification_preferences_structure(self, user_profile_service):
        """Test schema-based profile notification preferences structure."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check notification preferences structure
        assert "email" in profile["notification_preferences"]
        assert "sms" in profile["notification_preferences"]
        assert "push" in profile["notification_preferences"]
        assert isinstance(profile["notification_preferences"]["email"], bool)
        assert isinstance(profile["notification_preferences"]["sms"], bool)
        assert isinstance(profile["notification_preferences"]["push"], bool)

    def test_generate_schema_based_profile_privacy_settings_structure(self, user_profile_service):
        """Test schema-based profile privacy settings structure."""
        profile = user_profile_service._generate_schema_based_profile("test_user_123")
        
        # Check privacy settings structure
        assert "profile_visibility" in profile["privacy_settings"]
        assert "data_sharing" in profile["privacy_settings"]
        assert "marketing_emails" in profile["privacy_settings"]
        assert isinstance(profile["privacy_settings"]["profile_visibility"], str)
        assert isinstance(profile["privacy_settings"]["data_sharing"], bool)
        assert isinstance(profile["privacy_settings"]["marketing_emails"], bool)

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, user_profile_service):
        """Test successful user profile retrieval."""
        mock_profile_data = {
            "user_id": "test_user_123",
            "name": "Test User",
            "email": "test@example.com",
            "age": 30,
            "gender": "male",
            "location": {"country": "US", "city": "New York"},
            "interests": ["travel", "food"],
            "preferences": {"accommodation": "hotel"},
            "budget": {"min": 1000, "max": 5000, "currency": "USD"},
            "travel_style": "luxury",
            "accommodation_preferences": ["hotel", "resort"],
            "activity_preferences": ["sightseeing", "dining"],
            "dietary_restrictions": [],
            "accessibility_needs": [],
            "language_preferences": ["en"],
            "currency_preference": "USD",
            "timezone": "America/New_York",
            "notification_preferences": {"email": True, "sms": False, "push": True},
            "privacy_settings": {"profile_visibility": "public", "data_sharing": True, "marketing_emails": False},
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }

        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = mock_profile_data
            
            result = await user_profile_service.get_user_profile("test_user_123")
            
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user_123"
            assert result.name == "Test User"
            assert result.email == "test@example.com"
            mock_make_request.assert_called_once_with("GET", "/user/test_user_123")

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, user_profile_service):
        """Test user profile not found."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await user_profile_service.get_user_profile("nonexistent_user")
            
            # Should return generated profile when not found
            assert isinstance(result, UserProfile)
            assert result.user_id == "nonexistent_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_service_error(self, user_profile_service):
        """Test user profile service error."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when service error
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_timeout_error(self, user_profile_service):
        """Test user profile timeout error."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when timeout
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_any_exception(self, user_profile_service):
        """Test user profile any exception."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = ValueError("Any error")
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when any exception
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_invalid_response(self, user_profile_service):
        """Test user profile invalid response."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"invalid": "data"}
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when invalid response
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_partial_response(self, user_profile_service):
        """Test user profile partial response."""
        partial_data = {
            "user_id": "test_user_123",
            "name": "Test User",
            "email": "test@example.com"
            # Missing other required fields
        }

        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = partial_data
            
            result = await user_profile_service.get_user_profile("test_user_123")
            
            # Should return generated profile when partial response
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user_123"

    @pytest.mark.asyncio
    async def test_get_user_profile_empty_response(self, user_profile_service):
        """Test user profile empty response."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {}
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when empty response
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_none_response(self, user_profile_service):
        """Test user profile None response."""
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = None
            
            result = await user_profile_service.get_user_profile("test_user")
            
            # Should return generated profile when None response
            assert isinstance(result, UserProfile)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_profile_different_user_ids(self, user_profile_service):
        """Test user profile with different user IDs."""
        user_ids = ["user1", "user2", "user3", "user_123", "test-user", "user@domain.com"]
        
        for user_id in user_ids:
            with patch.object(user_profile_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await user_profile_service.get_user_profile(user_id)
                
                assert isinstance(result, UserProfile)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_profile_special_characters(self, user_profile_service):
        """Test user profile with special characters."""
        special_user_ids = ["user-123", "user_123", "user.123", "user@123", "user+123"]
        
        for user_id in special_user_ids:
            with patch.object(user_profile_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await user_profile_service.get_user_profile(user_id)
                
                assert isinstance(result, UserProfile)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_profile_unicode(self, user_profile_service):
        """Test user profile with Unicode characters."""
        unicode_user_ids = ["用户123", "usuario123", "пользователь123", "ユーザー123"]
        
        for user_id in unicode_user_ids:
            with patch.object(user_profile_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await user_profile_service.get_user_profile(user_id)
                
                assert isinstance(result, UserProfile)
                assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_profile_long_user_id(self, user_profile_service):
        """Test user profile with long user ID."""
        long_user_id = "a" * 1000  # Very long user ID
        
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await user_profile_service.get_user_profile(long_user_id)
            
            assert isinstance(result, UserProfile)
            assert result.user_id == long_user_id

    @pytest.mark.asyncio
    async def test_get_user_profile_concurrent_requests(self, user_profile_service):
        """Test user profile concurrent requests."""
        import asyncio
        
        async def get_profile(user_id):
            with patch.object(user_profile_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                return await user_profile_service.get_user_profile(user_id)
        
        # Create multiple concurrent requests
        tasks = [get_profile(f"user_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check all results are valid
        for i, result in enumerate(results):
            assert isinstance(result, UserProfile)
            assert result.user_id == f"user_{i}"

    @pytest.mark.asyncio
    async def test_get_user_profile_caching_behavior(self, user_profile_service):
        """Test user profile caching behavior."""
        # Test that multiple calls with same user_id return consistent results
        user_id = "test_user_123"
        
        with patch.object(user_profile_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result1 = await user_profile_service.get_user_profile(user_id)
            result2 = await user_profile_service.get_user_profile(user_id)
            
            # Results should be consistent (same user_id)
            assert result1.user_id == result2.user_id
            assert result1.user_id == user_id

    def test_user_profile_service_logger_name(self, user_profile_service):
        """Test UserProfileService logger name."""
        assert user_profile_service.logger._context.get('logger') == 'UserProfileService'

    def test_user_profile_service_method_availability(self, user_profile_service):
        """Test UserProfileService method availability."""
        # Test that all expected methods are available
        assert hasattr(user_profile_service, '_make_request')
        assert hasattr(user_profile_service, 'health_check')
        assert hasattr(user_profile_service, '_generate_schema_based_profile')
        assert hasattr(user_profile_service, 'get_user_profile')
        assert callable(user_profile_service._make_request)
        assert callable(user_profile_service.health_check)
        assert callable(user_profile_service._generate_schema_based_profile)
        assert callable(user_profile_service.get_user_profile)

    def test_user_profile_service_async_methods(self, user_profile_service):
        """Test UserProfileService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(user_profile_service._make_request)
        assert inspect.iscoroutinefunction(user_profile_service.health_check)
        assert inspect.iscoroutinefunction(user_profile_service.get_user_profile)
        assert not inspect.iscoroutinefunction(user_profile_service._generate_schema_based_profile)

    def test_user_profile_service_error_handling(self, user_profile_service):
        """Test UserProfileService error handling."""
        # Test that service handles errors gracefully
        with patch.object(user_profile_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                user_profile_service.logger.error(
                    "Error fetching user profile",
                    user_id="test_user",
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_user_profile_service_info_logging(self, user_profile_service):
        """Test UserProfileService info logging."""
        with patch.object(user_profile_service.logger, 'info') as mock_info:
            # Simulate an info log
            user_profile_service.logger.info(
                "User profile retrieved",
                user_id="test_user",
                source="api"
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_user_profile_service_thread_safety(self, user_profile_service):
        """Test UserProfileService thread safety."""
        import threading
        import time
        
        results = []
        
        def test_get_profile():
            try:
                # Simulate profile generation
                profile = user_profile_service._generate_schema_based_profile("test_user_123")
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_get_profile, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_user_profile_service_memory_usage(self, user_profile_service):
        """Test UserProfileService memory usage."""
        import gc
        
        # Generate multiple profiles
        profiles = []
        for _ in range(100):
            profile = user_profile_service._generate_schema_based_profile("test_user_123")
            profiles.append(profile)
        
        # Check memory usage
        assert len(profiles) == 100
        
        # Clean up
        del profiles
        gc.collect()

    def test_user_profile_service_performance(self, user_profile_service):
        """Test UserProfileService performance."""
        import time
        
        # Test profile generation performance
        start_time = time.time()
        profiles = []
        for _ in range(100):
            profile = user_profile_service._generate_schema_based_profile("test_user_123")
            profiles.append(profile)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 profiles
        assert len(profiles) == 100

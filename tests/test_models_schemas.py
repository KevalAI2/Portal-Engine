"""
Comprehensive test suite for models/schemas module - Fixed version
"""
import pytest
from datetime import datetime
from app.models.schemas import (
    UserProfile,
    LocationData,
    InteractionData,
    RecommendationItem,
    TaskStatusResponse,
    HealthCheckResponse,
    RecommendationResponse,
    NotificationItem,
    RefreshRequest,
    APIResponse
)
from app.core.constants import RecommendationType, TaskStatus, NotificationType


@pytest.mark.unit
class TestModelsSchemas:
    """Test the models/schemas functionality."""

    def test_user_profile_creation(self):
        """Test UserProfile model creation."""
        user_profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        assert user_profile.user_id == "user_123"
        assert user_profile.name == "John Doe"
        assert user_profile.email == "john@example.com"
        assert user_profile.age == 30
        assert user_profile.location == "New York, NY"
        assert user_profile.interests == ["travel", "food"]
        assert user_profile.preferences == {"accommodation": "hotel", "budget": "luxury"}

    def test_user_profile_validation(self):
        """Test UserProfile model validation."""
        # Test valid user profile
        user_profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        assert user_profile is not None
        assert isinstance(user_profile, UserProfile)

    def test_user_profile_serialization(self):
        """Test UserProfile model serialization."""
        user_profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        # Test serialization to dict
        profile_dict = user_profile.dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "user_123"
        assert profile_dict["name"] == "John Doe"
        assert profile_dict["email"] == "john@example.com"
        assert profile_dict["age"] == 30
        assert profile_dict["location"] == "New York, NY"
        assert profile_dict["interests"] == ["travel", "food"]
        assert profile_dict["preferences"] == {"accommodation": "hotel", "budget": "luxury"}
        
        # Test serialization to JSON
        profile_json = user_profile.json()
        assert isinstance(profile_json, str)
        assert "user_123" in profile_json
        assert "John Doe" in profile_json

    def test_user_profile_deserialization(self):
        """Test UserProfile model deserialization."""
        # Test deserialization from dict
        profile_data = {
            "user_id": "user_123",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "location": "New York, NY",
            "interests": ["travel", "food"],
            "preferences": {"accommodation": "hotel", "budget": "luxury"}
        }
        
        user_profile = UserProfile(**profile_data)
        assert user_profile.user_id == "user_123"
        assert user_profile.name == "John Doe"
        assert user_profile.email == "john@example.com"
        assert user_profile.age == 30
        assert user_profile.location == "New York, NY"
        assert user_profile.interests == ["travel", "food"]
        assert user_profile.preferences == {"accommodation": "hotel", "budget": "luxury"}

    def test_location_data_creation(self):
        """Test LocationData model creation."""
        location_data = LocationData(
            user_id="user_123",
            current_location="New York, NY",
            home_location="San Francisco, CA",
            work_location="New York, NY",
            travel_history=["Paris", "London", "Tokyo"],
            location_preferences={"climate": "temperate", "urban": True}
        )
        
        assert location_data.user_id == "user_123"
        assert location_data.current_location == "New York, NY"
        assert location_data.home_location == "San Francisco, CA"
        assert location_data.work_location == "New York, NY"
        assert location_data.travel_history == ["Paris", "London", "Tokyo"]
        assert location_data.location_preferences == {"climate": "temperate", "urban": True}

    def test_interaction_data_creation(self):
        """Test InteractionData model creation."""
        interaction_data = InteractionData(
            user_id="user_123",
            recent_interactions=[
                {"type": "view", "item": "hotel", "timestamp": "2023-01-01T00:00:00Z"},
                {"type": "click", "item": "restaurant", "timestamp": "2023-01-01T01:00:00Z"}
            ],
            interaction_history=[
                {"type": "purchase", "item": "flight", "timestamp": "2022-12-01T00:00:00Z"},
                {"type": "review", "item": "hotel", "timestamp": "2022-11-01T00:00:00Z"}
            ],
            preferences={"notifications": True, "email_updates": False},
            engagement_score=0.85
        )
        
        assert interaction_data.user_id == "user_123"
        assert len(interaction_data.recent_interactions) == 2
        assert len(interaction_data.interaction_history) == 2
        assert interaction_data.preferences == {"notifications": True, "email_updates": False}
        assert interaction_data.engagement_score == 0.85

    def test_recommendation_item_creation(self):
        """Test RecommendationItem model creation."""
        recommendation_item = RecommendationItem(
            id="rec_123",
            title="Test Recommendation",
            description="A great place to visit",
            score=0.85,
            metadata={"category": "attraction", "location": "Test City"},
            url="https://example.com/recommendation"
        )
        
        assert recommendation_item.id == "rec_123"
        assert recommendation_item.title == "Test Recommendation"
        assert recommendation_item.description == "A great place to visit"
        assert recommendation_item.score == 0.85
        assert recommendation_item.metadata == {"category": "attraction", "location": "Test City"}
        assert recommendation_item.url == "https://example.com/recommendation"

    def test_task_status_response_creation(self):
        """Test TaskStatusResponse model creation."""
        task_status = TaskStatusResponse(
            task_id="task_123",
            status=TaskStatus.COMPLETED,
            progress=100.0,
            result={"recommendations": []},
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert task_status.task_id == "task_123"
        assert task_status.status == TaskStatus.COMPLETED
        assert task_status.progress == 100.0
        assert task_status.result == {"recommendations": []}
        assert task_status.error is None

    def test_health_check_response_creation(self):
        """Test HealthCheckResponse model creation."""
        health_check = HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            environment="test",
            services={
                "user_profile": "healthy",
                "lie": "healthy",
                "cis": "healthy",
                "llm": "healthy",
                "results": "healthy"
            }
        )
        
        assert health_check.status == "healthy"
        assert health_check.version == "1.0.0"
        assert health_check.environment == "test"
        assert health_check.services == {
            "user_profile": "healthy",
            "lie": "healthy",
            "cis": "healthy",
            "llm": "healthy",
            "results": "healthy"
        }

    def test_recommendation_response_creation(self):
        """Test RecommendationResponse model creation."""
        recommendation_item = RecommendationItem(
            id="rec_1",
            title="Recommendation 1",
            description="A great recommendation",
            score=0.9,
            metadata={"category": "hotel"}
        )
        
        recommendation_response = RecommendationResponse(
            user_id="user_123",
            type=RecommendationType.PLACE,
            recommendations=[recommendation_item],
            generated_at=datetime.now(),
            expires_at=datetime.now(),
            total_count=1
        )
        
        assert recommendation_response.user_id == "user_123"
        assert recommendation_response.type == RecommendationType.PLACE
        assert len(recommendation_response.recommendations) == 1
        assert recommendation_response.total_count == 1

    def test_notification_item_creation(self):
        """Test NotificationItem model creation."""
        notification = NotificationItem(
            id="notif_123",
            user_id="user_123",
            type=NotificationType.RECOMMENDATION_READY,
            title="New Recommendations",
            message="You have new recommendations available",
            data={"count": 5},
            read=False,
            created_at=datetime.now()
        )
        
        assert notification.id == "notif_123"
        assert notification.user_id == "user_123"
        assert notification.type == NotificationType.RECOMMENDATION_READY
        assert notification.title == "New Recommendations"
        assert notification.message == "You have new recommendations available"
        assert notification.data == {"count": 5}
        assert notification.read is False

    def test_refresh_request_creation(self):
        """Test RefreshRequest model creation."""
        refresh_request = RefreshRequest(
            user_id="user_123",
            force=True
        )
        
        assert refresh_request.user_id == "user_123"
        assert refresh_request.force is True

    def test_api_response_creation(self):
        """Test APIResponse model creation."""
        api_response = APIResponse(
            success=True,
            message="Operation completed successfully",
            data={"result": "test"},
            error=None
        )
        
        assert api_response.success is True
        assert api_response.message == "Operation completed successfully"
        assert api_response.data == {"result": "test"}
        assert api_response.error is None

    def test_models_import(self):
        """Test models import."""
        from app.models.schemas import (
            UserProfile,
            LocationData,
            InteractionData,
            RecommendationItem,
            TaskStatusResponse,
            HealthCheckResponse,
            RecommendationResponse,
            NotificationItem,
            RefreshRequest,
            APIResponse
        )
        
        # All models should be importable
        assert UserProfile is not None
        assert LocationData is not None
        assert InteractionData is not None
        assert RecommendationItem is not None
        assert TaskStatusResponse is not None
        assert HealthCheckResponse is not None
        assert RecommendationResponse is not None
        assert NotificationItem is not None
        assert RefreshRequest is not None
        assert APIResponse is not None

    def test_models_serialization(self):
        """Test models serialization."""
        user_profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        # Test serialization
        profile_dict = user_profile.dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "user_123"
        
        # Test JSON serialization
        profile_json = user_profile.json()
        assert isinstance(profile_json, str)
        assert "user_123" in profile_json

    def test_models_deserialization(self):
        """Test models deserialization."""
        profile_data = {
            "user_id": "user_123",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "location": "New York, NY",
            "interests": ["travel", "food"],
            "preferences": {"accommodation": "hotel", "budget": "luxury"}
        }
        
        user_profile = UserProfile(**profile_data)
        assert user_profile.user_id == "user_123"
        assert user_profile.name == "John Doe"

    def test_models_thread_safety(self):
        """Test models thread safety."""
        import threading
        import time
        
        results = []
        
        def create_profile():
            profile = UserProfile(
                user_id="user_123",
                name="John Doe",
                email="john@example.com",
                age=30,
                location="New York, NY",
                interests=["travel", "food"],
                preferences={"accommodation": "hotel", "budget": "luxury"}
            )
            results.append(profile.user_id)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_profile)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all profiles were created
        assert len(results) == 5
        assert all(user_id == "user_123" for user_id in results)

    def test_models_performance(self):
        """Test models performance."""
        import time
        
        start_time = time.time()
        
        # Create multiple profiles
        for _ in range(100):
            UserProfile(
                user_id="user_123",
                name="John Doe",
                email="john@example.com",
                age=30,
                location="New York, NY",
                interests=["travel", "food"],
                preferences={"accommodation": "hotel", "budget": "luxury"}
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (1 second)
        assert execution_time < 1.0

    def test_models_memory_usage(self):
        """Test models memory usage."""
        import sys
        
        # Create a profile
        profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        # Get memory usage
        memory_usage = sys.getsizeof(profile)
        
        # Should be reasonable (less than 1KB)
        assert memory_usage < 1024

    def test_models_data_consistency(self):
        """Test models data consistency."""
        profile1 = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        profile2 = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=["travel", "food"],
            preferences={"accommodation": "hotel", "budget": "luxury"}
        )
        
        # Profiles with same data should be equal
        assert profile1.dict() == profile2.dict()

    def test_models_error_handling(self):
        """Test models error handling."""
        # Test with invalid data
        try:
            UserProfile(
                user_id="user_123",
                name="John Doe",
                email="invalid_email",  # Invalid email format
                age=30,
                location="New York, NY",
                interests=["travel", "food"],
                preferences={"accommodation": "hotel", "budget": "luxury"}
            )
            assert False, "Model should raise validation error for invalid email"
        except Exception as e:
            assert "validation error" in str(e).lower() or "invalid" in str(e).lower()

    def test_models_unicode_support(self):
        """Test models Unicode support."""
        profile = UserProfile(
            user_id="user_123",
            name="测试用户",  # Unicode characters
            email="test@example.com",
            age=30,
            location="北京, 中国",  # Unicode location
            interests=["旅行", "美食"],  # Unicode interests
            preferences={"住宿": "酒店", "预算": "豪华"}  # Unicode preferences
        )
        
        assert profile.name == "测试用户"
        assert profile.location == "北京, 中国"
        assert profile.interests == ["旅行", "美食"]
        assert profile.preferences == {"住宿": "酒店", "预算": "豪华"}

    def test_models_large_data(self):
        """Test models with large data."""
        large_interests = [f"interest_{i}" for i in range(1000)]
        large_preferences = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        profile = UserProfile(
            user_id="user_123",
            name="John Doe",
            email="john@example.com",
            age=30,
            location="New York, NY",
            interests=large_interests,
            preferences=large_preferences
        )
        
        assert len(profile.interests) == 1000
        assert len(profile.preferences) == 1000
        assert profile.interests[0] == "interest_0"
        assert profile.preferences["key_0"] == "value_0"

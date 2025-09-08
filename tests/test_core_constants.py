"""
Comprehensive test suite for core constants module
"""
import pytest
from app.core.constants import (
    RecommendationType, TaskStatus, NotificationType,
    REDIS_KEY_PATTERNS, CACHE_TTL, API_MESSAGES, SUPPORTED_RECOMMENDATION_TYPES
)


@pytest.mark.unit
class TestCoreConstants:
    """Test the core constants functionality."""

    def test_recommendation_type_enum(self):
        """Test RecommendationType enum values."""
        assert RecommendationType.MUSIC == "music"
        assert RecommendationType.MOVIE == "movie"
        assert RecommendationType.PLACE == "place"
        assert RecommendationType.EVENT == "event"

    def test_recommendation_type_enum_values(self):
        """Test RecommendationType enum values are strings."""
        for rec_type in RecommendationType:
            assert isinstance(rec_type.value, str)
            assert len(rec_type.value) > 0

    def test_recommendation_type_enum_membership(self):
        """Test RecommendationType enum membership."""
        assert "music" in [rt.value for rt in RecommendationType]
        assert "movie" in [rt.value for rt in RecommendationType]
        assert "place" in [rt.value for rt in RecommendationType]
        assert "event" in [rt.value for rt in RecommendationType]

    def test_recommendation_type_enum_iteration(self):
        """Test RecommendationType enum iteration."""
        types = list(RecommendationType)
        assert len(types) == 4
        assert RecommendationType.MUSIC in types
        assert RecommendationType.MOVIE in types
        assert RecommendationType.PLACE in types
        assert RecommendationType.EVENT in types

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_task_status_enum_values(self):
        """Test TaskStatus enum values are strings."""
        for status in TaskStatus:
            assert isinstance(status.value, str)
            assert len(status.value) > 0

    def test_task_status_enum_membership(self):
        """Test TaskStatus enum membership."""
        assert "pending" in [ts.value for ts in TaskStatus]
        assert "running" in [ts.value for ts in TaskStatus]
        assert "completed" in [ts.value for ts in TaskStatus]
        assert "failed" in [ts.value for ts in TaskStatus]

    def test_task_status_enum_iteration(self):
        """Test TaskStatus enum iteration."""
        statuses = list(TaskStatus)
        assert len(statuses) == 4
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.RUNNING in statuses
        assert TaskStatus.COMPLETED in statuses
        assert TaskStatus.FAILED in statuses

    def test_notification_type_enum(self):
        """Test NotificationType enum values."""
        assert NotificationType.RECOMMENDATION_READY == "recommendation_ready"
        assert NotificationType.TASK_COMPLETED == "task_completed"
        assert NotificationType.TASK_FAILED == "task_failed"
        assert NotificationType.SYSTEM_ALERT == "system_alert"

    def test_notification_type_enum_values(self):
        """Test NotificationType enum values are strings."""
        for notif_type in NotificationType:
            assert isinstance(notif_type.value, str)
            assert len(notif_type.value) > 0

    def test_notification_type_enum_membership(self):
        """Test NotificationType enum membership."""
        assert "recommendation_ready" in [nt.value for nt in NotificationType]
        assert "task_completed" in [nt.value for nt in NotificationType]
        assert "task_failed" in [nt.value for nt in NotificationType]
        assert "system_alert" in [nt.value for nt in NotificationType]

    def test_notification_type_enum_iteration(self):
        """Test NotificationType enum iteration."""
        types = list(NotificationType)
        assert len(types) == 4
        assert NotificationType.RECOMMENDATION_READY in types
        assert NotificationType.TASK_COMPLETED in types
        assert NotificationType.TASK_FAILED in types
        assert NotificationType.SYSTEM_ALERT in types

    def test_redis_key_patterns_structure(self):
        """Test REDIS_KEY_PATTERNS structure."""
        assert isinstance(REDIS_KEY_PATTERNS, dict)
        assert len(REDIS_KEY_PATTERNS) > 0

    def test_redis_key_patterns_keys(self):
        """Test REDIS_KEY_PATTERNS keys."""
        expected_keys = ["recommendation", "task_status", "notification", "user_data"]
        for key in expected_keys:
            assert key in REDIS_KEY_PATTERNS

    def test_redis_key_patterns_values(self):
        """Test REDIS_KEY_PATTERNS values."""
        for key, pattern in REDIS_KEY_PATTERNS.items():
            assert isinstance(pattern, str)
            assert "{namespace}" in pattern
            assert "{user_id}" in pattern or "{task_id}" in pattern

    def test_redis_key_patterns_formatting(self):
        """Test REDIS_KEY_PATTERNS formatting."""
        # Test recommendation pattern
        rec_pattern = REDIS_KEY_PATTERNS["recommendation"]
        formatted = rec_pattern.format(namespace="test", user_id="user1", type="movies")
        assert formatted == "test:user1:movies"

        # Test task_status pattern
        task_pattern = REDIS_KEY_PATTERNS["task_status"]
        formatted = task_pattern.format(namespace="test", task_id="task123")
        assert formatted == "test:task:task123"

        # Test notification pattern
        notif_pattern = REDIS_KEY_PATTERNS["notification"]
        formatted = notif_pattern.format(namespace="test", user_id="user1")
        assert formatted == "test:notification:user1"

        # Test user_data pattern
        user_pattern = REDIS_KEY_PATTERNS["user_data"]
        formatted = user_pattern.format(namespace="test", user_id="user1")
        assert formatted == "test:user_data:user1"

    def test_cache_ttl_structure(self):
        """Test CACHE_TTL structure."""
        assert isinstance(CACHE_TTL, dict)
        assert len(CACHE_TTL) > 0

    def test_cache_ttl_keys(self):
        """Test CACHE_TTL keys."""
        expected_keys = ["recommendation", "user_data", "task_status", "notification"]
        for key in expected_keys:
            assert key in CACHE_TTL

    def test_cache_ttl_values(self):
        """Test CACHE_TTL values."""
        for key, ttl in CACHE_TTL.items():
            assert isinstance(ttl, int)
            assert ttl > 0

    def test_cache_ttl_reasonable_values(self):
        """Test CACHE_TTL reasonable values."""
        # Recommendation cache should be reasonable (1 hour)
        assert CACHE_TTL["recommendation"] == 3600
        
        # User data cache should be shorter (30 minutes)
        assert CACHE_TTL["user_data"] == 1800
        
        # Task status cache should be longer (2 hours)
        assert CACHE_TTL["task_status"] == 7200
        
        # Notification cache should be longest (24 hours)
        assert CACHE_TTL["notification"] == 86400

    def test_api_messages_structure(self):
        """Test API_MESSAGES structure."""
        assert isinstance(API_MESSAGES, dict)
        assert len(API_MESSAGES) > 0

    def test_api_messages_keys(self):
        """Test API_MESSAGES keys."""
        expected_keys = [
            "recommendation_not_found", "user_not_found", "task_triggered",
            "invalid_recommendation_type", "service_unavailable"
        ]
        for key in expected_keys:
            assert key in API_MESSAGES

    def test_api_messages_values(self):
        """Test API_MESSAGES values."""
        for key, message in API_MESSAGES.items():
            assert isinstance(message, str)
            assert len(message) > 0

    def test_api_messages_content(self):
        """Test API_MESSAGES content."""
        assert "not found" in API_MESSAGES["recommendation_not_found"].lower()
        assert "not found" in API_MESSAGES["user_not_found"].lower()
        assert "triggered" in API_MESSAGES["task_triggered"].lower()
        assert "invalid" in API_MESSAGES["invalid_recommendation_type"].lower()
        assert "unavailable" in API_MESSAGES["service_unavailable"].lower()

    def test_supported_recommendation_types_structure(self):
        """Test SUPPORTED_RECOMMENDATION_TYPES structure."""
        assert isinstance(SUPPORTED_RECOMMENDATION_TYPES, list)
        assert len(SUPPORTED_RECOMMENDATION_TYPES) > 0

    def test_supported_recommendation_types_values(self):
        """Test SUPPORTED_RECOMMENDATION_TYPES values."""
        for rec_type in SUPPORTED_RECOMMENDATION_TYPES:
            assert isinstance(rec_type, str)
            assert rec_type in [rt.value for rt in RecommendationType]

    def test_supported_recommendation_types_completeness(self):
        """Test SUPPORTED_RECOMMENDATION_TYPES completeness."""
        enum_values = [rt.value for rt in RecommendationType]
        for enum_value in enum_values:
            assert enum_value in SUPPORTED_RECOMMENDATION_TYPES

    def test_supported_recommendation_types_no_duplicates(self):
        """Test SUPPORTED_RECOMMENDATION_TYPES has no duplicates."""
        assert len(SUPPORTED_RECOMMENDATION_TYPES) == len(set(SUPPORTED_RECOMMENDATION_TYPES))

    def test_enum_inheritance(self):
        """Test enum inheritance."""
        # All enums should inherit from str and Enum
        assert issubclass(RecommendationType, str)
        assert issubclass(TaskStatus, str)
        assert issubclass(NotificationType, str)

    def test_enum_comparison(self):
        """Test enum comparison."""
        # Test equality
        assert RecommendationType.MUSIC == "music"
        assert TaskStatus.PENDING == "pending"
        assert NotificationType.RECOMMENDATION_READY == "recommendation_ready"

        # Test inequality
        assert RecommendationType.MUSIC != "movie"
        assert TaskStatus.PENDING != "running"
        assert NotificationType.RECOMMENDATION_READY != "task_completed"

    def test_enum_string_representation(self):
        """Test enum string representation."""
        assert str(RecommendationType.MUSIC) == "music"
        assert str(TaskStatus.PENDING) == "pending"
        assert str(NotificationType.RECOMMENDATION_READY) == "recommendation_ready"

    def test_enum_repr(self):
        """Test enum representation."""
        assert repr(RecommendationType.MUSIC) == "<RecommendationType.MUSIC: 'music'>"
        assert repr(TaskStatus.PENDING) == "<TaskStatus.PENDING: 'pending'>"
        assert repr(NotificationType.RECOMMENDATION_READY) == "<NotificationType.RECOMMENDATION_READY: 'recommendation_ready'>"

    def test_enum_hash(self):
        """Test enum hash."""
        # Enums should be hashable
        assert hash(RecommendationType.MUSIC) is not None
        assert hash(TaskStatus.PENDING) is not None
        assert hash(NotificationType.RECOMMENDATION_READY) is not None

    def test_enum_membership_test(self):
        """Test enum membership."""
        assert "music" in RecommendationType
        assert "movie" in RecommendationType
        assert "place" in RecommendationType
        assert "event" in RecommendationType

        assert "pending" in TaskStatus
        assert "running" in TaskStatus
        assert "completed" in TaskStatus
        assert "failed" in TaskStatus

        assert "recommendation_ready" in NotificationType
        assert "task_completed" in NotificationType
        assert "task_failed" in NotificationType
        assert "system_alert" in NotificationType

    def test_enum_value_access(self):
        """Test enum value access."""
        assert RecommendationType.MUSIC.value == "music"
        assert TaskStatus.PENDING.value == "pending"
        assert NotificationType.RECOMMENDATION_READY.value == "recommendation_ready"

    def test_enum_name_access(self):
        """Test enum name access."""
        assert RecommendationType.MUSIC.name == "MUSIC"
        assert TaskStatus.PENDING.name == "PENDING"
        assert NotificationType.RECOMMENDATION_READY.name == "RECOMMENDATION_READY"

    def test_constants_immutability(self):
        """Test constants immutability."""
        # Test that constants are properly defined and accessible
        assert REDIS_KEY_PATTERNS is not None
        assert CACHE_TTL is not None
        assert API_MESSAGES is not None
        assert SUPPORTED_RECOMMENDATION_TYPES is not None

    def test_constants_type_consistency(self):
        """Test constants type consistency."""
        # Test that all constants have expected types
        assert isinstance(REDIS_KEY_PATTERNS, dict)
        assert isinstance(CACHE_TTL, dict)
        assert isinstance(API_MESSAGES, dict)
        assert isinstance(SUPPORTED_RECOMMENDATION_TYPES, list)

    def test_constants_content_validation(self):
        """Test constants content validation."""
        # Test that constants contain expected content
        assert len(REDIS_KEY_PATTERNS) >= 4
        assert len(CACHE_TTL) >= 4
        assert len(API_MESSAGES) >= 5
        assert len(SUPPORTED_RECOMMENDATION_TYPES) >= 4

    def test_enum_ordering(self):
        """Test enum ordering."""
        # Test that enums can be ordered
        rec_types = list(RecommendationType)
        assert rec_types[0] == RecommendationType.MUSIC
        assert rec_types[1] == RecommendationType.MOVIE
        assert rec_types[2] == RecommendationType.PLACE
        assert rec_types[3] == RecommendationType.EVENT

    def test_enum_iteration_order(self):
        """Test enum iteration order."""
        rec_types = [rt.value for rt in RecommendationType]
        expected_order = ["music", "movie", "place", "event"]
        assert rec_types == expected_order

    def test_constants_import(self):
        """Test constants import."""
        # Test that all constants can be imported
        from app.core.constants import (
            RecommendationType, TaskStatus, NotificationType,
            REDIS_KEY_PATTERNS, CACHE_TTL, API_MESSAGES, SUPPORTED_RECOMMENDATION_TYPES
        )
        
        assert RecommendationType is not None
        assert TaskStatus is not None
        assert NotificationType is not None
        assert REDIS_KEY_PATTERNS is not None
        assert CACHE_TTL is not None
        assert API_MESSAGES is not None
        assert SUPPORTED_RECOMMENDATION_TYPES is not None

    def test_enum_case_sensitivity(self):
        """Test enum case sensitivity."""
        # Test that enum values are case sensitive
        assert RecommendationType.MUSIC == "music"
        assert RecommendationType.MUSIC != "Music"
        assert RecommendationType.MUSIC != "MUSIC"

    def test_enum_equality_with_strings(self):
        """Test enum equality with strings."""
        # Test that enums can be compared with strings
        assert RecommendationType.MUSIC == "music"
        assert "music" == RecommendationType.MUSIC
        assert RecommendationType.MUSIC != "movie"
        assert "movie" != RecommendationType.MUSIC

    def test_enum_in_operator(self):
        """Test enum in operator."""
        # Test that enums can be used with 'in' operator
        assert RecommendationType.MUSIC in RecommendationType
        assert "music" in RecommendationType
        assert "invalid" not in RecommendationType

    def test_constants_usage_examples(self):
        """Test constants usage examples."""
        # Test practical usage examples
        user_id = "user123"
        namespace = "test"
        
        # Test Redis key pattern usage
        rec_key = REDIS_KEY_PATTERNS["recommendation"].format(
            namespace=namespace, user_id=user_id, type="movies"
        )
        assert rec_key == "test:user123:movies"
        
        # Test cache TTL usage
        rec_ttl = CACHE_TTL["recommendation"]
        assert rec_ttl == 3600
        
        # Test API message usage
        not_found_msg = API_MESSAGES["user_not_found"]
        assert "not found" in not_found_msg.lower()
        
        # Test supported types usage
        assert "music" in SUPPORTED_RECOMMENDATION_TYPES
        assert "movies" not in SUPPORTED_RECOMMENDATION_TYPES  # Should be "movie"

    def test_enum_serialization(self):
        """Test enum serialization."""
        # Test that enums can be serialized
        import json
        
        rec_type = RecommendationType.MUSIC
        serialized = json.dumps(rec_type)
        assert serialized == '"music"'
        
        # Test deserialization
        deserialized = json.loads(serialized)
        assert deserialized == "music"

    def test_constants_module_structure(self):
        """Test constants module structure."""
        import app.core.constants as constants
        
        # Test that module has expected attributes
        assert hasattr(constants, 'RecommendationType')
        assert hasattr(constants, 'TaskStatus')
        assert hasattr(constants, 'NotificationType')
        assert hasattr(constants, 'REDIS_KEY_PATTERNS')
        assert hasattr(constants, 'CACHE_TTL')
        assert hasattr(constants, 'API_MESSAGES')
        assert hasattr(constants, 'SUPPORTED_RECOMMENDATION_TYPES')

"""
Constants and enums for Portal Engine
"""
from enum import Enum, EnumMeta
from typing import List


class StrEnumMeta(EnumMeta):
    """Custom EnumMeta to allow membership test with strings"""
    def __contains__(cls, item):
        if isinstance(item, str):
            return item in cls._value2member_map_
        return super().__contains__(item)


class RecommendationType(str, Enum, metaclass=StrEnumMeta):
    """Types of recommendations supported by the system"""
    MUSIC = "music"
    MOVIE = "movie"
    PLACE = "place"
    EVENT = "event"

    def __str__(self):
        return self.value


class TaskStatus(str, Enum, metaclass=StrEnumMeta):
    """Status of background tasks"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    def __str__(self):
        return self.value


class NotificationType(str, Enum, metaclass=StrEnumMeta):
    """Types of notifications"""
    RECOMMENDATION_READY = "recommendation_ready"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SYSTEM_ALERT = "system_alert"

    def __str__(self):
        return self.value


# Redis key patterns
REDIS_KEY_PATTERNS = {
    "recommendation": "{namespace}:{user_id}:{type}",
    "task_status": "{namespace}:task:{task_id}",
    "notification": "{namespace}:notification:{user_id}",
    "user_data": "{namespace}:user_data:{user_id}",
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    "recommendation": 3600,  # 1 hour
    "user_data": 1800,       # 30 minutes
    "task_status": 7200,     # 2 hours
    "notification": 86400,   # 24 hours
}

# API Response Messages
API_MESSAGES = {
    "recommendation_not_found": "Recommendation not found for the specified type",
    "user_not_found": "User not found",
    "task_triggered": "Recommendation refresh task triggered successfully",
    "invalid_recommendation_type": "Invalid recommendation type",
    "service_unavailable": "Service temporarily unavailable",
}

# Supported recommendation types (auto-generated to avoid drift)
SUPPORTED_RECOMMENDATION_TYPES: List[str] = [e for e in RecommendationType]

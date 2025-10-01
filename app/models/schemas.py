"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.constants import RecommendationType, TaskStatus, NotificationType


class UserProfile(BaseModel):
    """User profile data from User Profile Service"""
    user_id: str = Field(..., description="Unique user identifier", min_length=1, max_length=100)
    name: str = Field(..., description="User's full name", min_length=1, max_length=200)
    email: str = Field(..., description="User's email address", min_length=5, max_length=254)
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    interests: List[str] = Field(default_factory=list, description="User interests", max_length=50)
    age: Optional[int] = Field(None, description="User's age", ge=0, le=120)
    location: Optional[str] = Field(None, description="User's location", max_length=200)

    # Pydantic v2 config to prevent recursion
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    @field_validator('email')
    @classmethod
    def _validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('age')
    @classmethod
    def _validate_age(cls, v):
        if v is None:
            return v
        if not isinstance(v, int) or v < 0 or v > 120:
            raise ValueError('age must be an integer between 0 and 120')
        return v

    @field_validator('interests')
    @classmethod
    def _validate_interests(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 interests allowed')
        return [interest.strip() for interest in v if interest.strip()]


class LocationData(BaseModel):
    """Location data from LIE (Location Information Engine) Service"""
    user_id: str = Field(..., description="Unique user identifier", min_length=1, max_length=100)
    current_location: Optional[str] = Field(None, description="Current location", max_length=200)
    home_location: Optional[str] = Field(None, description="Home location", max_length=200)
    work_location: Optional[str] = Field(None, description="Work location", max_length=200)
    travel_history: List[str] = Field(default_factory=list, description="Travel history", max_length=50)
    location_preferences: Dict[str, Any] = Field(default_factory=dict, description="Location preferences")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    @field_validator('travel_history')
    @classmethod
    def _validate_travel_history(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 travel history entries allowed')
        return [location.strip() for location in v if location.strip()]

    @field_validator('current_location', 'home_location', 'work_location')
    @classmethod
    def _validate_location(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class InteractionData(BaseModel):
    """Interaction data from CIS (Customer Interaction Service)"""
    user_id: str = Field(..., description="Unique user identifier", min_length=1, max_length=100)
    recent_interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Recent interactions", max_length=100)
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list, description="Interaction history", max_length=1000)
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Interaction preferences")
    engagement_score: Optional[float] = Field(None, description="User engagement score", ge=0.0, le=1.0)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    @field_validator('engagement_score')
    @classmethod
    def _validate_engagement(cls, v):
        if v is None:
            return v
        if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
            raise ValueError('engagement_score must be between 0.0 and 1.0')
        return float(v)

    @field_validator('recent_interactions')
    @classmethod
    def _validate_recent_interactions(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 recent interactions allowed')
        return v

    @field_validator('interaction_history')
    @classmethod
    def _validate_interaction_history(cls, v):
        if len(v) > 1000:
            raise ValueError('Maximum 1000 interaction history entries allowed')
        return v


class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    id: str = Field(..., description="Unique recommendation identifier", min_length=1, max_length=100)
    title: str = Field(..., description="Recommendation title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Recommendation description", max_length=1000)
    score: float = Field(..., description="Recommendation score/confidence", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    url: Optional[str] = Field(None, description="URL to the recommendation", max_length=500)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    @field_validator('url')
    @classmethod
    def _validate_url(cls, v):
        if v is not None:
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError('Invalid URL format')
        return v


class RecommendationResponse(BaseModel):
    """Recommendation response from cache"""
    user_id: str = Field(..., description="User identifier")
    type: RecommendationType = Field(..., description="Type of recommendation")
    recommendations: List[RecommendationItem] = Field(..., description="List of recommendations")
    generated_at: datetime = Field(..., description="When recommendations were generated")
    expires_at: datetime = Field(..., description="When recommendations expire")
    total_count: int = Field(..., description="Total number of recommendations")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[float] = Field(None, description="Task progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="When task was created")
    updated_at: datetime = Field(..., description="When task was last updated")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class NotificationItem(BaseModel):
    """Notification item"""
    id: str = Field(..., description="Notification identifier")
    user_id: str = Field(..., description="User identifier")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional notification data")
    read: bool = Field(default=False, description="Whether notification has been read")
    created_at: datetime = Field(..., description="When notification was created")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class RefreshRequest(BaseModel):
    """Request to refresh recommendations for a user"""
    user_id: str = Field(..., description="User identifier to refresh recommendations for")
    force: bool = Field(default=False, description="Force refresh even if recent data exists")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, str] = Field(..., description="Status of dependent services")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# Safe serialization methods to prevent recursion
def safe_model_dump(model_instance, **kwargs):
    """Safely convert Pydantic model to dict to prevent recursion"""
    if hasattr(model_instance, 'model_dump'):
        return model_instance.model_dump(**kwargs)
    elif hasattr(model_instance, 'dict'):
        return model_instance.dict(**kwargs)
    return model_instance


# Add safe dump methods to all models
for model_class in [
    UserProfile, LocationData, InteractionData, RecommendationItem,
    RecommendationResponse, TaskStatusResponse, NotificationItem,
    RefreshRequest, APIResponse, HealthCheckResponse
]:
    if hasattr(model_class, 'model_dump'):
        model_class.safe_dump = lambda self, **kwargs: safe_model_dump(self, **kwargs)
    else:
        model_class.safe_dump = lambda self, **kwargs: safe_model_dump(self, **kwargs)
"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import RecommendationType, TaskStatus, NotificationType


class UserProfile(BaseModel):
    """User profile data from User Profile Service"""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    interests: List[str] = Field(default_factory=list, description="User interests")
    age: Optional[int] = Field(None, description="User's age")
    location: Optional[str] = Field(None, description="User's location")

    # Pydantic v2 config to prevent recursion
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class LocationData(BaseModel):
    """Location data from LIE (Location Information Engine) Service"""
    user_id: str = Field(..., description="Unique user identifier")
    current_location: Optional[str] = Field(None, description="Current location")
    home_location: Optional[str] = Field(None, description="Home location")
    work_location: Optional[str] = Field(None, description="Work location")
    travel_history: List[str] = Field(default_factory=list, description="Travel history")
    location_preferences: Dict[str, Any] = Field(default_factory=dict, description="Location preferences")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class InteractionData(BaseModel):
    """Interaction data from CIS (Customer Interaction Service)"""
    user_id: str = Field(..., description="Unique user identifier")
    recent_interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Recent interactions")
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list, description="Interaction history")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Interaction preferences")
    engagement_score: Optional[float] = Field(None, description="User engagement score")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    id: str = Field(..., description="Unique recommendation identifier")
    title: str = Field(..., description="Recommendation title")
    description: Optional[str] = Field(None, description="Recommendation description")
    score: float = Field(..., description="Recommendation score/confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    url: Optional[str] = Field(None, description="URL to the recommendation")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


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
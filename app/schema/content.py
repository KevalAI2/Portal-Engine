from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    MUSIC = "music"
    MOVIE = "movie"
    EVENT = "event"
    PLACE = "place"


class InteractionType(str, Enum):
    VIEW = "view"
    CLICK = "click"
    IGNORE = "ignore"
    LIKE = "like"


# User Profile Schemas
class UserProfileBase(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    archetypes: List[str] = Field(default_factory=list)
    age_group: Optional[str] = None
    relationship_status: Optional[str] = None
    travel_history: List[Dict[str, Any]] = Field(default_factory=list)


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Content Recommendation Schemas
class ContentRecommendationBase(BaseModel):
    content_type: ContentType
    content_id: str
    title: str
    description: Optional[str] = None
    content_metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.0
    ranking_position: int = 0


class ContentRecommendationCreate(ContentRecommendationBase):
    pass


class ContentRecommendation(ContentRecommendationBase):
    id: int
    user_id: int
    is_cached: bool
    cache_key: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Content Interaction Schemas
class ContentInteractionBase(BaseModel):
    interaction_type: InteractionType
    interaction_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Any] = Field(default_factory=dict)


class ContentInteractionCreate(ContentInteractionBase):
    content_id: int


class ContentInteraction(ContentInteractionBase):
    id: int
    user_id: int
    content_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# API Request/Response Schemas
class GetContentRequest(BaseModel):
    content_types: Optional[List[ContentType]] = None
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class GetContentResponse(BaseModel):
    recommendations: List[ContentRecommendation]
    total_count: int
    has_more: bool


class LogInteractionRequest(BaseModel):
    content_id: int
    interaction_type: InteractionType
    interaction_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Any] = Field(default_factory=dict)


class LogInteractionResponse(BaseModel):
    success: bool
    interaction_id: int


# Recommendation Service Schemas
class RecommendationRequest(BaseModel):
    user_id: int
    content_types: List[ContentType]
    location: Optional[Dict[str, float]] = None  # {"latitude": 40.7128, "longitude": -74.0060}
    context: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    recommendations: List[ContentRecommendation]
    cache_hit: bool
    generated_at: datetime 
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


# Music-specific schemas
class GetMusicRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    genre: Optional[str] = Field(None, description="Filter by music genre")
    mood: Optional[str] = Field(None, description="Filter by mood (upbeat, chill, energetic)")
    decade: Optional[str] = Field(None, description="Filter by decade (e.g., '2020s', '90s')")


class GetMusicResponse(BaseModel):
    music_recommendations: List[ContentRecommendation]
    total_count: int
    has_more: bool


# Movie-specific schemas
class GetMovieRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    genre: Optional[str] = Field(None, description="Filter by movie genre")
    rating: Optional[str] = Field(None, description="Filter by rating (G, PG, PG-13, R)")
    release_year: Optional[int] = Field(None, description="Filter by release year")
    duration: Optional[str] = Field(None, description="Filter by duration (short, medium, long)")


class GetMovieResponse(BaseModel):
    movie_recommendations: List[ContentRecommendation]
    total_count: int
    has_more: bool


# Event-specific schemas
class GetEventRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    event_type: Optional[str] = Field(None, description="Filter by event type (concert, festival, sports, theater)")
    date_range: Optional[str] = Field(None, description="Filter by date range (today, this_week, this_month)")
    price_range: Optional[str] = Field(None, description="Filter by price range (free, budget, premium)")
    location_radius: Optional[float] = Field(None, description="Filter by distance in miles from user location")


class GetEventResponse(BaseModel):
    event_recommendations: List[ContentRecommendation]
    total_count: int
    has_more: bool


# Place-specific schemas
class GetPlaceRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    place_type: Optional[str] = Field(None, description="Filter by place type (restaurant, bar, cafe, attraction)")
    cuisine: Optional[str] = Field(None, description="Filter by cuisine type")
    price_range: Optional[str] = Field(None, description="Filter by price range ($, $$, $$$, $$$$)")
    atmosphere: Optional[str] = Field(None, description="Filter by atmosphere (casual, upscale, romantic, family-friendly)")
    location_radius: Optional[float] = Field(None, description="Filter by distance in miles from user location")


class GetPlaceResponse(BaseModel):
    place_recommendations: List[ContentRecommendation]
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
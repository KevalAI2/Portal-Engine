from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProfileValue(BaseModel):
    """A profile value with similarity score for ranking preferences"""
    value: str = Field(..., description="The actual value (e.g., 'hiking', 'Mexican cuisine')")
    similarity_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Similarity score between 0.0 and 1.0, where 1.0 is highest preference"
    )

    class Config:
        schema_extra = {
            "example": {
                "value": "hiking",
                "similarity_score": 0.9
            }
        }


class UserProfileBase(BaseModel):
    """Base user profile with comprehensive travel and lifestyle preferences"""
    
    # Long-term memory characteristics
    keywords: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Key interests and topics that define the user's personality"
    )
    archetypes: Optional[List[ProfileValue]] = Field(
        default=[],
        description="User personality archetypes (e.g., adventurer, luxury traveler, cultural explorer)"
    )
    demographics: Optional[Dict[str, Any]] = Field(
        default={},
        description="Demographic information including age, gender, health status"
    )
    home_location: Optional[str] = Field(
        default=None,
        description="User's home city and state/country"
    )
    trips_taken: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Previous travel destinations with similarity scores"
    )
    living_situation: Optional[str] = Field(
        default=None,
        description="Current living arrangement (e.g., 'Lives alone', 'With family')"
    )
    profession: Optional[str] = Field(
        default=None,
        description="User's professional occupation"
    )
    education: Optional[str] = Field(
        default=None,
        description="Highest level of education completed"
    )
    key_relationships: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Important relationships in user's life"
    )
    children: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Information about children if applicable"
    )
    relationship_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Relationship and social goals"
    )
    cultural_language_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Cultural and language preferences"
    )
    aesthetic_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Visual and aesthetic preferences"
    )
    dining_preferences_cuisine: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred cuisines and food types"
    )
    dining_preferences_other: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Dining atmosphere and service preferences"
    )
    indoor_activity_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred indoor activities and hobbies"
    )
    outdoor_activity_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred outdoor activities and adventures"
    )
    at_home_activity_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Activities preferred at home"
    )
    favorite_neighborhoods: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred neighborhood types and characteristics"
    )
    tv_movie_genres: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred TV and movie genres"
    )
    music_genres: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred music genres and artists"
    )
    podcast_genres: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred podcast topics and genres"
    )
    favorite_creators: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Favorite content creators and influencers"
    )
    accommodation_preferences: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred accommodation types (hotels, hostels, camping, etc.)"
    )
    travel_style: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred travel styles (backpacking, luxury, budget, etc.)"
    )
    vehicle_ownership: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Vehicle ownership and transportation preferences"
    )
    fitness_level: Optional[str] = Field(
        default=None,
        description="User's fitness level and physical capabilities"
    )
    medical_conditions: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Medical conditions and health considerations"
    )
    health_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Health and wellness goals"
    )
    career_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Professional and career objectives"
    )
    financial_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Financial objectives and budget preferences"
    )
    social_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Social interaction and relationship goals"
    )
    learning_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Educational and learning objectives"
    )
    travel_goals: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Travel destinations and experiences to achieve"
    )
    
    # Short-term memory characteristics
    recent_searches: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Recent search queries and topics of interest"
    )
    recent_content_likes: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Recently liked or engaged content"
    )
    recent_plan_discussions: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Recent travel planning discussions and preferences"
    )
    recently_visited_venues: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Recently visited places and venues"
    )
    recent_media_consumption: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Recently consumed media content"
    )
    user_mood: Optional[str] = Field(
        default=None,
        description="Current user mood and emotional state"
    )
    user_energy: Optional[str] = Field(
        default=None,
        description="Current energy level and activity readiness"
    )
    user_stress: Optional[str] = Field(
        default=None,
        description="Current stress level and relaxation needs"
    )
    
    # Behavioral & preference patterns
    typical_outing_times: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred times for outings and activities"
    )
    wake_sleep_time: Optional[Dict[str, str]] = Field(
        default={},
        description="Typical wake and sleep schedule"
    )
    meal_times: Optional[Dict[str, str]] = Field(
        default={},
        description="Typical meal timing preferences"
    )
    exercise_time: Optional[str] = Field(
        default=None,
        description="Preferred exercise and activity timing"
    )
    weekly_routines: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Regular weekly activities and routines"
    )
    productivity_windows: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Peak productivity and focus periods"
    )
    commute_patterns: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Typical commuting and transportation patterns"
    )
    preferred_budget: Optional[str] = Field(
        default=None,
        description="Budget preference level ($, $$, $$$, $$$$)"
    )
    preferred_vibe: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred atmosphere and vibe for activities"
    )
    content_discovery_sources: Optional[List[ProfileValue]] = Field(
        default=[],
        description="Preferred sources for discovering new content and activities"
    )
    typical_group_size: Optional[str] = Field(
        default=None,
        description="Typical group size for activities and travel"
    )
    
    # Environmental context
    current_location: Optional[str] = Field(
        default=None,
        description="Current location for context-aware recommendations"
    )
    time_of_day: Optional[str] = Field(
        default=None,
        description="Current time of day (morning, afternoon, evening, night)"
    )
    day_of_week: Optional[str] = Field(
        default=None,
        description="Current day of the week"
    )
    weather: Optional[str] = Field(
        default=None,
        description="Current weather conditions"
    )
    device_type_usage_mode: Optional[str] = Field(
        default=None,
        description="Current device type and usage mode"
    )

    class Config:
        schema_extra = {
            "example": {
                "keywords": [
                    {"value": "hiking", "similarity_score": 0.9},
                    {"value": "adventure", "similarity_score": 0.85}
                ],
                "archetypes": [
                    {"value": "adventurer", "similarity_score": 0.95},
                    {"value": "nature-lover", "similarity_score": 0.8}
                ],
                "demographics": {
                    "age": "30",
                    "gender": "male",
                    "health": "excellent"
                },
                "home_location": "Denver, CO",
                "preferred_budget": "$",
                "current_location": "Denver, CO",
                "time_of_day": "Morning",
                "day_of_week": "Saturday",
                "weather": "Sunny",
                "user_mood": "Excited",
                "user_energy": "High energy"
            }
        }


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile"""
    pass


class UserProfileUpdate(BaseModel):
    """Schema for updating an existing user profile - all fields optional"""
    # Allow partial updates
    keywords: Optional[List[ProfileValue]] = None
    archetypes: Optional[List[ProfileValue]] = None
    demographics: Optional[Dict[str, Any]] = None
    home_location: Optional[str] = None
    trips_taken: Optional[List[ProfileValue]] = None
    living_situation: Optional[str] = None
    profession: Optional[str] = None
    education: Optional[str] = None
    key_relationships: Optional[List[ProfileValue]] = None
    children: Optional[List[ProfileValue]] = None
    relationship_goals: Optional[List[ProfileValue]] = None
    cultural_language_preferences: Optional[List[ProfileValue]] = None
    aesthetic_preferences: Optional[List[ProfileValue]] = None
    dining_preferences_cuisine: Optional[List[ProfileValue]] = None
    dining_preferences_other: Optional[List[ProfileValue]] = None
    indoor_activity_preferences: Optional[List[ProfileValue]] = None
    outdoor_activity_preferences: Optional[List[ProfileValue]] = None
    at_home_activity_preferences: Optional[List[ProfileValue]] = None
    favorite_neighborhoods: Optional[List[ProfileValue]] = None
    tv_movie_genres: Optional[List[ProfileValue]] = None
    music_genres: Optional[List[ProfileValue]] = None
    podcast_genres: Optional[List[ProfileValue]] = None
    favorite_creators: Optional[List[ProfileValue]] = None
    accommodation_preferences: Optional[List[ProfileValue]] = None
    travel_style: Optional[List[ProfileValue]] = None
    vehicle_ownership: Optional[List[ProfileValue]] = None
    fitness_level: Optional[str] = None
    medical_conditions: Optional[List[ProfileValue]] = None
    health_goals: Optional[List[ProfileValue]] = None
    career_goals: Optional[List[ProfileValue]] = None
    financial_goals: Optional[List[ProfileValue]] = None
    social_goals: Optional[List[ProfileValue]] = None
    learning_goals: Optional[List[ProfileValue]] = None
    travel_goals: Optional[List[ProfileValue]] = None
    recent_searches: Optional[List[ProfileValue]] = None
    recent_content_likes: Optional[List[ProfileValue]] = None
    recent_plan_discussions: Optional[List[ProfileValue]] = None
    recently_visited_venues: Optional[List[ProfileValue]] = None
    recent_media_consumption: Optional[List[ProfileValue]] = None
    user_mood: Optional[str] = None
    user_energy: Optional[str] = None
    user_stress: Optional[str] = None
    typical_outing_times: Optional[List[ProfileValue]] = None
    wake_sleep_time: Optional[Dict[str, str]] = None
    meal_times: Optional[Dict[str, str]] = None
    exercise_time: Optional[str] = None
    weekly_routines: Optional[List[ProfileValue]] = None
    productivity_windows: Optional[List[ProfileValue]] = None
    commute_patterns: Optional[List[ProfileValue]] = None
    preferred_budget: Optional[str] = None
    preferred_vibe: Optional[List[ProfileValue]] = None
    content_discovery_sources: Optional[List[ProfileValue]] = None
    typical_group_size: Optional[str] = None
    current_location: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    weather: Optional[str] = None
    device_type_usage_mode: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "user_mood": "Excited",
                "user_energy": "High energy",
                "current_location": "Denver, CO",
                "weather": "Sunny"
            }
        }


class UserProfile(UserProfileBase):
    """Complete user profile with database fields"""
    id: int = Field(..., description="Unique profile identifier")
    user_id: int = Field(..., description="Associated user ID")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "created_at": "2024-08-12T10:00:00Z",
                "updated_at": "2024-08-12T15:30:00Z",
                "keywords": [
                    {"value": "hiking", "similarity_score": 0.9},
                    {"value": "adventure", "similarity_score": 0.85}
                ],
                "archetypes": [
                    {"value": "adventurer", "similarity_score": 0.95}
                ],
                "home_location": "Denver, CO",
                "preferred_budget": "$"
            }
        }


class ProfileRecommendationRequest(BaseModel):
    """Request schema for getting personalized recommendations"""
    user_id: int = Field(..., description="User ID for recommendations")
    context: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Additional context for recommendations (location, time, weather, etc.)"
    )
    limit: Optional[int] = Field(
        default=10, 
        ge=1, 
        le=50, 
        description="Maximum number of recommendations to return"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "context": {
                    "location": "Denver, CO",
                    "time": "afternoon",
                    "weather": "sunny",
                    "group_size": 2
                },
                "limit": 5
            }
        }


class ProfileRecommendationResponse(BaseModel):
    """Response schema for personalized recommendations"""
    recommendations: List[Dict[str, Any]] = Field(
        ..., 
        description="List of personalized recommendations with scores and reasoning"
    )
    reasoning: str = Field(
        ..., 
        description="Overall reasoning for the recommendations provided"
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Overall confidence in the recommendations (0.0 to 1.0)"
    )
    profile_insights: Dict[str, Any] = Field(
        ..., 
        description="Key insights derived from the user's profile"
    )

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "name": "Taco Fiesta",
                        "type": "restaurant",
                        "score": 0.9,
                        "confidence": 0.85,
                        "reasoning": ["Matches Mexican preference", "Matches casual atmosphere"],
                        "details": {
                            "cuisine": "Mexican",
                            "price_range": "$",
                            "location": "Downtown"
                        }
                    }
                ],
                "reasoning": "Based on your adventurer profile and Mexican cuisine preference",
                "confidence_score": 0.85,
                "profile_insights": {
                    "primary_archetype": "adventurer",
                    "travel_style": "adventure",
                    "budget_preference": "$"
                }
            }
        }


class ProfileAnalysisResponse(BaseModel):
    """Response schema for comprehensive profile analysis"""
    user_archetype: str = Field(..., description="Primary user personality archetype")
    travel_style: str = Field(..., description="Dominant travel style preference")
    budget_preference: str = Field(..., description="Budget preference level")
    activity_preferences: List[str] = Field(..., description="Top activity preferences")
    dietary_preferences: List[str] = Field(..., description="Top dietary preferences")
    confidence_scores: Dict[str, float] = Field(
        ..., 
        description="Confidence scores for different profile aspects"
    )
    recommendations_summary: str = Field(
        ..., 
        description="Summary of recommendations and insights"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_archetype": "adventurer",
                "travel_style": "adventure",
                "budget_preference": "$",
                "activity_preferences": ["hiking", "rock climbing", "camping"],
                "dietary_preferences": ["Mexican", "Thai", "casual dining"],
                "confidence_scores": {
                    "archetypes": 0.85,
                    "activities": 0.90,
                    "dining": 0.75,
                    "travel_history": 0.80
                },
                "recommendations_summary": "High confidence in outdoor adventure recommendations"
            }
        } 
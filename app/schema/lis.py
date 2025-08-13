from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LocationContextSchema(BaseModel):
    """Schema for location context information"""
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    location_name: str = Field(..., description="Human-readable location name")
    city: str = Field("", description="City name")
    state: str = Field("", description="State or province")
    country: str = Field("", description="Country name")
    timezone: str = Field("", description="Timezone identifier")
    weather: str = Field("", description="Current weather conditions")
    temperature: Optional[float] = Field(None, description="Current temperature")
    time_of_day: str = Field("", description="Time of day category (morning, afternoon, evening, night)")
    day_of_week: str = Field("", description="Day of the week")
    is_weekend: bool = Field(False, description="Whether it's a weekend")
    is_holiday: bool = Field(False, description="Whether it's a holiday")
    local_time: Optional[datetime] = Field(None, description="Local time at the location")

    model_config = {
        "json_schema_extra": {
            "example": {
                "location_name": "Denver, CO",
                "city": "Denver",
                "state": "CO",
                "country": "US",
                "weather": "sunny",
                "temperature": 72.0,
                "time_of_day": "afternoon",
                "day_of_week": "saturday",
                "is_weekend": True,
                "local_time": "2024-08-12T14:30:00Z"
            }
        }
    }


class UserContextSchema(BaseModel):
    """Schema for current user context"""
    mood: str = Field("neutral", description="Current user mood")
    energy_level: str = Field("medium", description="Current energy level")
    stress_level: str = Field("low", description="Current stress level")
    group_size: int = Field(1, description="Number of people in the group")
    budget_preference: str = Field("$$", description="Budget preference level")
    available_time: str = Field("quick", description="Available time for activities")
    transportation_mode: str = Field("walking", description="Preferred transportation mode")
    device_type: str = Field("mobile", description="Current device type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "mood": "excited",
                "energy_level": "high",
                "stress_level": "low",
                "group_size": 2,
                "budget_preference": "$$",
                "available_time": "half_day",
                "transportation_mode": "walking",
                "device_type": "mobile"
            }
        }
    }


class LISPromptSchema(BaseModel):
    """Schema for a location-based interest prompt"""
    prompt_id: str = Field(..., description="Unique prompt identifier")
    prompt_type: str = Field(..., description="Type of prompt (restaurant, activity, attraction, event, social, wellness)")
    title: str = Field(..., description="Prompt title")
    description: str = Field(..., description="Detailed prompt description")
    urgency: str = Field(..., description="Urgency level (low, medium, high, critical)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score between 0.0 and 1.0")
    reasoning: List[str] = Field(..., description="List of reasons why this prompt is relevant")
    context_factors: Dict[str, Any] = Field(..., description="Context factors that influenced this prompt")
    action_url: Optional[str] = Field(None, description="URL for taking action on this prompt")
    expires_at: Optional[datetime] = Field(None, description="When this prompt expires")
    created_at: Optional[datetime] = Field(None, description="When this prompt was created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt_id": "restaurant_sakura_sushi",
                "prompt_type": "restaurant",
                "title": "Try Sakura Sushi",
                "description": "Check out Sakura Sushi - great Japanese cuisine!",
                "urgency": "high",
                "relevance_score": 0.85,
                "reasoning": ["Matches your Japanese cuisine preference", "Matches your budget preference"],
                "context_factors": {
                    "cuisine": "Japanese",
                    "atmosphere": "quiet",
                    "price": "$$",
                    "weather": "sunny",
                    "time_of_day": "evening"
                },
                "created_at": "2024-08-12T14:30:00Z"
            }
        }
    }


class LISRequestSchema(BaseModel):
    """Request schema for LIS prompt generation"""
    user_id: int = Field(..., description="User ID for prompt generation")
    location: str = Field(..., description="Current location (city, state or coordinates)")
    context: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Additional context for prompt generation"
    )
    limit: Optional[int] = Field(
        default=10, 
        ge=1, 
        le=50, 
        description="Maximum number of prompts to return"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "location": "Denver, CO",
                "context": {
                    "mood": "excited",
                    "group_size": 2,
                    "available_time": "half_day"
                },
                "limit": 5
            }
        }
    }


class LISResponseSchema(BaseModel):
    """Response schema for LIS prompt generation"""
    location: str = Field(..., description="Location used for prompt generation")
    total_prompts: int = Field(..., description="Total number of prompts generated")
    prompts_by_type: Dict[str, List[Dict[str, Any]]] = Field(
        ..., 
        description="Prompts grouped by type"
    )
    top_prompts: List[Dict[str, Any]] = Field(
        ..., 
        description="Top prompts by relevance and urgency"
    )
    location_context: Optional[LocationContextSchema] = Field(
        None, 
        description="Location context information"
    )
    user_context: Optional[UserContextSchema] = Field(
        None, 
        description="User context information"
    )
    generated_at: datetime = Field(..., description="When the prompts were generated")

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Denver, CO",
                "total_prompts": 8,
                "prompts_by_type": {
                    "restaurant": [
                        {
                            "prompt_id": "restaurant_sakura_sushi",
                            "prompt_type": "restaurant",
                            "title": "Try Sakura Sushi",
                            "description": "Check out Sakura Sushi - great Japanese cuisine!",
                            "urgency": "high",
                            "relevance_score": 0.85,
                            "reasoning": ["Matches your Japanese cuisine preference", "Fits your budget"],
                            "context_factors": {
                                "cuisine": "Japanese",
                                "atmosphere": "quiet",
                                "price": "$$"
                            }
                        }
                    ],
                    "activity": [
                        {
                            "prompt_id": "activity_red_rocks_park",
                            "prompt_type": "activity",
                            "title": "Explore Red Rocks Park",
                            "description": "Explore Red Rocks Park - a great nature activity!",
                            "urgency": "medium",
                            "relevance_score": 0.75,
                            "reasoning": ["Perfect for your adventurous spirit", "Great weather for hiking"],
                            "context_factors": {
                                "type": "outdoor",
                                "category": "nature",
                                "duration": "2 hours"
                            }
                        }
                    ]
                },
                "top_prompts": [
                    {
                        "prompt_id": "restaurant_sakura_sushi",
                        "prompt_type": "restaurant",
                        "title": "Try Sakura Sushi",
                        "description": "Check out Sakura Sushi - great Japanese cuisine!",
                        "urgency": "high",
                        "relevance_score": 0.85,
                        "reasoning": ["Matches your Japanese cuisine preference", "Fits your budget"],
                        "context_factors": {
                            "cuisine": "Japanese",
                            "atmosphere": "quiet",
                            "price": "$$"
                        }
                    }
                ],
                "location_context": {
                    "location_name": "Denver, CO",
                    "city": "Denver",
                    "state": "CO",
                    "weather": "sunny",
                    "temperature": 72.0,
                    "time_of_day": "afternoon"
                },
                "user_context": {
                    "mood": "excited",
                    "energy_level": "high",
                    "group_size": 2,
                    "budget_preference": "$$"
                },
                "generated_at": "2024-08-12T14:30:00Z"
            }
        }
    }


class LISPromptUpdateSchema(BaseModel):
    """Schema for updating LIS prompt interactions"""
    prompt_id: str = Field(..., description="Prompt ID to update")
    interaction_type: str = Field(..., description="Type of interaction (view, click, dismiss, like)")
    interaction_data: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Additional interaction data"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt_id": "restaurant_sakura_sushi",
                "interaction_type": "click",
                "interaction_data": {
                    "click_time": "2024-08-12T14:35:00Z",
                    "device_type": "mobile",
                    "source": "app"
                }
            }
        }
    }


class LISAnalyticsSchema(BaseModel):
    """Schema for LIS analytics and insights"""
    total_prompts_generated: int = Field(..., description="Total prompts generated")
    prompts_by_type: Dict[str, int] = Field(..., description="Number of prompts by type")
    average_relevance_score: float = Field(..., description="Average relevance score")
    top_interaction_types: Dict[str, int] = Field(..., description="Most common interaction types")
    location_effectiveness: Dict[str, float] = Field(..., description="Effectiveness by location")
    user_engagement_rate: float = Field(..., description="Overall user engagement rate")
    generated_at: datetime = Field(..., description="When analytics were generated")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_prompts_generated": 150,
                "prompts_by_type": {
                    "restaurant": 60,
                    "activity": 45,
                    "attraction": 30,
                    "social": 15
                },
                "average_relevance_score": 0.72,
                "top_interaction_types": {
                    "view": 120,
                    "click": 45,
                    "dismiss": 30,
                    "like": 25
                },
                "location_effectiveness": {
                    "Denver, CO": 0.85,
                    "New York, NY": 0.78,
                    "Los Angeles, CA": 0.82
                },
                "user_engagement_rate": 0.67,
                "generated_at": "2024-08-12T14:30:00Z"
            }
        }
    } 
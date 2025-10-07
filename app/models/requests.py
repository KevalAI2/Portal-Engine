"""
Request models for API input validation
"""
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LocationPayload(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    city: Optional[str] = Field(None, max_length=120)
    country: Optional[str] = Field(None, max_length=120)
    timezone: Optional[str] = Field(None, max_length=64)

class DateRangePayload(BaseModel):
    start: Optional[str] = Field(None, description="ISO8601 start date/time")
    end: Optional[str] = Field(None, description="ISO8601 end date/time")

    @field_validator('start', 'end')
    @classmethod
    def validate_iso(cls, v):
        if v is None:
            return v
        try:
            # Accept date or datetime in ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except Exception:
            raise ValueError('DateRange values must be ISO8601 strings')


class RecommendationRequest(BaseModel):
    """Request model for generating recommendations"""
    prompt: Optional[str] = Field(
        default=None,
        description="User prompt for recommendations; if omitted, the server builds one"
    )
    location: Optional[LocationPayload] = Field(
        default=None,
        description="User location context from frontend"
    )
    date_range: Optional[DateRangePayload] = Field(
        default=None,
        description="Requested date window (for events filtering)"
    )
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "I like concerts",
                "location": {"lat": 29.7604, "lng": -95.3698, "city": "Houston", "country": "US", "timezone": "America/Chicago"},
                "date_range": {"start": "2025-10-07T00:00:00Z", "end": "2025-10-21T23:59:59Z"}
            }
        }
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError('Prompt must be a string')
        if len(v.strip()) == 0:
            return None
        return v.strip()


class UserProfileRequest(BaseModel):
    """Request model for user profile operations"""
    user_id: str = Field(..., description="User identifier", min_length=1, max_length=100)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not isinstance(v, str):
            raise ValueError('User ID must be a string')
        if len(v.strip()) == 0:
            raise ValueError('User ID cannot be empty')
        return v.strip()


class ProcessingRequest(BaseModel):
    """Request model for user processing operations"""
    user_id: str = Field(..., description="User identifier", min_length=1, max_length=100)
    priority: int = Field(default=5, description="Processing priority (1-10)", ge=1, le=10)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not isinstance(v, str):
            raise ValueError('User ID must be a string')
        if len(v.strip()) == 0:
            raise ValueError('User ID cannot be empty')
        return v.strip()


class RefreshRequest(BaseModel):
    """Request model for refreshing recommendations"""
    user_id: str = Field(..., description="User identifier", min_length=1, max_length=100)
    force: bool = Field(default=False, description="Force refresh even if recent data exists")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not isinstance(v, str):
            raise ValueError('User ID must be a string')
        if len(v.strip()) == 0:
            raise ValueError('User ID cannot be empty')
        return v.strip()


class ResultsFilterRequest(BaseModel):
    """Request model for filtering results"""
    category: Optional[str] = Field(None, description="Filter by category", max_length=50)
    limit: int = Field(default=5, description="Maximum results per category", ge=1, le=100)
    min_score: float = Field(default=0.0, description="Minimum ranking score", ge=0.0, le=1.0)
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None:
            valid_categories = ['music', 'movie', 'place', 'event']
            if v.lower() not in valid_categories:
                raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v


class TaskStatusRequest(BaseModel):
    """Request model for task status operations"""
    task_id: str = Field(..., description="Task identifier", min_length=1, max_length=100)
    
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v):
        if not isinstance(v, str):
            raise ValueError('Task ID must be a string')
        if len(v.strip()) == 0:
            raise ValueError('Task ID cannot be empty')
        return v.strip()

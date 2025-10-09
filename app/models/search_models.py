"""
Pydantic models for search integration functionality.

This module defines the data models used for search query capture,
storage, and API responses in the search integration system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.core.validators import validate_search_query, validate_user_id


class SearchQueryRequest(BaseModel):
    """Request model for search query operations"""
    prompt: str = Field(..., min_length=2, max_length=1000, description="Search query text")
    user_id: str = Field(..., min_length=3, max_length=50, description="User identifier")
    category: Optional[str] = Field(None, max_length=50, description="Search category")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    model_name: str = Field(..., min_length=1, max_length=100, description="Model name")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        return validate_search_query(v)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        return validate_user_id(v)
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Find me a good restaurant in Barcelona",
                "user_id": "user123",
                "category": "places",
                "filters": {"location": "Barcelona", "type": "restaurant"},
                "model_name": "gpt-4"
            }
        }


class SearchQueryResponse(BaseModel):
    """Response model for individual search queries"""
    query_id: str = Field(..., description="Unique query identifier")
    user_id: str = Field(..., description="User identifier")
    prompt: str = Field(..., description="Search query text")
    timestamp: float = Field(..., description="Unix timestamp")
    timestamp_readable: str = Field(..., description="Human-readable timestamp")
    model_name: str = Field(..., description="Model used")
    category: Optional[str] = Field(None, description="Search category")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    success: bool = Field(True, description="Whether query was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "query_id": "search_abc123def456",
                "user_id": "user123",
                "prompt": "Find me a good restaurant in Barcelona",
                "timestamp": 1703123456.789,
                "timestamp_readable": "2023-12-21 10:30:56",
                "model_name": "gpt-4",
                "category": "places",
                "filters": {"location": "Barcelona", "type": "restaurant"},
                "response_time": 1.234,
                "success": True,
                "error_message": None
            }
        }


class SearchQueriesListResponse(BaseModel):
    """Response model for search queries list"""
    queries: List[SearchQueryResponse] = Field(..., description="List of search queries")
    total_count: int = Field(..., description="Total number of queries found")
    returned_count: int = Field(..., description="Number of queries returned")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    pagination: Dict[str, int] = Field(..., description="Pagination info")
    
    class Config:
        schema_extra = {
            "example": {
                "queries": [
                    {
                        "query_id": "search_abc123def456",
                        "user_id": "user123",
                        "prompt": "Find me a good restaurant in Barcelona",
                        "timestamp": 1703123456.789,
                        "timestamp_readable": "2023-12-21 10:30:56",
                        "model_name": "gpt-4",
                        "category": "places",
                        "filters": {"location": "Barcelona", "type": "restaurant"},
                        "response_time": 1.234,
                        "success": True,
                        "error_message": None
                    }
                ],
                "total_count": 1,
                "returned_count": 1,
                "filters": {
                    "user_id": "user123",
                    "category": None,
                    "success_only": False
                },
                "pagination": {
                    "limit": 10,
                    "offset": 0
                }
            }
        }


class SearchAnalyticsResponse(BaseModel):
    """Response model for search analytics"""
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    categories: Dict[str, int] = Field(..., description="Category distribution")
    models: Dict[str, int] = Field(..., description="Model distribution")
    top_search_terms: List[List[str]] = Field(..., description="Top search terms")
    time_range_days: int = Field(..., description="Time range in days")
    user_id: Optional[str] = Field(None, description="User ID filter")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": {
                    "total_queries": 100,
                    "successful_queries": 95,
                    "failed_queries": 5,
                    "success_rate": 95.0,
                    "avg_response_time": 1.234
                },
                "categories": {
                    "places": 50,
                    "events": 30,
                    "movies": 20
                },
                "models": {
                    "gpt-4": 80,
                    "gpt-3.5-turbo": 20
                },
                "top_search_terms": [
                    ["restaurant", 25],
                    ["barcelona", 20],
                    ["movie", 15]
                ],
                "time_range_days": 7,
                "user_id": "user123"
            }
        }


class SearchQueryFilters(BaseModel):
    """Model for search query filtering parameters"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    category: Optional[str] = Field(None, description="Filter by category")
    success_only: bool = Field(False, description="Only return successful queries")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of queries to return")
    offset: int = Field(0, ge=0, description="Number of queries to skip")
    days: int = Field(7, ge=1, le=365, description="Number of days to look back")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if v is not None:
            return validate_user_id(v)
        return v


class SearchQueryCapture(BaseModel):
    """Model for capturing search queries during recommendation generation"""
    user_id: str = Field(..., description="User identifier")
    prompt: str = Field(..., description="Search query text")
    model_name: str = Field(..., description="Model name")
    category: Optional[str] = Field(None, description="Search category")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    start_time: Optional[float] = Field(None, description="Start time for response calculation")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        return validate_search_query(v)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        return validate_user_id(v)


class SearchQueryError(BaseModel):
    """Model for search query error information"""
    query_id: str = Field(..., description="Query identifier")
    error_message: str = Field(..., description="Error message")
    timestamp: float = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "query_id": "search_abc123def456",
                "error_message": "Model timeout after 30 seconds",
                "timestamp": 1703123456.789
            }
        }


class SearchIntegrationStats(BaseModel):
    """Model for search integration statistics"""
    total_queries: int = Field(..., description="Total queries captured")
    successful_queries: int = Field(..., description="Successful queries")
    failed_queries: int = Field(..., description="Failed queries")
    success_rate: float = Field(..., description="Success rate percentage")
    avg_response_time: float = Field(..., description="Average response time")
    unique_users: int = Field(..., description="Number of unique users")
    most_active_user: Optional[str] = Field(None, description="Most active user ID")
    most_common_category: Optional[str] = Field(None, description="Most common category")
    
    class Config:
        schema_extra = {
            "example": {
                "total_queries": 1000,
                "successful_queries": 950,
                "failed_queries": 50,
                "success_rate": 95.0,
                "avg_response_time": 1.234,
                "unique_users": 25,
                "most_active_user": "user123",
                "most_common_category": "places"
            }
        }

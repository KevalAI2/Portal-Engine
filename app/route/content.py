from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.logic.content import ContentRecommendationService
from app.schema.content import (
    GetContentRequest, GetContentResponse, LogInteractionRequest, LogInteractionResponse,
    UserProfileCreate, UserProfileUpdate, UserProfile, ContentType, RecommendationRequest,
    GetMusicRequest, GetMusicResponse, GetMovieRequest, GetMovieResponse,
    GetEventRequest, GetEventResponse, GetPlaceRequest, GetPlaceResponse
)
from app.logic.auth import get_current_user
from app.model.user import UserInDB

router = APIRouter()


@router.get("/music", response_model=GetMusicResponse)
async def get_music_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of music recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    genre: Optional[str] = Query(None, description="Filter by music genre"),
    mood: Optional[str] = Query(None, description="Filter by mood (upbeat, chill, energetic)"),
    decade: Optional[str] = Query(None, description="Filter by decade (e.g., '2020s', '90s')"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized music recommendations for the authenticated user.
    
    This endpoint returns music recommendations based on the user's profile, preferences, and interaction history.
    Supports filtering by genre, mood, and decade.
    """
    try:
        service = ContentRecommendationService(db)
        
        # Create recommendation request for music only
        context = {}
        if genre:
            context["genre"] = genre
        if mood:
            context["mood"] = mood
        if decade:
            context["decade"] = decade
            
        request = RecommendationRequest(
            user_id=current_user.id,
            content_types=[ContentType.MUSIC],
            context=context
        )
        
        # Get recommendations
        response = service.get_recommendations(request)
        
        # Apply pagination
        total_count = len(response.recommendations)
        paginated_recommendations = response.recommendations[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return GetMusicResponse(
            music_recommendations=paginated_recommendations,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving music recommendations: {str(e)}")


@router.get("/movies", response_model=GetMovieResponse)
async def get_movie_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of movie recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    genre: Optional[str] = Query(None, description="Filter by movie genre"),
    rating: Optional[str] = Query(None, description="Filter by rating (G, PG, PG-13, R)"),
    release_year: Optional[int] = Query(None, description="Filter by release year"),
    duration: Optional[str] = Query(None, description="Filter by duration (short, medium, long)"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized movie recommendations for the authenticated user.
    
    This endpoint returns movie recommendations based on the user's profile, preferences, and interaction history.
    Supports filtering by genre, rating, release year, and duration.
    """
    try:
        service = ContentRecommendationService(db)
        
        # Create recommendation request for movies only
        context = {}
        if genre:
            context["genre"] = genre
        if rating:
            context["rating"] = rating
        if release_year:
            context["release_year"] = release_year
        if duration:
            context["duration"] = duration
            
        request = RecommendationRequest(
            user_id=current_user.id,
            content_types=[ContentType.MOVIE],
            context=context
        )
        
        # Get recommendations
        response = service.get_recommendations(request)
        
        # Apply pagination
        total_count = len(response.recommendations)
        paginated_recommendations = response.recommendations[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return GetMovieResponse(
            movie_recommendations=paginated_recommendations,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movie recommendations: {str(e)}")


@router.get("/events", response_model=GetEventResponse)
async def get_event_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of event recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    event_type: Optional[str] = Query(None, description="Filter by event type (concert, festival, sports, theater)"),
    date_range: Optional[str] = Query(None, description="Filter by date range (today, this_week, this_month)"),
    price_range: Optional[str] = Query(None, description="Filter by price range (free, budget, premium)"),
    location_radius: Optional[float] = Query(None, description="Filter by distance in miles from user location"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized event recommendations for the authenticated user.
    
    This endpoint returns event recommendations based on the user's profile, preferences, and interaction history.
    Supports filtering by event type, date range, price range, and location radius.
    """
    try:
        service = ContentRecommendationService(db)
        
        # Create recommendation request for events only
        context = {}
        if event_type:
            context["event_type"] = event_type
        if date_range:
            context["date_range"] = date_range
        if price_range:
            context["price_range"] = price_range
        if location_radius:
            context["location_radius"] = location_radius
            
        request = RecommendationRequest(
            user_id=current_user.id,
            content_types=[ContentType.EVENT],
            context=context
        )
        
        # Get recommendations
        response = service.get_recommendations(request)
        
        # Apply pagination
        total_count = len(response.recommendations)
        paginated_recommendations = response.recommendations[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return GetEventResponse(
            event_recommendations=paginated_recommendations,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving event recommendations: {str(e)}")


@router.get("/places", response_model=GetPlaceResponse)
async def get_place_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of place recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    place_type: Optional[str] = Query(None, description="Filter by place type (restaurant, bar, cafe, attraction)"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    price_range: Optional[str] = Query(None, description="Filter by price range ($, $$, $$$, $$$$)"),
    atmosphere: Optional[str] = Query(None, description="Filter by atmosphere (casual, upscale, romantic, family-friendly)"),
    location_radius: Optional[float] = Query(None, description="Filter by distance in miles from user location"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized place recommendations for the authenticated user.
    
    This endpoint returns place recommendations based on the user's profile, preferences, and interaction history.
    Supports filtering by place type, cuisine, price range, atmosphere, and location radius.
    """
    try:
        service = ContentRecommendationService(db)
        
        # Create recommendation request for places only
        context = {}
        if place_type:
            context["place_type"] = place_type
        if cuisine:
            context["cuisine"] = cuisine
        if price_range:
            context["price_range"] = price_range
        if atmosphere:
            context["atmosphere"] = atmosphere
        if location_radius:
            context["location_radius"] = location_radius
            
        request = RecommendationRequest(
            user_id=current_user.id,
            content_types=[ContentType.PLACE],
            context=context
        )
        
        # Get recommendations
        response = service.get_recommendations(request)
        
        # Apply pagination
        total_count = len(response.recommendations)
        paginated_recommendations = response.recommendations[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return GetPlaceResponse(
            place_recommendations=paginated_recommendations,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving place recommendations: {str(e)}")


@router.get("/content", response_model=GetContentResponse)
async def get_mixed_content_recommendations(
    content_types: Optional[List[ContentType]] = Query(None, description="Filter by specific content types"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get mixed personalized content recommendations for the authenticated user.
    
    This endpoint returns recommendations from multiple content types based on the user's profile, preferences, and interaction history.
    Use this endpoint when you want mixed recommendations across different content types.
    For specific content types, use dedicated endpoints: /music, /movies, /events, /places
    """
    try:
        service = ContentRecommendationService(db)
        
        # If no content types specified, get all types
        if not content_types:
            content_types = [ContentType.MUSIC, ContentType.MOVIE, ContentType.EVENT, ContentType.PLACE]
        
        # Create recommendation request
        request = RecommendationRequest(
            user_id=current_user.id,
            content_types=content_types
        )
        
        # Get recommendations
        response = service.get_recommendations(request)
        
        # Apply pagination
        total_count = len(response.recommendations)
        paginated_recommendations = response.recommendations[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return GetContentResponse(
            recommendations=paginated_recommendations,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving mixed content recommendations: {str(e)}")


@router.post("/interaction", response_model=LogInteractionResponse)
async def log_interaction(
    interaction_data: LogInteractionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log user interaction with content (view, click, ignore, like).
    
    This endpoint tracks user behavior to improve future recommendations and analytics.
    """
    try:
        service = ContentRecommendationService(db)
        
        # Log the interaction
        interaction = service.log_interaction(current_user.id, interaction_data)
        
        return LogInteractionResponse(
            success=True,
            interaction_id=interaction.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging interaction: {str(e)}")


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile with preferences and settings.
    """
    try:
        service = ContentRecommendationService(db)
        profile = service.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user profile: {str(e)}")


@router.post("/profile", response_model=UserProfile)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update the current user's profile with preferences and settings.
    """
    try:
        service = ContentRecommendationService(db)
        profile = service.create_or_update_user_profile(current_user.id, profile_data)
        
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating/updating user profile: {str(e)}")


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile with new preferences and settings.
    """
    try:
        service = ContentRecommendationService(db)
        profile = service.create_or_update_user_profile(current_user.id, profile_data)
        
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")


@router.post("/refresh")
async def refresh_recommendations(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a refresh of recommendations for the current user.
    
    This endpoint triggers an asynchronous task to generate new recommendations
    based on the user's current profile and preferences.
    """
    try:
        from app.tasks.recommendation_tasks import refresh_user_recommendations
        
        # Trigger async refresh
        refresh_user_recommendations.delay(current_user.id)
        
        return {"message": "Recommendation refresh triggered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering refresh: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the content recommendation service.
    """
    return {
        "status": "healthy",
        "service": "content-recommendation",
        "timestamp": "2024-01-01T00:00:00Z"
    }
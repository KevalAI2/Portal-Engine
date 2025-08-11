from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.logic.content import ContentRecommendationService
from app.schema.content import (
    GetContentRequest, GetContentResponse, LogInteractionRequest, LogInteractionResponse,
    UserProfileCreate, UserProfileUpdate, UserProfile, ContentType, RecommendationRequest
)
from app.logic.auth import get_current_user
from app.model.user import UserInDB

router = APIRouter()


@router.get("/content", response_model=GetContentResponse)
async def get_content_recommendations(
    content_types: Optional[List[ContentType]] = Query(None, description="Filter by content types"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    offset: int = Query(0, ge=0, description="Number of recommendations to skip"),
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized content recommendations for the authenticated user.
    
    This endpoint returns recommendations based on the user's profile, preferences, and interaction history.
    Recommendations are cached in Redis for fast retrieval and generated asynchronously when needed.
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
        raise HTTPException(status_code=500, detail=f"Error retrieving recommendations: {str(e)}")


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
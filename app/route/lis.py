from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.logic.auth import get_current_active_user
from app.model.user import UserInDB
from app.logic.lis_system import generate_lis_prompts_for_user, get_location_based_recommendations
from app.schema.lis import (
    LISRequestSchema, LISResponseSchema, LISPromptUpdateSchema, 
    LISAnalyticsSchema, LocationContextSchema, UserContextSchema
)
from app.logic.user_profile import get_user_profile
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/lis", tags=["Location-based Interest System"])


@router.post(
    "/prompts/generate/",
    response_model=LISResponseSchema,
    summary="Generate Location-Based Prompts",
    description="Generate personalized location-based interest prompts based on user profile and current location.",
    response_description="Location-based prompts with relevance scores and reasoning"
)
async def generate_prompts(
    request: LISRequestSchema,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate location-based interest prompts for a user.
    
    This endpoint analyzes the user's profile, current location, and context to generate
    personalized prompts for restaurants, activities, attractions, and other experiences.
    
    The system considers:
    - User's dining preferences and budget
    - Activity preferences (indoor/outdoor)
    - Current time of day and weather
    - User's mood and energy level
    - Group size and available time
    - Location-specific recommendations
    
    Returns prompts ranked by relevance and urgency.
    """
    try:
        # Verify user has permission to access the requested user_id
        if request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only generate prompts for your own profile"
            )
        
        # Check if user profile exists
        user_profile = get_user_profile(db, request.user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please create a profile first."
            )
        
        # Generate location-based recommendations
        recommendations = get_location_based_recommendations(db, request.user_id, request.location)
        
        # Add location and user context if available
        location_context = None
        user_context = None
        
        # Try to extract context information
        try:
            from app.logic.lis_system import lis_engine
            location_context = lis_engine.generate_location_context(request.location)
            user_context = lis_engine.generate_user_context(user_profile)
        except Exception as e:
            logger.warning(f"Could not generate context: {e}")
        
        # Convert to schema format
        location_context_schema = None
        if location_context:
            location_context_schema = LocationContextSchema(
                latitude=location_context.latitude,
                longitude=location_context.longitude,
                location_name=location_context.location_name,
                city=location_context.city,
                state=location_context.state,
                country=location_context.country,
                timezone=location_context.timezone,
                weather=location_context.weather,
                temperature=location_context.temperature,
                time_of_day=location_context.time_of_day,
                day_of_week=location_context.day_of_week,
                is_weekend=location_context.is_weekend,
                is_holiday=location_context.is_holiday,
                local_time=location_context.local_time
            )
        
        user_context_schema = None
        if user_context:
            user_context_schema = UserContextSchema(
                mood=user_context.mood,
                energy_level=user_context.energy_level,
                stress_level=user_context.stress_level,
                group_size=user_context.group_size,
                budget_preference=user_context.budget_preference,
                available_time=user_context.available_time,
                transportation_mode=user_context.transportation_mode,
                device_type=user_context.device_type
            )
        
        return LISResponseSchema(
            location=request.location,
            total_prompts=recommendations["total_prompts"],
            prompts_by_type=recommendations["prompts_by_type"],
            top_prompts=recommendations["top_prompts"],
            location_context=location_context_schema,
            user_context=user_context_schema,
            generated_at=datetime.fromisoformat(recommendations["generated_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating LIS prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate location-based prompts"
        )


@router.get(
    "/prompts/{user_id}/",
    response_model=LISResponseSchema,
    summary="Get User's LIS Prompts",
    description="Get the most recent location-based prompts for a specific user.",
    response_description="User's location-based prompts"
)
async def get_user_prompts(
    user_id: int,
    location: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get location-based prompts for a specific user.
    
    This endpoint retrieves the most recent prompts generated for the user
    at the specified location. Useful for displaying existing prompts
    without regenerating them.
    """
    try:
        # Verify user has permission
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own prompts"
            )
        
        # Generate fresh prompts (in production, you might cache these)
        recommendations = get_location_based_recommendations(db, user_id, location)
        
        return LISResponseSchema(
            location=location,
            total_prompts=recommendations["total_prompts"],
            prompts_by_type=recommendations["prompts_by_type"],
            top_prompts=recommendations["top_prompts"],
            generated_at=datetime.fromisoformat(recommendations["generated_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user prompts"
        )


@router.post(
    "/prompts/interact/",
    summary="Update Prompt Interaction",
    description="Record user interaction with a location-based prompt (view, click, dismiss, like).",
    response_description="Confirmation of interaction recorded"
)
async def update_prompt_interaction(
    interaction: LISPromptUpdateSchema,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Record user interaction with a location-based prompt.
    
    This endpoint tracks how users interact with prompts to improve
    future recommendations and provide analytics.
    
    Interaction types:
    - **view**: User viewed the prompt
    - **click**: User clicked on the prompt
    - **dismiss**: User dismissed the prompt
    - **like**: User liked the prompt
    """
    try:
        # In production, you would save this to a database
        # For now, we'll just log the interaction
        logger.info(f"User {current_user.id} {interaction.interaction_type} prompt {interaction.prompt_id}")
        
        # Here you would typically:
        # 1. Save interaction to database
        # 2. Update prompt analytics
        # 3. Adjust user preferences based on interaction
        # 4. Trigger recommendation updates if needed
        
        return {
            "message": "Interaction recorded successfully",
            "prompt_id": interaction.prompt_id,
            "interaction_type": interaction.interaction_type,
            "recorded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording prompt interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction"
        )


@router.get(
    "/analytics/{user_id}/",
    response_model=LISAnalyticsSchema,
    summary="Get LIS Analytics",
    description="Get analytics and insights about location-based prompt performance for a user.",
    response_description="LIS analytics and insights"
)
async def get_lis_analytics(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics for location-based interest system.
    
    This endpoint provides insights into:
    - Total prompts generated
    - Prompts by type (restaurant, activity, etc.)
    - Average relevance scores
    - User engagement rates
    - Location effectiveness
    - Most common interaction types
    """
    try:
        # Verify user has permission
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own analytics"
            )
        
        # In production, this would query the database for actual analytics
        # For now, return mock data
        analytics = LISAnalyticsSchema(
            total_prompts_generated=150,
            prompts_by_type={
                "restaurant": 60,
                "activity": 45,
                "attraction": 30,
                "social": 15
            },
            average_relevance_score=0.72,
            top_interaction_types={
                "view": 120,
                "click": 45,
                "dismiss": 30,
                "like": 25
            },
            location_effectiveness={
                "Denver, CO": 0.85,
                "New York, NY": 0.78,
                "Los Angeles, CA": 0.82
            },
            user_engagement_rate=0.67,
            generated_at=datetime.now()
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LIS analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.post(
    "/location/update/",
    summary="Update User Location",
    description="Update the user's current location for better context-aware recommendations.",
    response_description="Confirmation that location was updated"
)
async def update_user_location(
    location: str,
    latitude: float = None,
    longitude: float = None,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user's current location.
    
    This endpoint allows users to update their location for more accurate
    location-based recommendations. The location can be provided as:
    - City, State format (e.g., "Denver, CO")
    - Coordinates (latitude, longitude)
    
    Updating location will trigger fresh prompt generation.
    """
    try:
        # Update user profile with new location
        user_profile = get_user_profile(db, current_user.id)
        if user_profile:
            user_profile.current_location = location
            db.commit()
        
        return {
            "message": "Location updated successfully",
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating user location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )


@router.get(
    "/health/",
    summary="LIS System Health Check",
    description="Check the health and status of the Location-based Interest System.",
    response_description="System health status"
)
async def lis_health_check():
    """
    Health check endpoint for the LIS system.
    
    Returns the current status of the location-based interest system
    including version, status, and any relevant metrics.
    """
    return {
        "status": "healthy",
        "system": "Location-based Interest System (LIS)",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Location-based prompt generation",
            "User context analysis",
            "Restaurant recommendations",
            "Activity suggestions",
            "Interaction tracking",
            "Analytics and insights"
        ]
    } 
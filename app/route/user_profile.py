from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.logic.auth import get_current_active_user
from app.logic.user_profile import (
    get_user_profile, create_user_profile, update_user_profile,
    add_recent_search, add_recent_venue_visit, update_user_context,
    get_profile_insights
)
from app.logic.profile_recommendations import get_personalized_recommendations
from app.schema.user_profile import (
    UserProfile, UserProfileCreate, UserProfileUpdate,
    ProfileRecommendationRequest, ProfileRecommendationResponse,
    ProfileAnalysisResponse
)
from app.schema.user import User
from typing import Optional, Dict, Any

router = APIRouter()


@router.post(
    "/profiles/", 
    response_model=UserProfile,
    summary="Create User Profile",
    description="Create a comprehensive user profile with travel preferences, demographics, and behavioral patterns. This endpoint allows users to establish their complete profile for personalized recommendations.",
    response_description="Successfully created user profile with all preferences and characteristics"
)
async def create_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new comprehensive user profile.
    
    This endpoint creates a detailed user profile that includes:
    - **Long-term characteristics**: Keywords, archetypes, demographics, travel history
    - **Activity preferences**: Indoor/outdoor activities, dining preferences
    - **Travel style**: Accommodation preferences, budget, travel goals
    - **Behavioral patterns**: Typical routines, social preferences
    - **Environmental context**: Current location, weather, time context
    
    The profile data is used to generate highly personalized travel recommendations.
    """
    # Check if profile already exists
    existing_profile = get_user_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    
    return create_user_profile(db, current_user.id, profile_data)


@router.get(
    "/profiles/me/", 
    response_model=UserProfile,
    summary="Get My Profile",
    description="Retrieve the current user's complete profile including all preferences, characteristics, and behavioral data.",
    response_description="Complete user profile with all preferences and characteristics"
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's complete profile.
    
    Returns all profile data including:
    - Personal characteristics and demographics
    - Travel preferences and history
    - Activity and dining preferences
    - Behavioral patterns and routines
    - Current environmental context
    """
    profile = get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put(
    "/profiles/me/", 
    response_model=UserProfile,
    summary="Update My Profile",
    description="Update specific fields in the user's profile. All fields are optional, allowing partial updates.",
    response_description="Updated user profile with modified fields"
)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile with new information.
    
    Supports partial updates - only include the fields you want to change.
    Common updates include:
    - Current location and environmental context
    - Recent activities and preferences
    - Mood and energy levels
    - New travel experiences
    """
    profile = update_user_profile(db, current_user.id, profile_update)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get(
    "/profiles/me/insights/", 
    response_model=Dict[str, Any],
    summary="Get Profile Insights",
    description="Generate intelligent insights from the user's profile data, including archetype analysis, preference patterns, and confidence scores.",
    response_description="Comprehensive profile insights and analysis"
)
async def get_my_profile_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get intelligent insights from the user's profile.
    
    Returns analysis including:
    - Primary personality archetype
    - Dominant travel style
    - Top activity and dining preferences
    - Confidence scores for different aspects
    - Behavioral pattern analysis
    """
    insights = get_profile_insights(db, current_user.id)
    if not insights:
        raise HTTPException(status_code=404, detail="Profile not found")
    return insights


@router.post(
    "/profiles/me/search/",
    summary="Add Recent Search",
    description="Add a recent search query to the user's profile for better understanding of current interests.",
    response_description="Confirmation that search was added to profile"
)
async def add_search_to_profile(
    search_query: str = Query(..., description="The search query to add to profile"),
    similarity_score: float = Query(0.9, ge=0.0, le=1.0, description="Relevance score for this search (0.0 to 1.0)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a recent search query to the user's profile.
    
    This helps the system understand current interests and improve recommendations.
    The similarity score indicates how relevant this search is to the user's preferences.
    """
    profile = add_recent_search(db, current_user.id, search_query, similarity_score)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Search added to profile", "search_query": search_query}


@router.post(
    "/profiles/me/venue-visit/",
    summary="Add Venue Visit",
    description="Record a recently visited venue to improve understanding of user preferences and behavior patterns.",
    response_description="Confirmation that venue visit was added to profile"
)
async def add_venue_visit_to_profile(
    venue_name: str = Query(..., description="Name of the visited venue"),
    similarity_score: float = Query(0.9, ge=0.0, le=1.0, description="Relevance score for this venue (0.0 to 1.0)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a recently visited venue to the user's profile.
    
    This helps track user behavior and preferences for better recommendations.
    Venue visits are used to understand what types of places the user enjoys.
    """
    profile = add_recent_venue_visit(db, current_user.id, venue_name, similarity_score)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Venue visit added to profile", "venue_name": venue_name}


@router.post(
    "/profiles/me/context/",
    summary="Update Environmental Context",
    description="Update the user's current environmental context including location, weather, time, and mood for context-aware recommendations.",
    response_description="Confirmation that context was updated"
)
async def update_context(
    context_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the user's current environmental context.
    
    Context data can include:
    - Current location
    - Weather conditions
    - Time of day and day of week
    - User mood and energy level
    - Group size and social context
    
    This information helps provide more relevant, context-aware recommendations.
    """
    profile = update_user_context(db, current_user.id, context_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Context updated successfully", "context": context_data}


@router.post(
    "/profiles/me/recommendations/", 
    response_model=ProfileRecommendationResponse,
    summary="Get Personalized Recommendations",
    description="Generate highly personalized travel recommendations based on the user's complete profile, current context, and behavioral patterns.",
    response_description="Personalized recommendations with detailed reasoning and confidence scores"
)
async def get_recommendations(
    request: ProfileRecommendationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized travel recommendations.
    
    Generates recommendations across multiple categories:
    - **Restaurants**: Based on cuisine preferences, budget, and atmosphere
    - **Activities**: Indoor/outdoor activities matching user interests
    - **Accommodations**: Hotels, hostels, camping based on travel style
    
    Each recommendation includes:
    - Relevance score and confidence level
    - Detailed reasoning for the recommendation
    - Specific details about the recommendation
    
    The system considers:
    - User's personality archetype and travel style
    - Current location and environmental context
    - Budget preferences and group size
    - Recent behavior and preferences
    """
    recommendations = get_personalized_recommendations(db, current_user.id, request)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Profile not found")
    return recommendations


@router.get(
    "/profiles/me/analysis/", 
    response_model=ProfileAnalysisResponse,
    summary="Get Comprehensive Profile Analysis",
    description="Generate a comprehensive analysis of the user's profile including archetype, preferences, confidence scores, and recommendation summary.",
    response_description="Detailed profile analysis with insights and recommendations"
)
async def get_profile_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive profile analysis.
    
    Provides detailed analysis including:
    - **User Archetype**: Primary personality type (adventurer, luxury traveler, etc.)
    - **Travel Style**: Dominant travel preferences and patterns
    - **Budget Preference**: Spending patterns and budget comfort level
    - **Activity Preferences**: Top indoor and outdoor activities
    - **Dietary Preferences**: Cuisine and dining atmosphere preferences
    - **Confidence Scores**: Reliability of different profile aspects
    - **Recommendations Summary**: High-level recommendation strategy
    
    This analysis helps users understand their profile and how it influences recommendations.
    """
    profile = get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Generate comprehensive analysis
    insights = get_profile_insights(db, current_user.id)
    
    # Create analysis response
    analysis = ProfileAnalysisResponse(
        user_archetype=insights.get('primary_archetype', 'Unknown'),
        travel_style=insights.get('travel_style', 'Unknown'),
        budget_preference=insights.get('budget_preference', 'Unknown'),
        activity_preferences=insights.get('top_activity_preferences', []),
        dietary_preferences=insights.get('top_dining_preferences', []),
        confidence_scores=insights.get('confidence_scores', {}),
        recommendations_summary=f"Based on your {insights.get('primary_archetype', 'profile')} preferences"
    )
    
    return analysis


# Admin routes for managing other users' profiles
@router.get(
    "/profiles/{user_id}/", 
    response_model=UserProfile,
    summary="Get User Profile (Admin)",
    description="Admin endpoint to retrieve any user's profile by ID.",
    response_description="Complete user profile for the specified user"
)
async def get_user_profile_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user's profile (Admin only).
    
    This endpoint allows administrators to view any user's profile
    for support, analysis, or management purposes.
    """
    # TODO: Add admin role check
    profile = get_user_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get(
    "/profiles/{user_id}/insights/", 
    response_model=Dict[str, Any],
    summary="Get User Profile Insights (Admin)",
    description="Admin endpoint to generate insights for any user's profile.",
    response_description="Profile insights for the specified user"
)
async def get_user_profile_insights_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get insights for a specific user's profile (Admin only).
    
    Generates the same insights as the user-facing endpoint
    but for any user ID specified.
    """
    # TODO: Add admin role check
    insights = get_profile_insights(db, user_id)
    if not insights:
        raise HTTPException(status_code=404, detail="Profile not found")
    return insights


@router.post(
    "/profiles/{user_id}/recommendations/", 
    response_model=ProfileRecommendationResponse,
    summary="Get User Recommendations (Admin)",
    description="Admin endpoint to generate personalized recommendations for any user.",
    response_description="Personalized recommendations for the specified user"
)
async def get_user_recommendations_by_id(
    user_id: int,
    request: ProfileRecommendationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for a specific user (Admin only).
    
    Generates the same recommendations as the user-facing endpoint
    but for any user ID specified.
    """
    # TODO: Add admin role check
    recommendations = get_personalized_recommendations(db, user_id, request)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Profile not found")
    return recommendations 
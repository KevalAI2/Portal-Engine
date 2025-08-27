"""
Users API router
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from core.logging import get_logger
from models.schemas import UserProfile, APIResponse
from services.user_profile import UserProfileService
from services.lie_service import LIEService
from services.cis_service import CISService
from workers.tasks import process_user_comprehensive, generate_user_prompt

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger("users_router")


@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """
    Get comprehensive user profile with mock data
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user profile", user_id=user_id)
        
        user_service = UserProfileService()
        user_profile = await user_service.get_user_profile(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail=f"User profile not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user profile", user_id=user_id)
        return user_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user profile", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user profile"
        )


@router.get("/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """
    Get user preferences with comprehensive mock data
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user preferences", user_id=user_id)
        
        user_service = UserProfileService()
        preferences = await user_service.get_user_preferences(user_id)
        
        if not preferences:
            raise HTTPException(
                status_code=404,
                detail=f"User preferences not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user preferences", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "preferences": preferences,
            "message": "User preferences retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user preferences", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user preferences"
        )


@router.get("/{user_id}/interests")
async def get_user_interests(user_id: str):
    """
    Get user interests
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user interests", user_id=user_id)
        
        user_service = UserProfileService()
        interests = await user_service.get_user_interests(user_id)
        
        if not interests:
            raise HTTPException(
                status_code=404,
                detail=f"User interests not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user interests", user_id=user_id, interest_count=len(interests))
        return {
            "success": True,
            "user_id": user_id,
            "interests": interests,
            "count": len(interests),
            "message": "User interests retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user interests", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user interests"
        )


@router.get("/{user_id}/profile/raw")
async def get_user_profile_raw(user_id: str):
    """
    Get raw user profile data (including all mock data details)
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting raw user profile data", user_id=user_id)
        
        user_service = UserProfileService()
        profile_data = user_service._generate_mock_profile_data(user_id)
        
        logger.info("Retrieved raw user profile data", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "profile_data": profile_data,
            "message": "Raw user profile data retrieved successfully"
        }
        
    except Exception as e:
        logger.error("Error getting raw user profile data", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve raw user profile data"
        )


@router.get("/{user_id}/location")
async def get_user_location_data(user_id: str):
    """
    Get comprehensive location data for a user
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user location data", user_id=user_id)
        
        lie_service = LIEService()
        location_data = await lie_service.get_location_data(user_id)
        
        if not location_data:
            raise HTTPException(
                status_code=404,
                detail=f"Location data not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user location data", user_id=user_id)
        return location_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user location data", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user location data"
        )


@router.get("/{user_id}/location/raw")
async def get_user_location_raw(user_id: str):
    """
    Get raw location data with all details
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting raw user location data", user_id=user_id)
        
        lie_service = LIEService()
        location_data = lie_service._generate_mock_location_data(user_id)
        
        logger.info("Retrieved raw user location data", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "location_data": location_data,
            "message": "Raw user location data retrieved successfully"
        }
        
    except Exception as e:
        logger.error("Error getting raw user location data", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve raw user location data"
        )


@router.get("/{user_id}/location/current")
async def get_user_current_location(user_id: str):
    """
    Get user's current location
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user current location", user_id=user_id)
        
        lie_service = LIEService()
        current_location = await lie_service.get_current_location(user_id)
        
        if not current_location:
            raise HTTPException(
                status_code=404,
                detail=f"Current location not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user current location", user_id=user_id, location=current_location)
        return {
            "success": True,
            "user_id": user_id,
            "current_location": current_location,
            "message": "User current location retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user current location", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user current location"
        )


@router.get("/{user_id}/location/history")
async def get_user_location_history(user_id: str):
    """
    Get user's location history
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user location history", user_id=user_id)
        
        lie_service = LIEService()
        location_history = await lie_service.get_location_history(user_id)
        
        if not location_history:
            raise HTTPException(
                status_code=404,
                detail=f"Location history not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user location history", user_id=user_id, history_count=len(location_history))
        return {
            "success": True,
            "user_id": user_id,
            "location_history": location_history,
            "count": len(location_history),
            "message": "User location history retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user location history", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user location history"
        )


@router.get("/{user_id}/location/insights")
async def get_user_location_insights(user_id: str):
    """
    Get location insights and patterns
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user location insights", user_id=user_id)
        
        lie_service = LIEService()
        insights = await lie_service.get_location_insights(user_id)
        
        if not insights:
            raise HTTPException(
                status_code=404,
                detail=f"Location insights not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user location insights", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "location_insights": insights,
            "message": "User location insights retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user location insights", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user location insights"
        )


@router.get("/{user_id}/interactions")
async def get_user_interaction_data(user_id: str):
    """
    Get comprehensive interaction data for a user
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user interaction data", user_id=user_id)
        
        cis_service = CISService()
        interaction_data = await cis_service.get_interaction_data(user_id)
        
        if not interaction_data:
            raise HTTPException(
                status_code=404,
                detail=f"Interaction data not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user interaction data", user_id=user_id)
        return interaction_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user interaction data", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user interaction data"
        )


@router.get("/{user_id}/interactions/raw")
async def get_user_interaction_raw(user_id: str):
    """
    Get raw interaction data with all details
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting raw user interaction data", user_id=user_id)
        
        cis_service = CISService()
        interaction_data = cis_service._generate_mock_interaction_data(user_id)
        
        logger.info("Retrieved raw user interaction data", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "interaction_data": interaction_data,
            "message": "Raw user interaction data retrieved successfully"
        }
        
    except Exception as e:
        logger.error("Error getting raw user interaction data", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve raw user interaction data"
        )


@router.get("/{user_id}/interactions/recent")
async def get_user_recent_interactions(user_id: str, limit: int = 10):
    """
    Get user's recent interactions
    
    - **user_id**: User identifier
    - **limit**: Number of recent interactions to return (default: 10)
    """
    try:
        logger.info("Getting user recent interactions", user_id=user_id, limit=limit)
        
        cis_service = CISService()
        recent_interactions = await cis_service.get_recent_interactions(user_id, limit)
        
        if not recent_interactions:
            raise HTTPException(
                status_code=404,
                detail=f"Recent interactions not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user recent interactions", user_id=user_id, interaction_count=len(recent_interactions))
        return {
            "success": True,
            "user_id": user_id,
            "recent_interactions": recent_interactions,
            "count": len(recent_interactions),
            "message": "User recent interactions retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user recent interactions", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user recent interactions"
        )


@router.get("/{user_id}/engagement")
async def get_user_engagement_score(user_id: str):
    """
    Get user's engagement score
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user engagement score", user_id=user_id)
        
        cis_service = CISService()
        engagement_score = await cis_service.get_engagement_score(user_id)
        
        if engagement_score is None:
            raise HTTPException(
                status_code=404,
                detail=f"Engagement score not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user engagement score", user_id=user_id, engagement_score=engagement_score)
        return {
            "success": True,
            "user_id": user_id,
            "engagement_score": engagement_score,
            "message": "User engagement score retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user engagement score", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user engagement score"
        )


@router.get("/{user_id}/interactions/insights")
async def get_user_interaction_insights(user_id: str):
    """
    Get interaction insights and patterns
    
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting user interaction insights", user_id=user_id)
        
        cis_service = CISService()
        insights = await cis_service.get_interaction_insights(user_id)
        
        if not insights:
            raise HTTPException(
                status_code=404,
                detail=f"Interaction insights not found for user_id: {user_id}"
            )
        
        logger.info("Retrieved user interaction insights", user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "interaction_insights": insights,
            "message": "User interaction insights retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user interaction insights", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user interaction insights"
        )


@router.post("/{user_id}/process-comprehensive")
async def process_user_comprehensive_endpoint(user_id: str, priority: int = 5):
    """
    Enqueue a user for comprehensive processing via RabbitMQ
    
    - **user_id**: User identifier to process
    - **priority**: Processing priority (1-10, default: 5)
    """
    try:
        logger.info("Enqueueing user for comprehensive processing", user_id=user_id, priority=priority)
        
        # Enqueue the user for comprehensive processing directly
        result = process_user_comprehensive.apply_async(
            args=[user_id],
            queue="user_processing",
            routing_key=f"user_processing_{hash(user_id) % 10}",  # Distribute across workers
            priority=priority,
            expires=None,
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        
        logger.info("User enqueued for comprehensive processing", user_id=user_id, task_id=result.id)
        
        return {
            "success": True,
            "user_id": user_id,
            "priority": priority,
            "task_id": result.id,
            "message": f"User {user_id} enqueued for comprehensive processing",
            "status": "queued",
            "queue": "user_processing"
        }
        
    except Exception as e:
        logger.error("Error enqueueing user for comprehensive processing", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue user {user_id} for comprehensive processing"
        )


@router.post("/{user_id}/process-comprehensive-direct")
async def process_user_comprehensive_direct_endpoint(user_id: str):
    """
    Process a user comprehensively (direct execution, not via queue)
    
    - **user_id**: User identifier to process
    """
    try:
        logger.info("Processing user comprehensively (direct)", user_id=user_id)
        
        # Process the user directly (synchronous)
        result = process_user_comprehensive.delay(user_id)
        
        # Wait for the result
        comprehensive_data = result.get(timeout=30)  # 30 second timeout
        
        if not comprehensive_data.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Comprehensive processing failed: {comprehensive_data.get('error', 'Unknown error')}"
            )
        
        logger.info("User processed comprehensively", user_id=user_id, task_id=result.id)
        
        return {
            "success": True,
            "user_id": user_id,
            "task_id": result.id,
            "comprehensive_data": comprehensive_data.get("comprehensive_data"),
            "message": f"User {user_id} processed comprehensively",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error("Error processing user comprehensively", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process user {user_id} comprehensively"
        )


@router.get("/{user_id}/processing-status/{task_id}")
async def get_processing_status(user_id: str, task_id: str):
    """
    Get the status of a comprehensive processing task
    
    - **user_id**: User identifier
    - **task_id**: Task identifier
    """
    try:
        logger.info("Getting processing status", user_id=user_id, task_id=task_id)
        
        # Import here to avoid circular import
        from workers.celery_app import celery_app
        
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        response = {
            "user_id": user_id,
            "task_id": task_id,
            "status": task_result.status,
            "created_at": task_result.date_done or task_result.date_done,
            "updated_at": task_result.date_done or task_result.date_done
        }
        
        if task_result.successful():
            response["result"] = task_result.result
            response["completed"] = True
        elif task_result.failed():
            response["error"] = str(task_result.info)
            response["completed"] = False
        else:
            response["completed"] = False
        
        logger.info("Retrieved processing status", user_id=user_id, task_id=task_id, status=task_result.status)
        
        return response
        
    except Exception as e:
        logger.error("Error getting processing status", user_id=user_id, task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing status for task {task_id}"
        )

"""
Users API router
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from core.logging import get_logger
from models.schemas import UserProfile, APIResponse
from services.user_profile import UserProfileService
from services.lie_service import LIEService
from services.cis_service import CISService
from services.llm_service import llm_service
from services.results_service import results_service
from workers.tasks import process_user_comprehensive

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


@router.post("/{user_id}/generate-recommendations")
async def generate_recommendations_endpoint(user_id: str, data: dict = Body(...)):
    """Generate recommendations using LLM service"""
    try:
        logger.info(f"Generating recommendations for user {user_id}")
        
        prompt = data.get("prompt", "")
        response = llm_service.generate_recommendations(prompt, user_id)
        
        return APIResponse(
            success=response.get("success", False),
            data=response,
            message="Recommendations generated successfully" if response.get("success") else "Failed to generate recommendations"
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/{user_id}/recommendations")
async def get_user_recommendations(user_id: str):
    """Get stored recommendations for a user"""
    try:
        logger.info(f"Retrieving recommendations for user {user_id}")
        
        recommendations = llm_service.get_recommendations_from_redis(user_id)
        
        if recommendations:
            return APIResponse(
                success=True,
                data=recommendations,
                message="Recommendations retrieved successfully"
            )
        else:
            return APIResponse(
                success=False,
                data=None,
                message="No recommendations found for this user"
            )
        
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving recommendations: {str(e)}")


@router.delete("/{user_id}/recommendations")
async def clear_user_recommendations(user_id: str):
    """Clear stored recommendations for a user"""
    try:
        logger.info(f"Clearing recommendations for user {user_id}")
        
        llm_service.clear_recommendations(user_id)
        
        return APIResponse(
            success=True,
            data=None,
            message="Recommendations cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Error clearing recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing recommendations: {str(e)}")


@router.post("/generate-recommendations")
async def generate_recommendations_direct(data: dict = Body(...)):
    """Generate recommendations without storing (for testing)"""
    try:
        logger.info("Generating recommendations without storing")
        
        prompt = data.get("prompt", "")
        response = llm_service.generate_recommendations(prompt)
        
        return APIResponse(
            success=response.get("success", False),
            data=response,
            message="Recommendations generated successfully" if response.get("success") else "Failed to generate recommendations"
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/{user_id}/results")
async def get_ranked_results(
    user_id: str,
    category: Optional[str] = Query(None, description="Filter by category (movies, music, places, events)"),
    limit: Optional[int] = Query(5, description="Limit results per category"),
    min_score: Optional[float] = Query(0.0, description="Minimum ranking score")
):
    """
    Get ranked and filtered final results for a user
    
    - **user_id**: User identifier
    - **category**: Optional category filter
    - **limit**: Maximum results per category (default: 5)
    - **min_score**: Minimum ranking score (default: 0.0)
    """
    try:
        logger.info(f"Getting ranked results for user {user_id}")
        
        # Prepare filters
        filters = {
            "category": category,
            "limit": limit,
            "min_score": min_score
        }
        
        # Get ranked results
        results = results_service.get_ranked_results(user_id, filters)
        
        if results.get("success"):
            return APIResponse(
                success=True,
                data=results,
                message="Ranked results retrieved successfully"
            )
        else:
            return APIResponse(
                success=False,
                data=None,
                message=results.get("error", "No results found")
            )
        
    except Exception as e:
        logger.error(f"Error getting ranked results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting ranked results: {str(e)}")

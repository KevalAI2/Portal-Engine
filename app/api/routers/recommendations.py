"""
Recommendations API router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.logging import get_logger
from app.core.constants import RecommendationType, API_MESSAGES, SUPPORTED_RECOMMENDATION_TYPES
from app.models.schemas import (
    RecommendationResponse, 
    RefreshRequest, 
    APIResponse,
    TaskStatusResponse
)
from app.services.cache_service import CacheService
from app.workers.celery_app import celery_app
from app.workers.tasks import generate_recommendations
from app.api.dependencies import get_cache_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = get_logger("recommendations_router")


@router.get("/{recommendation_type}", response_model=RecommendationResponse)
async def get_recommendations(
    recommendation_type: RecommendationType,
    user_id: str = Query(..., description="User identifier"),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Get recommendations for a specific type
    
    - **recommendation_type**: Type of recommendations (music, movie, place, event)
    - **user_id**: User identifier
    """
    try:
        logger.info("Getting recommendations", user_id=user_id, type=recommendation_type)
        
        # Validate recommendation type
        if recommendation_type not in SUPPORTED_RECOMMENDATION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=API_MESSAGES["invalid_recommendation_type"]
            )
        
        # Get recommendations from cache
        recommendations = await cache_service.get_recommendations(user_id, recommendation_type.value)
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=API_MESSAGES["recommendation_not_found"]
            )
        
        logger.info("Retrieved recommendations", user_id=user_id, type=recommendation_type, count=recommendations.total_count)
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting recommendations", user_id=user_id, type=recommendation_type, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=API_MESSAGES["service_unavailable"]
        )


@router.post("/refresh/{user_id}", response_model=APIResponse)
async def refresh_recommendations(
    user_id: str,
    request: RefreshRequest,
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Manually trigger refresh of recommendations for a user
    
    - **user_id**: User identifier
    - **request**: Refresh request with force option
    """
    try:
        logger.info("Refreshing recommendations", user_id=user_id, force=request.force)
        
        # Trigger background task for each recommendation type
        tasks = []
        for rec_type in SUPPORTED_RECOMMENDATION_TYPES:
            task = generate_recommendations.delay(
                user_id=user_id,
                recommendation_type=rec_type.value,
                force_refresh=request.force
            )
            tasks.append({
                "type": rec_type.value,
                "task_id": task.id
            })
        
        logger.info("Refresh tasks triggered", user_id=user_id, task_count=len(tasks))
        
        return APIResponse(
            success=True,
            message=API_MESSAGES["task_triggered"],
            data={
                "user_id": user_id,
                "tasks": tasks,
                "force_refresh": request.force
            }
        )
        
    except Exception as e:
        logger.error("Error refreshing recommendations", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger recommendation refresh"
        )


@router.get("/types", response_model=List[str])
async def get_recommendation_types():
    """
    Get list of supported recommendation types
    """
    return [rt.value for rt in SUPPORTED_RECOMMENDATION_TYPES]


@router.delete("/{recommendation_type}")
async def delete_recommendations(
    recommendation_type: RecommendationType,
    user_id: str = Query(..., description="User identifier"),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Delete cached recommendations for a user and type
    
    - **recommendation_type**: Type of recommendations to delete
    - **user_id**: User identifier
    """
    try:
        logger.info("Deleting recommendations", user_id=user_id, type=recommendation_type)
        
        success = await cache_service.delete_recommendations(user_id, recommendation_type.value)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete recommendations"
            )
        
        return APIResponse(
            success=True,
            message="Recommendations deleted successfully",
            data={
                "user_id": user_id,
                "type": recommendation_type.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting recommendations", user_id=user_id, type=recommendation_type, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to delete recommendations"
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a background task
    
    - **task_id**: Task identifier
    """
    try:
        logger.info("Getting task status", task_id=task_id)
        
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        # Build response
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
            created_at=task_result.date_done or task_result.date_done,
            updated_at=task_result.date_done or task_result.date_done
        )
        
        if task_result.successful():
            response.result = task_result.result
        elif task_result.failed():
            response.error = str(task_result.info)
        
        return response
        
    except Exception as e:
        logger.error("Error getting task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to get task status"
        )

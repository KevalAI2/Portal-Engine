"""
Async Celery tasks with proper async/await patterns
"""
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from celery import Celery
from app.workers.celery_app import celery_app
from app.core.logging import get_logger, log_background_task, log_exception
from app.core.config import settings
from app.core.constants import RecommendationType
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.llm_service import llm_service
from app.services.cache_service import cache_service
from app.utils.prompt_builder import PromptBuilder
import time

logger = get_logger("async_celery_tasks")


class AsyncTaskExecutor:
    """Helper class to execute async operations in Celery tasks"""
    
    @staticmethod
    def run_async(coro):
        """Run async coroutine in new event loop"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            logger.error("Async execution failed", error=str(e))
            raise


@celery_app.task(
    bind=True, 
    name="async_fetch_user_data",
    autoretry_for=(ConnectionError, TimeoutError, HTTPException,),
    retry_kwargs={'max_retries': 5, 'countdown': 30},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def async_fetch_user_data(self, user_id: str) -> Dict[str, Any]:
    """Async fetch user data from external services"""
    task_id = self.request.id
    log_background_task("async_fetch_user_data", task_id, "started", user_id=user_id)
    
    async def _fetch_data():
        """Async data fetching logic"""
        try:
            logger.info("Starting async user data fetch", user_id=user_id, task_id=task_id)
            
            # Create service instances
            user_service = UserProfileService(timeout=30)
            lie_service = LIEService(timeout=30)
            cis_service = CISService(timeout=30)
            
            # Fetch data concurrently
            user_profile_task = user_service.get_user_profile(user_id)
            location_data_task = lie_service.get_location_data(user_id)
            interaction_data_task = cis_service.get_interaction_data(user_id)
            
            # Wait for all tasks to complete
            user_profile, location_data, interaction_data = await asyncio.gather(
                user_profile_task,
                location_data_task,
                interaction_data_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(user_profile, Exception):
                logger.warning("User profile fetch failed", user_id=user_id, error=str(user_profile))
                user_profile = None
            if isinstance(location_data, Exception):
                logger.warning("Location data fetch failed", user_id=user_id, error=str(location_data))
                location_data = None
            if isinstance(interaction_data, Exception):
                logger.warning("Interaction data fetch failed", user_id=user_id, error=str(interaction_data))
                interaction_data = None
            
            # Combine all data
            user_data = {
                "user_profile": user_profile.model_dump() if user_profile else None,
                "location_data": location_data.model_dump() if location_data else None,
                "interaction_data": interaction_data.model_dump() if interaction_data else None,
                "fetched_at": time.time()
            }
            
            # Cache the data
            await cache_service.set("user_data", user_id, user_data)
            
            log_background_task("async_fetch_user_data", task_id, "completed", user_id=user_id)
            logger.info("Async user data fetch completed", user_id=user_id, task_id=task_id)
            
            return {
                "success": True,
                "user_data": user_data,
                "message": "User data fetched successfully"
            }
            
        except Exception as e:
            log_background_task("async_fetch_user_data", task_id, "failed", user_id=user_id, error=str(e))
            logger.error("Async user data fetch failed", user_id=user_id, task_id=task_id, error=str(e))
            log_exception("async_celery_tasks", e, {"user_id": user_id, "task": "async_fetch_user_data", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to fetch user data"
            }
    
    try:
        return AsyncTaskExecutor.run_async(_fetch_data())
    except Exception as e:
        log_background_task("async_fetch_user_data", task_id, "failed", user_id=user_id, error=str(e))
        logger.error("Async fetch execution failed", user_id=user_id, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute async fetch"
        }


@celery_app.task(
    bind=True, 
    name="async_build_prompt",
    autoretry_for=(ValueError, KeyError, TypeError,),
    retry_kwargs={'max_retries': 3, 'countdown': 15},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def async_build_prompt(self, user_data: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Async build dynamic prompt for recommendation generation"""
    task_id = self.request.id
    log_background_task("async_build_prompt", task_id, "started", recommendation_type=recommendation_type)
    
    async def _build_prompt():
        """Async prompt building logic"""
        try:
            logger.info("Building async prompt", recommendation_type=recommendation_type, task_id=task_id)
            
            # Validate recommendation type
            if recommendation_type not in [rt.value for rt in RecommendationType]:
                raise ValueError(f"Invalid recommendation type: {recommendation_type}")
            
            # Create prompt builder
            prompt_builder = PromptBuilder()
            
            # Extract user data components
            user_profile_data = user_data.get("user_profile")
            location_data = user_data.get("location_data")
            interaction_data = user_data.get("interaction_data")
            
            # Check if any component is missing
            missing_any = not any([user_profile_data, location_data, interaction_data])
            
            if missing_any:
                logger.warning("Missing user data components, using fallback prompt", 
                             recommendation_type=recommendation_type, task_id=task_id)
                prompt = await prompt_builder.build_fallback_prompt(recommendation_type)
            else:
                # Build comprehensive prompt
                prompt = await prompt_builder.build_prompt(
                    user_profile_data=user_profile_data,
                    location_data=location_data,
                    interaction_data=interaction_data,
                    recommendation_type=recommendation_type
                )
            
            # Cache the prompt
            await cache_service.set("prompt", f"{user_data.get('user_id', 'unknown')}_{recommendation_type}", {
                "prompt": prompt,
                "recommendation_type": recommendation_type,
                "built_at": time.time()
            })
            
            log_background_task("async_build_prompt", task_id, "completed", recommendation_type=recommendation_type)
            logger.info("Async prompt built successfully", recommendation_type=recommendation_type, task_id=task_id)
            
            return {
                "success": True,
                "prompt": prompt,
                "recommendation_type": recommendation_type,
                "message": "Prompt built successfully"
            }
            
        except Exception as e:
            log_background_task("async_build_prompt", task_id, "failed", recommendation_type=recommendation_type, error=str(e))
            logger.error("Async prompt building failed", recommendation_type=recommendation_type, task_id=task_id, error=str(e))
            log_exception("async_celery_tasks", e, {"recommendation_type": recommendation_type, "task": "async_build_prompt", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to build prompt"
            }
    
    try:
        return AsyncTaskExecutor.run_async(_build_prompt())
    except Exception as e:
        log_background_task("async_build_prompt", task_id, "failed", recommendation_type=recommendation_type, error=str(e))
        logger.error("Async prompt execution failed", recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute async prompt building"
        }


@celery_app.task(
    bind=True, 
    name="async_call_llm",
    autoretry_for=(ConnectionError, TimeoutError, HTTPException, ValueError,),
    retry_kwargs={'max_retries': 4, 'countdown': 20},
    retry_backoff=True,
    retry_backoff_max=400,
    retry_jitter=True
)
def async_call_llm(self, prompt: str, user_context: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Async call LLM service to generate recommendations"""
    task_id = self.request.id
    log_background_task("async_call_llm", task_id, "started", recommendation_type=recommendation_type)
    
    async def _call_llm():
        """Async LLM calling logic"""
        try:
            logger.info("Starting async LLM call", recommendation_type=recommendation_type, task_id=task_id)
            
            # Call LLM service asynchronously
            recommendations = await llm_service.generate_recommendations_async(
                prompt=prompt,
                user_context=user_context,
                recommendation_type=recommendation_type
            )
            
            if not recommendations:
                raise ValueError("No recommendations generated by LLM")
            
            # Cache the recommendations
            user_id = user_context.get("user_id", "unknown")
            await cache_service.set("recommendations", f"{user_id}_{recommendation_type}", {
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "generated_at": time.time()
            })
            
            log_background_task("async_call_llm", task_id, "completed", 
                               recommendation_type=recommendation_type, 
                               recommendations_count=len(recommendations))
            logger.info("Async LLM call completed", 
                       recommendation_type=recommendation_type, 
                       task_id=task_id, 
                       count=len(recommendations))
            
            return {
                "success": True,
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "message": "Recommendations generated successfully"
            }
            
        except Exception as e:
            log_background_task("async_call_llm", task_id, "failed", 
                               recommendation_type=recommendation_type, 
                               error=str(e))
            logger.error("Async LLM call failed", 
                       recommendation_type=recommendation_type, 
                       task_id=task_id, 
                       error=str(e))
            log_exception("async_celery_tasks", e, {"recommendation_type": recommendation_type, "task": "async_call_llm", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate recommendations"
            }
    
    try:
        return AsyncTaskExecutor.run_async(_call_llm())
    except Exception as e:
        log_background_task("async_call_llm", task_id, "failed", recommendation_type=recommendation_type, error=str(e))
        logger.error("Async LLM execution failed", recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute async LLM call"
        }


@celery_app.task(
    bind=True, 
    name="async_cache_results",
    autoretry_for=(ConnectionError, TimeoutError, ValueError,),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=200,
    retry_jitter=True
)
def async_cache_results(self, user_id: str, recommendations: List[Dict[str, Any]], recommendation_type: str) -> Dict[str, Any]:
    """Async cache recommendation results in Redis"""
    task_id = self.request.id
    log_background_task("async_cache_results", task_id, "started", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type,
                       recommendations_count=len(recommendations))
    
    async def _cache_results():
        """Async caching logic"""
        try:
            logger.info("Caching async results", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id,
                       recommendations_count=len(recommendations))
            
            # Store recommendations in cache asynchronously
            success = await llm_service.store_recommendations_async(
                user_id=user_id,
                recommendation_type=recommendation_type,
                recommendations=recommendations
            )
            
            if not success:
                raise ValueError("Failed to store recommendations in cache")
            
            log_background_task("async_cache_results", task_id, "completed", 
                               user_id=user_id, 
                               recommendation_type=recommendation_type,
                               cached_count=len(recommendations))
            logger.info("Async results cached successfully", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id,
                       cached_count=len(recommendations))
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "cached_count": len(recommendations),
                "message": "Results cached successfully"
            }
            
        except Exception as e:
            log_background_task("async_cache_results", task_id, "failed", 
                               user_id=user_id, 
                               recommendation_type=recommendation_type,
                               error=str(e))
            logger.error("Async caching failed", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id, 
                       error=str(e))
            log_exception("async_celery_tasks", e, {"user_id": user_id, "recommendation_type": recommendation_type, "task": "async_cache_results", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cache results"
            }
    
    try:
        return AsyncTaskExecutor.run_async(_cache_results())
    except Exception as e:
        log_background_task("async_cache_results", task_id, "failed", user_id=user_id, recommendation_type=recommendation_type, error=str(e))
        logger.error("Async cache execution failed", user_id=user_id, recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute async caching"
        }


@celery_app.task(
    bind=True, 
    name="async_generate_recommendations",
    autoretry_for=(ConnectionError, TimeoutError, HTTPException, ValueError,),
    retry_kwargs={'max_retries': 3, 'countdown': 15},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def async_generate_recommendations(self, user_id: str, recommendation_type: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Async complete recommendation generation workflow"""
    task_id = self.request.id
    log_background_task("async_generate_recommendations", task_id, "started", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type,
                       force_refresh=force_refresh)
    
    async def _generate_recommendations():
        """Async recommendation generation workflow"""
        try:
            logger.info("Starting async recommendation generation", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id)
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = await cache_service.get("recommendations", f"{user_id}_{recommendation_type}")
                if cached_data:
                    logger.info("Using cached recommendations", user_id=user_id, recommendation_type=recommendation_type)
                    return {
                        "success": True,
                        "user_id": user_id,
                        "recommendation_type": recommendation_type,
                        "recommendations": cached_data.get("recommendations", []),
                        "cached": True,
                        "message": "Recommendations retrieved from cache"
                    }
            
            # Fetch user data
            user_data_result = await async_fetch_user_data(user_id)
            if not user_data_result.get("success"):
                raise ValueError(f"Failed to fetch user data: {user_data_result.get('error')}")
            
            user_data = user_data_result["user_data"]
            
            # Build prompt
            prompt_result = await async_build_prompt(user_data, recommendation_type)
            if not prompt_result.get("success"):
                raise ValueError(f"Failed to build prompt: {prompt_result.get('error')}")
            
            prompt = prompt_result["prompt"]
            
            # Call LLM
            llm_result = await async_call_llm(prompt, user_data, recommendation_type)
            if not llm_result.get("success"):
                raise ValueError(f"Failed to call LLM: {llm_result.get('error')}")
            
            recommendations = llm_result["recommendations"]
            
            # Cache results
            cache_result = await async_cache_results(user_id, recommendations, recommendation_type)
            if not cache_result.get("success"):
                logger.warning("Failed to cache results", user_id=user_id, error=cache_result.get("error"))
            
            log_background_task("async_generate_recommendations", task_id, "completed", 
                               user_id=user_id, 
                               recommendation_type=recommendation_type,
                               recommendations_count=len(recommendations))
            logger.info("Async recommendation generation completed", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id,
                       count=len(recommendations))
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "recommendations": recommendations,
                "cached": False,
                "message": "Recommendations generated successfully"
            }
            
        except Exception as e:
            log_background_task("async_generate_recommendations", task_id, "failed", 
                               user_id=user_id, 
                               recommendation_type=recommendation_type,
                               error=str(e))
            logger.error("Async recommendation generation failed", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id, 
                       error=str(e))
            log_exception("async_celery_tasks", e, {"user_id": user_id, "recommendation_type": recommendation_type, "task": "async_generate_recommendations", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate recommendations"
            }
    
    try:
        return AsyncTaskExecutor.run_async(_generate_recommendations())
    except Exception as e:
        log_background_task("async_generate_recommendations", task_id, "failed", user_id=user_id, recommendation_type=recommendation_type, error=str(e))
        logger.error("Async generation execution failed", user_id=user_id, recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute async recommendation generation"
        }

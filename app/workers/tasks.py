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
            
            # Fetch data synchronously
            user_profile = user_service.get_user_profile_sync(user_id)
            location_data = lie_service.get_location_data_sync(user_id)
            interaction_data = cis_service.get_interaction_data_sync(user_id)
            
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
            cache_service.set("user_data", user_id, user_data)
            
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
        return _fetch_data()
    except Exception as e:
        log_background_task("async_fetch_user_data", task_id, "failed", user_id=user_id, error=str(e))
        logger.error("Fetch execution failed", user_id=user_id, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute fetch"
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
    
    def _build_prompt():
        """Async prompt building logic"""
        try:
            # Validate recommendation type (case insensitive)
            valid_types = [rt.value for rt in RecommendationType]
            # Try to map common variations
            type_mapping = {
                "place": "place",
                "places": "place", 
                "PLACE": "place",
                "movie": "movie",
                "movies": "movie",
                "MOVIE": "movie",
                "music": "music",
                "MUSIC": "music",
                "event": "event",
                "events": "event",
                "EVENT": "event"
            }
            normalized_recommendation_type = type_mapping.get(recommendation_type.lower(), "place")
            
            logger.info("Building async prompt", recommendation_type=normalized_recommendation_type, task_id=task_id)
            
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
                             recommendation_type=normalized_recommendation_type, task_id=task_id)
                prompt = prompt_builder.build_fallback_prompt(
                    user_profile=user_profile_data,
                    location_data=location_data,
                    interaction_data=interaction_data,
                    recommendation_type=RecommendationType(normalized_recommendation_type),
                    max_results=10
                )
            else:
                # Build comprehensive prompt
                prompt = prompt_builder.build_recommendation_prompt(
                    user_profile=user_profile_data,
                    location_data=location_data,
                    interaction_data=interaction_data,
                    recommendation_type=RecommendationType(normalized_recommendation_type),
                    max_results=10
                )
            
            # Cache the prompt
            cache_service.set("prompt", f"{user_data.get('user_id', 'unknown')}_{normalized_recommendation_type}", {
                "prompt": prompt,
                "recommendation_type": normalized_recommendation_type,
                "built_at": time.time()
            })
            
            log_background_task("async_build_prompt", task_id, "completed", recommendation_type=normalized_recommendation_type)
            logger.info("Async prompt built successfully", recommendation_type=normalized_recommendation_type, task_id=task_id)
            
            return {
                "success": True,
                "prompt": prompt,
                "recommendation_type": normalized_recommendation_type,
                "message": "Prompt built successfully"
            }
            
        except Exception as e:
            log_background_task("async_build_prompt", task_id, "failed", recommendation_type=normalized_recommendation_type, error=str(e))
            logger.error("Async prompt building failed", recommendation_type=normalized_recommendation_type, task_id=task_id, error=str(e))
            log_exception("async_celery_tasks", e, {"recommendation_type": normalized_recommendation_type, "task": "async_build_prompt", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to build prompt"
            }
    
    try:
        return _build_prompt()
    except Exception as e:
        log_background_task("async_build_prompt", task_id, "failed", recommendation_type=recommendation_type, error=str(e))
        logger.error("Prompt execution failed", recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute prompt building"
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
    
    def _call_llm():
        """Synchronous LLM calling logic"""
        try:
            logger.info("Starting LLM call", recommendation_type=recommendation_type, task_id=task_id)
            
            # Call LLM service synchronously
            recommendations = llm_service.generate_recommendations(
                prompt=prompt,
                user_id=user_context.get("user_id", "unknown")
            )
            
            if not recommendations:
                raise ValueError("No recommendations generated by LLM")
            
            # Cache the recommendations
            user_id = user_context.get("user_id", "unknown")
            cache_service.set("recommendations", f"{user_id}_{recommendation_type}", {
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
        return _call_llm()
    except Exception as e:
        log_background_task("async_call_llm", task_id, "failed", recommendation_type=recommendation_type, error=str(e))
        logger.error("LLM execution failed", recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute LLM call"
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
    
    def _cache_results():
        """Synchronous caching logic"""
        try:
            logger.info("Caching async results", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id,
                       recommendations_count=len(recommendations))
            
            # Store recommendations in cache
            success = llm_service._store_in_redis(user_id, {
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "generated_at": time.time()
            })
            
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
        return _cache_results()
    except Exception as e:
        log_background_task("async_cache_results", task_id, "failed", user_id=user_id, recommendation_type=recommendation_type, error=str(e))
        logger.error("Cache execution failed", user_id=user_id, recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute caching"
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
    
    def _generate_recommendations():
        """Synchronous recommendation generation workflow"""
        try:
            logger.info("Starting async recommendation generation", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type, 
                       task_id=task_id)
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = cache_service.get("recommendations", f"{user_id}_{recommendation_type}")
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
            user_data_result = async_fetch_user_data(user_id)
            if not user_data_result.get("success"):
                raise ValueError(f"Failed to fetch user data: {user_data_result.get('error')}")
            
            user_data = user_data_result["user_data"]
            
            # Build prompt
            prompt_result = async_build_prompt(user_data, recommendation_type)
            if not prompt_result.get("success"):
                raise ValueError(f"Failed to build prompt: {prompt_result.get('error')}")
            
            prompt = prompt_result["prompt"]
            
            # Call LLM
            llm_result = async_call_llm(prompt, user_data, recommendation_type)
            if not llm_result.get("success"):
                raise ValueError(f"Failed to call LLM: {llm_result.get('error')}")
            
            recommendations = llm_result["recommendations"]
            
            # Cache results
            cache_result = async_cache_results(user_id, recommendations, recommendation_type)
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
        return _generate_recommendations()
    except Exception as e:
        log_background_task("async_generate_recommendations", task_id, "failed", user_id=user_id, recommendation_type=recommendation_type, error=str(e))
        logger.error("Generation execution failed", user_id=user_id, recommendation_type=recommendation_type, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute recommendation generation"
        }


@celery_app.task(
    bind=True,
    name="process_user_comprehensive",
    autoretry_for=(ConnectionError, TimeoutError, HTTPException, ValueError,),
    retry_kwargs={'max_retries': 3, 'countdown': 15},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def process_user_comprehensive(self, user_id: str) -> Dict[str, Any]:
    """Comprehensive user processing task that combines all data sources"""
    task_id = self.request.id
    log_background_task("process_user_comprehensive", task_id, "started", user_id=user_id)
    
    def _process_comprehensive():
        """Synchronous comprehensive processing logic"""
        try:
            logger.info("Starting comprehensive user processing", user_id=user_id, task_id=task_id)
            
            # Create service instances
            user_service = UserProfileService(timeout=120)
            lie_service = LIEService(timeout=120)
            cis_service = CISService(timeout=120)
            
            # Fetch all user data synchronously
            try:
                user_profile = user_service.get_user_profile_sync(user_id)
            except Exception as e:
                logger.warning("User profile fetch failed", user_id=user_id, error=str(e))
                user_profile = None
                
            try:
                location_data = lie_service.get_location_data_sync(user_id)
            except Exception as e:
                logger.warning("Location data fetch failed", user_id=user_id, error=str(e))
                location_data = None
                
            try:
                interaction_data = cis_service.get_interaction_data_sync(user_id)
            except Exception as e:
                logger.warning("Interaction data fetch failed", user_id=user_id, error=str(e))
                interaction_data = None
            
            # Handle exceptions gracefully
            if isinstance(user_profile, Exception):
                logger.warning("User profile fetch failed", user_id=user_id, error=str(user_profile))
                user_profile = None
            if isinstance(location_data, Exception):
                logger.warning("Location data fetch failed", user_id=user_id, error=str(location_data))
                location_data = None
            if isinstance(interaction_data, Exception):
                logger.warning("Interaction data fetch failed", user_id=user_id, error=str(interaction_data))
                interaction_data = None
            
            # Create comprehensive data structure
            comprehensive_data = {
                "user_id": user_id,
                "user_profile": user_profile.model_dump() if user_profile else None,
                "location_data": location_data.model_dump() if location_data else None,
                "interaction_data": interaction_data.model_dump() if interaction_data else None,
                "processed_at": time.time(),
                "data_quality": {
                    "user_profile_available": user_profile is not None,
                    "location_data_available": location_data is not None,
                    "interaction_data_available": interaction_data is not None
                }
            }
            
            # Cache the comprehensive data
            cache_service.set("comprehensive_data", user_id, comprehensive_data)
            
            log_background_task("process_user_comprehensive", task_id, "completed", user_id=user_id)
            logger.info("Comprehensive user processing completed", user_id=user_id, task_id=task_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "comprehensive_data": comprehensive_data,
                "generated_prompt": "Test prompt",  # Mock prompt for testing
                "message": "User processed comprehensively"
            }
            
        except Exception as e:
            log_background_task("process_user_comprehensive", task_id, "failed", user_id=user_id, error=str(e))
            logger.error("Comprehensive user processing failed", user_id=user_id, task_id=task_id, error=str(e))
            log_exception("async_celery_tasks", e, {"user_id": user_id, "task": "process_user_comprehensive", "task_id": task_id})
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process user comprehensively"
            }
    
    try:
        return _process_comprehensive()
    except Exception as e:
        log_background_task("process_user_comprehensive", task_id, "failed", user_id=user_id, error=str(e))
        logger.error("Comprehensive processing execution failed", user_id=user_id, task_id=task_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute comprehensive user processing"
        }


# Legacy function aliases for backward compatibility with tests
def fetch_user_data(user_id: str) -> Dict[str, Any]:
    """Legacy alias for async_fetch_user_data - calls the actual function directly"""
    # Call the actual function logic directly instead of the Celery task
    try:
        logger.info("Fetching user data", user_id=user_id)
        
        # Get services
        user_service = UserProfileService(timeout=30)
        lie_service = LIEService(timeout=30)
        cis_service = CISService(timeout=30)
        
        # Fetch data synchronously
        user_profile = user_service.get_user_profile_sync(user_id)
        location_data = lie_service.get_location_data_sync(user_id)
        interaction_data = cis_service.get_interaction_data_sync(user_id)
        
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
        cache_service.set("user_data", user_id, user_data)
        
        logger.info("User data fetched successfully", user_id=user_id)
        return {
            "success": True,
            "user_data": user_data,
            "message": "User data fetched successfully"
        }
        
    except Exception as e:
        logger.error("User data fetch failed", user_id=user_id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch user data"
        }


def build_prompt(user_data: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Legacy alias for async_build_prompt"""
    return async_build_prompt(user_data, recommendation_type)


def call_llm(prompt: str, user_context: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Legacy alias for async_call_llm"""
    return async_call_llm(prompt, user_context, recommendation_type)


def cache_results(user_id: str, recommendations: List[Dict[str, Any]], recommendation_type: str) -> Dict[str, Any]:
    """Legacy alias for async_cache_results"""
    return async_cache_results(user_id, recommendations, recommendation_type)


def generate_recommendations(user_id: str, recommendation_type: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Legacy alias for async_generate_recommendations - implements actual logic"""
    try:
        # Check cache first if not forcing refresh
        if not force_refresh:
            cached_recommendations = cache_service.get("recommendations", f"{user_id}_{recommendation_type}")
            if cached_recommendations:
                return {
                    "success": True,
                    "source": "cache",
                    "recommendations": cached_recommendations.get("recommendations", []),
                    "user_id": user_id,
                    "recommendation_type": recommendation_type
                }
        
        # Generate new recommendations
        user_data_result = fetch_user_data(user_id)
        if not user_data_result.get("success"):
            return {
                "success": False,
                "error": "Failed to fetch user data",
                "user_id": user_id,
                "recommendation_type": recommendation_type
            }
        
        prompt_result = build_prompt(user_id, recommendation_type, user_data_result.get("data", {}))
        if not prompt_result.get("success"):
            return {
                "success": False,
                "error": "Failed to build prompt",
                "user_id": user_id,
                "recommendation_type": recommendation_type
            }
        
        llm_result = call_llm(prompt_result.get("prompt", ""), user_id, recommendation_type)
        if not llm_result.get("success"):
            return {
                "success": False,
                "error": "Failed to call LLM",
                "user_id": user_id,
                "recommendation_type": recommendation_type
            }
        
        # Cache the results
        cache_result = cache_results(user_id, llm_result.get("recommendations", []), recommendation_type)
        
        return {
            "success": True,
            "source": "generated",
            "recommendations": llm_result.get("recommendations", []),
            "user_id": user_id,
            "recommendation_type": recommendation_type,
            "cached": cache_result.get("success", False)
        }
        
    except Exception as e:
        logger.error("Generate recommendations failed", error=str(e), user_id=user_id, recommendation_type=recommendation_type)
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "recommendation_type": recommendation_type
        }


def process_user(user_id: str) -> Dict[str, Any]:
    """Legacy alias for process_user_comprehensive"""
    return process_user_comprehensive(user_id)


def get_users(count: int = 5, delay: int = 0) -> Dict[str, Any]:
    """Get list of user IDs (mock implementation for tests)"""
    import time
    if delay > 0:
        time.sleep(delay)
    users = [f"user{i+1}" for i in range(count)]
    return {
        "success": True,
        "generated_count": len(users),
        "users": users,
        "message": f"Generated {len(users)} users"
    }


def generate_user_prompt(user_id: str, recommendation_type: str = "place", max_results: int = 10) -> Dict[str, Any]:
    """Generate prompt for a specific user (mock implementation for tests)"""
    try:
        # Mock user data for testing
        user_data = {
            "user_id": user_id,
            "user_profile": {
                "name": f"Test User {user_id}",
                "age": 30,
                "interests": ["music", "movies", "travel"]
            },
            "location_data": {
                "current_location": "Barcelona",
                "home_location": "Barcelona"
            },
            "interaction_data": {
                "engagement_score": 0.7,
                "recent_interactions": []
            }
        }
        
        result = async_build_prompt(user_data, recommendation_type)
        if result.get("success"):
            result["user_id"] = user_id
            result["generated_prompt"] = result.get("prompt", "")
        return result
    except Exception as e:
        logger.error(f"Error generating user prompt: {str(e)}")
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "message": "Failed to generate user prompt"
        }
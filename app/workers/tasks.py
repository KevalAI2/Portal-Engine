"""
Celery tasks for recommendation processing
"""
import asyncio
from typing import Dict, Any, List, Optional
from app.workers.celery_app import celery_app
from app.core.logging import get_logger
from app.core.constants import RecommendationType, TaskStatus
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.prefetch_service import PrefetchService
from app.services.cache_service import CacheService
from app.utils.prompt_builder import PromptBuilder


logger = get_logger("celery_tasks")


@celery_app.task(bind=True, name="fetch_user_data")
def fetch_user_data(self, user_id: str) -> Dict[str, Any]:
    """Fetch user data from external services"""
    try:
        logger.info("Starting user data fetch", user_id=user_id, task_id=self.request.id)
        
        # Create service instances
        user_service = UserProfileService()
        lie_service = LIEService()
        cis_service = CISService()
        cache_service = CacheService()
        
        # Run async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Fetch data from all services
            user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
            location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
            interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
            
            # Combine all data
            user_data = {
                "user_profile": user_profile.model_dump() if user_profile else None,
                "location_data": location_data.model_dump() if location_data else None,
                "interaction_data": interaction_data.model_dump() if interaction_data else None,
                "fetched_at": asyncio.get_event_loop().time()
            }
            
            # Cache the user data
            loop.run_until_complete(cache_service.store_user_data(user_id, user_data))
            
            logger.info("User data fetch completed", user_id=user_id, task_id=self.request.id)
            
            return {
                "success": True,
                "user_data": user_data,
                "message": "User data fetched successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("User data fetch failed", user_id=user_id, task_id=self.request.id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch user data"
        }


@celery_app.task(bind=True, name="build_prompt")
def build_prompt(self, user_data: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Build dynamic prompt for recommendation generation"""
    try:
        logger.info("Building prompt", recommendation_type=recommendation_type, task_id=self.request.id)
        
        # Validate recommendation type
        if recommendation_type not in [rt.value for rt in RecommendationType]:
            raise ValueError(f"Invalid recommendation type: {recommendation_type}")
        
        # Create prompt builder
        prompt_builder = PromptBuilder()
        
        # Extract user data components
        user_profile_data = user_data.get("user_profile")
        location_data = user_data.get("location_data")
        interaction_data = user_data.get("interaction_data")
        
        if not all([user_profile_data, location_data, interaction_data]):
            raise ValueError("Incomplete user data for prompt building")
        
        # Convert to Pydantic models
        from app.models.schemas import UserProfile, LocationData, InteractionData
        
        user_profile = UserProfile(**user_profile_data)
        location = LocationData(**location_data)
        interaction = InteractionData(**interaction_data)
        
        # Build the prompt
        prompt = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=location,
            interaction_data=interaction,
            recommendation_type=RecommendationType(recommendation_type),
            max_results=10
        )
        
        logger.info("Prompt built successfully", recommendation_type=recommendation_type, task_id=self.request.id)
        
        return {
            "success": True,
            "prompt": prompt,
            "recommendation_type": recommendation_type,
            "message": "Prompt built successfully"
        }
        
    except Exception as e:
        logger.error("Prompt building failed", recommendation_type=recommendation_type, task_id=self.request.id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to build prompt"
        }


@celery_app.task(bind=True, name="call_llm")
def call_llm(self, prompt: str, user_context: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Call LLM service to generate recommendations"""
    try:
        logger.info("Calling LLM service", recommendation_type=recommendation_type, task_id=self.request.id)
        
        # Create prefetch service
        prefetch_service = PrefetchService()
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generate recommendations
            recommendations = loop.run_until_complete(
                prefetch_service.generate_recommendations(
                    prompt=prompt,
                    user_context=user_context,
                    recommendation_type=recommendation_type,
                    max_results=10
                )
            )
            
            if not recommendations:
                raise ValueError("No recommendations generated by LLM")
            
            logger.info("LLM call completed", recommendation_type=recommendation_type, task_id=self.request.id, count=len(recommendations))
            
            return {
                "success": True,
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "message": "Recommendations generated successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("LLM call failed", recommendation_type=recommendation_type, task_id=self.request.id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate recommendations"
        }


@celery_app.task(bind=True, name="cache_results")
def cache_results(self, user_id: str, recommendations: List[Dict[str, Any]], recommendation_type: str) -> Dict[str, Any]:
    """Cache recommendation results in Redis"""
    try:
        logger.info("Caching results", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id)
        
        # Create cache service
        cache_service = CacheService()
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Store recommendations in cache
            success = loop.run_until_complete(
                cache_service.store_recommendations(
                    user_id=user_id,
                    recommendation_type=recommendation_type,
                    recommendations=recommendations
                )
            )
            
            if not success:
                raise ValueError("Failed to store recommendations in cache")
            
            logger.info("Results cached successfully", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id)
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "cached_count": len(recommendations),
                "message": "Results cached successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Caching failed", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to cache results"
        }


@celery_app.task(bind=True, name="generate_recommendations")
def generate_recommendations(self, user_id: str, recommendation_type: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Complete recommendation generation workflow"""
    try:
        logger.info("Starting recommendation generation", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id)
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cache_service = CacheService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cached_recommendations = loop.run_until_complete(
                    cache_service.get_recommendations(user_id, recommendation_type)
                )
                
                if cached_recommendations:
                    logger.info("Returning cached recommendations", user_id=user_id, recommendation_type=recommendation_type)
                    return {
                        "success": True,
                        "user_id": user_id,
                        "recommendation_type": recommendation_type,
                        "source": "cache",
                        "recommendations": cached_recommendations.model_dump(),
                        "message": "Cached recommendations returned"
                    }
            finally:
                loop.close()
        
        # Step 1: Fetch user data
        user_data_result = fetch_user_data.delay(user_id)
        user_data_result.wait()
        
        if not user_data_result.result.get("success"):
            raise Exception(f"Failed to fetch user data: {user_data_result.result.get('error')}")
        
        user_data = user_data_result.result.get("user_data")
        
        # Step 2: Build prompt
        prompt_result = build_prompt.delay(user_data, recommendation_type)
        prompt_result.wait()
        
        if not prompt_result.result.get("success"):
            raise Exception(f"Failed to build prompt: {prompt_result.result.get('error')}")
        
        prompt = prompt_result.result.get("prompt")
        
        # Step 3: Call LLM
        llm_result = call_llm.delay(prompt, user_data, recommendation_type)
        llm_result.wait()
        
        if not llm_result.result.get("success"):
            raise Exception(f"Failed to call LLM: {llm_result.result.get('error')}")
        
        recommendations = llm_result.result.get("recommendations")
        
        # Step 4: Cache results
        cache_result = cache_results.delay(user_id, recommendations, recommendation_type)
        cache_result.wait()
        
        if not cache_result.result.get("success"):
            raise Exception(f"Failed to cache results: {cache_result.result.get('error')}")
        
        logger.info("Recommendation generation completed", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id)
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendation_type": recommendation_type,
            "source": "generated",
            "recommendations": recommendations,
            "message": "Recommendations generated and cached successfully"
        }
        
    except Exception as e:
        logger.error("Recommendation generation failed", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate recommendations"
        }

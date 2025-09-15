"""
Celery tasks for recommendation processing
"""
import asyncio
import os
from typing import Dict, Any, List
from app.workers.celery_app import celery_app
from app.core.logging import get_logger, log_background_task, log_exception
from app.core.config import settings
from app.core.constants import RecommendationType
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.llm_service import llm_service
from app.utils.prompt_builder import PromptBuilder
import time

logger = get_logger("celery_tasks")


@celery_app.task(bind=True, name="fetch_user_data")
def fetch_user_data(self, user_id: str) -> Dict[str, Any]:
    """Fetch user data from external services"""
    task_id = self.request.id
    log_background_task("fetch_user_data", task_id, "started", user_id=user_id)
    
    try:
        logger.info("Starting user data fetch", user_id=user_id, task_id=task_id)
        
        # Create service instances
        user_service = UserProfileService(timeout=30)
        lie_service = LIEService(timeout=30)
        cis_service = CISService(timeout=30)
        
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
            
            log_background_task("fetch_user_data", task_id, "completed", user_id=user_id)
            logger.info("User data fetch completed", user_id=user_id, task_id=task_id)
            
            return {
                "success": True,
                "user_data": user_data,
                "message": "User data fetched successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        log_background_task("fetch_user_data", task_id, "failed", user_id=user_id, error=str(e))
        logger.error("User data fetch failed", user_id=user_id, task_id=task_id, error=str(e))
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "fetch_user_data", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch user data"
        }


@celery_app.task(bind=True, name="build_prompt")
def build_prompt(self, user_data: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Build dynamic prompt for recommendation generation"""
    task_id = self.request.id
    log_background_task("build_prompt", task_id, "started", recommendation_type=recommendation_type)
    
    try:
        logger.info("Building prompt", recommendation_type=recommendation_type, task_id=task_id)
        
        # Validate recommendation type
        if recommendation_type not in [rt.value for rt in RecommendationType]:
            raise ValueError(f"Invalid recommendation type: {recommendation_type}")
        
        # Create prompt builder
        prompt_builder = PromptBuilder()
        
        # Extract user data components
        user_profile_data = user_data.get("user_profile")
        location_data = user_data.get("location_data")
        interaction_data = user_data.get("interaction_data")
        
        # If any component is missing, build a fallback prompt that can still yield useful recs
        # rather than failing the pipeline.
        missing_any = not any([user_profile_data, location_data, interaction_data])
        
        from app.models.schemas import UserProfile, LocationData, InteractionData
        if missing_any:
            # Use best-available partial objects to inform fallback
            user_profile = UserProfile(**user_profile_data) if user_profile_data else None
            location = LocationData(**location_data) if location_data else None
            interaction = InteractionData(**interaction_data) if interaction_data else None
            prompt = prompt_builder.build_fallback_prompt(
                user_profile=user_profile,
                location_data=location,
                interaction_data=interaction,
                recommendation_type=RecommendationType(recommendation_type),
                max_results=10,
            )
        else:
            # Convert to Pydantic models
            user_profile = UserProfile(**user_profile_data)
            location = LocationData(**location_data)
            interaction = InteractionData(**interaction_data)
            # Build the standard prompt
            prompt = prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=location,
                interaction_data=interaction,
                recommendation_type=RecommendationType(recommendation_type),
                max_results=10
            )
        
        log_background_task("build_prompt", task_id, "completed", 
                           recommendation_type=recommendation_type, 
                           prompt_length=len(prompt))
        logger.info("Prompt built successfully", 
                   recommendation_type=recommendation_type, 
                   task_id=task_id,
                   prompt_length=len(prompt))
        
        return {
            "success": True,
            "prompt": prompt,
            "recommendation_type": recommendation_type,
            "message": "Prompt built successfully"
        }
        
    except Exception as e:
        log_background_task("build_prompt", task_id, "failed", 
                           recommendation_type=recommendation_type, 
                           error=str(e))
        logger.error("Prompt building failed", 
                   recommendation_type=recommendation_type, 
                   task_id=task_id, 
                   error=str(e))
        log_exception("celery_tasks", e, {"recommendation_type": recommendation_type, "task": "build_prompt", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to build prompt"
        }


@celery_app.task(bind=True, name="call_llm")
def call_llm(self, prompt: str, user_context: Dict[str, Any], recommendation_type: str) -> Dict[str, Any]:
    """Call LLM service to generate recommendations"""
    task_id = self.request.id
    log_background_task("call_llm", task_id, "started", recommendation_type=recommendation_type)
    
    try:
        logger.info("Calling LLM service", recommendation_type=recommendation_type, task_id=task_id)
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generate recommendations
            recommendations = loop.run_until_complete(
                llm_service.generate_recommendations(
                    prompt=prompt,
                    user_id=user_context.get("user_id"),
                    current_city=user_context.get("current_city", "Barcelona")
                )
            )
            
            if not recommendations:
                raise ValueError("No recommendations generated by LLM")
            
            log_background_task("call_llm", task_id, "completed", 
                               recommendation_type=recommendation_type, 
                               recommendations_count=len(recommendations))
            logger.info("LLM call completed", 
                       recommendation_type=recommendation_type, 
                       task_id=task_id, 
                       count=len(recommendations))
            
            return {
                "success": True,
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "message": "Recommendations generated successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        log_background_task("call_llm", task_id, "failed", 
                           recommendation_type=recommendation_type, 
                           error=str(e))
        logger.error("LLM call failed", 
                   recommendation_type=recommendation_type, 
                   task_id=task_id, 
                   error=str(e))
        log_exception("celery_tasks", e, {"recommendation_type": recommendation_type, "task": "call_llm", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate recommendations"
        }


@celery_app.task(bind=True, name="cache_results")
def cache_results(self, user_id: str, recommendations: List[Dict[str, Any]], recommendation_type: str) -> Dict[str, Any]:
    """Cache recommendation results in Redis"""
    task_id = self.request.id
    log_background_task("cache_results", task_id, "started", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type,
                       recommendations_count=len(recommendations))
    
    try:
        logger.info("Caching results", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id,
                   recommendations_count=len(recommendations))
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Store recommendations in cache
            success = loop.run_until_complete(
                llm_service.store_recommendations(
                    user_id=user_id,
                    recommendation_type=recommendation_type,
                    recommendations=recommendations
                )
            )
            
            if not success:
                raise ValueError("Failed to store recommendations in cache")
            
            log_background_task("cache_results", task_id, "completed", 
                               user_id=user_id, 
                               recommendation_type=recommendation_type,
                               cached_count=len(recommendations))
            logger.info("Results cached successfully", 
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
            
        finally:
            loop.close()
            
    except Exception as e:
        log_background_task("cache_results", task_id, "failed", 
                           user_id=user_id, 
                           recommendation_type=recommendation_type,
                           error=str(e))
        logger.error("Caching failed", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id, 
                   error=str(e))
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "cache_results", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to cache results"
        }


@celery_app.task(bind=True, name="generate_recommendations")
def generate_recommendations(self, user_id: str, recommendation_type: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Complete recommendation generation workflow"""
    task_id = self.request.id
    log_background_task("generate_recommendations", task_id, "started", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type,
                       force_refresh=force_refresh)
    
    try:
        logger.info("Starting recommendation generation", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id,
                   force_refresh=force_refresh)
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cached_recommendations = loop.run_until_complete(
                    llm_service.get_recommendations(user_id, recommendation_type)
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
        
        log_background_task("generate_recommendations", task_id, "completed", 
                           user_id=user_id, 
                           recommendation_type=recommendation_type,
                           recommendations_count=len(recommendations))
        logger.info("Recommendation generation completed", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id,
                   recommendations_count=len(recommendations))
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendation_type": recommendation_type,
            "source": "generated",
            "recommendations": recommendations,
            "message": "Recommendations generated and cached successfully"
        }
        
    except Exception as e:
        log_background_task("generate_recommendations", task_id, "failed", 
                           user_id=user_id, 
                           recommendation_type=recommendation_type,
                           error=str(e))
        logger.error("Recommendation generation failed", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id, 
                   error=str(e))
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "generate_recommendations", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate recommendations"
        }

@celery_app.task(bind=True, name="process_user", acks_late=True, reject_on_worker_lost=True)
def process_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
    """Consumer task: process each user independently on separate worker"""
    task_id = self.request.id
    user_id = user.get('id')
    user_name = user.get('name')
    priority = user.get('priority', 0)
    
    log_background_task("process_user", task_id, "started", 
                       user_id=user_id, 
                       user_name=user_name,
                       priority=priority)
    
    try:
        logger.info("Processing user", 
                   user_id=user_id, 
                   user_name=user_name, 
                   task_id=task_id,
                   priority=priority)
        
        # Get worker info for independent processing tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        # Simulate processing time (you can replace this with actual processing logic)
        import time
        time.sleep(0.1)  # 100ms processing time
        
        # Log worker processing details
        logger.info("Independent worker processing completed",
                   user_id=user_id,
                   user_name=user_name,
                   worker_id=worker_id,
                   worker_pid=worker_pid,
                   task_id=self.request.id,
                   priority=priority,
                   processing_time_ms=100,
                   status="completed_independently")
        
        logger.info("User processing completed independently", user_id=user_id, worker_id=worker_id, task_id=self.request.id)
        
        log_background_task("process_user", task_id, "completed", 
                           user_id=user_id, 
                           user_name=user_name,
                           worker_id=worker_id,
                           priority=priority)
        
        return {
            "success": True,
            "user_id": user_id,
            "user_name": user_name,
            "worker_id": worker_id,
            "worker_pid": worker_pid,
            "priority": priority,
            "processed_at": time.time(),
            "task_id": task_id,
            "message": f"Hello World! User {user_name} processed on dedicated worker"
        }
        
    except Exception as e:
        log_background_task("process_user", task_id, "failed", 
                           user_id=user_id, 
                           user_name=user_name,
                           error=str(e))
        logger.error("User processing failed", 
                   user_id=user_id, 
                   task_id=task_id, 
                   error=str(e))
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "process_user", "task_id": task_id})
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process user"
        }


@celery_app.task(bind=True, name="get_users")
def get_users(self, count: int = 5, delay: int = 1) -> Dict[str, Any]:
    """
    Producer task: generate dummy users and enqueue them for independent processing
    Each user gets assigned to a separate worker for parallel processing
    """
    task_id = self.request.id
    log_background_task("get_users", task_id, "started", 
                       count=count, 
                       delay=delay)
    
    logger.info("Starting user generation", 
               count=count, 
               delay=delay, 
               task_id=task_id)
    
    logger.info("Producer task started",
               count=count,
               task_id=self.request.id,
               interval_seconds=settings.task_interval_seconds,
               worker_concurrency=settings.celery_worker_concurrency,
               strategy="independent_processing")

    for i in range(1, count + 1):
        user = {
            "id": i, 
            "name": f"User-{i}", 
            "email": f"user{i}@example.com",
            "timestamp": time.time(),
            "priority": i  # Add priority for better worker assignment
        }
        logger.info("Generated user", user_id=i, user_name=user["name"])
        
        logger.info("Queuing user for processing",
                   user_id=i,
                   user_name=user["name"],
                   queue="user_processing",
                   routing_key=f"user_processing_{i % settings.celery_worker_concurrency}")

        # Send into RabbitMQ → Each user gets a separate worker
        # Using apply_async with routing_key based on user ID for worker isolation
        process_user_comprehensive.apply_async(
            args=[str(user['id'])],  # Pass user_id as string
            queue="user_processing",
            routing_key=f"user_processing_{i % settings.celery_worker_concurrency}",  # Distribute across workers
            priority=i,  # Higher priority for newer users
            expires=None,  # No expiration - queue is independent
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )

        if delay > 0:
            time.sleep(delay)

    log_background_task("get_users", task_id, "completed", 
                       count=count, 
                       generated_count=count)
    logger.info("User generation completed", 
               count=count, 
               task_id=task_id,
               status="producer_completed")
    return {"success": True, "generated_count": count}


@celery_app.task(bind=True, name="process_user_comprehensive", acks_late=True, reject_on_worker_lost=True)
def process_user_comprehensive(self, user_id: str) -> Dict[str, Any]:
    """
    Comprehensive user processing task: 
    - Takes user_id from RabbitMQ
    - Fetches user profile, location, and interaction data
    - Processes and combines all data
    - Returns comprehensive user insights
    """
    task_id = self.request.id
    log_background_task("process_user_comprehensive", task_id, "started", user_id=user_id)
    
    try:
        logger.info("Starting comprehensive user processing", 
                   user_id=user_id, 
                   task_id=task_id)
        
        # Get worker info for tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        logger.info("Comprehensive user processing started",
                   user_id=user_id,
                   worker_id=worker_id,
                   worker_pid=worker_pid,
                   task_id=self.request.id,
                   status="fetching_user_data")
        
        # Create service instances
        user_service = UserProfileService(timeout=30)
        lie_service = LIEService(timeout=30)
        cis_service = CISService(timeout=30)
        
        # Run async operations to fetch all user data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.info("Fetching user data from all services",
                       user_id=user_id,
                       services=["user_profile", "location_intelligence", "content_interaction"])
            
            # Fetch user profile data
            logger.info("Fetching user profile data", user_id=user_id, service="user_profile")
            user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
            if not user_profile:
                raise Exception(f"Failed to fetch user profile for user_id: {user_id}")
            
            logger.info("User profile data fetched successfully",
                       user_id=user_id,
                       user_name=user_profile.name,
                       user_email=user_profile.email,
                       service="user_profile")
            
            # Fetch location data
            logger.info("Fetching location data", user_id=user_id, service="location_intelligence")
            location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
            if not location_data:
                raise Exception(f"Failed to fetch location data for user_id: {user_id}")
            
            logger.info("Location data fetched successfully",
                       user_id=user_id,
                       current_location=location_data.current_location,
                       home_location=location_data.home_location,
                       service="location_intelligence")
            
            # Fetch interaction data
            logger.info("Fetching interaction data", user_id=user_id, service="content_interaction")
            interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
            if not interaction_data:
                raise Exception(f"Failed to fetch interaction data for user_id: {user_id}")
            
            logger.info("Interaction data fetched successfully",
                       user_id=user_id,
                       engagement_score=interaction_data.engagement_score,
                       service="content_interaction")
            
            logger.info("All user data fetched successfully",
                       user_id=user_id,
                       status="data_fetch_complete")
            
            # Combine all data into comprehensive user profile
            comprehensive_data = {
                "user_id": user_id,
                "processing_info": {
                    "worker_id": worker_id,
                    "worker_pid": worker_pid,
                    "task_id": self.request.id,
                    "processed_at": time.time(),
                    "processing_duration_ms": 0  # Will calculate below
                },
                "user_profile": {
                    "name": user_profile.name,
                    "email": user_profile.email,
                    "age": user_profile.age,
                    "location": user_profile.location,
                    "interests": user_profile.interests,
                    "profile_completeness": user_profile.preferences.get("profile_completeness", 0.0),
                    "key_preferences": {
                        "keywords": [item["value"] for item in user_profile.preferences.get("Keywords (legacy)", {}).get("example_values", [])[:5]],
                        "archetypes": [item["value"] for item in user_profile.preferences.get("Archetypes (legacy)", {}).get("example_values", [])[:3]],
                        "demographics": user_profile.preferences.get("Demographics", {}).get("example_values", [{}])[0].get("value", ""),
                        "cuisines": [item["value"] for item in user_profile.preferences.get("Dining preferences (cuisine)", {}).get("example_values", [])[:3]]
                    }
                },
                "location_intelligence": {
                    "current_location": location_data.current_location,
                    "home_location": location_data.home_location,
                    "work_location": location_data.work_location,
                    "travel_history": location_data.travel_history[:5],  # Top 5 recent trips
                    "location_preferences": location_data.location_preferences
                },
                "interaction_analytics": {
                    "engagement_score": interaction_data.engagement_score,
                    "recent_interactions_count": len(interaction_data.recent_interactions),
                    "interaction_history_count": len(interaction_data.interaction_history),
                    "interaction_preferences": interaction_data.preferences
                },
                "combined_insights": {
                    "user_persona": f"{user_profile.name} is a {user_profile.age}-year-old {user_profile.preferences.get('Demographics', {}).get('example_values', [{}])[0].get('value', 'person')} living in {location_data.current_location}",
                    "activity_pattern": f"Engagement level: {interaction_data.engagement_score:.2f} ({'High' if interaction_data.engagement_score > 0.7 else 'Medium' if interaction_data.engagement_score > 0.4 else 'Low'} engagement)",
                    "location_pattern": f"Based in {location_data.home_location}, works in {location_data.work_location}, currently in {location_data.current_location}",
                    "interest_summary": f"Interests include: {', '.join(user_profile.interests[:5])}",
                    "travel_style": f"Has visited {len(location_data.travel_history)} destinations including {', '.join(location_data.travel_history[:3])}",
                    "content_preferences": f"Most engaged with {interaction_data.preferences.get('preferred_content_types', ['various'])[0]} content on {interaction_data.preferences.get('preferred_platforms', ['multiple'])[0]}"
                },
                "recommendations": {
                    "content_suggestions": [
                        f"Recommend {user_profile.preferences.get('Dining preferences (cuisine)', {}).get('example_values', [{}])[0].get('value', 'restaurants')} in {location_data.current_location}",
                        f"Suggest {user_profile.interests[0] if user_profile.interests else 'activities'} events in {location_data.current_location}",
                        f"Show {interaction_data.preferences.get('preferred_content_types', ['entertainment'])[0]} content from {interaction_data.preferences.get('preferred_platforms', ['popular platforms'])[0]}"
                    ],
                    "location_suggestions": [
                        f"Nearby {user_profile.preferences.get('Outdoor Activity Preferences', {}).get('example_values', [{}])[0].get('value', 'activities')} in {location_data.current_location}",
                        f"Popular {user_profile.preferences.get('Indoor Activity Preferences', {}).get('example_values', [{}])[0].get('value', 'venues')} in the area"
                    ]
                }
            }
            
            # Calculate processing duration
            comprehensive_data["processing_info"]["processing_duration_ms"] = int((time.time() - comprehensive_data["processing_info"]["processed_at"]) * 1000)
            
            # Generate prompt using all the collected data
            logger.info("Generating personalized prompt",
                       user_id=user_id,
                       recommendation_type="PLACE",
                       max_results=5)
            
            prompt_builder = PromptBuilder()
            
            # Generate prompt for general recommendations (you can modify this to use specific recommendation types)
            generated_prompt = prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=location_data,
                interaction_data=interaction_data,
                recommendation_type=RecommendationType.PLACE,  # Default to place recommendations
                max_results=5
            )
            
            logger.info("Prompt generated successfully",
                       user_id=user_id,
                       prompt_length=len(generated_prompt),
                       recommendation_type="PLACE")
            
            # Log the actual prompt content (first 500 chars for readability)
            prompt_preview = generated_prompt[:500] + "..." if len(generated_prompt) > 500 else generated_prompt
            logger.info("Generated prompt preview", 
                       user_id=user_id,
                       prompt_preview=prompt_preview,
                       prompt_length=len(generated_prompt),
                       task_id=self.request.id)
            
            # Remove duplicate logging
            
            # Add prompt to comprehensive data
            comprehensive_data["generated_prompt"] = {
                "prompt_text": generated_prompt,
                "prompt_length": len(generated_prompt),
                "recommendation_type": "PLACE",
                "max_results": 5,
                "generated_at": time.time()
            }
            
            logger.info("Comprehensive analysis completed",
                       user_id=user_id,
                       user_name=comprehensive_data['user_profile']['name'],
                       current_location=comprehensive_data['location_intelligence']['current_location'],
                       engagement_score=comprehensive_data['interaction_analytics']['engagement_score'],
                       prompt_length=len(generated_prompt),
                       processing_time_ms=comprehensive_data['processing_info']['processing_duration_ms'],
                       worker_id=worker_id,
                       status="comprehensive_processing_complete")
            
            log_background_task("process_user_comprehensive", task_id, "completed", 
                               user_id=user_id, 
                               worker_id=worker_id,
                               processing_duration_ms=comprehensive_data["processing_info"]["processing_duration_ms"],
                               prompt_length=len(generated_prompt))
            logger.info("Comprehensive user processing completed successfully", 
                       user_id=user_id, 
                       worker_id=worker_id, 
                       task_id=task_id,
                       processing_duration_ms=comprehensive_data["processing_info"]["processing_duration_ms"],
                       prompt_length=len(generated_prompt))
            
            return {
                "success": True,
                "user_id": user_id,
                "comprehensive_data": comprehensive_data,
                "generated_prompt": generated_prompt,
                "message": f"Comprehensive user data processed and prompt generated successfully for {user_profile.name}"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        log_background_task("process_user_comprehensive", task_id, "failed", 
                           user_id=user_id, 
                           error=str(e))
        logger.error("Comprehensive user processing failed", 
                    user_id=user_id, 
                    task_id=task_id, 
                    error=str(e))
        
        logger.error("Comprehensive processing failed",
                    user_id=user_id,
                    worker_id=self.request.hostname,
                    error=str(e),
                    task_id=task_id,
                    status="processing_failed")
        
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "process_user_comprehensive", "task_id": task_id})
        
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "message": f"Failed to process comprehensive user data for user_id: {user_id}"
        }


@celery_app.task(bind=True, name="generate_user_prompt", acks_late=True, reject_on_worker_lost=True)
def generate_user_prompt(self, user_id: str, recommendation_type: str = "PLACE", max_results: int = 5) -> Dict[str, Any]:
    """
    Generate personalized prompt for a user based on their profile, location, and interaction data
    
    - Takes user_id from RabbitMQ
    - Fetches user profile, location, and interaction data
    - Generates a personalized prompt using PromptBuilder
    - Returns the generated prompt
    """
    task_id = self.request.id
    log_background_task("generate_user_prompt", task_id, "started", 
                       user_id=user_id, 
                       recommendation_type=recommendation_type,
                       max_results=max_results)
    
    try:
        logger.info("Starting user prompt generation", 
                   user_id=user_id, 
                   recommendation_type=recommendation_type, 
                   task_id=task_id,
                   max_results=max_results)
        
        # Get worker info for tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        logger.info("User prompt generation started",
                   user_id=user_id,
                   worker_id=worker_id,
                   worker_pid=worker_pid,
                   task_id=self.request.id,
                   recommendation_type=recommendation_type,
                   max_results=max_results,
                   status="fetching_user_data")
        
        # Create service instances
        user_service = UserProfileService(timeout=30)
        lie_service = LIEService(timeout=30)
        cis_service = CISService(timeout=30)
        prompt_builder = PromptBuilder()
        
        # Run async operations to fetch all user data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.info("Fetching user data for prompt generation",
                       user_id=user_id,
                       services=["user_profile", "location_intelligence", "content_interaction"])
            
            # Fetch user profile data
            logger.info("Fetching user profile data", user_id=user_id, service="user_profile")
            user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
            if not user_profile:
                raise Exception(f"Failed to fetch user profile for user_id: {user_id}")
            
            logger.info("User profile data fetched successfully",
                       user_id=user_id,
                       user_name=user_profile.name,
                       user_email=user_profile.email,
                       service="user_profile")
            
            # Fetch location data
            logger.info("Fetching location data", user_id=user_id, service="location_intelligence")
            location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
            if not location_data:
                raise Exception(f"Failed to fetch location data for user_id: {user_id}")
            
            logger.info("Location data fetched successfully",
                       user_id=user_id,
                       current_location=location_data.current_location,
                       home_location=location_data.home_location,
                       service="location_intelligence")
            
            # Fetch interaction data
            logger.info("Fetching interaction data", user_id=user_id, service="content_interaction")
            interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
            if not interaction_data:
                raise Exception(f"Failed to fetch interaction data for user_id: {user_id}")
            
            logger.info("Interaction data fetched successfully",
                       user_id=user_id,
                       engagement_score=interaction_data.engagement_score,
                       service="content_interaction")
            
            logger.info("All user data fetched successfully for prompt generation",
                       user_id=user_id,
                       status="data_fetch_complete")
            
            # Generate the prompt
            logger.info("Generating personalized prompt",
                       user_id=user_id,
                       recommendation_type=recommendation_type,
                       max_results=max_results)
            
            # Convert recommendation_type string to enum
            try:
                rec_type_enum = RecommendationType(recommendation_type.upper())
            except ValueError:
                rec_type_enum = RecommendationType.PLACE  # Default fallback
                logger.warning("Invalid recommendation type, using PLACE as default",
                             user_id=user_id,
                             invalid_type=recommendation_type,
                             default_type="PLACE")
            
            generated_prompt = prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=location_data,
                interaction_data=interaction_data,
                recommendation_type=rec_type_enum,
                max_results=max_results
            )
            
            logger.info("Prompt generated successfully",
                       user_id=user_id,
                       prompt_length=len(generated_prompt),
                       recommendation_type=recommendation_type)
            
            # Generate recommendations using LLM service
            logger.info("Generating recommendations using LLM service",
                       user_id=user_id,
                       prompt_length=len(generated_prompt))
            
            # Use asyncio to call the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llm_response = loop.run_until_complete(
                llm_service.generate_recommendations(generated_prompt, user_id)
            )
            
            if llm_response.get("success"):
                logger.info("Recommendations generated successfully",
                           user_id=user_id,
                           total_recommendations=llm_response['metadata']['total_recommendations'],
                           categories=llm_response['metadata']['categories'])
            else:
                logger.error("Failed to generate recommendations",
                            user_id=user_id,
                            error=llm_response.get('error', 'Unknown error'))
            
            # Create comprehensive result
            result_data = {
                "user_id": user_id,
                "processing_info": {
                    "worker_id": worker_id,
                    "worker_pid": worker_pid,
                    "task_id": self.request.id,
                    "processed_at": time.time(),
                    "recommendation_type": recommendation_type,
                    "max_results": max_results
                },
                "user_summary": {
                    "name": user_profile.name,
                    "age": user_profile.age,
                    "location": user_profile.location,
                    "engagement_score": interaction_data.engagement_score,
                    "current_location": location_data.current_location,
                    "interests_count": len(user_profile.interests) if user_profile.interests else 0
                },
                "generated_prompt": {
                    "prompt_text": generated_prompt,
                    "prompt_length": len(generated_prompt),
                    "recommendation_type": recommendation_type,
                    "max_results": max_results,
                    "generated_at": time.time()
                },
                "recommendations": llm_response if llm_response.get("success") else None
            }
            
            logger.info("Comprehensive processing completed",
                       user_id=user_id,
                       user_name=result_data['user_summary']['name'],
                       current_location=result_data['user_summary']['current_location'],
                       engagement_score=result_data['user_summary']['engagement_score'],
                       prompt_length=len(generated_prompt),
                       total_recommendations=llm_response['metadata']['total_recommendations'] if llm_response.get("success") else 0,
                       worker_id=worker_id,
                       status="processing_complete")
            
            log_background_task("generate_user_prompt", task_id, "completed", 
                               user_id=user_id, 
                               worker_id=worker_id,
                               recommendation_type=recommendation_type,
                               prompt_length=len(generated_prompt),
                               total_recommendations=llm_response['metadata']['total_recommendations'] if llm_response.get("success") else 0)
            logger.info("User prompt generation completed successfully", 
                       user_id=user_id, 
                       worker_id=worker_id, 
                       task_id=task_id,
                       recommendation_type=recommendation_type,
                       prompt_length=len(generated_prompt))
            
            return {
                "success": True,
                "user_id": user_id,
                "result_data": result_data,
                "generated_prompt": generated_prompt,
                "recommendations": llm_response if llm_response.get("success") else None,
                "message": f"Comprehensive processing completed successfully for {user_profile.name}"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        log_background_task("generate_user_prompt", task_id, "failed", 
                           user_id=user_id, 
                           error=str(e))
        logger.error("User prompt generation failed", 
                    user_id=user_id, 
                    task_id=task_id, 
                    error=str(e))
        
        logger.error("Prompt generation failed",
                    user_id=user_id,
                    worker_id=self.request.hostname,
                    error=str(e),
                    task_id=task_id,
                    status="prompt_generation_failed")
        
        log_exception("celery_tasks", e, {"user_id": user_id, "task": "generate_user_prompt", "task_id": task_id})
        
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "message": f"Failed to generate prompt for user_id: {user_id}"
        }
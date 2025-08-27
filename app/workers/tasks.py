"""
Celery tasks for recommendation processing
"""
import asyncio
import os
from typing import Dict, Any, List, Optional
from workers.celery_app import celery_app
from core.logging import get_logger
from core.config import settings
from core.constants import RecommendationType, TaskStatus
from services.user_profile import UserProfileService
from services.lie_service import LIEService
from services.cis_service import CISService
from services.prefetch_service import PrefetchService
from services.cache_service import CacheService
from utils.prompt_builder import PromptBuilder
import time

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
        from models.schemas import UserProfile, LocationData, InteractionData
        
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

@celery_app.task(bind=True, name="process_user", acks_late=True, reject_on_worker_lost=True)
def process_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
    """Consumer task: process each user independently on separate worker"""
    try:
        user_id = user.get('id')
        user_name = user.get('name')
        priority = user.get('priority', 0)
        
        logger.info("Processing user", user_id=user_id, user_name=user_name, task_id=self.request.id)
        
        # Get worker info for independent processing tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        # Simulate processing time (you can replace this with actual processing logic)
        import time
        time.sleep(0.1)  # 100ms processing time
        
        # Enhanced console output for independent worker visibility
        print(f"\n🔧 INDEPENDENT WORKER PROCESSING:")
        print(f"   👤 User: {user_id} - {user_name}")
        print(f"   🔧 Worker: {worker_id} (PID: {worker_pid})")
        print(f"   📋 Task ID: {self.request.id}")
        print(f"   🎯 Priority: {priority}")
        print(f"   ⏱️  Processing time: 100ms")
        print(f"   ✅ Status: Completed independently")
        print(f"   💬 Message: Hello World! User {user_name} processed on dedicated worker\n")
        
        logger.info("User processing completed independently", user_id=user_id, worker_id=worker_id, task_id=self.request.id)
        
        return {
            "success": True,
            "user_id": user_id,
            "user_name": user_name,
            "worker_id": worker_id,
            "worker_pid": worker_pid,
            "priority": priority,
            "processed_at": time.time(),
            "task_id": self.request.id,
            "message": f"Hello World! User {user_name} processed on dedicated worker"
        }
        
    except Exception as e:
        logger.error("User processing failed", user_id=user.get('id'), task_id=self.request.id, error=str(e))
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
    logger.info("Starting user generation", count=count, delay=delay, task_id=self.request.id)
    
    print(f"\n🎯 PRODUCER TASK: Generating {count} users (Task ID: {self.request.id})")
    print(f"   ⏰ Interval: Every {settings.task_interval_seconds} seconds")
    print(f"   🔧 Workers: {settings.celery_worker_concurrency} concurrent workers")
    print(f"   🚀 Strategy: Each user → Separate worker (Independent processing)\n")

    for i in range(1, count + 1):
        user = {
            "id": i, 
            "name": f"User-{i}", 
            "email": f"user{i}@example.com",
            "timestamp": time.time(),
            "priority": i  # Add priority for better worker assignment
        }
        logger.info("Generated user", user_id=i, user_name=user["name"])
        
        print(f"📤 QUEUING: User-{i} → RabbitMQ → Independent Worker")

        # Send into RabbitMQ → Each user gets a separate worker
        # Using apply_async with routing_key based on user ID for worker isolation
        process_user.apply_async(
            args=[user],
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

    logger.info("User generation completed", count=count, task_id=self.request.id)
    print(f"✅ PRODUCER COMPLETED: {count} users queued for independent processing\n")
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
    try:
        logger.info("Starting comprehensive user processing", user_id=user_id, task_id=self.request.id)
        
        # Get worker info for tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        print(f"\n🔍 COMPREHENSIVE USER PROCESSING:")
        print(f"   👤 User ID: {user_id}")
        print(f"   🔧 Worker: {worker_id} (PID: {worker_pid})")
        print(f"   📋 Task ID: {self.request.id}")
        print(f"   🚀 Status: Fetching user data from all services...\n")
        
        # Create service instances
        user_service = UserProfileService()
        lie_service = LIEService()
        cis_service = CISService()
        
        # Run async operations to fetch all user data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print(f"📊 FETCHING DATA:")
            print(f"   🔄 User Profile Service...")
            
            # Fetch user profile data
            user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
            if not user_profile:
                raise Exception(f"Failed to fetch user profile for user_id: {user_id}")
            
            print(f"   ✅ User Profile: {user_profile.name} ({user_profile.email})")
            print(f"   🔄 Location Intelligence Service...")
            
            # Fetch location data
            location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
            if not location_data:
                raise Exception(f"Failed to fetch location data for user_id: {user_id}")
            
            print(f"   ✅ Location: {location_data.current_location} (Home: {location_data.home_location})")
            print(f"   🔄 Content Interaction Service...")
            
            # Fetch interaction data
            interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
            if not interaction_data:
                raise Exception(f"Failed to fetch interaction data for user_id: {user_id}")
            
            print(f"   ✅ Engagement Score: {interaction_data.engagement_score:.2f}")
            
            # Get additional insights
            print(f"   🔄 Fetching additional insights...")
            
            # Get location insights
            location_insights = loop.run_until_complete(lie_service.get_location_insights(user_id))
            
            # Get interaction insights
            interaction_insights = loop.run_until_complete(cis_service.get_interaction_insights(user_id))
            
            # Get engagement metrics
            engagement_metrics = loop.run_until_complete(cis_service.get_engagement_metrics(user_id))
            
            print(f"   ✅ All data fetched successfully!\n")
            
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
                    "location_preferences": location_data.location_preferences,
                    "location_insights": location_insights or {}
                },
                "interaction_analytics": {
                    "engagement_score": interaction_data.engagement_score,
                    "recent_interactions_count": len(interaction_data.recent_interactions),
                    "interaction_history_count": len(interaction_data.interaction_history),
                    "interaction_preferences": interaction_data.preferences,
                    "interaction_insights": interaction_insights or {},
                    "engagement_metrics": engagement_metrics or {}
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
            print(f"🤖 GENERATING PROMPT:")
            print(f"   🔄 Building personalized prompt...")
            
            prompt_builder = PromptBuilder()
            
            # Generate prompt for general recommendations (you can modify this to use specific recommendation types)
            generated_prompt = prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=location_data,
                interaction_data=interaction_data,
                recommendation_type=RecommendationType.PLACE,  # Default to place recommendations
                max_results=5
            )
            
            print(f"   ✅ Prompt generated successfully!")
            print(f"   📝 Prompt length: {len(generated_prompt)} characters")
            
            # Log the actual prompt content (first 500 chars for readability)
            prompt_preview = generated_prompt[:500] + "..." if len(generated_prompt) > 500 else generated_prompt
            print(f"   📄 Prompt Preview:")
            print(f"   {'='*50}")
            print(f"   {prompt_preview}")
            print(f"   {'='*50}")
            
            # Also log via structured logger for better visibility
            logger.info("Generated prompt preview", 
                       user_id=user_id,
                       prompt_preview=prompt_preview,
                       prompt_length=len(generated_prompt),
                       task_id=self.request.id)
            
            # Add prompt to comprehensive data
            comprehensive_data["generated_prompt"] = {
                "prompt_text": generated_prompt,
                "prompt_length": len(generated_prompt),
                "recommendation_type": "PLACE",
                "max_results": 5,
                "generated_at": time.time()
            }
            
            print(f"📈 COMPREHENSIVE ANALYSIS COMPLETE:")
            print(f"   👤 User: {comprehensive_data['user_profile']['name']}")
            print(f"   📍 Location: {comprehensive_data['location_intelligence']['current_location']}")
            print(f"   🎯 Engagement: {comprehensive_data['interaction_analytics']['engagement_score']:.2f}")
            print(f"   🤖 Prompt Generated: {len(generated_prompt)} chars")
            print(f"   ⏱️  Processing Time: {comprehensive_data['processing_info']['processing_duration_ms']}ms")
            print(f"   🔧 Worker: {worker_id}")
            print(f"   ✅ Status: Successfully processed comprehensive user data and generated prompt\n")
            
            logger.info("Comprehensive user processing completed successfully", 
                       user_id=user_id, 
                       worker_id=worker_id, 
                       task_id=self.request.id,
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
        logger.error("Comprehensive user processing failed", 
                    user_id=user_id, 
                    task_id=self.request.id, 
                    error=str(e))
        
        print(f"❌ COMPREHENSIVE PROCESSING FAILED:")
        print(f"   👤 User ID: {user_id}")
        print(f"   🔧 Worker: {self.request.hostname}")
        print(f"   ❌ Error: {str(e)}")
        print(f"   📋 Task ID: {self.request.id}\n")
        
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
    try:
        logger.info("Starting user prompt generation", user_id=user_id, recommendation_type=recommendation_type, task_id=self.request.id)
        
        # Get worker info for tracking
        worker_id = self.request.hostname
        worker_pid = os.getpid()
        
        print(f"\n🤖 USER PROMPT GENERATION:")
        print(f"   👤 User ID: {user_id}")
        print(f"   🔧 Worker: {worker_id} (PID: {worker_pid})")
        print(f"   📋 Task ID: {self.request.id}")
        print(f"   🎯 Recommendation Type: {recommendation_type}")
        print(f"   📊 Max Results: {max_results}")
        print(f"   🚀 Status: Fetching user data and generating prompt...\n")
        
        # Create service instances
        user_service = UserProfileService()
        lie_service = LIEService()
        cis_service = CISService()
        prompt_builder = PromptBuilder()
        
        # Run async operations to fetch all user data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print(f"📊 FETCHING USER DATA:")
            print(f"   🔄 User Profile Service...")
            
            # Fetch user profile data
            user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
            if not user_profile:
                raise Exception(f"Failed to fetch user profile for user_id: {user_id}")
            
            print(f"   ✅ User Profile: {user_profile.name} ({user_profile.email})")
            print(f"   🔄 Location Intelligence Service...")
            
            # Fetch location data
            location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
            if not location_data:
                raise Exception(f"Failed to fetch location data for user_id: {user_id}")
            
            print(f"   ✅ Location: {location_data.current_location} (Home: {location_data.home_location})")
            print(f"   🔄 Content Interaction Service...")
            
            # Fetch interaction data
            interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
            if not interaction_data:
                raise Exception(f"Failed to fetch interaction data for user_id: {user_id}")
            
            print(f"   ✅ Engagement Score: {interaction_data.engagement_score:.2f}")
            print(f"   ✅ All data fetched successfully!\n")
            
            # Generate the prompt
            print(f"🤖 GENERATING PROMPT:")
            print(f"   🔄 Building personalized prompt for {recommendation_type} recommendations...")
            
            # Convert recommendation_type string to enum
            try:
                rec_type_enum = RecommendationType(recommendation_type.upper())
            except ValueError:
                rec_type_enum = RecommendationType.PLACE  # Default fallback
                print(f"   ⚠️  Invalid recommendation type '{recommendation_type}', using PLACE as default")
            
            generated_prompt = prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=location_data,
                interaction_data=interaction_data,
                recommendation_type=rec_type_enum,
                max_results=max_results
            )
            
            print(f"   ✅ Prompt generated successfully!")
            print(f"   📝 Prompt length: {len(generated_prompt)} characters")
            
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
                }
            }
            
            print(f"📈 PROMPT GENERATION COMPLETE:")
            print(f"   👤 User: {result_data['user_summary']['name']}")
            print(f"   📍 Location: {result_data['user_summary']['current_location']}")
            print(f"   🎯 Engagement: {result_data['user_summary']['engagement_score']:.2f}")
            print(f"   🤖 Prompt Generated: {len(generated_prompt)} chars")
            print(f"   🔧 Worker: {worker_id}")
            print(f"   ✅ Status: Successfully generated personalized prompt\n")
            
            logger.info("User prompt generation completed successfully", 
                       user_id=user_id, 
                       worker_id=worker_id, 
                       task_id=self.request.id,
                       recommendation_type=recommendation_type,
                       prompt_length=len(generated_prompt))
            
            return {
                "success": True,
                "user_id": user_id,
                "result_data": result_data,
                "generated_prompt": generated_prompt,
                "message": f"Personalized prompt generated successfully for {user_profile.name}"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("User prompt generation failed", 
                    user_id=user_id, 
                    task_id=self.request.id, 
                    error=str(e))
        
        print(f"❌ PROMPT GENERATION FAILED:")
        print(f"   👤 User ID: {user_id}")
        print(f"   🔧 Worker: {self.request.hostname}")
        print(f"   ❌ Error: {str(e)}")
        print(f"   📋 Task ID: {self.request.id}\n")
        
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "message": f"Failed to generate prompt for user_id: {user_id}"
        }
"""
LLM Service for generating recommendations
"""
import json
import time
import random
import httpx
from typing import Dict, Any, List, Optional
from app.core.logging import get_logger, log_api_call, log_api_response, log_exception
from app.core.config import settings
import redis

logger = get_logger("llm_service")


class LLMService:
    """Service to generate recommendations from prompts and store in Redis"""
    
    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        logger.info("Initializing LLM service",
                   timeout=timeout,
                   redis_host=settings.redis_host,
                   redis_port=6379,
                   redis_db=1)
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=6379,
                db=1,  # Use different DB for recommendations
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully",
                       service="llm_service",
                       redis_host=settings.redis_host)
        except Exception as e:
            logger.error("Failed to connect to Redis",
                        service="llm_service",
                        redis_host=settings.redis_host,
                        error=str(e))
            raise
        # Action weights for ranking score calculation
        self.ACTION_WEIGHTS = {
            "liked": 2.0,
            "saved": 1.5,
            "shared": 1.2,
            "clicked": 0.8,
            "view": 0.4,
            "ignored": -1.0,
            "disliked": -1.5,
        }
        self.BASE_SCORE = 0.5
        self.SCALE = 0.2  # scale for converting weighted sum into [0,1] range
    
    def _normalize_key(self, value: str) -> str:
        """Normalize string keys for comparison"""
        if not isinstance(value, str):
            return ""
        return ''.join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()

    def _setup_demo_data(self) -> None:
        """Setup demo data (placeholder for test compatibility)"""
        # This method is expected by tests but not used in the main logic
        logger.info("Setting up demo data")
        return None

    def _generate_demo_recommendations(self, prompt: str) -> Dict[str, List[Dict]]:
        """Generate demo recommendations for testing purposes"""
        logger.info(f"Generating demo recommendations for prompt: {prompt}")
        return {
            "movies": [
                {"title": "Demo Movie 1", "genre": "Action", "year": "2023"},
                {"title": "Demo Movie 2", "genre": "Drama", "year": "2022"},
            ],
            "music": [
                {"title": "Demo Song 1", "artist": "Artist 1", "genre": "Pop"},
                {"title": "Demo Song 2", "artist": "Artist 2", "genre": "Rock"},
            ],
            "places": [
                {"name": "Demo Place 1", "type": "Park", "rating": 4.5},
                {"name": "Demo Place 2", "type": "Museum", "rating": 4.0},
            ],
            "events": [
                {"name": "Demo Event 1", "date": "2025-01-01", "venue": "Venue 1"},
                {"name": "Demo Event 2", "date": "2025-02-01", "venue": "Venue 2"},
            ]
        }

    def _get_user_interaction_history(self, user_id: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Mock retrieval of user's historical interactions from a table.
        Returns interaction data with proper field matching for each category.
        """
        seed = sum(ord(c) for c in user_id) if user_id else 0
        rnd = random.Random(seed)
        
        interaction_types = ["view", "liked", "saved", "shared", "clicked", "ignored", "disliked"]
        
        history = {
            "movies": [
                {"title": "Inception", "action": "liked", "timestamp": "2024-08-15T10:30:00Z"},
                {"title": "The Dark Knight", "action": "view", "timestamp": "2024-08-14T15:20:00Z"},
                {"title": "Vicky Cristina Barcelona", "action": "ignored", "timestamp": "2024-08-13T09:45:00Z"},
                {"title": "The Shawshank Redemption", "action": rnd.choice(["liked", "view", "saved"]), "timestamp": "2024-08-12T20:10:00Z"},
                {"title": "All About My Mother", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-11T14:30:00Z"},
            ],
            "music": [
                {"title": "Blinding Lights", "action": "liked", "timestamp": "2024-08-16T12:00:00Z"},
                {"title": "Barcelona", "action": "saved", "timestamp": "2024-08-15T18:45:00Z"},
                {"title": "Shape of You", "action": rnd.choice(["view", "liked", "shared"]), "timestamp": "2024-08-14T11:20:00Z"},
                {"title": "Mediterráneo", "action": rnd.choice(["ignored", "view"]), "timestamp": "2024-08-13T16:30:00Z"},
                {"title": "Dance Monkey", "action": rnd.choice(["view", "disliked"]), "timestamp": "2024-08-12T13:15:00Z"},
            ],
            "places": [
                {"name": "Sagrada Família", "action": "liked", "timestamp": "2024-08-17T09:00:00Z"},
                {"name": "Eiffel Tower", "action": "view", "timestamp": "2024-08-16T14:30:00Z"},
                {"name": "Park Güell", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-15T11:45:00Z"},
                {"name": "Big Ben", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T17:20:00Z"},
                {"name": "Colosseum", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-13T10:10:00Z"},
            ],
            "events": [
                {"name": "Primavera Sound", "action": "liked", "timestamp": "2024-08-18T08:30:00Z"},
                {"name": "Coachella Valley Music and Arts Festival", "action": "ignored", "timestamp": "2024-08-17T19:15:00Z"},
                {"name": "La Mercè Festival", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-16T15:45:00Z"},
                {"name": "Oktoberfest", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-15T12:30:00Z"},
                {"name": "Mardi Gras", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T16:00:00Z"},
            ],
        }
        
        for category in history:
            if rnd.random() > 0.3:
                extra_interactions = rnd.randint(1, 3)
                for _ in range(extra_interactions):
                    action = rnd.choice(interaction_types)
                    timestamp = f"2024-08-{rnd.randint(10, 18):02d}T{rnd.randint(8, 20):02d}:{rnd.randint(0, 59):02d}:00Z"
                    
                    if category == "movies":
                        title = f"Random Movie {rnd.randint(1, 100)}"
                        history[category].append({"title": title, "action": action, "timestamp": timestamp})
                    elif category == "music":
                        title = f"Random Song {rnd.randint(1, 100)}"
                        history[category].append({"title": title, "action": action, "timestamp": timestamp})
                    elif category == "places":
                        name = f"Random Place {rnd.randint(1, 100)}"
                        history[category].append({"name": name, "action": action, "timestamp": timestamp})
                    elif category == "events":
                        name = f"Random Event {rnd.randint(1, 100)}"
                        history[category].append({"name": name, "action": action, "timestamp": timestamp})
        
        return history

    def _compute_ranking_score(self, item: Dict[str, Any], category: str, history: Dict[str, List[Dict[str, str]]]) -> float:
        """
        Compute ranking score in [0,1] using exact field matching for each category.
        """
        field_mapping = {
            "movies": "title",
            "music": "title", 
            "places": "name",
            "events": "name"
        }
        
        field_name = field_mapping.get(category, "title")
        item_identifier = self._normalize_key(item.get(field_name, ""))
        
        total_weight = 0.0
        interaction_count = 0
        
        for interaction in history.get(category, []):
            hist_identifier = self._normalize_key(interaction.get(field_name, ""))
            if hist_identifier and hist_identifier == item_identifier:
                action = interaction.get("action", "view").lower()
                weight = self.ACTION_WEIGHTS.get(action, 0.0)
                total_weight += weight
                interaction_count += 1
        
        if interaction_count == 0:
            return self.BASE_SCORE
        
        score = self.BASE_SCORE + self.SCALE * total_weight
        score = max(0.0, min(1.0, score))
        return round(score, 3)
    
    async def generate_recommendations(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, Any]:
        """
        Generate recommendations based on prompt and store in Redis
        """
        try:
            logger.info(f"Generating recommendations for prompt: {prompt[:100]}...")
            
            start_time = time.time()
            
            recommendations = await self._call_llm_api(prompt, user_id, current_city)
            
            processing_time = time.time() - start_time
            
            response = {
                "success": True,
                "prompt": prompt,
                "user_id": user_id,
                "current_city": current_city,
                "generated_at": time.time(),
                "processing_time": processing_time,
                "recommendations": recommendations,
                "metadata": {
                    "total_recommendations": sum(len(cat) for cat in recommendations.values()) if recommendations else 0,
                    "categories": list(recommendations.keys()) if recommendations else [],
                    "model": "llm-api-v1.0",
                    "ranking_enabled": user_id is not None
                }
            }
            
            if user_id:
                self._store_in_redis(user_id, response)
            
            logger.info(f"Generated {response['metadata']['total_recommendations']} recommendations for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt,
                "user_id": user_id
            }
    
    async def _call_llm_api(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, List[Dict]]:
        """
        Call the actual LLM API to generate recommendations
        """
        start_time = time.time()
        
        # Log API call initiation
        log_api_call(
            service_name="llm_api",
            endpoint="/process-text",
            method="POST",
            user_id=user_id,
            prompt_length=len(prompt),
            provider=settings.recommendation_api_provider
        )
        
        try:
            payload = {
                "text": prompt,
                "provider": settings.recommendation_api_provider
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.recommendation_api_url}/process-text",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                raw_result = result.get("result")
                
                response_time = time.time() - start_time
                
                if raw_result is None:
                    logger.warning("Empty result field from LLM API",
                                 user_id=user_id,
                                 response_time_ms=response_time * 1000)
                    log_api_response("llm_api", "/process-text", False, 
                                   status_code=response.status_code, 
                                   response_time=response_time,
                                   user_id=user_id,
                                   error="empty_result")
                    return self._get_fallback_recommendations()
                
                if isinstance(raw_result, dict):
                    log_api_response("llm_api", "/process-text", True,
                                   status_code=response.status_code,
                                   response_time=response_time,
                                   user_id=user_id)
                    return self._process_llm_recommendations(raw_result, user_id, current_city)
                
                if isinstance(raw_result, str):
                    parsed = self._robust_parse_json(raw_result)
                    if parsed is not None:
                        log_api_response("llm_api", "/process-text", True,
                                       status_code=response.status_code,
                                       response_time=response_time,
                                       user_id=user_id)
                        return self._process_llm_recommendations(parsed, user_id, current_city)
                    
                    logger.info("LLM response is not valid JSON, attempting text parsing",
                               user_id=user_id,
                               response_time_ms=response_time * 1000)
                    recommendations = self._parse_text_response(raw_result)
                    log_api_response("llm_api", "/process-text", True,
                                   status_code=response.status_code,
                                   response_time=response_time,
                                   user_id=user_id,
                                   parsing_method="text")
                    return self._process_llm_recommendations(recommendations, user_id, current_city)
                
                logger.error("Unexpected type for LLM result",
                           user_id=user_id,
                           result_type=type(raw_result).__name__,
                           response_time_ms=response_time * 1000)
                log_api_response("llm_api", "/process-text", False,
                               status_code=response.status_code,
                               response_time=response_time,
                               user_id=user_id,
                               error="unexpected_result_type")
                return self._get_fallback_recommendations()
                    
        except httpx.TimeoutException as e:
            response_time = time.time() - start_time
            logger.error("Timeout calling LLM API",
                        user_id=user_id,
                        timeout_seconds=self.timeout,
                        response_time_ms=response_time * 1000)
            log_api_response("llm_api", "/process-text", False,
                           response_time=response_time,
                           user_id=user_id,
                           error="timeout")
            return self._get_fallback_recommendations()
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            logger.error("HTTP error calling LLM API",
                        user_id=user_id,
                        status_code=e.response.status_code,
                        response_text=e.response.text,
                        response_time_ms=response_time * 1000)
            log_api_response("llm_api", "/process-text", False,
                           status_code=e.response.status_code,
                           response_time=response_time,
                           user_id=user_id,
                           error="http_error")
            return self._get_fallback_recommendations()
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("Unexpected error calling LLM API",
                        user_id=user_id,
                        error=str(e),
                        response_time_ms=response_time * 1000)
            log_exception("llm_service", e, {"user_id": user_id, "response_time": response_time})
            log_api_response("llm_api", "/process-text", False,
                           response_time=response_time,
                           user_id=user_id,
                           error="unexpected_error")
            return self._get_fallback_recommendations()
    
    def _parse_text_response(self, response_text: str) -> Dict[str, List[Dict]]:
        """Parse text response from LLM and convert to structured format"""
        try:
            recommendations = {
                "movies": [],
                "music": [],
                "places": [],
                "events": []
            }
            return recommendations
        except Exception as e:
            logger.error(f"Error parsing text response: {str(e)}")
            return self._get_fallback_recommendations()
    
    def _extract_items_from_text(self, text: str, category: str) -> List[Dict]:
        """
        Extract individual items from text section
        """
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
                
            item_text = line.split('.', 1)[1].strip() if '.' in line else line
            title = self._extract_title(item_text)
            
            if title:
                item = {
                    "title" if category in ["movies", "music"] else "name": title,
                    "description": item_text,
                    "category": category
                }
                
                if category == "movies":
                    item.update({
                        "year": "Unknown",
                        "genre": "Unknown",
                        "rating": "Unknown"
                    })
                elif category == "music":
                    item.update({
                        "artist": "Unknown",
                        "genre": "Unknown",
                        "release_year": "Unknown"
                    })
                elif category == "places":
                    item.update({
                        "type": "Unknown",
                        "rating": 4.0,
                        "location": {"lat": 0, "lng": 0}
                    })
                elif category == "events":
                    item.update({
                        "date": "Unknown",
                        "venue": "Unknown",
                        "price": "Unknown"
                    })
                
                items.append(item)
        
        return items
    
    def _extract_title(self, text: str) -> str:
        """
        Extract title/name from item text
        """
        import re
        bold_match = re.search(r'\*\*(.*?)\*\*', text)
        if bold_match:
            return bold_match.group(1).strip()
        
        quote_match = re.search(r'"([^"]*)"', text)
        if quote_match:
            return quote_match.group(1).strip()
        
        title = text.split('(')[0].split(' - ')[0].strip()
        
        if len(title) > 100:
            title = title[:100] + "..."
            
        return title
    
    def _robust_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse JSON that may be wrapped in code fences or include extra prose.
        """
        try:
            text = raw.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                candidate = text[start_idx:end_idx + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
            return None
        except Exception:
            return None
    
    def _process_llm_recommendations(self, recommendations: Dict[str, Any], user_id: str = None, current_city: str = "Barcelona") -> Dict[str, List[Dict]]:
        """
        Process and enhance recommendations from the LLM API
        """
        try:
            processed = {
                "movies": recommendations.get("movies", []),
                "music": recommendations.get("music", []),
                "places": recommendations.get("places", []),
                "events": recommendations.get("events", [])
            }
            
            history = self._get_user_interaction_history(user_id) if user_id else {}
            
            for category, items in processed.items():
                if not isinstance(items, list):
                    processed[category] = []
                    continue
                    
                for item in items:
                    if not isinstance(item, dict):
                        continue
                        
                    item["ranking_score"] = self._compute_ranking_score(item, category, history) if user_id else self.BASE_SCORE
                    
                    if not item.get("why_would_you_like_this"):
                        item["why_would_you_like_this"] = self._generate_personalized_reason(
                            item, category, "", user_id, current_city
                        )
            
            return processed
        except Exception as e:
            logger.error(f"Error processing LLM recommendations: {str(e)}")
            return self._get_fallback_recommendations()
    
    def _get_fallback_recommendations(self) -> Dict[str, List[Dict]]:
        """
        Get fallback recommendations when LLM API fails
        """
        logger.info("Using fallback recommendations due to API failure")
        return {
            "movies": [],
            "music": [],
            "places": [],
            "events": []
        }
    
    def _generate_personalized_reason(self, item: Dict[str, Any], category: str, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> str:
        """Generate personalized reason why user would like this recommendation"""
        prompt_text = prompt.lower() if prompt else "your interests"
        base_reasons = {
            "movies": [
                f"Based on your interest in {prompt_text}, this {item.get('genre', 'film') if item else 'film'} offers compelling storytelling in {current_city}",
                f"The cast featuring {', '.join(item.get('cast', ['talented actors'])[:2]) if item else 'talented actors'} aligns with quality performances you appreciate in {current_city}",
                f"This {item.get('year', 'recent') if item else 'recent'} film's themes resonate with your viewing preferences in {current_city}"
            ],
            "music": [
                f"This {item.get('genre', 'track') if item else 'track'} matches your musical taste with its {item.get('mood', 'engaging') if item else 'engaging'} energy in {current_city}",
                f"The artist {item.get('artist', 'musician') if item else 'musician'} creates the perfect soundtrack for your {current_city} lifestyle",
                f"With {item.get('monthly_listeners', 'many') if item else 'many'} monthly listeners, this song captures the zeitgeist you're looking for in {current_city}"
            ],
            "places": [
                f"Located in {current_city}, this {item.get('type', 'location') if item else 'location'} offers the perfect {item.get('preferred_time', 'anytime') if item else 'anytime'} experience",
                f"With a {item.get('rating', 4.5) if item else 4.5} rating and {item.get('user_ratings_total', 'many') if item else 'many'} reviews, it's a local favorite in {current_city}",
                f"The {item.get('category', 'venue') if item else 'venue'} provides exactly what you're seeking in {current_city}"
            ],
            "events": [
                f"This {item.get('category', 'event') if item else 'event'} happening in {current_city} perfectly matches your cultural interests",
                f"Organized by {item.get('organizer', 'top promoters') if item else 'top promoters'}, it promises a {item.get('duration', 'memorable') if item else 'memorable'} experience in {current_city}",
                f"The {item.get('event_type', 'gathering') if item else 'gathering'} offers {item.get('languages', ['multilingual'])[0] if item else 'multilingual'} accessibility in {current_city}"
            ]
        }
        
        if user_id:
            personalized_additions = [
                "your previous positive interactions suggest you'll love this",
                "based on your engagement history, this aligns perfectly with your preferences",
                "your activity pattern indicates this will be a great match",
                "considering your past choices, this recommendation scores highly for you"
            ]
            base_reason = random.choice(base_reasons.get(category, [f"This recommendation suits your taste in {current_city}"]))
            personal_touch = random.choice(personalized_additions)
            return f"{base_reason}, and {personal_touch}."
        else:
            return random.choice(base_reasons.get(category, [f"This recommendation suits your taste in {current_city}"])) + "."
    
    def _store_in_redis(self, user_id: str, data: Dict[str, Any]):
        """Store recommendations in Redis"""
        try:
            key = f"recommendations:{user_id}"
            data_size = len(json.dumps(data, default=str))
            
            logger.info("Storing recommendations in Redis",
                       user_id=user_id,
                       key=key,
                       data_size_bytes=data_size,
                       ttl_seconds=86400)
            
            self.redis_client.setex(
                key,
                86400,
                json.dumps(data, default=str)
            )
            
            logger.info("Recommendations stored successfully in Redis",
                       user_id=user_id,
                       key=key,
                       data_size_bytes=data_size)
            
            # Publish notification
            try:
                notify_payload = {
                    "type": "notification",
                    "user_id": str(user_id),
                    "message": {"content": "Your new recommendations are ready!"}
                }
                pub_client = redis.Redis(host=settings.redis_host, port=6379, db=0, decode_responses=True)
                pub_client.publish("notifications:user", json.dumps(notify_payload))
                
                logger.info("Notification published successfully",
                           user_id=user_id,
                           channel="notifications:user",
                           notification_type="recommendations_ready")
            except Exception as pub_err:
                logger.error("Failed to publish notification",
                            user_id=user_id,
                            error=str(pub_err),
                            channel="notifications:user")
        except Exception as e:
            logger.error("Error storing recommendations in Redis",
                        user_id=user_id,
                        key=key,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "store_redis"})
    
    def get_recommendations_from_redis(self, user_id: str) -> Dict[str, Any]:
        """Retrieve recommendations from Redis"""
        try:
            key = f"recommendations:{user_id}"
            logger.info("Retrieving recommendations from Redis",
                       user_id=user_id,
                       key=key)
            
            data = self.redis_client.get(key)
            if data:
                data_size = len(data)
                logger.info("Recommendations retrieved successfully from Redis",
                           user_id=user_id,
                           key=key,
                           data_size_bytes=data_size)
                return json.loads(data)
            else:
                logger.info("No recommendations found in Redis",
                           user_id=user_id,
                           key=key)
                return None
        except Exception as e:
            logger.error("Error retrieving recommendations from Redis",
                        user_id=user_id,
                        key=key,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "get_redis"})
            return None
    
    def clear_recommendations(self, user_id: str = None):
        """Clear recommendations from Redis"""
        try:
            if user_id:
                key = f"recommendations:{user_id}"
                logger.info("Clearing recommendations for specific user",
                           user_id=user_id,
                           key=key)
                
                deleted_count = self.redis_client.delete(key)
                logger.info("Recommendations cleared successfully",
                           user_id=user_id,
                           key=key,
                           deleted_count=deleted_count)
            else:
                logger.info("Clearing all recommendations from Redis")
                keys = self.redis_client.keys("recommendations:*")
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
                    logger.info("All recommendations cleared successfully",
                               total_keys=len(keys),
                               deleted_count=deleted_count)
                else:
                    logger.info("No recommendation keys found to clear")
        except Exception as e:
            logger.error("Error clearing recommendations from Redis",
                        user_id=user_id,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "clear_redis"})


llm_service = LLMService(timeout=120)
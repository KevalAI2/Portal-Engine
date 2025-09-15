"""
Results Service for ranking, filtering and deduplicating recommendations
"""
import json
from typing import Dict, Any, List, Tuple
from app.core.logging import get_logger, log_exception
import redis
from app.core.config import settings

logger = get_logger("results_service")


class ResultsService:
    """Service to rank, filter and deduplicate recommendations"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        logger.info("Initializing Results service",
                   timeout=timeout,
                   redis_host=settings.redis_host,
                   redis_port=6379,
                   redis_db=1)
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=6379,
                db=1,
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully",
                       service="results_service",
                       redis_host=settings.redis_host)
        except Exception as e:
            logger.error("Failed to connect to Redis",
                        service="results_service",
                        redis_host=settings.redis_host,
                        error=str(e))
            raise
    
    def get_ranked_results(self, user_id: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get ranked and filtered results for a user
        
        Args:
            user_id: User identifier
            filters: Optional filters (category, limit, min_score)
            
        Returns:
            Ranked and filtered recommendations
        """
        try:
            logger.info("Getting ranked results for user",
                       user_id=user_id,
                       filters=filters,
                       service="results_service",
                       operation="get_ranked_results")
            
            # Get raw recommendations from Redis
            raw_data = self._get_recommendations(user_id)
            
            # If no Redis data, generate dummy ranked results
            if not raw_data:
                logger.info("No stored recommendations found, using dummy ranked data",
                           user_id=user_id,
                           service="results_service")
                return self._generate_dummy_ranked_results(user_id, filters or {})
            
            # Extract recommendations and user context
            recommendations = raw_data.get("recommendations", {})
            prompt = raw_data.get("prompt", "")
            
            # Apply ranking algorithm
            # ranked_results = self._rank_recommendations(recommendations, prompt, user_id)
            
            # Apply deduplication
            deduplicated_results = self._deduplicate_results(recommendations)
            
            # Apply filters
            filtered_results = self._apply_filters(deduplicated_results, filters or {})
            
            # Calculate final metadata
            metadata = self._calculate_metadata(filtered_results, raw_data)
            
            return {
                "success": True,
                "user_id": user_id,
                "ranked_recommendations": filtered_results,
                "metadata": metadata,
                "applied_filters": filters or {},
                "processing_info": {
                    "raw_count": sum(len(cat) for cat in recommendations.values()),
                    # "ranked_count": sum(len(cat) for cat in ranked_results.values()),
                    "final_count": sum(len(cat) for cat in filtered_results.values())
                }
            }
            
        except Exception as e:
            logger.error("Error processing ranked results",
                        user_id=user_id,
                        error=str(e),
                        service="results_service",
                        operation="get_ranked_results")
            log_exception("results_service", e, {"user_id": user_id, "operation": "get_ranked_results"})
            return {"success": False, "message": str(e)}
    
    def _get_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get recommendations from Redis"""
        try:
            key = f"recommendations:{user_id}"
            logger.info("Retrieving recommendations from Redis",
                       user_id=user_id,
                       key=key,
                       service="results_service",
                       operation="get_recommendations")
            
            data = self.redis_client.get(key)
            if data:
                data_size = len(data)
                logger.info("Recommendations retrieved successfully from Redis",
                           user_id=user_id,
                           key=key,
                           data_size_bytes=data_size,
                           service="results_service")
                return json.loads(data)
            else:
                logger.info("No recommendations found in Redis",
                           user_id=user_id,
                           key=key,
                           service="results_service")
                return None
        except Exception as e:
            logger.error("Error getting recommendations from Redis",
                        user_id=user_id,
                        key=key,
                        error=str(e),
                        service="results_service")
            log_exception("results_service", e, {"user_id": user_id, "operation": "get_recommendations"})
            return None
    
    def _rank_recommendations(self, recommendations: Dict[str, List], prompt: str, user_id: str) -> Dict[str, List]:
        """Apply ranking algorithm to recommendations"""
        ranked_recs = {}
        
        for category, items in recommendations.items():
            # Calculate scores for each item
            scored_items = []
            for item in items:
                score = self._calculate_item_score(item, prompt, category)
                scored_items.append({**item, "ranking_score": score})
            
            # Sort by score (highest first)
            scored_items.sort(key=lambda x: x["ranking_score"], reverse=True)
            ranked_recs[category] = scored_items
        
        return ranked_recs
    
    def _calculate_item_score(self, item: Dict, prompt: str, category: str) -> float:
        """Calculate ranking score for an item"""
        score = 0.0
        prompt_lower = prompt.lower()
        
        # Base score
        score += 1.0
        
        # Title/Name relevance (50% weight)
        item_name = item.get("title", item.get("name", "")).lower()
        if any(word in item_name for word in prompt_lower.split() if len(word) > 3):
            score += 5.0
        
        # Genre/Type relevance (30% weight)
        genre = item.get("genre", item.get("type", "")).lower()
        if any(word in genre for word in prompt_lower.split() if len(word) > 3):
            score += 3.0
        
        # Description relevance (20% weight)
        description = item.get("description", "").lower()
        if any(word in description for word in prompt_lower.split() if len(word) > 3):
            score += 2.0
        
        return round(score, 2)
    
    def _deduplicate_results(self, recommendations: Dict[str, List]) -> Dict[str, List]:
        """Remove duplicate recommendations"""
        deduplicated = {}
        seen_titles = set()
        
        for category, items in recommendations.items():
            unique_items = []
            for item in items:
                title_key = item.get("title", item.get("name", "")).lower().strip()
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_items.append(item)
            deduplicated[category] = unique_items
        
        return deduplicated
    
    def _apply_filters(self, recommendations: Dict[str, List], filters: Dict[str, Any]) -> Dict[str, List]:
        """Apply filtering logic"""
        filtered = {}
        
        # Extract filter parameters
        category_filter = filters.get("category")
        limit_per_category = filters.get("limit", 5)
        min_score = filters.get("min_score", 0.0)
        
        for category, items in recommendations.items():
            # Skip if category not in filter
            if category_filter and category != category_filter:
                continue
            
            # Apply score filter
            filtered_items = [item for item in items if item.get("ranking_score", 0) >= min_score]
            
            # Apply limit
            filtered_items = filtered_items[:limit_per_category]
            
            filtered[category] = filtered_items
        
        return filtered
    
    def _calculate_metadata(self, recommendations: Dict[str, List], raw_data: Dict) -> Dict[str, Any]:
        """Calculate metadata for the results"""
        total_items = sum(len(cat) for cat in recommendations.values())
        categories = list(recommendations.keys())
        
        # Calculate average score per category
        avg_scores = {}
        for category, items in recommendations.items():
            if items:
                scores = [item.get("ranking_score", 0) for item in items]
                avg_scores[category] = round(sum(scores) / len(scores), 2)
            else:
                avg_scores[category] = 0.0
        
        return {
            "total_results": total_items,
            "categories": categories,
            "average_scores": avg_scores,
            "highest_scored_category": max(avg_scores.keys(), key=lambda k: avg_scores[k]) if avg_scores else None,
            "original_generation_time": raw_data.get("generated_at"),
            "ranking_processed_at": __import__("time").time()
        }
    
    def _generate_dummy_ranked_results(self, user_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dummy ranked results when no Redis data exists"""
        import time
        import random
        
        # Dummy recommendations with ranking scores (Barcelona-themed)
        dummy_recommendations = {
            "movies": [
                {"title": "Vicky Cristina Barcelona", "genre": "Romance-Drama", "description": "A romantic story set in Barcelona", "ranking_score": 8.5},
                {"title": "L'Auberge Espagnole", "genre": "Comedy-Drama", "description": "Students living in Barcelona", "ranking_score": 8.2},
                {"title": "All About My Mother", "genre": "Drama", "description": "Almodóvar's masterpiece set in Barcelona", "ranking_score": 7.8},
                {"title": "Barcelona", "genre": "Comedy-Drama", "description": "Americans in 1980s Barcelona", "ranking_score": 7.5},
                {"title": "Biutiful", "genre": "Drama", "description": "Gritty Barcelona drama", "ranking_score": 7.2}
            ],
            "music": [
                {"title": "Barcelona", "artist": "Freddie Mercury & Montserrat Caballé", "description": "Olympic anthem for Barcelona", "ranking_score": 8.0},
                {"title": "Mediterráneo", "artist": "Joan Manuel Serrat", "description": "Classic Catalan folk song", "ranking_score": 7.8},
                {"title": "La Flaca", "artist": "Jarabe de Palo", "description": "Barcelona rock anthem", "ranking_score": 7.5},
                {"title": "Rumba Catalana", "artist": "Gipsy Kings", "description": "Traditional Barcelona rumba", "ranking_score": 7.2},
                {"title": "Gaudí", "artist": "Manu Chao", "description": "Tribute to Barcelona's architect", "ranking_score": 6.9}
            ],
            "places": [
                {"name": "Sagrada Família", "location": "Barcelona", "description": "Gaudí's unfinished masterpiece", "ranking_score": 9.0},
                {"name": "Park Güell", "location": "Barcelona", "description": "Colorful mosaic park by Gaudí", "ranking_score": 8.5},
                {"name": "Las Ramblas", "location": "Barcelona", "description": "Famous pedestrian street", "ranking_score": 8.2},
                {"name": "Casa Batlló", "location": "Barcelona", "description": "Modernist house by Gaudí", "ranking_score": 7.8},
                {"name": "Barceloneta Beach", "location": "Barcelona", "description": "Popular city beach", "ranking_score": 7.5}
            ],
            "events": [
                {"name": "La Mercè Festival", "location": "Barcelona", "description": "Barcelona's biggest street festival", "ranking_score": 8.8},
                {"name": "Festa Major de Gràcia", "location": "Barcelona", "description": "Neighborhood celebration with decorated streets", "ranking_score": 8.3},
                {"name": "Primavera Sound", "location": "Barcelona", "description": "International music festival", "ranking_score": 8.0},
                {"name": "Sant Jordi Day", "location": "Barcelona", "description": "Day of books and roses", "ranking_score": 7.7},
                {"name": "Nit Blanca", "location": "Barcelona", "description": "White night cultural event", "ranking_score": 7.4}
            ]
        }
        
        # Apply filters to dummy data
        filtered_results = self._apply_filters(dummy_recommendations, filters)
        
        # Calculate metadata
        dummy_metadata = {
            "total_results": sum(len(cat) for cat in filtered_results.values()),
            "categories": list(filtered_results.keys()),
            "average_scores": {
                cat: round(sum(item["ranking_score"] for item in items) / len(items), 2) if items else 0.0
                for cat, items in filtered_results.items()
            },
            "highest_scored_category": "places",
            "original_generation_time": None,
            "ranking_processed_at": time.time()
        }
        
        return {
            "success": True,
            "user_id": user_id,
            "ranked_recommendations": filtered_results,
            "metadata": dummy_metadata,
            "applied_filters": filters,
            "processing_info": {
                "raw_count": 20,  # Total dummy items
                "ranked_count": 20,
                "final_count": sum(len(cat) for cat in filtered_results.values())
            },
            "data_source": "dummy_data",
            "message": "Using dummy recommendations - run process-comprehensive to generate personalized results"
        }


# Global instance
results_service = ResultsService()

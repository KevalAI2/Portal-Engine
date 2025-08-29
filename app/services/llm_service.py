"""
LLM Service for generating recommendations
"""
import json
import time
import random
from typing import Dict, Any, List
from core.logging import get_logger
from core.config import settings
import redis

logger = get_logger("llm_service")


class LLMService:
    """Service to generate recommendations from prompts and store in Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=6379,
            db=1,  # Use different DB for recommendations
            decode_responses=True
        )
        self._setup_demo_data()
    
    def _setup_demo_data(self):
        """Setup demo recommendation data"""
        self.demo_recommendations = {
            "movies": {
                "indian": [
                    {"title": "3 Idiots", "genre": "Comedy-Drama", "description": "A heartwarming story about friendship and education"},
                    {"title": "Lagaan", "genre": "Sports-Drama", "description": "Epic cricket match against British rule"},
                    {"title": "Dangal", "genre": "Biographical-Sports", "description": "True story of wrestling champions"},
                    {"title": "PK", "genre": "Comedy-Satire", "description": "Alien questions religious beliefs"},
                    {"title": "Queen", "genre": "Comedy-Drama", "description": "Woman's solo honeymoon journey"}
                ],
                "western": [
                    {"title": "The Shawshank Redemption", "genre": "Drama", "description": "Hope and friendship in prison"},
                    {"title": "Inception", "genre": "Sci-Fi-Thriller", "description": "Dreams within dreams"},
                    {"title": "The Dark Knight", "genre": "Action-Drama", "description": "Batman vs Joker"},
                    {"title": "Interstellar", "genre": "Sci-Fi-Adventure", "description": "Space exploration to save humanity"},
                    {"title": "Forrest Gump", "genre": "Drama-Comedy", "description": "Life story of a simple man"}
                ]
            },
            "music": {
                "indian": [
                    {"title": "Tum Hi Ho", "artist": "Arijit Singh", "description": "Romantic Bollywood melody"},
                    {"title": "Kesariya", "artist": "Arijit Singh", "description": "Modern romantic song"},
                    {"title": "Raataan Lambiyan", "artist": "Jubin Nautiyal", "description": "Soulful love ballad"},
                    {"title": "Chaleya", "artist": "Arijit Singh", "description": "Upbeat romantic track"},
                    {"title": "Tere Vaaste", "artist": "Varun Jain", "description": "Contemporary love song"}
                ],
                "western": [
                    {"title": "Blinding Lights", "artist": "The Weeknd", "description": "80s-inspired pop hit"},
                    {"title": "Shape of You", "artist": "Ed Sheeran", "description": "Catchy pop love song"},
                    {"title": "Dance Monkey", "artist": "Tones and I", "description": "Viral pop sensation"},
                    {"title": "Bad Guy", "artist": "Billie Eilish", "description": "Dark pop anthem"},
                    {"title": "Old Town Road", "artist": "Lil Nas X", "description": "Country-rap fusion"}
                ]
            },
            "places": {
                "indian": [
                    {"name": "Taj Mahal", "location": "Agra", "description": "Iconic white marble mausoleum"},
                    {"name": "Golden Temple", "location": "Amritsar", "description": "Sacred Sikh gurdwara"},
                    {"name": "Gateway of India", "location": "Mumbai", "description": "Historic monument"},
                    {"name": "Hawa Mahal", "location": "Jaipur", "description": "Palace of winds"},
                    {"name": "Mysore Palace", "location": "Mysore", "description": "Royal palace complex"}
                ],
                "western": [
                    {"name": "Eiffel Tower", "location": "Paris", "description": "Iconic iron lattice tower"},
                    {"name": "Statue of Liberty", "location": "New York", "description": "Freedom symbol"},
                    {"name": "Big Ben", "location": "London", "description": "Famous clock tower"},
                    {"name": "Colosseum", "location": "Rome", "description": "Ancient amphitheater"},
                    {"name": "Sydney Opera House", "location": "Sydney", "description": "Architectural masterpiece"}
                ]
            },
            "events": {
                "indian": [
                    {"name": "Diwali Festival", "location": "Pan India", "description": "Festival of lights"},
                    {"name": "Holi Festival", "location": "Pan India", "description": "Festival of colors"},
                    {"name": "Ganesh Chaturthi", "location": "Mumbai", "description": "Elephant god celebration"},
                    {"name": "Durga Puja", "location": "Kolkata", "description": "Goddess worship festival"},
                    {"name": "Onam", "location": "Kerala", "description": "Harvest festival"}
                ],
                "western": [
                    {"name": "Coachella", "location": "California", "description": "Music and arts festival"},
                    {"name": "Mardi Gras", "location": "New Orleans", "description": "Carnival celebration"},
                    {"name": "Oktoberfest", "location": "Munich", "description": "Beer festival"},
                    {"name": "Carnival", "location": "Rio de Janeiro", "description": "Brazilian street festival"},
                    {"name": "Glastonbury", "location": "England", "description": "Music festival"}
                ]
            }
        }
    
    def generate_recommendations(self, prompt: str, user_id: str = None) -> Dict[str, Any]:
        """
        Generate recommendations based on prompt and store in Redis
        
        Args:
            prompt: The input prompt
            user_id: Optional user ID for storing results
            
        Returns:
            Dictionary with recommendations and metadata
        """
        try:
            logger.info(f"Generating recommendations for prompt: {prompt[:100]}...")
            
            # Simulate LLM processing time
            time.sleep(random.uniform(0.5, 2.0))
            
            # Generate recommendations based on prompt content
            recommendations = self._generate_demo_recommendations(prompt)
            
            # Create response structure
            response = {
                "success": True,
                "prompt": prompt,
                "user_id": user_id,
                "generated_at": time.time(),
                "processing_time": random.uniform(0.5, 2.0),
                "recommendations": recommendations,
                "metadata": {
                    "total_recommendations": sum(len(cat) for cat in recommendations.values()),
                    "categories": list(recommendations.keys()),
                    "model": "demo-llm-v1.0"
                }
            }
            
            # Store in Redis if user_id provided
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
    
    def _generate_demo_recommendations(self, prompt: str) -> Dict[str, List[Dict]]:
        """Generate demo recommendations based on prompt content"""
        recommendations = {
            "movies": [],
            "music": [],
            "places": [],
            "events": []
        }
        
        # Analyze prompt to determine preferences
        prompt_lower = prompt.lower()
        
        # Determine cultural preference
        indian_weight = 0.5
        if any(word in prompt_lower for word in ["indian", "bollywood", "hindi", "desi"]):
            indian_weight = 0.8
        elif any(word in prompt_lower for word in ["western", "hollywood", "english", "american"]):
            indian_weight = 0.2
        
        # Generate recommendations for each category
        for category in recommendations.keys():
            category_recommendations = []
            
            # Add Indian recommendations
            if random.random() < indian_weight:
                indian_items = random.sample(
                    self.demo_recommendations[category]["indian"],
                    min(3, len(self.demo_recommendations[category]["indian"]))
                )
                category_recommendations.extend(indian_items)
            
            # Add Western recommendations
            if random.random() < (1 - indian_weight):
                western_items = random.sample(
                    self.demo_recommendations[category]["western"],
                    min(3, len(self.demo_recommendations[category]["western"]))
                )
                category_recommendations.extend(western_items)
            
            # Ensure we have at least 2 recommendations per category
            if len(category_recommendations) < 2:
                remaining_items = (
                    self.demo_recommendations[category]["indian"] + 
                    self.demo_recommendations[category]["western"]
                )
                additional_items = random.sample(
                    remaining_items,
                    min(2 - len(category_recommendations), len(remaining_items))
                )
                category_recommendations.extend(additional_items)
            
            recommendations[category] = category_recommendations[:5]  # Limit to 5 per category
        
        return recommendations
    
    def _store_in_redis(self, user_id: str, data: Dict[str, Any]):
        """Store recommendations in Redis"""
        try:
            key = f"recommendations:{user_id}"
            # Store for 24 hours
            self.redis_client.setex(
                key,
                86400,  # 24 hours in seconds
                json.dumps(data)
            )
            logger.info(f"Stored recommendations in Redis for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing in Redis: {str(e)}")
    
    def get_recommendations_from_redis(self, user_id: str) -> Dict[str, Any]:
        """Retrieve recommendations from Redis"""
        try:
            key = f"recommendations:{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Redis: {str(e)}")
            return None
    
    def clear_recommendations(self, user_id: str = None):
        """Clear recommendations from Redis"""
        try:
            if user_id:
                key = f"recommendations:{user_id}"
                self.redis_client.delete(key)
                logger.info(f"Cleared recommendations for user {user_id}")
            else:
                # Clear all recommendation keys
                keys = self.redis_client.keys("recommendations:*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared all recommendations ({len(keys)} keys)")
        except Exception as e:
            logger.error(f"Error clearing recommendations: {str(e)}")


# Global instance
llm_service = LLMService()

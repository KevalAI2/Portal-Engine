"""
Redis cache service for storing and retrieving recommendations
"""
import json
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from core.logging import get_logger
from core.config import settings
from core.constants import REDIS_KEY_PATTERNS, CACHE_TTL
from models.schemas import RecommendationResponse, RecommendationItem


class CacheService:
    """Redis cache service for recommendations and other data"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.logger = get_logger(self.__class__.__name__)
    
    def _get_key(self, key_type: str, **kwargs) -> str:
        """Generate Redis key with namespace"""
        pattern = REDIS_KEY_PATTERNS.get(key_type, key_type)
        return pattern.format(
            namespace=settings.redis_namespace,
            **kwargs
        )
    
    async def store_recommendations(
        self, 
        user_id: str, 
        recommendation_type: str, 
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """Store recommendations in Redis cache"""
        try:
            key = self._get_key("recommendation", user_id=user_id, type=recommendation_type)
            
            # Convert to RecommendationResponse format
            recommendation_items = [
                RecommendationItem(**rec) for rec in recommendations
            ]
            
            response = RecommendationResponse(
                user_id=user_id,
                type=recommendation_type,
                recommendations=recommendation_items,
                generated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=CACHE_TTL["recommendation"]),
                total_count=len(recommendation_items)
            )
            
            # Store in Redis with TTL
            self.redis_client.setex(
                key,
                CACHE_TTL["recommendation"],
                response.model_dump_json()
            )
            
            self.logger.info(
                "Stored recommendations in cache",
                user_id=user_id,
                type=recommendation_type,
                count=len(recommendation_items)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to store recommendations in cache",
                user_id=user_id,
                type=recommendation_type,
                error=str(e)
            )
            return False
    
    async def get_recommendations(
        self, 
        user_id: str, 
        recommendation_type: str
    ) -> Optional[RecommendationResponse]:
        """Retrieve recommendations from Redis cache"""
        try:
            key = self._get_key("recommendation", user_id=user_id, type=recommendation_type)
            
            data = self.redis_client.get(key)
            if not data:
                return None
            
            response = RecommendationResponse.model_validate_json(data)
            
            # Check if expired
            if response.expires_at < datetime.utcnow():
                self.redis_client.delete(key)
                return None
            
            self.logger.info(
                "Retrieved recommendations from cache",
                user_id=user_id,
                type=recommendation_type,
                count=response.total_count
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve recommendations from cache",
                user_id=user_id,
                type=recommendation_type,
                error=str(e)
            )
            return None
    
    async def store_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Store user data in cache"""
        try:
            key = self._get_key("user_data", user_id=user_id)
            
            self.redis_client.setex(
                key,
                CACHE_TTL["user_data"],
                json.dumps(data)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to store user data in cache",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user data from cache"""
        try:
            key = self._get_key("user_data", user_id=user_id)
            
            data = self.redis_client.get(key)
            if not data:
                return None
            
            return json.loads(data)
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve user data from cache",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def delete_recommendations(self, user_id: str, recommendation_type: str) -> bool:
        """Delete recommendations from cache"""
        try:
            key = self._get_key("recommendation", user_id=user_id, type=recommendation_type)
            self.redis_client.delete(key)
            
            self.logger.info(
                "Deleted recommendations from cache",
                user_id=user_id,
                type=recommendation_type
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete recommendations from cache",
                user_id=user_id,
                type=recommendation_type,
                error=str(e)
            )
            return False
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

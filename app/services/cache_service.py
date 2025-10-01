"""
Advanced caching service with multi-level caching strategy.

This module provides a comprehensive caching solution with Redis pipelining,
TTL management, cache invalidation, and warming strategies.

Classes:
    MultiLevelCacheService: Main caching service with advanced features.

Features:
    - Redis pipelining for improved performance
    - TTL management with configurable expiration times
    - Cache invalidation (single and pattern-based)
    - Cache warming for frequently accessed data
    - Batch operations for multiple items
    - Comprehensive error handling and logging
    - Cache statistics and monitoring

Example:
    >>> from app.services.cache_service import cache_service
    >>> cache_service.set("user_profile", "user123", {"name": "John"})
    >>> data = cache_service.get("user_profile", "user123")
    >>> cache_service.invalidate("user_profile", "user123")
"""
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
import redis
from app.core.config import settings
from app.core.logging import get_logger, log_exception

logger = get_logger("cache_service")


class MultiLevelCacheService:
    """
    Multi-level caching service with TTL, invalidation, and warming strategies.
    
    This class provides advanced caching capabilities including Redis pipelining,
    TTL management, cache invalidation, and warming strategies for optimal
    performance and data consistency.
    
    Attributes:
        redis_client (redis.Redis): Redis client instance.
        cache_hits (int): Number of cache hits.
        cache_misses (int): Number of cache misses.
        cache_ttl (Dict[str, int]): TTL configuration for different cache types.
        
    Methods:
        get(key_type, identifier, **kwargs): Get data from cache.
        set(key_type, identifier, data, ttl, **kwargs): Set data in cache.
        get_multiple(key_type, identifiers, **kwargs): Get multiple items from cache.
        set_multiple(key_type, data_dict, ttl, **kwargs): Set multiple items in cache.
        invalidate(key_type, identifier, **kwargs): Invalidate specific cache entry.
        invalidate_pattern(key_type, pattern): Invalidate cache entries matching pattern.
        warm_cache(key_type, data_func, identifiers, **kwargs): Warm cache with data.
        get_stats(): Get cache statistics.
        cleanup_expired(key_type): Clean up expired cache entries.
        
    Example:
        >>> cache = MultiLevelCacheService()
        >>> cache.set("user_profile", "user123", {"name": "John"}, ttl=3600)
        >>> data = cache.get("user_profile", "user123")
        >>> cache.invalidate("user_profile", "user123")
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._create_redis_client()
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_ttl = {
            'user_profile': 3600,  # 1 hour
            'location_data': 1800,  # 30 minutes
            'interaction_data': 900,  # 15 minutes
            'recommendations': 1800,  # 30 minutes
            'prompts': 7200,  # 2 hours
            'api_responses': 300,  # 5 minutes
        }
        
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client with proper configuration"""
        return redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_connect_timeout=3,
            socket_timeout=5,
            health_check_interval=30,
            decode_responses=True
        )
    
    def _get_cache_key(self, key_type: str, identifier: str, **kwargs: Any) -> str:
        """Generate namespaced cache key"""
        namespace = settings.redis_namespace
        return f"{namespace}:{key_type}:{identifier}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
    
    def get(self, key_type: str, identifier: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Get data from cache with pipelining support"""
        try:
            cache_key = self._get_cache_key(key_type, identifier, **kwargs)
            
            # Use pipeline for better performance
            with self.redis_client.pipeline(transaction=False) as pipe:
                pipe.get(cache_key)
                pipe.ttl(cache_key)
                results = pipe.execute()
            
            if len(results) >= 2:
                data, ttl = results[0], results[1]
            else:
                data, ttl = None, 0
            if data:
                self.cache_hits += 1
                logger.debug("Cache hit", key_type=key_type, identifier=identifier, ttl=ttl)
                return json.loads(data)
            else:
                self.cache_misses += 1
                logger.debug("Cache miss", key_type=key_type, identifier=identifier)
                return None
                
        except Exception as e:
            logger.error("Cache get error", key_type=key_type, identifier=identifier, error=str(e))
            log_exception("cache_service", e, {"operation": "get", "key_type": key_type, "identifier": identifier})
            return None
    
    def set(self, key_type: str, identifier: str, data: Dict[str, Any], ttl: Optional[int] = None, **kwargs: Any) -> bool:
        """Set data in cache with TTL"""
        try:
            cache_key = self._get_cache_key(key_type, identifier, **kwargs)
            ttl = ttl or self.cache_ttl.get(key_type, 3600)
            
            # Serialize data
            serialized_data = json.dumps(data, default=str)
            
            # Use pipeline for better performance
            with self.redis_client.pipeline(transaction=False) as pipe:
                pipe.setex(cache_key, ttl, serialized_data)
                pipe.sadd(f"{settings.redis_namespace}:keys:{key_type}", cache_key)
                pipe.execute()
            
            logger.debug("Cache set", key_type=key_type, identifier=identifier, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("Cache set error", key_type=key_type, identifier=identifier, error=str(e))
            log_exception("cache_service", e, {"operation": "set", "key_type": key_type, "identifier": identifier})
            return False
    
    def get_multiple(self, key_type: str, identifiers: List[str], **kwargs: Any) -> Dict[str, Dict[str, Any]]:
        """Get multiple items from cache using pipelining"""
        try:
            if not identifiers:
                return {}
            
            cache_keys = [self._get_cache_key(key_type, identifier, **kwargs) for identifier in identifiers]
            
            # Use pipeline for batch retrieval
            with self.redis_client.pipeline(transaction=False) as pipe:
                for key in cache_keys:
                    pipe.get(key)
                results = pipe.execute()
            
            # Process results
            cached_data = {}
            for i, (identifier, data) in enumerate(zip(identifiers, results)):
                if data:
                    try:
                        cached_data[identifier] = json.loads(data)
                        self.cache_hits += 1
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in cache", identifier=identifier)
                        self.cache_misses += 1
                else:
                    self.cache_misses += 1
            
            logger.debug("Batch cache retrieval", 
                        key_type=key_type, 
                        requested=len(identifiers), 
                        found=len(cached_data))
            return cached_data
            
        except Exception as e:
            logger.error("Batch cache get error", key_type=key_type, error=str(e))
            log_exception("cache_service", e, {"operation": "get_multiple", "key_type": key_type})
            return {}
    
    def set_multiple(self, key_type: str, data_dict: Dict[str, Dict[str, Any]], ttl: Optional[int] = None, **kwargs: Any) -> int:
        """Set multiple items in cache using pipelining"""
        try:
            if not data_dict:
                return 0
            
            ttl = ttl or self.cache_ttl.get(key_type, 3600)
            set_count = 0
            
            # Use pipeline for batch operations
            with self.redis_client.pipeline(transaction=False) as pipe:
                for identifier, data in data_dict.items():
                    cache_key = self._get_cache_key(key_type, identifier, **kwargs)
                    serialized_data = json.dumps(data, default=str)
                    pipe.setex(cache_key, ttl, serialized_data)
                    pipe.sadd(f"{settings.redis_namespace}:keys:{key_type}", cache_key)
                
                pipe.execute()
                set_count = len(data_dict)
            
            logger.debug("Batch cache set", key_type=key_type, count=set_count, ttl=ttl)
            return set_count
            
        except Exception as e:
            logger.error("Batch cache set error", key_type=key_type, error=str(e))
            log_exception("cache_service", e, {"operation": "set_multiple", "key_type": key_type})
            return 0
    
    def invalidate(self, key_type: str, identifier: str, **kwargs: Any) -> bool:
        """Invalidate specific cache entry"""
        try:
            cache_key = self._get_cache_key(key_type, identifier, **kwargs)
            
            with self.redis_client.pipeline(transaction=False) as pipe:
                pipe.delete(cache_key)
                pipe.srem(f"{settings.redis_namespace}:keys:{key_type}", cache_key)
                pipe.execute()
            
            logger.debug("Cache invalidated", key_type=key_type, identifier=identifier)
            return True
            
        except Exception as e:
            logger.error("Cache invalidation error", key_type=key_type, identifier=identifier, error=str(e))
            log_exception("cache_service", e, {"operation": "invalidate", "key_type": key_type, "identifier": identifier})
            return False
    
    def invalidate_pattern(self, key_type: str, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            namespace_pattern = f"{settings.redis_namespace}:{key_type}:{pattern}*"
            keys = self.redis_client.keys(namespace_pattern)
            
            if keys:
                with self.redis_client.pipeline(transaction=False) as pipe:
                    for key in keys:
                        pipe.delete(key)
                        pipe.srem(f"{settings.redis_namespace}:keys:{key_type}", key)
                    pipe.execute()
            
            logger.debug("Pattern cache invalidation", key_type=key_type, pattern=pattern, count=len(keys))
            return len(keys)
            
        except Exception as e:
            logger.error("Pattern cache invalidation error", key_type=key_type, pattern=pattern, error=str(e))
            log_exception("cache_service", e, {"operation": "invalidate_pattern", "key_type": key_type, "pattern": pattern})
            return 0
    
    def warm_cache(self, key_type: str, data_func: Callable[[str], Dict[str, Any]], identifiers: List[str], **kwargs: Any) -> int:
        """Warm cache with data from function"""
        try:
            warmed_count = 0
            for identifier in identifiers:
                try:
                    data = data_func(identifier)
                    if data and self.set(key_type, identifier, data, **kwargs):
                        warmed_count += 1
                except Exception as e:
                    logger.warning("Cache warming failed for identifier", 
                                 identifier=identifier, error=str(e))
            
            logger.info("Cache warming completed", key_type=key_type, 
                       requested=len(identifiers), warmed=warmed_count)
            return warmed_count
            
        except Exception as e:
            logger.error("Cache warming error", key_type=key_type, error=str(e))
            log_exception("cache_service", e, {"operation": "warm_cache", "key_type": key_type})
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests
            }
        except Exception as e:
            logger.error("Cache stats error", error=str(e))
            return {"error": str(e)}
    
    def cleanup_expired(self, key_type: str) -> int:
        """Clean up expired cache entries"""
        try:
            pattern = f"{settings.redis_namespace}:{key_type}:*"
            keys = self.redis_client.keys(pattern)
            cleaned_count = 0
            
            if keys:
                with self.redis_client.pipeline(transaction=False) as pipe:
                    for key in keys:
                        pipe.ttl(key)
                    ttls = pipe.execute()
                
                expired_keys = [key for key, ttl in zip(keys, ttls) if ttl == -1]
                
                if expired_keys:
                    with self.redis_client.pipeline(transaction=False) as pipe:
                        for key in expired_keys:
                            pipe.delete(key)
                            pipe.srem(f"{settings.redis_namespace}:keys:{key_type}", key)
                        pipe.execute()
                    cleaned_count = len(expired_keys)
            
            logger.debug("Cache cleanup completed", key_type=key_type, cleaned=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            logger.error("Cache cleanup error", key_type=key_type, error=str(e))
            log_exception("cache_service", e, {"operation": "cleanup_expired", "key_type": key_type})
            return 0


# Global cache service instance
cache_service = MultiLevelCacheService()

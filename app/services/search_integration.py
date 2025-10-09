"""
Search Integration Service

This service handles the capture, storage, and retrieval of user search queries
(prompts) used for generating recommendations. It provides comprehensive search
analytics and debugging capabilities.
"""
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from app.core.logging import get_logger, log_api_call, log_api_response, log_exception
from app.core.config import settings
from app.core.validators import validate_search_query, validate_user_id
from app.core.exceptions import ValidationError as CustomValidationError
import redis

logger = get_logger("search_integration")


@dataclass
class SearchQuery:
    """Data class representing a search query"""
    query_id: str
    user_id: str
    prompt: str
    timestamp: float
    model_name: str
    category: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchQuery':
        """Create from dictionary"""
        return cls(**data)


class SearchIntegrationService:
    """
    Service for managing search query integration and analytics.
    
    This service provides comprehensive search query management including:
    - Capturing user search queries during recommendation generation
    - Storing queries in Redis with proper metadata
    - Retrieving and filtering search queries
    - Providing analytics and debugging capabilities
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize the search integration service"""
        self.redis_client = redis_client or self._create_redis_client()
        self.search_ttl = 86400 * 7  # 7 days
        self.analytics_ttl = 86400 * 30  # 30 days
        
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client with proper configuration"""
        try:
            client = redis.Redis(
                host=settings.redis_host,
                port=getattr(settings, "redis_port", 6379),
                db=1,  # Use DB 1 for search queries
                password=getattr(settings, "redis_password", None),
                socket_connect_timeout=3,
                socket_timeout=5,
                health_check_interval=30,
                decode_responses=True
            )
            # Test connection
            client.ping()
            logger.info("Search integration Redis connection established",
                       redis_host=settings.redis_host)
            return client
        except Exception as e:
            logger.error("Failed to connect to Redis for search integration",
                        redis_host=settings.redis_host,
                        error=str(e))
            raise
    
    def capture_search_query(
        self,
        user_id: str,
        prompt: str,
        model_name: str,
        category: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[float] = None
    ) -> str:
        """
        Capture a search query and store it in Redis.
        
        Args:
            user_id: User identifier
            prompt: Search query/prompt text
            model_name: Name of the model used
            category: Optional category for the search
            filters: Optional filters applied
            start_time: Optional start time for response time calculation
            
        Returns:
            query_id: Unique identifier for the search query
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate inputs
            user_id = validate_user_id(user_id)
            prompt = validate_search_query(prompt)
            
            # Generate unique query ID
            query_id = f"search_{uuid.uuid4().hex[:12]}"
            
            # Calculate response time if start time provided
            response_time = None
            if start_time:
                response_time = time.time() - start_time
            
            # Create search query object
            search_query = SearchQuery(
                query_id=query_id,
                user_id=user_id,
                prompt=prompt,
                timestamp=time.time(),
                model_name=model_name,
                category=category,
                filters=filters,
                response_time=response_time,
                success=True
            )
            
            # Store in Redis
            self._store_search_query(search_query)
            
            logger.info("Search query captured successfully",
                       query_id=query_id,
                       user_id=user_id,
                       prompt_length=len(prompt),
                       model_name=model_name)
            
            return query_id
            
        except CustomValidationError:
            raise
        except Exception as e:
            logger.error("Error capturing search query",
                        user_id=user_id,
                        error=str(e))
            log_exception("search_integration", e, {
                "user_id": user_id,
                "operation": "capture_query"
            })
            raise
    
    def mark_query_failed(
        self,
        query_id: str,
        error_message: str
    ) -> bool:
        """
        Mark a search query as failed.
        
        Args:
            query_id: Query identifier
            error_message: Error message
            
        Returns:
            bool: True if successful
        """
        try:
            # Get existing query
            query_data = self.redis_client.get(f"search_query:{query_id}")
            if not query_data:
                logger.warning("Query not found for failure marking",
                              query_id=query_id)
                return False
            
            # Parse and update
            query_dict = json.loads(query_data)
            query_dict["success"] = False
            query_dict["error_message"] = error_message
            
            # Store updated query
            self.redis_client.setex(
                f"search_query:{query_id}",
                self.search_ttl,
                json.dumps(query_dict, default=str)
            )
            
            logger.info("Search query marked as failed",
                       query_id=query_id,
                       error_message=error_message)
            
            return True
            
        except Exception as e:
            logger.error("Error marking query as failed",
                        query_id=query_id,
                        error=str(e))
            return False
    
    def get_search_queries(
        self,
        user_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        category: Optional[str] = None,
        success_only: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve search queries with optional filtering.
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of queries to return
            offset: Number of queries to skip
            category: Optional category filter
            success_only: Only return successful queries
            
        Returns:
            Dictionary containing queries and metadata
        """
        try:
            queries = []
            total_count = 0
            
            # Scan for search query keys
            pattern = "search_query:*"
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    query_data = self.redis_client.get(key)
                    if not query_data:
                        continue
                    
                    query_dict = json.loads(query_data)
                    
                    # Apply filters
                    if user_id and query_dict.get("user_id") != user_id:
                        continue
                    
                    if category and query_dict.get("category") != category:
                        continue
                    
                    if success_only and not query_dict.get("success", True):
                        continue
                    
                    total_count += 1
                    
                    # Apply pagination
                    if len(queries) >= offset + limit:
                        continue
                    
                    if len(queries) >= offset:
                        # Convert timestamp to readable format
                        query_dict["timestamp_readable"] = datetime.fromtimestamp(
                            query_dict["timestamp"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        queries.append(query_dict)
                        
                except Exception as e:
                    logger.warning("Error parsing search query data",
                                  key=key,
                                  error=str(e))
                    continue
            
            # Sort by timestamp (newest first)
            queries.sort(key=lambda x: x["timestamp"], reverse=True)
            
            logger.info("Search queries retrieved successfully",
                       total_queries=len(queries),
                       total_count=total_count,
                       user_id=user_id,
                       category=category)
            
            return {
                "queries": queries,
                "total_count": total_count,
                "returned_count": len(queries),
                "filters": {
                    "user_id": user_id,
                    "category": category,
                    "success_only": success_only
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                }
            }
            
        except Exception as e:
            logger.error("Error retrieving search queries",
                        error=str(e))
            log_exception("search_integration", e, {
                "operation": "get_queries",
                "user_id": user_id
            })
            raise
    
    def get_search_analytics(
        self,
        user_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get search analytics and statistics.
        
        Args:
            user_id: Optional user ID filter
            days: Number of days to analyze
            
        Returns:
            Dictionary containing analytics data
        """
        try:
            cutoff_time = time.time() - (days * 86400)
            
            # Get all queries within time range
            all_queries = self.get_search_queries(
                user_id=user_id,
                limit=1000,  # Large limit for analytics
                success_only=False
            )["queries"]
            
            # Filter by time range
            recent_queries = [
                q for q in all_queries
                if q["timestamp"] >= cutoff_time
            ]
            
            # Calculate analytics
            total_queries = len(recent_queries)
            successful_queries = len([q for q in recent_queries if q.get("success", True)])
            failed_queries = total_queries - successful_queries
            
            # Response time statistics
            response_times = [
                q["response_time"] for q in recent_queries
                if q.get("response_time") is not None
            ]
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Category distribution
            categories = {}
            for query in recent_queries:
                cat = query.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            # Model distribution
            models = {}
            for query in recent_queries:
                model = query.get("model_name", "unknown")
                models[model] = models.get(model, 0) + 1
            
            # Most common search terms
            search_terms = {}
            for query in recent_queries:
                prompt = query.get("prompt", "").lower()
                # Simple word extraction (could be enhanced)
                words = prompt.split()[:5]  # First 5 words
                for word in words:
                    if len(word) > 3:  # Only words longer than 3 chars
                        search_terms[word] = search_terms.get(word, 0) + 1
            
            # Top search terms
            top_terms = sorted(
                search_terms.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            analytics = {
                "summary": {
                    "total_queries": total_queries,
                    "successful_queries": successful_queries,
                    "failed_queries": failed_queries,
                    "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                    "avg_response_time": round(avg_response_time, 3)
                },
                "categories": categories,
                "models": models,
                "top_search_terms": top_terms,
                "time_range_days": days,
                "user_id": user_id
            }
            
            logger.info("Search analytics generated successfully",
                       total_queries=total_queries,
                       success_rate=analytics["summary"]["success_rate"],
                       user_id=user_id)
            
            return analytics
            
        except Exception as e:
            logger.error("Error generating search analytics",
                        error=str(e))
            log_exception("search_integration", e, {
                "operation": "get_analytics",
                "user_id": user_id
            })
            raise
    
    def cleanup_old_queries(self, days: int = 30) -> int:
        """
        Clean up old search queries.
        
        Args:
            days: Number of days to keep queries
            
        Returns:
            Number of queries cleaned up
        """
        try:
            cutoff_time = time.time() - (days * 86400)
            cleaned_count = 0
            
            # Scan for old queries
            pattern = "search_query:*"
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    query_data = self.redis_client.get(key)
                    if not query_data:
                        continue
                    
                    query_dict = json.loads(query_data)
                    if query_dict.get("timestamp", 0) < cutoff_time:
                        self.redis_client.delete(key)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning("Error cleaning up query",
                                  key=key,
                                  error=str(e))
                    continue
            
            logger.info("Search query cleanup completed",
                       cleaned_count=cleaned_count,
                       days=days)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Error during search query cleanup",
                        error=str(e))
            return 0
    
    def _store_search_query(self, search_query: SearchQuery) -> None:
        """Store search query in Redis"""
        try:
            key = f"search_query:{search_query.query_id}"
            data = json.dumps(search_query.to_dict(), default=str)
            
            self.redis_client.setex(key, self.search_ttl, data)
            
            # Also store in analytics collection
            analytics_key = f"search_analytics:{search_query.user_id}:{int(search_query.timestamp)}"
            self.redis_client.setex(analytics_key, self.analytics_ttl, data)
            
        except Exception as e:
            logger.error("Error storing search query",
                        query_id=search_query.query_id,
                        error=str(e))
            raise


# Global instance
search_service = SearchIntegrationService()

"""
Data Retention and Cleanup Service

This module provides automated data retention policies and cleanup jobs
for Redis data to ensure compliance and optimal performance.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
from app.core.config import settings
from app.core.logging import get_logger, log_exception
from app.services.cache_service import cache_service

logger = get_logger("data_retention")


class RetentionPolicy(str, Enum):
    """Data retention policy types"""
    IMMEDIATE = "immediate"  # Delete immediately
    SHORT_TERM = "short_term"  # 1 hour
    MEDIUM_TERM = "medium_term"  # 24 hours
    LONG_TERM = "long_term"  # 7 days
    EXTENDED = "extended"  # 30 days
    PERMANENT = "permanent"  # Never delete


@dataclass
class RetentionRule:
    """Data retention rule definition"""
    key_pattern: str
    policy: RetentionPolicy
    ttl_seconds: int
    description: str
    enabled: bool = True
    last_cleanup: Optional[datetime] = None
    cleanup_count: int = 0


class DataRetentionService:
    """Automated data retention and cleanup service"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._create_redis_client()
        self.retention_rules: Dict[str, RetentionRule] = {}
        self.cleanup_stats: Dict[str, Any] = {
            "total_cleanups": 0,
            "total_keys_deleted": 0,
            "last_cleanup": None,
            "cleanup_duration": 0
        }
        self._setup_default_rules()
    
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client for cleanup operations"""
        return redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_connect_timeout=5,
            socket_timeout=10,
            decode_responses=True
        )
    
    def _setup_default_rules(self):
        """Setup default retention rules"""
        now = datetime.now()
        
        # Session data - short term
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:session:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=3600,  # 1 hour
            description="User session data"
        )
        
        # Temporary cache - medium term
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:temp:*",
            policy=RetentionPolicy.MEDIUM_TERM,
            ttl_seconds=86400,  # 24 hours
            description="Temporary cache data"
        )
        
        # User recommendations - long term
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:recommendations:*",
            policy=RetentionPolicy.LONG_TERM,
            ttl_seconds=604800,  # 7 days
            description="User recommendation data"
        )
        
        # User profiles - extended
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:user_profile:*",
            policy=RetentionPolicy.EXTENDED,
            ttl_seconds=2592000,  # 30 days
            description="User profile data"
        )
        
        # Analytics data - extended
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:analytics:*",
            policy=RetentionPolicy.EXTENDED,
            ttl_seconds=2592000,  # 30 days
            description="Analytics and metrics data"
        )
        
        # Logs - medium term
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:logs:*",
            policy=RetentionPolicy.MEDIUM_TERM,
            ttl_seconds=86400,  # 24 hours
            description="Application logs"
        )
        
        # Test data - immediate
        self.add_retention_rule(
            key_pattern=f"{settings.redis_namespace}:test:*",
            policy=RetentionPolicy.IMMEDIATE,
            ttl_seconds=0,
            description="Test data"
        )
    
    def add_retention_rule(
        self,
        key_pattern: str,
        policy: RetentionPolicy,
        ttl_seconds: int,
        description: str,
        enabled: bool = True
    ) -> str:
        """Add a new retention rule"""
        rule_id = f"{key_pattern}_{policy.value}"
        rule = RetentionRule(
            key_pattern=key_pattern,
            policy=policy,
            ttl_seconds=ttl_seconds,
            description=description,
            enabled=enabled
        )
        self.retention_rules[rule_id] = rule
        logger.info("Retention rule added", rule_id=rule_id, pattern=key_pattern, policy=policy.value)
        return rule_id
    
    def remove_retention_rule(self, rule_id: str) -> bool:
        """Remove a retention rule"""
        if rule_id in self.retention_rules:
            del self.retention_rules[rule_id]
            logger.info("Retention rule removed", rule_id=rule_id)
            return True
        return False
    
    def update_retention_rule(
        self,
        rule_id: str,
        policy: Optional[RetentionPolicy] = None,
        ttl_seconds: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """Update an existing retention rule"""
        if rule_id not in self.retention_rules:
            return False
        
        rule = self.retention_rules[rule_id]
        if policy is not None:
            rule.policy = policy
        if ttl_seconds is not None:
            rule.ttl_seconds = ttl_seconds
        if enabled is not None:
            rule.enabled = enabled
        
        logger.info("Retention rule updated", rule_id=rule_id)
        return True
    
    async def cleanup_expired_data(self) -> Dict[str, Any]:
        """Clean up expired data based on retention rules"""
        start_time = time.time()
        cleanup_results = {
            "rules_processed": 0,
            "keys_deleted": 0,
            "errors": 0,
            "duration": 0
        }
        
        try:
            logger.info("Starting data cleanup", rules_count=len(self.retention_rules))
            
            for rule_id, rule in self.retention_rules.items():
                if not rule.enabled:
                    continue
                
                try:
                    deleted_count = await self._cleanup_rule(rule)
                    cleanup_results["rules_processed"] += 1
                    cleanup_results["keys_deleted"] += deleted_count
                    
                    # Update rule stats
                    rule.last_cleanup = datetime.now()
                    rule.cleanup_count += 1
                    
                except Exception as e:
                    cleanup_results["errors"] += 1
                    logger.error("Rule cleanup failed", rule_id=rule_id, error=str(e))
                    log_exception("data_retention", e, {"rule_id": rule_id, "operation": "cleanup_rule"})
            
            cleanup_results["duration"] = time.time() - start_time
            
            # Update global stats
            self.cleanup_stats["total_cleanups"] += 1
            self.cleanup_stats["total_keys_deleted"] += cleanup_results["keys_deleted"]
            self.cleanup_stats["last_cleanup"] = datetime.now()
            self.cleanup_stats["cleanup_duration"] = cleanup_results["duration"]
            
            logger.info("Data cleanup completed", **cleanup_results)
            return cleanup_results
            
        except Exception as e:
            logger.error("Data cleanup failed", error=str(e))
            log_exception("data_retention", e, {"operation": "cleanup_expired_data"})
            cleanup_results["errors"] += 1
            cleanup_results["duration"] = time.time() - start_time
            return cleanup_results
    
    async def _cleanup_rule(self, rule: RetentionRule) -> int:
        """Clean up data for a specific rule"""
        deleted_count = 0
        
        try:
            # Get all keys matching the pattern
            keys = self.redis_client.keys(rule.key_pattern)
            
            if not keys:
                return 0
            
            # Process keys based on policy
            if rule.policy == RetentionPolicy.IMMEDIATE:
                # Delete immediately
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            else:
                # Check TTL and delete expired keys
                for key in keys:
                    ttl = self.redis_client.ttl(key)
                    if ttl == -1:  # No TTL set
                        # Set TTL based on rule
                        self.redis_client.expire(key, rule.ttl_seconds)
                    elif ttl == -2:  # Key doesn't exist
                        continue
                    elif ttl <= 0:  # Expired
                        self.redis_client.delete(key)
                        deleted_count += 1
            
            logger.debug("Rule cleanup completed", 
                        pattern=rule.key_pattern, 
                        keys_found=len(keys), 
                        keys_deleted=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Rule cleanup error", pattern=rule.key_pattern, error=str(e))
            raise
    
    async def cleanup_by_age(self, max_age_hours: int) -> Dict[str, Any]:
        """Clean up data older than specified age"""
        start_time = time.time()
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        errors = []
        
        try:
            # Get all keys
            all_keys = self.redis_client.keys(f"{settings.redis_namespace}:*")
            
            for key in all_keys:
                try:
                    # Get key creation time (approximate)
                    key_info = self.redis_client.object("idletime", key)
                    if key_info and key_info > max_age_hours * 3600:
                        self.redis_client.delete(key)
                        deleted_count += 1
                except Exception as e:
                    error_msg = f"Key cleanup error for {key}: {str(e)}"
                    logger.warning("Key cleanup error", key=key, error=str(e))
                    errors.append(error_msg)
                    continue
            
            duration = time.time() - start_time
            logger.info("Age-based cleanup completed", 
                       max_age_hours=max_age_hours, 
                       keys_deleted=deleted_count, 
                       duration=duration)
            
            result = {
                "keys_deleted": deleted_count,
                "max_age_hours": max_age_hours,
                "duration": duration
            }
            
            if errors:
                result["error"] = "; ".join(errors)
            
            return result
            
        except Exception as e:
            logger.error("Age-based cleanup failed", error=str(e))
            log_exception("data_retention", e, {"operation": "cleanup_by_age"})
            return {"keys_deleted": 0, "error": str(e)}
    
    async def cleanup_by_size(self, max_memory_mb: int) -> Dict[str, Any]:
        """Clean up data to stay within memory limits"""
        start_time = time.time()
        
        try:
            # Get Redis memory info
            memory_info = self.redis_client.memory_usage()
            current_memory_mb = memory_info / (1024 * 1024)
            
            if current_memory_mb <= max_memory_mb:
                return {
                    "memory_freed_mb": 0,
                    "current_memory_mb": current_memory_mb,
                    "target_memory_mb": max_memory_mb
                }
            
            # Calculate how much to free
            memory_to_free_mb = current_memory_mb - max_memory_mb
            
            # Get all keys with their memory usage
            all_keys = self.redis_client.keys(f"{settings.redis_namespace}:*")
            key_sizes = []
            
            for key in all_keys:
                try:
                    size = self.redis_client.memory_usage(key)
                    key_sizes.append((key, size))
                except Exception:
                    continue
            
            # Sort by size (largest first)
            key_sizes.sort(key=lambda x: x[1], reverse=True)
            
            # Delete largest keys until we free enough memory
            freed_memory = 0
            deleted_count = 0
            
            for key, size in key_sizes:
                if freed_memory >= memory_to_free_mb * 1024 * 1024:
                    break
                
                self.redis_client.delete(key)
                freed_memory += size
                deleted_count += 1
            
            duration = time.time() - start_time
            freed_memory_mb = freed_memory / (1024 * 1024)
            
            logger.info("Size-based cleanup completed", 
                       memory_freed_mb=freed_memory_mb, 
                       keys_deleted=deleted_count, 
                       duration=duration)
            
            return {
                "memory_freed_mb": freed_memory_mb,
                "keys_deleted": deleted_count,
                "current_memory_mb": current_memory_mb,
                "target_memory_mb": max_memory_mb,
                "duration": duration
            }
            
        except Exception as e:
            logger.error("Size-based cleanup failed", error=str(e))
            log_exception("data_retention", e, {"operation": "cleanup_by_size"})
            return {"memory_freed_mb": 0, "error": str(e)}
    
    def get_retention_stats(self) -> Dict[str, Any]:
        """Get retention service statistics"""
        return {
            "rules_count": len(self.retention_rules),
            "active_rules": len([r for r in self.retention_rules.values() if r.enabled]),
            "cleanup_stats": self.cleanup_stats,
            "rules": {
                rule_id: {
                    "pattern": rule.key_pattern,
                    "policy": rule.policy.value,
                    "ttl_seconds": rule.ttl_seconds,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "last_cleanup": rule.last_cleanup.isoformat() if rule.last_cleanup else None,
                    "cleanup_count": rule.cleanup_count
                }
                for rule_id, rule in self.retention_rules.items()
            }
        }
    
    async def schedule_cleanup(self, interval_hours: int = 1):
        """Schedule periodic cleanup"""
        logger.info("Starting scheduled cleanup", interval_hours=interval_hours)
        
        while True:
            try:
                await self.cleanup_expired_data()
                await asyncio.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error("Scheduled cleanup error", error=str(e))
                log_exception("data_retention", e, {"operation": "schedule_cleanup"})
                await asyncio.sleep(300)  # Wait 5 minutes before retrying


# Global data retention service instance
data_retention_service = DataRetentionService()
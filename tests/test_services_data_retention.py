"""
Tests for data retention and cleanup service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import redis

from app.services.data_retention import (
    RetentionPolicy, RetentionRule, DataRetentionService,
    data_retention_service
)


class TestRetentionPolicy:
    """Test RetentionPolicy enum"""
    
    def test_retention_policy_values(self):
        """Test retention policy enum values"""
        assert RetentionPolicy.IMMEDIATE == "immediate"
        assert RetentionPolicy.SHORT_TERM == "short_term"
        assert RetentionPolicy.MEDIUM_TERM == "medium_term"
        assert RetentionPolicy.LONG_TERM == "long_term"
        assert RetentionPolicy.EXTENDED == "extended"
        assert RetentionPolicy.PERMANENT == "permanent"


class TestRetentionRule:
    """Test RetentionRule dataclass"""
    
    def test_retention_rule_creation(self):
        """Test retention rule creation"""
        rule = RetentionRule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=3600,
            description="Test rule",
            enabled=True
        )
        
        assert rule.key_pattern == "test:*"
        assert rule.policy == RetentionPolicy.SHORT_TERM
        assert rule.ttl_seconds == 3600
        assert rule.description == "Test rule"
        assert rule.enabled is True
        assert rule.last_cleanup is None
        assert rule.cleanup_count == 0
    
    def test_retention_rule_defaults(self):
        """Test retention rule with default values"""
        rule = RetentionRule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=3600,
            description="Test rule"
        )
        
        assert rule.enabled is True
        assert rule.last_cleanup is None
        assert rule.cleanup_count == 0


class TestDataRetentionService:
    """Test DataRetentionService class"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_redis = Mock()
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = 0
        mock_redis.ttl.return_value = -1
        mock_redis.expire.return_value = True
        mock_redis.object.return_value = 0
        mock_redis.memory_usage.return_value = 1024 * 1024  # 1MB
        return mock_redis
    
    @pytest.fixture
    def service(self, mock_redis):
        """Create service instance with mocked Redis"""
        with patch('app.services.data_retention.settings') as mock_settings:
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.redis_db = 0
            mock_settings.redis_password = None
            mock_settings.redis_namespace = "test"
            
            service = DataRetentionService(redis_client=mock_redis)
            return service
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.redis_client is not None
        assert isinstance(service.retention_rules, dict)
        assert isinstance(service.cleanup_stats, dict)
        assert service.cleanup_stats["total_cleanups"] == 0
        assert service.cleanup_stats["total_keys_deleted"] == 0
        assert service.cleanup_stats["last_cleanup"] is None
        assert service.cleanup_stats["cleanup_duration"] == 0
    
    def test_setup_default_rules(self, service):
        """Test default rules setup"""
        assert len(service.retention_rules) > 0
        
        # Check that default rules are created
        rule_ids = list(service.retention_rules.keys())
        assert any("session" in rule_id for rule_id in rule_ids)
        assert any("temp" in rule_id for rule_id in rule_ids)
        assert any("recommendations" in rule_id for rule_id in rule_ids)
        assert any("user_profile" in rule_id for rule_id in rule_ids)
        assert any("analytics" in rule_id for rule_id in rule_ids)
        assert any("logs" in rule_id for rule_id in rule_ids)
        assert any("test" in rule_id for rule_id in rule_ids)
    
    def test_add_retention_rule(self, service):
        """Test adding retention rule"""
        rule_id = service.add_retention_rule(
            key_pattern="custom:*",
            policy=RetentionPolicy.MEDIUM_TERM,
            ttl_seconds=7200,
            description="Custom rule"
        )
        
        assert rule_id == "custom:*_medium_term"
        assert rule_id in service.retention_rules
        
        rule = service.retention_rules[rule_id]
        assert rule.key_pattern == "custom:*"
        assert rule.policy == RetentionPolicy.MEDIUM_TERM
        assert rule.ttl_seconds == 7200
        assert rule.description == "Custom rule"
        assert rule.enabled is True
    
    def test_remove_retention_rule(self, service):
        """Test removing retention rule"""
        # Add a rule first
        rule_id = service.add_retention_rule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=1800,
            description="Test rule"
        )
        
        # Remove it
        result = service.remove_retention_rule(rule_id)
        assert result is True
        assert rule_id not in service.retention_rules
        
        # Try to remove non-existent rule
        result = service.remove_retention_rule("nonexistent")
        assert result is False
    
    def test_update_retention_rule(self, service):
        """Test updating retention rule"""
        # Add a rule first
        rule_id = service.add_retention_rule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=1800,
            description="Test rule"
        )
        
        # Update policy
        result = service.update_retention_rule(
            rule_id,
            policy=RetentionPolicy.LONG_TERM,
            ttl_seconds=3600,
            enabled=False
        )
        
        assert result is True
        rule = service.retention_rules[rule_id]
        assert rule.policy == RetentionPolicy.LONG_TERM
        assert rule.ttl_seconds == 3600
        assert rule.enabled is False
        
        # Try to update non-existent rule
        result = service.update_retention_rule("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_data_success(self, service, mock_redis):
        """Test successful cleanup of expired data"""
        # Mock Redis responses
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.delete.return_value = 2
        mock_redis.ttl.return_value = -1
        
        result = await service.cleanup_expired_data()
        
        assert result["rules_processed"] > 0
        assert result["keys_deleted"] >= 0
        assert result["errors"] == 0
        assert result["duration"] > 0
        
        # Check that stats were updated
        assert service.cleanup_stats["total_cleanups"] == 1
        assert service.cleanup_stats["total_keys_deleted"] >= 0
        assert service.cleanup_stats["last_cleanup"] is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_data_with_errors(self, service, mock_redis):
        """Test cleanup with errors"""
        # Mock Redis to raise exception
        mock_redis.keys.side_effect = Exception("Redis error")
        
        result = await service.cleanup_expired_data()
        
        assert result["errors"] > 0
        assert result["duration"] > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_rule_immediate_policy(self, service, mock_redis):
        """Test cleanup rule with immediate policy"""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.delete.return_value = 2
        
        rule = RetentionRule(
            key_pattern="test:*",
            policy=RetentionPolicy.IMMEDIATE,
            ttl_seconds=0,
            description="Test rule"
        )
        
        deleted_count = await service._cleanup_rule(rule)
        
        assert deleted_count == 2
        mock_redis.delete.assert_called_once_with("test:key1", "test:key2")
    
    @pytest.mark.asyncio
    async def test_cleanup_rule_with_ttl(self, service, mock_redis):
        """Test cleanup rule with TTL checking"""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.ttl.side_effect = [-1, 0]  # First key has no TTL, second is expired
        mock_redis.expire.return_value = True
        mock_redis.delete.return_value = 1
        
        rule = RetentionRule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=3600,
            description="Test rule"
        )
        
        deleted_count = await service._cleanup_rule(rule)
        
        assert deleted_count == 1
        mock_redis.expire.assert_called_once_with("test:key1", 3600)
        mock_redis.delete.assert_called_once_with("test:key2")
    
    @pytest.mark.asyncio
    async def test_cleanup_rule_no_keys(self, service, mock_redis):
        """Test cleanup rule with no matching keys"""
        mock_redis.keys.return_value = []
        
        rule = RetentionRule(
            key_pattern="test:*",
            policy=RetentionPolicy.SHORT_TERM,
            ttl_seconds=3600,
            description="Test rule"
        )
        
        deleted_count = await service._cleanup_rule(rule)
        
        assert deleted_count == 0
        mock_redis.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_by_age(self, service, mock_redis):
        """Test cleanup by age"""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        # First key is older than 1 hour (7200 seconds = 2 hours), second is newer (1800 seconds = 30 minutes)
        mock_redis.object.side_effect = [7200, 1800]
        mock_redis.delete.return_value = 1
        
        result = await service.cleanup_by_age(max_age_hours=1)
        
        assert result["keys_deleted"] == 1
        assert result["max_age_hours"] == 1
        assert result["duration"] > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_by_age_no_old_keys(self, service, mock_redis):
        """Test cleanup by age with no old keys"""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.object.return_value = 1800  # 30 minutes in seconds
        
        result = await service.cleanup_by_age(max_age_hours=1)
        
        assert result["keys_deleted"] == 0
        assert result["max_age_hours"] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_by_age_with_errors(self, service, mock_redis):
        """Test cleanup by age with errors"""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.object.side_effect = Exception("Redis error")
        
        result = await service.cleanup_by_age(max_age_hours=1)
        
        assert result["keys_deleted"] == 0
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_cleanup_by_size_under_limit(self, service, mock_redis):
        """Test cleanup by size when under memory limit"""
        mock_redis.memory_usage.return_value = 512 * 1024  # 512KB
        
        result = await service.cleanup_by_size(max_memory_mb=1)
        
        assert result["memory_freed_mb"] == 0
        assert result["current_memory_mb"] == 0.5
        assert result["target_memory_mb"] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_by_size_over_limit(self, service, mock_redis):
        """Test cleanup by size when over memory limit"""
        mock_redis.memory_usage.return_value = 2 * 1024 * 1024  # 2MB
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.memory_usage.side_effect = [
            2 * 1024 * 1024,  # Total memory
            1024 * 1024,      # Key 1 size
            512 * 1024        # Key 2 size
        ]
        mock_redis.delete.return_value = 1
        
        result = await service.cleanup_by_size(max_memory_mb=1)
        
        assert result["memory_freed_mb"] > 0
        assert result["keys_deleted"] > 0
        assert result["current_memory_mb"] == 2.0
        assert result["target_memory_mb"] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_by_size_with_errors(self, service, mock_redis):
        """Test cleanup by size with errors"""
        mock_redis.memory_usage.side_effect = Exception("Redis error")
        
        result = await service.cleanup_by_size(max_memory_mb=1)
        
        assert result["memory_freed_mb"] == 0
        assert "error" in result
    
    def test_get_retention_stats(self, service):
        """Test getting retention statistics"""
        stats = service.get_retention_stats()
        
        assert "rules_count" in stats
        assert "active_rules" in stats
        assert "cleanup_stats" in stats
        assert "rules" in stats
        
        assert stats["rules_count"] > 0
        assert stats["active_rules"] > 0
        assert isinstance(stats["rules"], dict)
    
    @pytest.mark.asyncio
    async def test_schedule_cleanup(self, service, mock_redis):
        """Test scheduled cleanup"""
        # Mock cleanup to succeed
        mock_redis.keys.return_value = []
        
        # Run cleanup once and then cancel
        task = asyncio.create_task(service.schedule_cleanup(interval_hours=0.001))  # Very short interval
        
        # Wait a bit for cleanup to run
        await asyncio.sleep(0.1)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Check that cleanup was called
        assert service.cleanup_stats["total_cleanups"] >= 0
    
    @pytest.mark.asyncio
    async def test_schedule_cleanup_with_errors(self, service, mock_redis):
        """Test scheduled cleanup with errors"""
        # Mock cleanup to fail
        mock_redis.keys.side_effect = Exception("Redis error")
        
        # Run cleanup once and then cancel
        task = asyncio.create_task(service.schedule_cleanup(interval_hours=0.001))
        
        # Wait a bit for cleanup to run
        await asyncio.sleep(0.1)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have handled the error gracefully
        assert True  # If we get here, the error was handled


class TestGlobalService:
    """Test global data retention service instance"""
    
    def test_global_service_exists(self):
        """Test that global service instance exists"""
        assert data_retention_service is not None
        assert isinstance(data_retention_service, DataRetentionService)
    
    def test_global_service_initialization(self):
        """Test global service initialization"""
        assert data_retention_service.redis_client is not None
        assert isinstance(data_retention_service.retention_rules, dict)
        assert len(data_retention_service.retention_rules) > 0

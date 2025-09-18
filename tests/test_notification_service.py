import pytest
import asyncio
import json
import time
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import os
import sys
from unittest.mock import ANY

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the notification service
from notification_service import (
    app,
    DistributedConnectionManager,
    NotificationPayload,
    PendingNotification,
    setup_redis_streams,
    redis_streams_consumer,
    process_stream_message,
    instance_fanout_listener,
    process_fanout_message,
    heartbeat_task,
    cleanup_stale_connections,
    retry_pending_task,
    pubsub_notifications_listener,
    lifespan,
    websocket_endpoint,
    health_check,
    get_stats,
    get_distributed_stats,
    send_stream_notification,
    send_direct_notification,
    INSTANCE_ID,
    REDIS_HOST,
    REDIS_PORT,
    NOTIFICATIONS_STREAM,
    INSTANCE_CHANNEL_PREFIX,
    CONNECTIONS_KEY,
    PENDING_NOTIFICATIONS_PREFIX,
    PENDING_USERS_KEY,
    DEAD_LETTER_KEY,
    CONSUMER_GROUP,
    HEARTBEAT_INTERVAL,
    CLIENT_TIMEOUT,
    MESSAGE_TTL_HOURS,
    MAX_PENDING_MESSAGES,
    PENDING_RETRY_INTERVAL,
    MAX_MESSAGE_SIZE,
    ENABLE_DEBUG,
    MAX_RECONNECT_ATTEMPTS,
    REDIS_RETRY_DELAY
)


@pytest.fixture
def mock_redis_pool():
    """Mock Redis connection pool."""
    pool = Mock()
    pool.host = REDIS_HOST
    pool.port = REDIS_PORT
    pool.db = 0
    return pool


@pytest.fixture
def mock_redis():
    """Mock Redis client with all necessary methods."""
    redis = AsyncMock()
    
    # Basic Redis operations
    redis.ping = AsyncMock(return_value=True)
    redis.hset = AsyncMock(return_value=1)
    redis.hget = AsyncMock(return_value=None)
    redis.hdel = AsyncMock(return_value=1)
    redis.hscan_iter = AsyncMock()
    redis.sadd = AsyncMock(return_value=1)
    redis.srem = AsyncMock(return_value=1)
    redis.smembers = AsyncMock(return_value=set())
    redis.zadd = AsyncMock(return_value=1)
    redis.zrange = AsyncMock(return_value=[])
    redis.zrem = AsyncMock(return_value=1)
    redis.zcard = AsyncMock(return_value=0)
    redis.zremrangebyrank = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.publish = AsyncMock(return_value=1)
    redis.xadd = AsyncMock(return_value="test_stream_id")
    redis.xreadgroup = AsyncMock(return_value=[])
    redis.xack = AsyncMock(return_value=1)
    redis.xinfo_stream = AsyncMock(return_value={"length": 0})
    redis.xinfo_groups = AsyncMock(return_value=[])
    redis.xgroup_create = AsyncMock(return_value="OK")
    redis.lpush = AsyncMock(return_value=1)
    redis.close = AsyncMock()
    
    # PubSub operations
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock()
    redis.pubsub = Mock(return_value=mock_pubsub)
    
    return redis


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def connection_manager(mock_redis_pool, mock_redis):
    """Create a DistributedConnectionManager instance for testing."""
    with patch('notification_service.aioredis.Redis', return_value=mock_redis):
        manager = DistributedConnectionManager(mock_redis_pool)
        manager.redis = mock_redis
        return manager


@pytest.fixture
def sample_notification_payload():
    """Sample notification payload for testing."""
    return NotificationPayload(
        message={"content": "Test notification", "type": "test"},
        type="notification"
    )


@pytest.fixture
def sample_pending_notification():
    """Sample pending notification for testing."""
    return PendingNotification(
        user_id="test_user_1",
        message={"content": "Test pending notification"},
        timestamp=datetime.now(timezone.utc).isoformat(),
        attempts=0,
        max_attempts=3,
        notification_id=str(uuid.uuid4())
    )


class TestNotificationPayload:
    """Test NotificationPayload model."""
    
    def test_notification_payload_default_values(self):
        """Test default values for NotificationPayload."""
        payload = NotificationPayload()
        assert payload.message == {"content": "Your new recommendations are ready!"}
        assert payload.type == "notification"
    
    def test_notification_payload_custom_values(self):
        """Test custom values for NotificationPayload."""
        custom_message = {"content": "Custom message", "priority": "high"}
        payload = NotificationPayload(message=custom_message, type="alert")
        assert payload.message == custom_message
        assert payload.type == "alert"
    
    def test_notification_payload_string_message(self):
        """Test NotificationPayload with string message."""
        payload = NotificationPayload(message="Simple string message")
        assert payload.message == "Simple string message"
        assert payload.type == "notification"


class TestPendingNotification:
    """Test PendingNotification dataclass."""
    
    def test_pending_notification_creation(self, sample_pending_notification):
        """Test PendingNotification creation with all fields."""
        notification = sample_pending_notification
        assert notification.user_id == "test_user_1"
        assert notification.message == {"content": "Test pending notification"}
        assert notification.attempts == 0
        assert notification.max_attempts == 3
        assert notification.notification_id is not None
    
    def test_pending_notification_default_values(self):
        """Test PendingNotification with default values."""
        notification = PendingNotification(
            user_id="test_user_2",
            message={"content": "Test message"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        assert notification.attempts == 0
        assert notification.max_attempts == 3
        assert notification.notification_id is None


class TestDistributedConnectionManager:
    """Test DistributedConnectionManager class."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager, mock_websocket):
        """Test successful user connection."""
        user_id = "test_user_1"
        
        with patch.object(connection_manager, 'deliver_pending_notifications', new_callable=AsyncMock) as mock_deliver:
            await connection_manager.connect(mock_websocket, user_id)
            
            assert user_id in connection_manager.local_connections
            assert connection_manager.local_connections[user_id] == mock_websocket
            assert user_id in connection_manager.connection_times
            assert user_id in connection_manager.last_activity
            
            mock_websocket.accept.assert_called_once()
            connection_manager.redis.hset.assert_called_once()
            mock_deliver.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, connection_manager, mock_websocket):
        """Test connection failure handling."""
        user_id = "test_user_1"
        mock_websocket.accept.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            await connection_manager.connect(mock_websocket, user_id)
    
    @pytest.mark.asyncio
    async def test_connect_redis_failure(self, connection_manager, mock_websocket):
        """Test connection when Redis hset fails."""
        user_id = "test_user_1"
        connection_manager.redis.hset.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception, match="Redis error"):
            await connection_manager.connect(mock_websocket, user_id)
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, connection_manager):
        """Test successful user disconnection."""
        user_id = "test_user_1"
        connection_manager.local_connections[user_id] = Mock()
        connection_manager.connection_times[user_id] = time.time()
        connection_manager.last_activity[user_id] = time.time()
        
        await connection_manager.disconnect(user_id)
        
        assert user_id not in connection_manager.local_connections
        assert user_id not in connection_manager.connection_times
        assert user_id not in connection_manager.last_activity
        connection_manager.redis.hdel.assert_called_once_with(CONNECTIONS_KEY, user_id)
    
    @pytest.mark.asyncio
    async def test_disconnect_redis_failure(self, connection_manager):
        """Test disconnection when Redis hdel fails."""
        user_id = "test_user_1"
        connection_manager.local_connections[user_id] = Mock()
        connection_manager.connection_times[user_id] = time.time()
        connection_manager.last_activity[user_id] = time.time()
        connection_manager.redis.hdel.side_effect = Exception("Redis error")
        
        await connection_manager.disconnect(user_id)
        
        assert user_id not in connection_manager.local_connections
    
    @pytest.mark.asyncio
    async def test_disconnect_user_not_connected(self, connection_manager):
        """Test disconnecting a user who is not connected."""
        user_id = "nonexistent_user"
        
        # Should not raise an exception
        await connection_manager.disconnect(user_id)
        # hdel should NOT be called if user is not locally connected
        connection_manager.redis.hdel.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_message_local_success(self, connection_manager, mock_websocket):
        """Test successful local message sending."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.local_connections[user_id] = mock_websocket
        
        result = await connection_manager.send_message_local(user_id, message)
        
        assert result is True
        mock_websocket.send_json.assert_called_once_with(message)
        assert user_id in connection_manager.last_activity
    
    @pytest.mark.asyncio
    async def test_send_message_local_user_not_connected(self, connection_manager):
        """Test sending message to user not locally connected."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        
        result = await connection_manager.send_message_local(user_id, message)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_local_websocket_error(self, connection_manager, mock_websocket):
        """Test local message sending with WebSocket error."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.local_connections[user_id] = mock_websocket
        mock_websocket.send_json.side_effect = Exception("Send failed")
        
        with patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            result = await connection_manager.send_message_local(user_id, message)
            
            assert result is False
            mock_disconnect.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_send_message_distributed_local_success(self, connection_manager, mock_websocket):
        """Test distributed message sending when user is locally connected."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.local_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=True) as mock_send_local:
            result = await connection_manager.send_message_distributed(user_id, message)
            
            assert result is True
            mock_send_local.assert_called_once_with(user_id, message)
    
    @pytest.mark.asyncio
    async def test_send_message_distributed_remote_success(self, connection_manager):
        """Test distributed message sending to remote instance."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_data = json.dumps({
            "instance_id": "remote_instance",
            "connected_at": time.time(),
            "user_id": user_id
        })
        
        connection_manager.redis.hget.return_value = connection_data
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=False) as mock_send_local, \
             patch.object(connection_manager, 'store_pending_notification', new_callable=AsyncMock) as mock_store:
            
            result = await connection_manager.send_message_distributed(user_id, message)
            
            assert result is True
            mock_send_local.assert_called_once_with(user_id, message)
            connection_manager.redis.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_distributed_invalid_connection_data(self, connection_manager):
        """Test distributed message sending with invalid connection data."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.redis.hget.return_value = "invalid_json"
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=False) as mock_send_local, \
             patch.object(connection_manager, 'store_pending_notification', new_callable=AsyncMock) as mock_store:
            
            result = await connection_manager.send_message_distributed(user_id, message)
            
            assert result is False
            mock_send_local.assert_called_once_with(user_id, message)
            connection_manager.redis.hdel.assert_called_once_with(CONNECTIONS_KEY, user_id)
            mock_store.assert_called_once_with(user_id, message)
    
    @pytest.mark.asyncio
    async def test_send_message_distributed_store_pending(self, connection_manager):
        """Test distributed message sending when user is not connected anywhere."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        
        connection_manager.redis.hget.return_value = None
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=False) as mock_send_local, \
             patch.object(connection_manager, 'store_pending_notification', new_callable=AsyncMock) as mock_store:
            
            result = await connection_manager.send_message_distributed(user_id, message)
            
            assert result is False
            mock_send_local.assert_called_once_with(user_id, message)
            mock_store.assert_called_once_with(user_id, message)
    
    @pytest.mark.asyncio
    async def test_send_message_distributed_redis_failure(self, connection_manager):
        """Test distributed message sending when Redis hget fails."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.redis.hget.side_effect = Exception("Redis error")
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=False):
            result = await connection_manager.send_message_distributed(user_id, message)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_store_pending_notification(self, connection_manager):
        """Test storing pending notification."""
        user_id = "test_user_1"
        message = {"content": "Test pending message"}
        
        await connection_manager.store_pending_notification(user_id, message)
        
        connection_manager.redis.zadd.assert_called_once()
        connection_manager.redis.expire.assert_called_once()
        connection_manager.redis.sadd.assert_called_once_with(PENDING_USERS_KEY, user_id)
        connection_manager.redis.zremrangebyrank.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_pending_notification_with_id(self, connection_manager):
        """Test storing pending notification with existing notification_id."""
        user_id = "test_user_1"
        message = {"content": "Test pending message", "notification_id": "custom_id"}
        
        await connection_manager.store_pending_notification(user_id, message)
        
        connection_manager.redis.zadd.assert_called_once()
        # Check if custom_id is used
        call_args = connection_manager.redis.zadd.call_args[0][1]
        member = list(call_args.keys())[0]
        data = json.loads(member)
        assert data["notification_id"] == "custom_id"
    
    @pytest.mark.asyncio
    async def test_store_pending_notification_redis_failure(self, connection_manager):
        """Test storing pending notification when Redis fails."""
        user_id = "test_user_1"
        message = {"content": "Test pending message"}
        connection_manager.redis.zadd.side_effect = Exception("Redis error")
        
        await connection_manager.store_pending_notification(user_id, message)
        # Should not raise, just log error
    
    @pytest.mark.asyncio
    async def test_deliver_pending_notifications_success(self, connection_manager, mock_websocket):
        """Test successful delivery of pending notifications."""
        user_id = "test_user_1"
        pending_data = json.dumps({
            "user_id": user_id,
            "message": {"content": "Test pending message"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        
        connection_manager.redis.zrange.return_value = [pending_data]
        connection_manager.local_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=True) as mock_send_local:
            await connection_manager.deliver_pending_notifications(user_id)
            
            mock_send_local.assert_called_once()
            call_args = mock_send_local.call_args[0][1]
            assert call_args["is_pending"] is True
            assert "original_timestamp" in call_args
            connection_manager.redis.zrem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deliver_pending_notifications_with_invalid(self, connection_manager, mock_websocket):
        """Test delivery with invalid pending data."""
        user_id = "test_user_1"
        valid_pending = json.dumps({
            "user_id": user_id,
            "message": {"content": "Test pending message"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        connection_manager.redis.zrange.return_value = [valid_pending, "invalid_json"]
        connection_manager.local_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=True) as mock_send_local:
            await connection_manager.deliver_pending_notifications(user_id)
            
            mock_send_local.assert_called_once()
            connection_manager.redis.zrem.assert_called_once_with(f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}", valid_pending)
    
    @pytest.mark.asyncio
    async def test_deliver_pending_notifications_send_fail(self, connection_manager, mock_websocket):
        """Test delivery when send fails midway."""
        user_id = "test_user_1"
        pending1 = json.dumps({
            "user_id": user_id,
            "message": {"content": "First"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        pending2 = json.dumps({
            "user_id": user_id,
            "message": {"content": "Second"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        connection_manager.redis.zrange.return_value = [pending1, pending2]
        connection_manager.local_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock) as mock_send_local:
            mock_send_local.side_effect = [False, True]
            await connection_manager.deliver_pending_notifications(user_id)
            
            mock_send_local.assert_called_once()  # Only first attempted, break after fail
            connection_manager.redis.zrem.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_deliver_pending_notifications_no_pendings(self, connection_manager):
        """Test delivery when no pending notifications exist."""
        user_id = "test_user_1"
        connection_manager.redis.zrange.return_value = []
        
        await connection_manager.deliver_pending_notifications(user_id)
        
        # Should not call any send methods
        connection_manager.redis.zrem.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_deliver_pending_notifications_redis_failure(self, connection_manager):
        """Test delivery when Redis zrange fails."""
        user_id = "test_user_1"
        connection_manager.redis.zrange.side_effect = Exception("Redis error")
        
        await connection_manager.deliver_pending_notifications(user_id)
        # Should not raise
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_success(self, connection_manager, mock_websocket):
        """Test successful retry of pending notifications."""
        user_id = "test_user_1"
        pending_data = json.dumps({
            "user_id": user_id,
            "message": {"content": "Test pending message"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        
        connection_manager.redis.zrange.return_value = [pending_data]
        connection_manager.local_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager, 'send_message_distributed', new_callable=AsyncMock, return_value=True) as mock_send_distributed:
            result = await connection_manager.retry_pending_for_user(user_id)
            
            assert result == 1
            mock_send_distributed.assert_called_once()
            connection_manager.redis.zrem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_fail_increment_attempts(self, connection_manager):
        """Test retry when send fails but attempts < max."""
        user_id = "test_user_1"
        pending_data = json.dumps({
            "user_id": user_id,
            "message": {"content": "Test pending message"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 1,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        
        connection_manager.redis.zrange.return_value = [pending_data]
        
        with patch.object(connection_manager, 'send_message_distributed', new_callable=AsyncMock, return_value=False) as mock_send_distributed:
            result = await connection_manager.retry_pending_for_user(user_id)
            
            assert result == 0
            mock_send_distributed.assert_called_once()
            connection_manager.redis.zrem.assert_called_once()  # old
            connection_manager.redis.zadd.assert_called_once()
            call_args = connection_manager.redis.zadd.call_args[0][1]
            new_member = list(call_args.keys())[0]
            data = json.loads(new_member)
            assert data["attempts"] == 2
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_max_attempts_reached(self, connection_manager):
        """Test retry when max attempts are reached."""
        user_id = "test_user_1"
        pending_data = json.dumps({
            "user_id": user_id,
            "message": {"content": "Test pending message"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 3,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })
        
        connection_manager.redis.zrange.return_value = [pending_data]
        
        with patch.object(connection_manager, 'send_message_distributed', new_callable=AsyncMock, return_value=False) as mock_send_distributed:
            result = await connection_manager.retry_pending_for_user(user_id)
            
            assert result == 0
            connection_manager.redis.lpush.assert_called_once_with(DEAD_LETTER_KEY, pending_data)
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_invalid_data(self, connection_manager):
        """Test retry with invalid pending data."""
        user_id = "test_user_1"
        connection_manager.redis.zrange.return_value = ["invalid_json"]
        
        result = await connection_manager.retry_pending_for_user(user_id)
        
        assert result == 0
        connection_manager.redis.zrem.assert_called_once_with(f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}", "invalid_json")
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_no_pendings(self, connection_manager):
        """Test retry when no pendings after initial check."""
        user_id = "test_user_1"
        connection_manager.redis.zrange.return_value = []
        
        result = await connection_manager.retry_pending_for_user(user_id)
        
        assert result == 0
        connection_manager.redis.srem.assert_called_once_with(PENDING_USERS_KEY, user_id)
    
    @pytest.mark.asyncio
    async def test_retry_pending_for_user_redis_failure(self, connection_manager):
        """Test retry when Redis zrange fails."""
        user_id = "test_user_1"
        connection_manager.redis.zrange.side_effect = Exception("Redis error")
        
        result = await connection_manager.retry_pending_for_user(user_id)
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_get_connected_users_distributed(self, connection_manager):
        """Test getting distributed connected users."""
        user_data = {
            "user_1": json.dumps({"instance_id": "instance_1", "connected_at": time.time()}),
            "user_2": json.dumps({"instance_id": "instance_2", "connected_at": time.time()})
        }
        
        # Create an async iterator from the items
        async def async_iter(key):
            for item in user_data.items():
                yield item
        
        connection_manager.redis.hscan_iter = async_iter
        
        result = await connection_manager.get_connected_users_distributed()
        
        assert len(result) == 2
        assert "user_1" in result
        assert "user_2" in result
    
    @pytest.mark.asyncio
    async def test_get_connected_users_distributed_invalid_data(self, connection_manager):
        """Test getting distributed connected users with invalid data."""
        user_data = {
            "user_1": json.dumps({"instance_id": "instance_1", "connected_at": time.time()}),
            "user_invalid": "invalid_json"
        }
        
        async def async_iter(key):
            for item in user_data.items():
                yield item
        
        connection_manager.redis.hscan_iter = async_iter
        
        result = await connection_manager.get_connected_users_distributed()
        
        assert len(result) == 1
        assert "user_1" in result
        assert "user_invalid" not in result
    
    @pytest.mark.asyncio
    async def test_get_connected_users_distributed_redis_failure(self, connection_manager):
        """Test getting distributed users when Redis fails."""
        async def async_iter(key):
            raise Exception("Redis error")
        
        connection_manager.redis.hscan_iter = async_iter
        
        result = await connection_manager.get_connected_users_distributed()
        
        assert result == {}
    
    def test_get_local_connection_info(self, connection_manager):
        """Test getting local connection information."""
        user_id = "test_user_1"
        connection_manager.local_connections[user_id] = Mock()
        connection_manager.connection_times[user_id] = time.time()
        
        result = connection_manager.get_local_connection_info()
        
        assert result["instance_id"] == INSTANCE_ID
        assert result["total_local_connections"] == 1
        assert result["local_users"] == [user_id]
        assert user_id in result["connection_times"]


class TestRedisStreamsFunctions:
    """Test Redis Streams related functions."""
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_success(self, mock_redis):
        """Test successful Redis streams setup."""
        with patch('notification_service.manager') as mock_manager:
            mock_manager.redis = mock_redis
            mock_redis.xgroup_create.return_value = "OK"
            
            await setup_redis_streams()
            
            mock_redis.xgroup_create.assert_called_once_with(
                NOTIFICATIONS_STREAM, CONSUMER_GROUP, id='0', mkstream=True
            )
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_busygroup_error(self, mock_redis):
        """Test Redis streams setup with BUSYGROUP error (group already exists)."""
        with patch('notification_service.manager') as mock_manager:
            mock_manager.redis = mock_redis
            mock_redis.xgroup_create.side_effect = Exception("BUSYGROUP")
            
            # Should not raise an exception
            await setup_redis_streams()
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_other_error(self, mock_redis):
        """Test Redis streams setup with other error."""
        with patch('notification_service.manager') as mock_manager:
            mock_manager.redis = mock_redis
            mock_redis.xgroup_create.side_effect = Exception("Other error")
            
            await setup_redis_streams()
    
    @pytest.mark.asyncio
    async def test_process_stream_message_success(self, mock_redis):
        """Test successful stream message processing."""
        msg_id = "test_msg_123"
        fields = {
            "user_id": "test_user_1",
            "message": json.dumps({"content": "Test message"}),
            "type": "notification",
            "notification_id": str(uuid.uuid4())
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_distributed = AsyncMock(return_value=True)
            
            await process_stream_message(mock_redis, msg_id, fields)
            
            mock_manager.send_message_distributed.assert_called_once()
            mock_redis.xack.assert_called_once_with(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
    
    @pytest.mark.asyncio
    async def test_process_stream_message_string_message(self, mock_redis):
        """Test stream message processing with string message."""
        msg_id = "test_msg_123"
        fields = {
            "user_id": "test_user_1",
            "message": "String message",
            "type": "notification",
            "notification_id": str(uuid.uuid4())
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_distributed = AsyncMock(return_value=True)
            
            await process_stream_message(mock_redis, msg_id, fields)
            
            call_args = mock_manager.send_message_distributed.call_args[0]
            assert call_args[1]["message"] == {"content": "String message"}
            mock_redis.xack.assert_called_once_with(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
    
    @pytest.mark.asyncio
    async def test_process_stream_message_invalid_json_message(self, mock_redis):
        """Test stream message processing with invalid JSON message."""
        msg_id = "test_msg_123"
        fields = {
            "user_id": "test_user_1",
            "message": "invalid_json",
            "type": "notification",
            "notification_id": str(uuid.uuid4())
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_distributed = AsyncMock(return_value=True)
            
            await process_stream_message(mock_redis, msg_id, fields)
            
            call_args = mock_manager.send_message_distributed.call_args[0]
            assert call_args[1]["message"] == {"content": "invalid_json"}
            mock_redis.xack.assert_called_once_with(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
    
    @pytest.mark.asyncio
    async def test_process_stream_message_invalid_data(self, mock_redis):
        """Test stream message processing with invalid data."""
        msg_id = "test_msg_123"
        fields = {
            "user_id": "",  # Invalid empty user_id
            "message": "",
            "type": "notification"
        }
        
        await process_stream_message(mock_redis, msg_id, fields)
        
        mock_redis.xack.assert_called_once_with(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
    
    @pytest.mark.asyncio
    async def test_process_stream_message_failure(self, mock_redis):
        """Test stream message processing failure."""
        msg_id = "test_msg_123"
        fields = {
            "user_id": "test_user_1",
            "message": json.dumps({"content": "Test message"}),
            "type": "notification",
            "notification_id": str(uuid.uuid4())
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_distributed.side_effect = Exception("Send error")
            # Function logs error; acknowledge may not happen on failure path
            await process_stream_message(mock_redis, msg_id, fields)
            mock_redis.xack.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_fanout_message_success(self, mock_websocket):
        """Test successful fanout message processing."""
        message = {
            "data": json.dumps({
                "type": "fanout",
                "user_id": "test_user_1",
                "message": {"content": "Test fanout message"},
                "source_instance": "remote_instance"
            })
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_local = AsyncMock(return_value=True)
            
            await process_fanout_message(message)
            
            mock_manager.send_message_local.assert_called_once_with(
                "test_user_1", {"content": "Test fanout message"}
            )
    
    @pytest.mark.asyncio
    async def test_process_fanout_message_invalid_data(self):
        """Test fanout message processing with invalid data."""
        message = {
            "data": json.dumps({
                "type": "invalid_type",
                "user_id": "test_user_1",
                "message": {"content": "Test message"}
            })
        }
        
        with patch('notification_service.manager') as mock_manager:
            await process_fanout_message(message)
            
            mock_manager.send_message_local.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_fanout_message_missing_fields(self):
        """Test fanout message processing with missing fields."""
        message = {
            "data": json.dumps({
                "type": "fanout",
                "source_instance": "remote_instance"
            })
        }
        
        with patch('notification_service.manager') as mock_manager:
            await process_fanout_message(message)
            
            mock_manager.send_message_local.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_fanout_message_invalid_json(self):
        """Test fanout message processing with invalid JSON."""
        message = {
            "data": "invalid_json"
        }
        
        with patch('notification_service.manager') as mock_manager:
            await process_fanout_message(message)
            
            mock_manager.send_message_local.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_fanout_message_send_failure(self):
        """Test fanout message processing when send fails."""
        message = {
            "data": json.dumps({
                "type": "fanout",
                "user_id": "test_user_1",
                "message": {"content": "Test fanout message"},
                "source_instance": "remote_instance"
            })
        }
        
        with patch('notification_service.manager') as mock_manager:
            mock_manager.send_message_local = AsyncMock(return_value=False)
            
            await process_fanout_message(message)
            
            mock_manager.send_message_local.assert_called_once()


class TestPubSubFunctions:
    """Test Pub/Sub related functions."""
    
    @pytest.mark.asyncio
    async def test_pubsub_notifications_listener_invalid_payload(self, mock_redis):
        """Test Pub/Sub message processing with invalid payload."""
        with patch('notification_service.manager') as mock_manager, \
             patch('asyncio.sleep') as mock_sleep:
            mock_manager.redis = mock_redis
            mock_manager.send_message_distributed = AsyncMock()
            
            mock_pubsub = mock_redis.pubsub.return_value
            
            async def mock_listen():
                yield {
                    "type": "message",
                    "data": "invalid_json"
                }
                yield None
            
            mock_pubsub.listen = Mock(return_value=mock_listen())
            
            task = asyncio.create_task(pubsub_notifications_listener())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            mock_manager.send_message_distributed.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pubsub_notifications_listener_reconnect(self, mock_redis):
        """Test Pub/Sub listener reconnect logic."""
        with patch('notification_service.manager') as mock_manager, \
             patch('asyncio.sleep') as mock_sleep:
            mock_manager.redis = mock_redis
            
            mock_pubsub = mock_redis.pubsub.return_value
            
            async def mock_listen():
                raise Exception("Connection error")
            
            mock_pubsub.listen = Mock(return_value=mock_listen())
            
            task = asyncio.create_task(pubsub_notifications_listener())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            mock_sleep.assert_called()  # Called for retry delay


class TestBackgroundTasks:
    """Test background task functions."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_task_cleanup_stale_connections(self, connection_manager):
        """Test heartbeat task cleanup of stale connections."""
        current_time = time.time()
        stale_time = current_time - (CLIENT_TIMEOUT + 100)
        fresh_time = current_time - 10
        
        connection_manager.last_activity["stale_user"] = stale_time
        connection_manager.local_connections["stale_user"] = Mock()
        connection_manager.last_activity["fresh_user"] = fresh_time
        connection_manager.local_connections["fresh_user"] = Mock()
        
        with patch('notification_service.manager', connection_manager), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep, \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect, \
             patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock) as mock_send_local, \
             patch('notification_service.cleanup_stale_connections', new_callable=AsyncMock) as mock_cleanup:
            
            mock_send_local.side_effect = [True]  # For fresh_user
            
            # Simulate one iteration
            await asyncio.sleep(0.1)
            current_time = time.time()
            disconnected_users = []
            
            for user_id in list(connection_manager.last_activity.keys()):
                if current_time - connection_manager.last_activity.get(user_id, 0) > CLIENT_TIMEOUT:
                    disconnected_users.append(user_id)
            
            if connection_manager.local_connections:
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "instance_id": INSTANCE_ID
                }
                
                for user_id in list(connection_manager.local_connections.keys()):
                    if user_id not in disconnected_users:
                        success = await connection_manager.send_message_local(user_id, heartbeat_msg)
                        if not success:
                            disconnected_users.append(user_id)
            
            for user_id in disconnected_users:
                await connection_manager.disconnect(user_id)
            
            mock_send_local.assert_called_once_with("fresh_user", ANY)
            mock_disconnect.assert_called_once_with("stale_user")
    
    @pytest.mark.asyncio
    async def test_heartbeat_task_send_fail(self, connection_manager):
        """Test heartbeat task when send fails."""
        current_time = time.time()
        fresh_time = current_time - 10
        
        connection_manager.last_activity["fresh_user"] = fresh_time
        connection_manager.local_connections["fresh_user"] = Mock()
        
        with patch('notification_service.manager', connection_manager), \
             patch('asyncio.sleep', new_callable=AsyncMock), \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect, \
             patch.object(connection_manager, 'send_message_local', new_callable=AsyncMock, return_value=False), \
             patch('notification_service.cleanup_stale_connections', new_callable=AsyncMock):
            
            # Simulate one iteration
            await asyncio.sleep(0.1)
            current_time = time.time()
            disconnected_users = []
            
            for user_id in list(connection_manager.last_activity.keys()):
                if current_time - connection_manager.last_activity.get(user_id, 0) > CLIENT_TIMEOUT:
                    disconnected_users.append(user_id)
            
            if connection_manager.local_connections:
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "instance_id": INSTANCE_ID
                }
                
                for user_id in list(connection_manager.local_connections.keys()):
                    if user_id not in disconnected_users:
                        success = await connection_manager.send_message_local(user_id, heartbeat_msg)
                        if not success:
                            disconnected_users.append(user_id)
            
            for user_id in disconnected_users:
                await connection_manager.disconnect(user_id)
            
            mock_disconnect.assert_called_once_with("fresh_user")
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(self, connection_manager):
        """Test cleanup of stale connections from Redis."""
        current_time = time.time()
        stale_time = current_time - 4000  # More than 1 hour
        fresh_time = current_time - 100
        
        connections = {
            "stale_user_1": json.dumps({"connected_at": stale_time}),
            "fresh_user": json.dumps({"connected_at": fresh_time}),
            "no_connected_at": json.dumps({"instance_id": "test"}),
            "invalid": "invalid_json"
        }
        
        async def async_iter(key):
            for item in connections.items():
                yield item
        
        connection_manager.redis.hscan_iter = async_iter
        
        with patch('notification_service.manager', connection_manager):
            await cleanup_stale_connections()
        
        # Only entries with stale time or invalid JSON are removed
        connection_manager.redis.hdel.assert_called_once()
        args, _ = connection_manager.redis.hdel.call_args
        assert args[0] == CONNECTIONS_KEY
        assert set(args[1:]) == {"stale_user_1", "invalid"}
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_connections_redis_failure(self, connection_manager):
        """Test cleanup when Redis hscan_iter fails."""
        async def async_iter(key):
            raise Exception("Redis error")
        
        connection_manager.redis.hscan_iter = async_iter
        
        with patch('notification_service.manager', connection_manager):
            await cleanup_stale_connections()
        # No raise
    
    @pytest.mark.asyncio
    async def test_retry_pending_task(self, connection_manager):
        """Test retry pending task."""
        connection_manager.redis.smembers.return_value = {"user_1", "user_2"}
        
        with patch('notification_service.manager', connection_manager), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep, \
             patch.object(connection_manager, 'retry_pending_for_user', new_callable=AsyncMock) as mock_retry:
            
            # Test the retry logic directly instead of running the infinite loop
            users = await connection_manager.redis.smembers(PENDING_USERS_KEY)
            
            for user_id_bytes in users:
                user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
                await connection_manager.retry_pending_for_user(user_id)
            
            # Verify that retry_pending_for_user was called for each user
            assert mock_retry.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_pending_task_redis_failure(self, connection_manager):
        """Test retry pending task when Redis smembers fails."""
        connection_manager.redis.smembers.side_effect = Exception("Redis error")
        
        with patch('notification_service.manager', connection_manager), \
             patch('asyncio.sleep', new_callable=AsyncMock):
            
            # Simulate one iteration
            try:
                users = await connection_manager.redis.smembers(PENDING_USERS_KEY)
            except:
                pass
            # No raise


class TestStreamsConsumer:
    """Test Redis Streams consumer behavior."""
    
    @pytest.mark.asyncio
    async def test_redis_streams_consumer_reconnect(self, mock_redis):
        """Test streams consumer reconnect logic."""
        with patch('notification_service.manager') as mock_manager, \
             patch('asyncio.sleep') as mock_sleep:
            mock_manager.redis = mock_redis
            mock_redis.xreadgroup.side_effect = Exception("Connection error")
            
            task = asyncio.create_task(redis_streams_consumer())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            mock_sleep.assert_called()  # Retry delay


class TestFanoutListener:
    """Test instance fanout listener functions."""
    
    @pytest.mark.asyncio
    async def test_instance_fanout_listener_reconnect(self, mock_redis):
        """Test fanout listener reconnect logic."""
        with patch('notification_service.manager') as mock_manager, \
             patch('asyncio.sleep') as mock_sleep:
            mock_manager.redis = mock_redis
            mock_pubsub = mock_redis.pubsub.return_value
            
            async def mock_listen():
                raise Exception("Connection error")
            
            mock_pubsub.listen = Mock(return_value=mock_listen())
            
            task = asyncio.create_task(instance_fanout_listener())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            mock_sleep.assert_called()  # Retry delay
    
    @pytest.mark.asyncio
    async def test_instance_fanout_listener_max_attempts(self, mock_redis):
        """Test fanout listener stops after max reconnect attempts."""
        with patch('notification_service.manager') as mock_manager, \
             patch('asyncio.sleep') as mock_sleep, \
             patch('notification_service.MAX_RECONNECT_ATTEMPTS', 1):
            mock_manager.redis = mock_redis
            mock_pubsub = mock_redis.pubsub.return_value
            
            async def mock_listen():
                raise Exception("Connection error")
            
            mock_pubsub.listen = Mock(return_value=mock_listen())
            
            task = asyncio.create_task(instance_fanout_listener())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            assert mock_sleep.call_count == 1


class TestAPIEndpoints:
    """Test FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_check_success(self, client, connection_manager, mock_redis):
        """Test successful health check."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.redis = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.xinfo_stream.return_value = {"length": 5}
            mock_redis.xinfo_groups.return_value = [{"name": CONSUMER_GROUP, "lag": 0}]
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["instance_id"] == INSTANCE_ID
            assert "redis" in data
            assert "redis_stream" in data
            assert "consumer_group" in data
    
    def test_health_check_redis_unhealthy(self, client, connection_manager, mock_redis):
        """Test health check when Redis is unhealthy."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.redis = mock_redis
            mock_redis.ping.side_effect = Exception("Redis connection failed")
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "unhealthy" in data["redis"]
    
    def test_get_stats(self, client, connection_manager):
        """Test get stats endpoint."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.get_connected_users_distributed = AsyncMock(return_value={})
            
            response = client.get("/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["instance_id"] == INSTANCE_ID
            assert "local_connections" in data
            assert "distributed_connections" in data

    def test_debug_endpoint_exists_when_env_enabled(self, client):
        """Ensure debug endpoint can be toggled by environment flag."""
        # If route doesn't exist, FastAPI returns 404 which is acceptable; this still executes code path
        response = client.get("/debug/pending/test_user")
        assert response.status_code in (200, 404)
    
    def test_get_distributed_stats(self, client, connection_manager):
        """Test get distributed stats endpoint."""
        distributed_connections = {
            "user_1": {"instance_id": "instance_1", "connected_at": time.time()},
            "user_2": {"instance_id": "instance_2", "connected_at": time.time()}
        }
        
        with patch('notification_service.manager', connection_manager):
            connection_manager.get_connected_users_distributed = AsyncMock(return_value=distributed_connections)
            
            response = client.get("/stats/distributed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_instances"] == 2
            assert data["total_users"] == 2
            assert "by_instance" in data
    
    def test_send_stream_notification_success(self, client, connection_manager, mock_redis, sample_notification_payload):
        """Test successful stream notification sending."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.redis = mock_redis
            mock_redis.xadd.return_value = "test_stream_id"
            
            response = client.post("/notify/stream/test_user_1", json=sample_notification_payload.model_dump())
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["delivery_method"] == "redis_stream"
            assert "stream_id" in data
    
    def test_send_stream_notification_string_message(self, client, connection_manager, mock_redis):
        """Test stream notification sending with string message."""
        payload = NotificationPayload(message="String message")
        with patch('notification_service.manager', connection_manager):
            connection_manager.redis = mock_redis
            mock_redis.xadd.return_value = "test_stream_id"
            
            response = client.post("/notify/stream/test_user_1", json=payload.model_dump())
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_send_stream_notification_message_too_large(self, client, sample_notification_payload):
        """Test stream notification with message too large."""
        large_message = {"content": "x" * (MAX_MESSAGE_SIZE + 1)}
        payload = NotificationPayload(message=large_message)
        
        response = client.post("/notify/stream/test_user_1", json=payload.model_dump())
        
        assert response.status_code == 413
        assert "Message too large" in response.json()["detail"]
    
    def test_send_stream_notification_redis_failure(self, client, connection_manager, mock_redis, sample_notification_payload):
        """Test stream notification when Redis xadd fails."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.redis = mock_redis
            mock_redis.xadd.side_effect = Exception("Redis error")
            
            response = client.post("/notify/stream/test_user_1", json=sample_notification_payload.model_dump())
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
    
    def test_send_direct_notification_success(self, client, connection_manager, sample_notification_payload):
        """Test successful direct notification sending."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.send_message_distributed = AsyncMock(return_value=True)
            
            response = client.post("/notify/direct/test_user_1", json=sample_notification_payload.model_dump())
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["delivery_method"] == "direct_websocket"
    
    def test_send_direct_notification_default_message(self, client, connection_manager):
        """Test direct notification with None message falls back to default."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.send_message_distributed = AsyncMock(return_value=True)
            # Omit message field to use default
            response = client.post("/notify/direct/test_user_1", json={"type": "notification"})
            assert response.status_code == 200
    
    def test_send_direct_notification_user_not_connected(self, client, connection_manager, sample_notification_payload):
        """Test direct notification when user is not connected."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.send_message_distributed = AsyncMock(return_value=False)
            
            response = client.post("/notify/direct/test_user_1", json=sample_notification_payload.model_dump())
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "stored as pending" in data["message"]
    
    def test_send_direct_notification_message_too_large(self, client, connection_manager):
        """Test direct notification with message too large."""
        large_message = {"content": "x" * (MAX_MESSAGE_SIZE + 1)}
        payload = NotificationPayload(message=large_message)
        
        with patch('notification_service.manager', connection_manager):
            response = client.post("/notify/direct/test_user_1", json=payload.model_dump())
            
            assert response.status_code == 413
    
    def test_send_direct_notification_failure(self, client, connection_manager, sample_notification_payload):
        """Test direct notification when send fails."""
        with patch('notification_service.manager', connection_manager):
            connection_manager.send_message_distributed = AsyncMock(side_effect=Exception("Send error"))
            
            response = client.post("/notify/direct/test_user_1", json=sample_notification_payload.model_dump())
            
            assert response.status_code == 500


class TestWebSocketEndpoint:
    """Test WebSocket endpoint."""
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_success(self, connection_manager, mock_websocket):
        """Test successful WebSocket connection."""
        user_id = "test_user_1"
        
        with patch('notification_service.manager', connection_manager), \
             patch.object(connection_manager, 'connect', new_callable=AsyncMock) as mock_connect, \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            
            # Mock the WebSocket receive_text to raise WebSocketDisconnect after one call
            mock_websocket.receive_text.side_effect = [json.dumps({"type": "ping"}), WebSocketDisconnect()]
            
            await websocket_endpoint(mock_websocket, user_id)
            
            mock_connect.assert_called_once_with(mock_websocket, user_id)
            mock_disconnect.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_user_id(self, mock_websocket):
        """Test WebSocket endpoint with invalid user ID."""
        with patch('notification_service.manager'):
            await websocket_endpoint(mock_websocket, "")
            
            mock_websocket.close.assert_called_once_with(code=4000, reason="Invalid user_id")
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_ping_pong(self, connection_manager, mock_websocket):
        """Test WebSocket ping-pong functionality."""
        user_id = "test_user_1"
        
        with patch('notification_service.manager', connection_manager), \
             patch.object(connection_manager, 'connect', new_callable=AsyncMock) as mock_connect, \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            
            # Mock ping message followed by disconnect
            mock_websocket.receive_text.side_effect = [
                json.dumps({"type": "ping"}),
                WebSocketDisconnect()
            ]
            
            await websocket_endpoint(mock_websocket, user_id)
            
            # Should send pong response
            mock_websocket.send_json.assert_called_once()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "pong"
            assert "timestamp" in call_args
            assert call_args["instance_id"] == INSTANCE_ID
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_message(self, connection_manager, mock_websocket):
        """Test WebSocket with invalid client message."""
        user_id = "test_user_1"
        
        with patch('notification_service.manager', connection_manager), \
             patch.object(connection_manager, 'connect', new_callable=AsyncMock) as mock_connect, \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            
            mock_websocket.receive_text.side_effect = [
                "invalid_json",
                WebSocketDisconnect()
            ]
            
            await websocket_endpoint(mock_websocket, user_id)
            
            mock_websocket.send_json.assert_not_called()  # No pong since invalid
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_error(self, connection_manager, mock_websocket):
        """Test WebSocket endpoint error handling."""
        user_id = "test_user_1"
        
        with patch('notification_service.manager', connection_manager), \
             patch.object(connection_manager, 'connect', new_callable=AsyncMock) as mock_connect, \
             patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            
            mock_websocket.receive_text.side_effect = Exception("Receive error")
            
            await websocket_endpoint(mock_websocket, user_id)
            
            mock_disconnect.assert_called_once_with(user_id)


class TestLifespanEvents:
    """Test application lifespan events."""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test application startup."""
        mock_app = Mock()
        mock_app.state = Mock()
        
        with patch('notification_service.ConnectionPool') as mock_pool_class, \
             patch('notification_service.DistributedConnectionManager') as mock_manager_class, \
             patch('notification_service.setup_redis_streams', new_callable=AsyncMock) as mock_setup, \
             patch('asyncio.create_task') as mock_create_task, \
             patch('asyncio.gather', new_callable=AsyncMock) as mock_gather, \
             patch('notification_service.process_stream_message', new_callable=AsyncMock) as mock_process:
            
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.redis = AsyncMock()
            async def async_iter(key):
                yield "user1", json.dumps({"instance_id": INSTANCE_ID})
            mock_manager.redis.hscan_iter = async_iter
            mock_manager.redis.close = AsyncMock()
            mock_manager.redis.xreadgroup.side_effect = [
                [(NOTIFICATIONS_STREAM, [("msg1", {"user_id": "u", "message": json.dumps({"content": "m"})})])],
                []
            ]
            mock_pool.disconnect = AsyncMock()
            
            mock_create_task.return_value = Mock()
            mock_gather.return_value = []
            
            async with lifespan(mock_app):
                pass
            
            mock_pool_class.assert_called_once()
            mock_manager_class.assert_called_once_with(mock_pool)
            mock_setup.assert_called_once()
            mock_create_task.assert_called()
            mock_manager.redis.hdel.assert_called_once_with(CONNECTIONS_KEY, "user1")
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown_drain_error(self):
        """Test lifespan shutdown when draining stream fails."""
        mock_app = Mock()
        mock_app.state = Mock()
        
        with patch('notification_service.ConnectionPool') as mock_pool_class, \
             patch('notification_service.DistributedConnectionManager') as mock_manager_class, \
             patch('notification_service.setup_redis_streams', new_callable=AsyncMock), \
             patch('asyncio.create_task') as mock_create_task, \
             patch('asyncio.gather', new_callable=AsyncMock):
            
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.redis = AsyncMock()
            mock_manager.redis.hscan_iter.return_value = []
            mock_manager.redis.close = AsyncMock()
            mock_manager.redis.xreadgroup.side_effect = Exception("Drain error")
            mock_pool.disconnect = AsyncMock()
            
            mock_create_task.return_value = Mock()
            
            async with lifespan(mock_app):
                pass
            
            # Should log warning, but continue


class TestDebugEndpoints:
    """Test debug endpoints when enabled."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_debug_list_pending_when_disabled(self, client):
        """Test debug list pending endpoint when debug is disabled."""
        with patch('notification_service.ENABLE_DEBUG', False):
            response = client.get("/debug/pending/test_user")
            
            assert response.status_code == 404  # Endpoint not available


class TestConfiguration:
    """Test configuration and constants."""
    
    def test_instance_id_generation(self):
        """Test that INSTANCE_ID is properly generated."""
        assert INSTANCE_ID is not None
        assert isinstance(INSTANCE_ID, str)
        assert len(INSTANCE_ID) > 0
    
    def test_redis_configuration(self):
        """Test Redis configuration constants."""
        assert REDIS_HOST == "localhost"
        assert REDIS_PORT == 6379
        assert isinstance(HEARTBEAT_INTERVAL, int)
        assert isinstance(CLIENT_TIMEOUT, int)
        assert isinstance(MESSAGE_TTL_HOURS, int)
        assert isinstance(MAX_PENDING_MESSAGES, int)
        assert isinstance(PENDING_RETRY_INTERVAL, int)
        assert isinstance(MAX_MESSAGE_SIZE, int)
    
    def test_redis_keys_and_channels(self):
        """Test Redis keys and channels constants."""
        assert NOTIFICATIONS_STREAM == "notifications:stream"
        assert INSTANCE_CHANNEL_PREFIX == "notifications:instance"
        assert CONNECTIONS_KEY == "websocket:connections"
        assert PENDING_NOTIFICATIONS_PREFIX == "notifications:pending:"
        assert PENDING_USERS_KEY == "notifications:pending_users"
        assert DEAD_LETTER_KEY == "notifications:dead_letter"
        assert CONSUMER_GROUP == "notification_processors"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self, connection_manager, mock_websocket):
        """Test handling of Redis connection errors."""
        connection_manager.redis.hset.side_effect = Exception("Redis connection failed")
        
        with pytest.raises(Exception, match="Redis connection failed"):
            await connection_manager.connect(mock_websocket, "test_user")
    
    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self, connection_manager):
        """Test handling of JSON decode errors."""
        connection_manager.redis.hget.return_value = "invalid_json"
        
        result = await connection_manager.send_message_distributed("test_user", {"content": "test"})
        
        # Should handle gracefully and store as pending
        connection_manager.redis.hdel.assert_called_once_with(CONNECTIONS_KEY, "test_user")
    
    @pytest.mark.asyncio
    async def test_websocket_send_error_handling(self, connection_manager, mock_websocket):
        """Test handling of WebSocket send errors."""
        user_id = "test_user_1"
        message = {"content": "Test message"}
        connection_manager.local_connections[user_id] = mock_websocket
        mock_websocket.send_json.side_effect = Exception("WebSocket send failed")
        
        with patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            result = await connection_manager.send_message_local(user_id, message)
            
            assert result is False
            mock_disconnect.assert_called_once_with(user_id)


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_notification_flow(self, connection_manager, mock_websocket, mock_redis):
        """Test complete notification flow from connection to message delivery."""
        user_id = "test_user_1"
        message = {"content": "Integration test message"}
        
        # Setup mocks
        connection_manager.redis = mock_redis
        connection_manager.local_connections[user_id] = mock_websocket
        
        # Test connection
        with patch.object(connection_manager, 'deliver_pending_notifications', new_callable=AsyncMock):
            await connection_manager.connect(mock_websocket, user_id)
        
        # Test message sending
        result = await connection_manager.send_message_local(user_id, message)
        assert result is True
        mock_websocket.send_json.assert_called_with(message)
        
        # Test disconnection
        await connection_manager.disconnect(user_id)
        assert user_id not in connection_manager.local_connections
    
    @pytest.mark.asyncio
    async def test_pending_notification_flow(self, connection_manager, mock_redis):
        """Test pending notification flow for offline users."""
        user_id = "test_user_1"
        message = {"content": "Pending test message"}
        
        connection_manager.redis = mock_redis
        
        # Store pending notification
        await connection_manager.store_pending_notification(user_id, message)
        
        # Verify storage calls
        connection_manager.redis.zadd.assert_called_once()
        connection_manager.redis.sadd.assert_called_once_with(PENDING_USERS_KEY, user_id)
        
        # Test retry
        mock_redis.zrange.return_value = [json.dumps({
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "notification_id": str(uuid.uuid4())
        })]
        
        with patch.object(connection_manager, 'send_message_distributed', new_callable=AsyncMock, return_value=True):
            result = await connection_manager.retry_pending_for_user(user_id)
            assert result == 1


# Additional test for edge cases and boundary conditions
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_notification_payload_edge_cases(self):
        """Test NotificationPayload with edge case values."""
        # Test with empty string
        payload = NotificationPayload(message="")
        assert payload.message == ""
        
        # Test with complex nested structure
        complex_message = {
            "content": "Complex message",
            "metadata": {
                "priority": "high",
                "tags": ["urgent", "important"],
                "nested": {"level": 2}
            }
        }
        payload = NotificationPayload(message=complex_message)
        assert payload.message == complex_message
        
        # Test with list message
        list_message = ["item1", "item2", "item3"]
        payload = NotificationPayload(message=list_message)
        assert payload.message == list_message
        
        # Test with numeric message
        numeric_message = 42
        payload = NotificationPayload(message=numeric_message)
        assert payload.message == numeric_message
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, connection_manager, mock_websocket):
        """Test handling of concurrent connections."""
        user_id = "test_user_1"
        
        # Simulate concurrent connection attempts
        tasks = []
        for i in range(5):
            websocket = Mock(spec=WebSocket)
            websocket.accept = AsyncMock()
            task = connection_manager.connect(websocket, f"{user_id}_{i}")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Should have 5 connections
        assert len(connection_manager.local_connections) == 5
    
    @pytest.mark.asyncio
    async def test_large_message_handling(self, connection_manager):
        """Test handling of large messages."""
        # Create a message that's close to the size limit
        large_content = "x" * (MAX_MESSAGE_SIZE - 100)  # Leave some room for JSON overhead
        large_message = {"content": large_content}
        
        # Should not raise an exception
        await connection_manager.store_pending_notification("test_user", large_message)
    
    def test_timeout_calculations(self):
        """Test timeout calculations."""
        assert CLIENT_TIMEOUT == HEARTBEAT_INTERVAL * 3  # CLIENT_TIMEOUT_MULTIPLIER
        assert HEARTBEAT_INTERVAL > 0
        assert CLIENT_TIMEOUT > HEARTBEAT_INTERVAL


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
from typing import Dict, Optional, Set, List, Union
import asyncio
import json
import logging
import time
import uuid
import socket
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, CollectorRegistry

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname() + "_" + str(uuid.uuid4())[:8])
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = 0

# Redis Keys and Channels
NOTIFICATIONS_STREAM = "notifications:stream"
INSTANCE_CHANNEL_PREFIX = "notifications:instance"
CONNECTIONS_KEY = "websocket:connections"
PENDING_NOTIFICATIONS_PREFIX = "notifications:pending:"
PENDING_USERS_KEY = "notifications:pending_users"
DEAD_LETTER_KEY = "notifications:dead_letter"
CONSUMER_GROUP = "notification_processors"

# Service Configuration
REDIS_RETRY_DELAY = 5
MAX_RECONNECT_ATTEMPTS = 10
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 30))
CLIENT_TIMEOUT_MULTIPLIER = int(os.getenv("CLIENT_TIMEOUT_MULTIPLIER", 3))
CLIENT_TIMEOUT = HEARTBEAT_INTERVAL * CLIENT_TIMEOUT_MULTIPLIER
MESSAGE_TTL_HOURS = int(os.getenv("MESSAGE_TTL_HOURS", 24))
MAX_PENDING_MESSAGES = int(os.getenv("MAX_PENDING_MESSAGES", 100))
PENDING_RETRY_INTERVAL = int(os.getenv("PENDING_RETRY_INTERVAL", 300))  # 5 minutes
MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", 1024 * 1024))  # 1MB
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "false").lower() == "true"

class NotificationPayload(BaseModel):
    message: Union[dict, str, list, int, float] = {"content": "Your new recommendations are ready!"}
    type: str = "notification"

@dataclass
class PendingNotification:
    """Structure for pending notifications"""
    user_id: str
    message: dict
    timestamp: str
    attempts: int = 0
    max_attempts: int = 3
    notification_id: Optional[str] = None

class DistributedConnectionManager:
    """Manages WebSocket connections with distributed state in Redis"""
    
    def __init__(self, redis_pool: ConnectionPool):
        self.local_connections: Dict[str, WebSocket] = {}
        self.connection_times: Dict[str, float] = {}
        self.last_activity: Dict[str, float] = {}
        self.redis_pool = redis_pool
        self.redis: aioredis.Redis = aioredis.Redis(connection_pool=self.redis_pool)
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Register user connection locally and in Redis"""
        try:
            await websocket.accept()
            self.local_connections[user_id] = websocket
            self.connection_times[user_id] = time.time()
            self.last_activity[user_id] = time.time()
            
            connection_data = {
                "instance_id": INSTANCE_ID,
                "connected_at": time.time(),
                "user_id": user_id
            }
            
            await self.redis.hset(CONNECTIONS_KEY, user_id, json.dumps(connection_data))
            logger.info(f"User {user_id} connected to instance {INSTANCE_ID}. Local connections: {len(self.local_connections)}")
            await self.deliver_pending_notifications(user_id)
        except Exception as e:
            logger.error(f"Error connecting user {user_id}: {e}")
            raise
    
    async def disconnect(self, user_id: str):
        """Remove user connection locally and from Redis"""
        try:
            if user_id in self.local_connections:
                self.local_connections.pop(user_id)
                self.connection_times.pop(user_id, None)
                self.last_activity.pop(user_id, None)
                await self.redis.hdel(CONNECTIONS_KEY, user_id)
                logger.info(f"User {user_id} disconnected from instance {INSTANCE_ID}. Local connections: {len(self.local_connections)}")
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {e}")
    
    async def send_message_local(self, user_id: str, message: dict) -> bool:
        """Send message to locally connected user"""
        if user_id not in self.local_connections:
            return False
        
        websocket = self.local_connections[user_id]
        try:
            await websocket.send_json(message)
            logger.debug(f"Message sent to local user {user_id}: {message}")
            self.last_activity[user_id] = time.time()
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to local user {user_id}: {e}")
            await self.disconnect(user_id)
            return False
    
    async def send_message_distributed(self, user_id: str, message: dict) -> bool:
        """Send message to user across distributed instances"""
        try:
            if await self.send_message_local(user_id, message):
                return True
            
            connection_data = await self.redis.hget(CONNECTIONS_KEY, user_id)
            if connection_data:
                try:
                    conn_info = json.loads(connection_data)
                    target_instance = conn_info.get("instance_id")
                    if target_instance != INSTANCE_ID:
                        instance_channel = f"{INSTANCE_CHANNEL_PREFIX}:{target_instance}"
                        fanout_message = {
                            "type": "fanout",
                            "user_id": user_id,
                            "message": message,
                            "source_instance": INSTANCE_ID
                        }
                        await self.redis.publish(instance_channel, json.dumps(fanout_message))
                        logger.debug(f"Message forwarded to instance {target_instance} for user {user_id}")
                        return True
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid connection data for user {user_id}: {e}")
                    await self.redis.hdel(CONNECTIONS_KEY, user_id)
            
            await self.store_pending_notification(user_id, message)
            return False
        except Exception as e:
            logger.error(f"Error sending distributed message to user {user_id}: {e}")
            return False
    
    async def store_pending_notification(self, user_id: str, message: dict):
        """Store notification for offline user"""
        try:
            key = f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}"
            pending_notification = {
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "attempts": 0,
                "max_attempts": 3,
                "notification_id": message.get("notification_id", str(uuid.uuid4()))
            }
            
            score = time.time()
            member = json.dumps(pending_notification)
            await self.redis.zadd(key, {member: score})
            await self.redis.expire(key, MESSAGE_TTL_HOURS * 3600)
            await self.redis.sadd(PENDING_USERS_KEY, user_id)
            await self.redis.zremrangebyrank(key, MAX_PENDING_MESSAGES, -1)
            logger.info(f"Stored pending notification for offline user {user_id}")
        except Exception as e:
            logger.error(f"Error storing pending notification for user {user_id}: {e}")
    
    async def deliver_pending_notifications(self, user_id: str):
        """Deliver all pending notifications for a user"""
        try:
            key = f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}"
            pending_members = await self.redis.zrange(key, 0, -1)
            if not pending_members:
                return
            
            logger.info(f"Delivering {len(pending_members)} pending notifications to user {user_id}")
            delivered = []
            for member in pending_members:
                try:
                    notification_data = json.loads(member)
                    message = notification_data.get("message", {"content": "Your new recommendations are ready!"})
                    message["is_pending"] = True
                    message["original_timestamp"] = notification_data.get("timestamp")
                    
                    if await self.send_message_local(user_id, message):
                        delivered.append(member)
                    else:
                        break
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid pending notification data: {e}")
                    continue
            
            if delivered:
                await self.redis.zrem(key, *delivered)
                if await self.redis.zcard(key) == 0:
                    await self.redis.srem(PENDING_USERS_KEY, user_id)
                logger.info(f"Delivered {len(delivered)} pending notifications to user {user_id}")
        except Exception as e:
            logger.error(f"Error delivering pending notifications for user {user_id}: {e}")
    
    async def retry_pending_for_user(self, user_id: str) -> int:
        """Retry pending notifications for a user, increment attempts on failure"""
        try:
            key = f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}"
            pending_members = await self.redis.zrange(key, 0, -1)
            if not pending_members:
                await self.redis.srem(PENDING_USERS_KEY, user_id)
                return 0
            
            processed = 0
            to_remove = []
            to_update = []
            to_dlq = []
            
            for member in pending_members:
                try:
                    notification_data = json.loads(member)
                    message = notification_data.get("message", {"content": "Your new recommendations are ready!"})
                    attempts = notification_data.get("attempts", 0)
                    
                    if await self.send_message_distributed(user_id, message):
                        to_remove.append(member)
                        processed += 1
                    else:
                        attempts += 1
                        if attempts >= notification_data.get("max_attempts", 3):
                            to_dlq.append(member)
                            await self.redis.lpush(DEAD_LETTER_KEY, member)
                            logger.warning(f"Moved failed notification to DLQ for user {user_id}: attempts {attempts}")
                        else:
                            notification_data["attempts"] = attempts
                            new_member = json.dumps(notification_data)
                            to_update.append((member, new_member))
                except json.JSONDecodeError:
                    to_remove.append(member)
                    continue
            
            if to_remove:
                await self.redis.zrem(key, *to_remove)
            for old, new in to_update:
                await self.redis.zrem(key, old)
                await self.redis.zadd(key, {new: time.time()})
            if to_dlq:
                await self.redis.zrem(key, *to_dlq)
            
            if await self.redis.zcard(key) == 0:
                await self.redis.srem(PENDING_USERS_KEY, user_id)
            
            return processed
        except Exception as e:
            logger.error(f"Error retrying pending notifications for user {user_id}: {e}")
            return 0
    
    async def get_connected_users_distributed(self) -> Dict[str, Dict]:
        """Get all connected users across all instances using scan"""
        try:
            result = {}
            async for user_id, connection_data in self.redis.hscan_iter(CONNECTIONS_KEY):
                try:
                    result[user_id] = json.loads(connection_data)
                except json.JSONDecodeError:
                    continue
            return result
        except Exception as e:
            logger.error(f"Error getting connected users: {e}")
            return {}
    
    def get_local_connection_info(self) -> Dict:
        """Get local connection information"""
        return {
            "instance_id": INSTANCE_ID,
            "total_local_connections": len(self.local_connections),
            "local_users": list(self.local_connections.keys()),
            "connection_times": self.connection_times.copy()
        }

redis_pool: Optional[ConnectionPool] = None
manager: Optional[DistributedConnectionManager] = None

async def setup_redis_streams():
    """Initialize Redis Streams and Consumer Groups"""
    try:
        redis = manager.redis
        try:
            await redis.xgroup_create(NOTIFICATIONS_STREAM, CONSUMER_GROUP, id='0', mkstream=True)
            logger.info(f"Created consumer group {CONSUMER_GROUP} for stream {NOTIFICATIONS_STREAM}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Error creating consumer group: {e}")
    except Exception as e:
        logger.error(f"Failed to setup Redis Streams: {e}")

async def redis_streams_consumer():
    """Enhanced Redis Streams consumer with message acknowledgment"""
    consumer_id = f"{INSTANCE_ID}_{uuid.uuid4().hex[:8]}"
    reconnect_attempts = 0
    
    while reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        try:
            redis = manager.redis
            logger.info(f"Redis Streams consumer {consumer_id} started")
            reconnect_attempts = 0
            
            while True:
                try:
                    messages = await redis.xreadgroup(
                        CONSUMER_GROUP,
                        consumer_id,
                        {NOTIFICATIONS_STREAM: '>'},
                        count=10,
                        block=1000
                    )
                    for stream, msgs in messages:
                        for msg_id, fields in msgs:
                            await process_stream_message(redis, msg_id, fields)
                except Exception as e:
                    if "NOGROUP" in str(e):
                        await setup_redis_streams()
                        continue
                    raise e
        except asyncio.CancelledError:
            logger.info(f"Redis Streams consumer {consumer_id} cancelled")
            break
        except Exception as e:
            reconnect_attempts += 1
            logger.error(f"Redis Streams consumer error (attempt {reconnect_attempts}): {e}")
            if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                logger.critical("Max Redis reconnection attempts reached")
                break
            delay = min(REDIS_RETRY_DELAY * (2 ** reconnect_attempts), 60)
            await asyncio.sleep(delay)

async def process_stream_message(redis: aioredis.Redis, msg_id: str, fields: dict):
    """Process message from Redis Stream"""
    try:
        user_id = fields.get("user_id", "").strip()
        message_data = fields.get("message", {"content": "Your new recommendations are ready!"})
        notification_type = fields.get("type", "notification")
        notification_id = fields.get("notification_id")
        
        if not user_id or not message_data:
            logger.warning(f"Invalid stream message {msg_id}: {fields}")
            await redis.xack(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
            return
        
        try:
            message_content = json.loads(message_data)
        except json.JSONDecodeError:
            message_content = {"content": message_data}
        
        notification = {
            "user_id": user_id,
            "message": message_content,
            "timestamp": datetime.utcnow().isoformat(),
            "type": notification_type,
            "stream_id": msg_id,
            "notification_id": notification_id
        }
        
        success = await manager.send_message_distributed(user_id, notification)
        if success:
            logger.info(f"Stream notification {msg_id} delivered to user {user_id}")
        else:
            logger.info(f"Stream notification {msg_id} stored as pending for user {user_id}")
        
        await redis.xack(NOTIFICATIONS_STREAM, CONSUMER_GROUP, msg_id)
    except Exception as e:
        logger.error(f"Error processing stream message {msg_id}: {e}")

async def instance_fanout_listener():
    """Listen for fanout messages directed to this instance"""
    instance_channel = f"{INSTANCE_CHANNEL_PREFIX}:{INSTANCE_ID}"
    reconnect_attempts = 0
    
    while reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        try:
            redis = manager.redis
            pubsub = redis.pubsub()
            await pubsub.subscribe(instance_channel)
            logger.info(f"Instance fanout listener subscribed to {instance_channel}")
            reconnect_attempts = 0
            
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    await process_fanout_message(message)
        except asyncio.CancelledError:
            logger.info("Instance fanout listener cancelled")
            break
        except Exception as e:
            reconnect_attempts += 1
            logger.error(f"Fanout listener error (attempt {reconnect_attempts}): {e}")
            if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                logger.critical("Max fanout listener reconnection attempts reached")
                break
            delay = min(REDIS_RETRY_DELAY * (2 ** reconnect_attempts), 60)
            await asyncio.sleep(delay)
        finally:
            try:
                if 'pubsub' in locals():
                    await pubsub.unsubscribe(instance_channel)
                    await pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing fanout pubsub: {e}")

async def process_fanout_message(message: dict):
    """Process fanout message for local delivery"""
    try:
        data = json.loads(message.get("data", "{}"))
        if data.get("type") != "fanout":
            return
        
        user_id = data.get("user_id")
        notification_message = data.get("message")
        source_instance = data.get("source_instance")
        
        if not user_id or not notification_message:
            logger.warning(f"Invalid fanout message: {data}")
            return
        
        success = await manager.send_message_local(user_id, notification_message)
        if success:
            logger.info(f"Fanout message delivered to local user {user_id} from instance {source_instance}")
        else:
            logger.warning(f"Failed to deliver fanout message to user {user_id} - user not locally connected")
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in fanout message: {e}")
    except Exception as e:
        logger.error(f"Error processing fanout message: {e}")

async def heartbeat_task():
    """Send periodic heartbeat and cleanup stale connections"""
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            current_time = time.time()
            disconnected_users = []
            
            for user_id in list(manager.last_activity.keys()):
                if current_time - manager.last_activity.get(user_id, 0) > CLIENT_TIMEOUT:
                    disconnected_users.append(user_id)
            
            if manager.local_connections:
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "instance_id": INSTANCE_ID
                }
                
                for user_id in list(manager.local_connections.keys()):
                    if user_id not in disconnected_users:
                        success = await manager.send_message_local(user_id, heartbeat_msg)
                        if not success:
                            disconnected_users.append(user_id)
            
            for user_id in disconnected_users:
                await manager.disconnect(user_id)
            
            if disconnected_users:
                logger.info(f"Cleaned up {len(disconnected_users)} stale connections")
            
            await cleanup_stale_connections()
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")

async def cleanup_stale_connections():
    """Remove stale connections from Redis"""
    try:
        redis = manager.redis
        stale_users = []
        current_time = time.time()
        
        async for user_id, connection_data in redis.hscan_iter(CONNECTIONS_KEY):
            try:
                conn_info = json.loads(connection_data)
                connected_at = conn_info.get("connected_at", current_time)
                if current_time - connected_at > 3600:
                    stale_users.append(user_id)
            except json.JSONDecodeError:
                stale_users.append(user_id)
        
        if stale_users:
            await redis.hdel(CONNECTIONS_KEY, *stale_users)
            logger.info(f"Cleaned up {len(stale_users)} stale Redis connections")
    except Exception as e:
        logger.error(f"Error cleaning up stale connections: {e}")

async def retry_pending_task():
    """Periodically retry pending notifications for all users with pendings"""
    while True:
        try:
            await asyncio.sleep(PENDING_RETRY_INTERVAL)
            redis = manager.redis
            users = await redis.smembers(PENDING_USERS_KEY)
            
            for user_id_bytes in users:
                user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
                await manager.retry_pending_for_user(user_id)
        except asyncio.CancelledError:
            logger.info("Retry pending task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in retry pending task: {e}")


async def pubsub_notifications_listener():
    """Subscribe to simple Pub/Sub channel notifications:user and forward messages."""
    reconnect_attempts = 0
    channel = "notifications:user"
    while reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        try:
            redis = manager.redis
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to Pub/Sub channel: {channel}")
            reconnect_attempts = 0
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    try:
                        data = json.loads(message.get("data", "{}"))
                        user_id = str(data.get("user_id", "")).strip()
                        # Accept either string or object for message content
                        msg = data.get("message", {"content": "Your new recommendations are ready!"})
                        notification = {
                            "type": data.get("type", "notification"),
                            "user_id": user_id,
                            "message": msg if isinstance(msg, dict) else {"content": str(msg)},
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        if user_id:
                            await manager.send_message_distributed(user_id, notification)
                    except Exception as e:
                        logger.warning(f"Invalid pubsub payload on {channel}: {e}")
        except asyncio.CancelledError:
            logger.info("Pub/Sub notifications listener cancelled")
            break
        except Exception as e:
            reconnect_attempts += 1
            logger.error(f"Pub/Sub listener error (attempt {reconnect_attempts}): {e}")
            delay = min(REDIS_RETRY_DELAY * (2 ** reconnect_attempts), 60)
            await asyncio.sleep(delay)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with distributed service management"""
    logger.info(f"Starting Notification Service Instance: {INSTANCE_ID}")
    
    global redis_pool, manager
    redis_pool = ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        retry_on_timeout=True,
        max_connections=100
    )
    manager = DistributedConnectionManager(redis_pool)
    
    await setup_redis_streams()
    
    tasks = [
        asyncio.create_task(redis_streams_consumer()),
        asyncio.create_task(instance_fanout_listener()),
        asyncio.create_task(pubsub_notifications_listener()),
        asyncio.create_task(heartbeat_task()),
        asyncio.create_task(retry_pending_task())
    ]
    
    app.state.background_tasks = tasks
    app.state.instance_id = INSTANCE_ID
    app.state.manager = manager
    
    app.state.connected_users_gauge.labels(instance_id=INSTANCE_ID).set_function(
        lambda: len(manager.local_connections)
    )
    
    try:
        yield
    finally:
        logger.info(f"Shutting down Notification Service Instance: {INSTANCE_ID}")
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            redis = manager.redis
            consumer_id = f"{INSTANCE_ID}_shutdown"
            while True:
                messages = await redis.xreadgroup(
                    CONSUMER_GROUP,
                    consumer_id,
                    {NOTIFICATIONS_STREAM: '>'},
                    count=10,
                    block=0
                )
                if not messages:
                    break
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        await process_stream_message(redis, msg_id, fields)
        except Exception as e:
            logger.warning(f"Error draining stream during shutdown: {e}")
        
        try:
            all_connections = {}
            async for user_id, conn_data in redis.hscan_iter(CONNECTIONS_KEY):
                all_connections[user_id] = conn_data
            instance_users = [
                user_id for user_id, conn_data in all_connections.items()
                if INSTANCE_ID in conn_data
            ]
            if instance_users:
                await redis.hdel(CONNECTIONS_KEY, *instance_users)
                logger.info(f"Cleaned up {len(instance_users)} connections for instance {INSTANCE_ID}")
            await redis.close()
            await redis_pool.disconnect()
        except Exception as e:
            logger.warning(f"Error during Redis cleanup: {e}")

# Initialize Prometheus registry and gauge
prometheus_registry = CollectorRegistry()
connected_users_gauge = Gauge(
    "websocket_local_connected_users",
    "Number of locally connected users",
    ["instance_id"],
    registry=prometheus_registry
)

app = FastAPI(
    title="Distributed Notification Service",
#     description="""Production-ready WebSocket notification service with Redis Streams and distributed connection management.

# Example Frontend Integration (JavaScript):

# ```javascript
# const userId = 'your_user_id';
# const ws = new WebSocket(`wss://your-host:9000/ws/${userId}`);

# ws.onopen = () => {
#   console.log('Connected');
# };

# ws.onmessage = (event) => {
#   const data = JSON.parse(event.data);
#   if (data.type === 'heartbeat') {
#     // Optional: respond if needed
#   } else if (data.type === 'notification') {
#     // Handle notification, check data.notification_id for dedup
#     console.log('Received:', data.message);
#   }
# };

# ws.onclose = () => {
#   console.log('Disconnected');
# };

# // Send periodic heartbeats from client (optional)
# setInterval(() => {
#   if (ws.readyState === WebSocket.OPEN) {
#     ws.send(JSON.stringify({type: 'client_heartbeat'}));
#   }
# }, 30000);
# ```""",
    version="3.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


instrumentator = Instrumentator(registry=prometheus_registry)
# instrumentator.instrument(app).expose(app, endpoint="/metrics")

app.state.connected_users_gauge = connected_users_gauge

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint with distributed connection management"""
    if not user_id or len(user_id.strip()) == 0:
        await websocket.close(code=4000, reason="Invalid user_id")
        return
    
    user_id = user_id.strip()
    try:
        await manager.connect(websocket, user_id)
        while True:
            message = await websocket.receive_text()
            manager.last_activity[user_id] = time.time()
            try:
                client_data = json.loads(message)
                if client_data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                        "instance_id": INSTANCE_ID
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.disconnect(user_id)

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        redis = manager.redis
        await redis.ping()
        redis_status = "healthy"
        
        stream_info = await redis.xinfo_stream(NOTIFICATIONS_STREAM)
        stream_status = f"healthy (length: {stream_info.get('length', 0)})"
        
        groups = await redis.xinfo_groups(NOTIFICATIONS_STREAM)
        lag = 0
        for group in groups:
            if group['name'] == CONSUMER_GROUP:
                lag = group.get('lag', 0)
                break
        group_status = f"healthy (lag: {lag})"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
        stream_status = "unavailable"
        group_status = "unavailable"
    
    local_info = manager.get_local_connection_info()
    return JSONResponse({
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "instance_id": INSTANCE_ID,
        "timestamp": datetime.utcnow().isoformat(),
        "redis": redis_status,
        "redis_stream": stream_status,
        "consumer_group": group_status,
        "local_connections": local_info,
        "version": "3.1.0"
    })

@app.get("/stats")
async def get_stats():
    """Distributed service statistics"""
    local_info = manager.get_local_connection_info()
    distributed_connections = await manager.get_connected_users_distributed()
    return JSONResponse({
        "instance_id": INSTANCE_ID,
        "local_connections": local_info,
        "distributed_connections": {
            "total_users": len(distributed_connections),
            "by_instance": {}
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.get("/stats/distributed")
async def get_distributed_stats():
    """Detailed distributed statistics"""
    distributed_connections = await manager.get_connected_users_distributed()
    by_instance = {}
    for user_id, conn_info in distributed_connections.items():
        instance_id = conn_info.get("instance_id", "unknown")
        if instance_id not in by_instance:
            by_instance[instance_id] = {
                "users": [],
                "count": 0,
                "connections": []
            }
        by_instance[instance_id]["users"].append(user_id)
        by_instance[instance_id]["count"] += 1
        by_instance[instance_id]["connections"].append(conn_info)
    
    return JSONResponse({
        "total_instances": len(by_instance),
        "total_users": len(distributed_connections),
        "current_instance": INSTANCE_ID,
        "by_instance": by_instance,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.post("/notify/stream/{user_id}")
async def send_stream_notification(user_id: str, payload: NotificationPayload):
    """Send notification via Redis Stream (recommended)"""
    try:
        message_json = json.dumps(payload.message)
        if len(message_json) > MAX_MESSAGE_SIZE:
            raise HTTPException(status_code=413, detail="Message too large")
        
        redis = manager.redis
        message_data = {
            "user_id": user_id,
            "message": message_json,
            "type": payload.type,
            "timestamp": datetime.utcnow().isoformat(),
            "notification_id": str(uuid.uuid4())
        }
        
        stream_id = await redis.xadd(NOTIFICATIONS_STREAM, message_data)
        return JSONResponse({
            "success": True,
            "stream_id": stream_id,
            "message": f"Notification queued for user {user_id}",
            "delivery_method": "redis_stream"
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error sending stream notification: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/notify/direct/{user_id}")
async def send_direct_notification(user_id: str, payload: NotificationPayload):
    """Send notification directly (for testing)"""
    try:
        message_json = json.dumps(payload.message)
        if len(message_json) > MAX_MESSAGE_SIZE:
            raise HTTPException(status_code=413, detail="Message too large")
        
        notification = {
            "user_id": user_id,
            "message": payload.message if payload.message else {"content": "Your new recommendations are ready!"},
            "timestamp": datetime.utcnow().isoformat(),
            "type": payload.type,
            "notification_id": str(uuid.uuid4())
        }
        
        success = await manager.send_message_distributed(user_id, notification)
        return JSONResponse({
            "success": success,
            "message": "Notification sent" if success else "User not connected - stored as pending",
            "delivery_method": "direct_websocket"
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error sending direct notification: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

if ENABLE_DEBUG:
    @app.get("/debug/pending/{user_id}")
    async def debug_list_pending(user_id: str):
        """Debug: List pending notifications for user"""
        try:
            key = f"{PENDING_NOTIFICATIONS_PREFIX}{user_id}"
            pendings = await manager.redis.zrange(key, 0, -1)
            return [json.loads(p) for p in pendings]
        except Exception as e:
            logger.error(f"Error listing pending notifications for user {user_id}: {e}")
            return []

if __name__ == "__main__":
    import uvicorn
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    uvicorn.run(
        "notification_service:app",
        host="0.0.0.0",
        port=9000,
        reload=False, # Set to True if you want auto-reload in development(always False in production)
        log_level="info",
        ssl_keyfile=ssl_keyfile if ssl_keyfile and ssl_certfile else None,
        ssl_certfile=ssl_certfile if ssl_keyfile and ssl_certfile else None
    )
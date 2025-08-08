# Background Tasks & Caching Features

## New Features Added

### 1. Celery + RabbitMQ Background Tasks
- **Asynchronous Task Processing**: Long-running tasks are processed in the background
- **Task Queues**: Separate queues for different types of tasks (default, scraping, notifications)
- **Task Monitoring**: Real-time task status and progress tracking

### 2. Redis Caching
- **Fast Cache Storage**: High-performance caching for task results and frequently accessed data
- **TTL Support**: Automatic expiration of cached data
- **JSON Serialization**: Support for complex data structures

### 3. Push Notification Service
- **Background Notifications**: Asynchronous push notification delivery
- **Batch Notifications**: Send multiple notifications efficiently
- **Notification Tracking**: Monitor notification delivery status

## New Endpoints

### Background Tasks
- `POST /smart_application/tasks/background-task/` - Create generic background task
- `POST /smart_application/tasks/long-running-task/` - Create long-running task
- `POST /smart_application/tasks/background-scraping/` - Background web scraping
- `GET /smart_application/tasks/task-status/{task_id}` - Get task status
- `GET /smart_application/tasks/task-progress/{task_id}` - Get task progress

### Push Notifications
- `POST /smart_application/tasks/send-notification/` - Send single notification
- `POST /smart_application/tasks/batch-notifications/` - Send batch notifications

### Cache Management
- `GET /smart_application/tasks/cache/{key}` - Get cached value
- `DELETE /smart_application/tasks/cache/{key}` - Delete cached value

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Services with Docker Compose
```bash
docker-compose up -d
```

This will start:
- FastAPI application (port 8000)
- Celery worker
- Celery beat (scheduler)
- Redis cache (port 6379)
- RabbitMQ broker (port 5672) and management UI (port 15672)

### 3. Manual Setup (Alternative)
```bash
# Start Redis
redis-server

# Start RabbitMQ
rabbitmq-server

# Start Celery Worker
celery -A core.celery_app worker --loglevel=info

# Start Celery Beat (optional)
celery -A core.celery_app beat --loglevel=info

# Start FastAPI
uvicorn main:app --reload
```

## Usage Examples

### 1. Create Background Task
```bash
curl -X POST "http://localhost:8000/smart_application/tasks/background-task/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "data_processing",
    "data": {"input": "sample_data"}
  }'
```

### 2. Background Web Scraping
```bash
curl -X POST "http://localhost:8000/smart_application/tasks/background-scraping/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "openai_key": "your_openai_key",
    "model": "gpt-4o"
  }'
```

### 3. Send Push Notification
```bash
curl -X POST "http://localhost:8000/smart_application/tasks/send-notification/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "Task Completed",
    "message": "Your background task has finished",
    "data": {"task_id": "abc123"}
  }'
```

### 4. Check Task Status
```bash
curl -X GET "http://localhost:8000/smart_application/tasks/task-status/TASK_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Environment Variables
- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `RABBITMQ_HOST`: RabbitMQ server host (default: localhost)
- `RABBITMQ_PORT`: RabbitMQ server port (default: 5672)

### Task Queues
- `default`: General background tasks
- `scraping`: Web scraping tasks
- `notifications`: Push notification tasks

## Monitoring

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: guest
- Password: guest

### Redis Monitoring
```bash
redis-cli monitor
```

### Celery Monitoring
```bash
celery -A core.celery_app flower
```

## Performance Features

### 1. Task Prefetch
- Optimized worker prefetch settings for better performance
- Late acknowledgment for better reliability

### 2. Cache TTL
- Configurable cache expiration times
- Automatic cleanup of expired data

### 3. Batch Processing
- Efficient batch notification delivery
- Progress tracking for long-running operations

## Error Handling

- Comprehensive error handling for all background tasks
- Task retry mechanisms
- Detailed error logging and reporting
- Graceful degradation when services are unavailable
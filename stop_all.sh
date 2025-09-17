NOTIFICATION_PORT=9000
FASTAPI_PORT=3031
RABBITMQ_PORT=5672
REDIS_PORT=6379

echo "Stopping Celery Beat..."
pkill -f "celery -A workers.celery_app beat"

echo "Stopping Celery Worker..."
pkill -f "python.*celery"

echo "Stopping Notification Service (port $NOTIFICATION_PORT)..."
lsof -ti:$NOTIFICATION_PORT | xargs kill -9 2>/dev/null

echo "Stopping FastAPI Service (port $FASTAPI_PORT)..."
lsof -ti:$FASTAPI_PORT | xargs kill -9 2>/dev/null

echo "Stopping RabbitMQ on port $RABBITMQ_PORT..."
lsof -ti:$RABBITMQ_PORT | xargs kill -9

echo "Stopping Redis on port $REDIS_PORT..."
if lsof -ti:$REDIS_PORT > /dev/null 2>&1; then
    PID=$(lsof -ti:$REDIS_PORT | head -1)
    kill -9 $PID
    echo "✅ Redis (PID: $PID) stopped"
else
    echo "❌ Redis not running"
fi

echo "All services stopped!"
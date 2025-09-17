#!/bin/bash

# Your specific ports
NOTIFICATION_PORT=9000
FASTAPI_PORT=3031
RABBITMQ_PORT=5672
REDIS_PORT=6379

echo "=== Service Status Check ==="
echo ""

# Check Redis
echo "Redis (port $REDIS_PORT):"
if lsof -ti:$REDIS_PORT > /dev/null 2>&1; then
    echo "✅ RUNNING - PID: $(lsof -ti:$REDIS_PORT | head -1)"
else
    echo "❌ STOPPED"
fi
echo ""

# Check RabbitMQ
echo "RabbitMQ (port $RABBITMQ_PORT):"
if lsof -ti:$RABBITMQ_PORT > /dev/null 2>&1; then
    echo "✅ RUNNING - PID: $(lsof -ti:$RABBITMQ_PORT | head -1)"
    # Check if RabbitMQ is actually responding with timeout
    timeout 2s /usr/local/Cellar/rabbitmq/4.1.3/sbin/rabbitmqctl status >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ RabbitMQ responding properly"
    else
        echo "   ⚠️  RabbitMQ port open but slow to respond"
    fi
else
    echo "❌ STOPPED"
fi
echo ""

# Check Celery Worker
echo "Celery Worker:"
if pgrep -f "celery.*worker.*user_processing_alt" > /dev/null; then
    echo "✅ RUNNING - PID: $(pgrep -f "celery.*worker.*user_processing_alt")"
else
    echo "❌ STOPPED"
fi
echo ""

# Check Celery Beat
echo "Celery Beat:"
if pgrep -f "celery.*beat" > /dev/null; then
    echo "✅ RUNNING - PID: $(pgrep -f "celery.*beat")"
else
    echo "❌ STOPPED"
fi
echo ""

# Check Notification Service
echo "Notification Service (port $NOTIFICATION_PORT):"
if lsof -ti:$NOTIFICATION_PORT > /dev/null 2>&1; then
    echo "✅ RUNNING - PID: $(lsof -ti:$NOTIFICATION_PORT | head -1)"
else
    echo "❌ STOPPED"
fi
echo ""

# Check FastAPI Service
echo "FastAPI Service (port $FASTAPI_PORT):"
if lsof -ti:$FASTAPI_PORT > /dev/null 2>&1; then
    echo "✅ RUNNING - PID: $(lsof -ti:$FASTAPI_PORT | head -1)"
else
    echo "❌ STOPPED"
fi
echo ""

echo "=== Status Check Complete ==="
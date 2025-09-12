#!/bin/bash

echo "Starting all services..."
echo "confirm current directory is /Users/apple/Downloads/GenAIforTravel"
cd /Users/apple/Downloads/GenAIforTravel
pwd

echo "Starting Redis on port 6379..."
redis-server --port 6379 --daemonize yes

echo "Starting RabbitMQ on port 5672..."
# Stop any existing RabbitMQ
/usr/local/Cellar/rabbitmq/4.1.3/sbin/rabbitmqctl stop 2>/dev/null || true

# Start with custom port using full path
RABBITMQ_NODE_PORT=5672 /usr/local/Cellar/rabbitmq/4.1.3/sbin/rabbitmq-server -detached
sleep 5

sleep 3

echo "Starting Celery Worker..."
export PYTHONPATH=$(pwd)
cd app  # Change to app directory where workers module is located
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672// \
CELERY_RESULT_BACKEND=redis://localhost:6379/0 \
celery -A workers.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=user_processing_alt \
  --hostname=worker_alt@%h \
  --prefetch-multiplier=1 \
  --without-gossip \
  --without-mingle \
  --without-heartbeat \
  --pool=prefork \
  --max-tasks-per-child=1000 \
  --time-limit=300 \
  --soft-time-limit=240 \
  --autoscale=1,10 \
  --max-memory-per-child=200000 &
cd ..  # Go back to root

sleep 2

echo "Starting Celery Beat..."
export PYTHONPATH=$(pwd)
cd app  # Change to app directory where workers module is located
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672// \
CELERY_RESULT_BACKEND=redis://localhost:6379/0 \
celery -A workers.celery_app beat \
  --loglevel=warning \
  --scheduler=celery.beat:PersistentScheduler &
cd ..  # Go back to root

sleep 2

echo "Starting Notification Service..."
cd /Users/apple/Downloads/GenAIforTravel
python notification_service.py &

sleep 2

echo "Starting FastAPI Service..."
cd /Users/apple/Downloads/GenAIforTravel
python app/main.py &

echo "All services started! Use './stop_all.sh' to stop them."
echo "Check status with: './status_all.sh'"
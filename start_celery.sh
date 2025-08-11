#!/bin/bash

# StuckAI for Travel - Celery Startup Script
# This script helps you start Celery workers and beat scheduler

echo "🚀 StuckAI for Travel - Celery Startup"
echo "======================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment is not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment is active"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "Please start Redis: sudo systemctl start redis-server"
    exit 1
fi

echo "✅ Redis is running"

# Check if RabbitMQ is running
if ! sudo systemctl is-active --quiet rabbitmq-server; then
    echo "❌ RabbitMQ is not running!"
    echo "Please start RabbitMQ: sudo systemctl start rabbitmq-server"
    exit 1
fi

echo "✅ RabbitMQ is running"

echo ""
echo "📋 Available Celery Commands:"
echo "============================="
echo ""
echo "1. 🐛 Start Celery Worker (Development)"
echo "   celery -A app.tasks.celery_worker worker --loglevel=info"
echo ""
echo "2. 🚀 Start Celery Worker (Production)"
echo "   celery -A app.tasks.celery_worker worker --loglevel=info --concurrency=4"
echo ""
echo "3. ⏰ Start Celery Beat Scheduler"
echo "   celery -A app.tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=info"
echo ""
echo "4. 🔄 Start Celery Beat with Auto-restart (Development)"
echo "   watchmedo auto-restart -d . -p '*.py' -R -- celery -A app.tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=INFO"
echo ""
echo "5. 🎯 Start Both Worker and Beat (Separate terminals)"
echo "   Terminal 1: celery -A app.tasks.celery_worker worker --loglevel=info"
echo "   Terminal 2: celery -A app.tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=info"
echo ""

# Function to start Celery worker
start_worker() {
    echo "🐛 Starting Celery Worker..."
    celery -A app.tasks.celery_worker worker --loglevel=info
}

# Function to start Celery beat
start_beat() {
    echo "⏰ Starting Celery Beat Scheduler..."
    celery -A app.tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=info
}

# Function to start Celery beat with auto-restart
start_beat_auto() {
    echo "🔄 Starting Celery Beat with Auto-restart..."
    watchmedo auto-restart -d . -p '*.py' -R -- celery -A app.tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=INFO
}

# Interactive menu
echo "Select an option:"
echo "1) Start Celery Worker"
echo "2) Start Celery Beat Scheduler"
echo "3) Start Celery Beat with Auto-restart"
echo "4) Show commands only"
echo "5) Exit"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        start_worker
        ;;
    2)
        start_beat
        ;;
    3)
        start_beat_auto
        ;;
    4)
        echo "Commands saved! You can run them manually."
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac 
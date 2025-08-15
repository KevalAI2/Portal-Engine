#!/bin/bash

# Content Recommendation System Startup Script
# This script starts all required services for the content recommendation system

echo "🚀 Starting Content Recommendation System..."
echo "=============================================="

# Function to check if a service is running and handle existing process
check_service() {
    local service_name=$1
    local port=$2
    local pid_file="pids/${service_name}.pid"
    
    # Check if PID file exists
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "⚠️  $service_name is already running with PID $pid"
            read -p "Do you want to stop it and start a new instance? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "🛑 Stopping existing $service_name..."
                kill $pid
                rm "$pid_file"
                sleep 2
            else
                echo "Exiting..."
                exit 1
            fi
        else
            echo "🧹 Cleaning up stale PID file..."
            rm "$pid_file"
        fi
    fi
    
    if sudo lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local running_pid=$(sudo lsof -Pi :$port -sTCP:LISTEN -t)
        echo "⚠️  Port $port is in use by PID $running_pid"
        read -p "Do you want to stop it and start a new instance? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🛑 Stopping process on port $port..."
            kill $running_pid
            sleep 2
        else
            echo "Exiting..."
            exit 1
        fi
    fi
    
    return 0
}

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    
    echo "Starting $service_name..."
    $command > logs/${service_name}.log 2>&1 &
    local pid=$!
    echo $pid > pids/${service_name}.pid
    echo "✅ Started $service_name (PID: $pid)"
    local pid=$!
    echo $pid > pids/${service_name}.pid
    echo "✅ $service_name started with PID $pid"
    
    # Wait a bit for service to start
    sleep 2
    
    # Check if service is running
    if check_service $service_name $port; then
        echo "✅ $service_name is ready"
    else
        echo "❌ Failed to start $service_name"
        return 1
    fi
}

# Create necessary directories
mkdir -p logs pids

echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3 found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check PostgreSQL
if ! check_service "PostgreSQL" 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   You can start it with: sudo systemctl start postgresql"
    exit 1
fi

# Check Redis
if ! check_service "Redis" 6379; then
    echo "🔄 Starting Redis..."
    redis-server > logs/redis.log 2>&1 &
    echo $! > pids/redis.pid
    sleep 2
    if check_service "Redis" 6379; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
fi

# Check RabbitMQ
if ! check_service "RabbitMQ" 5672; then
    echo "🔄 Starting RabbitMQ..."
    # Try to start RabbitMQ (this might need sudo on some systems)
    if command -v rabbitmq-server &> /dev/null; then
        rabbitmq-server > logs/rabbitmq.log 2>&1 &
        echo $! > pids/rabbitmq.pid
        sleep 5
        if check_service "RabbitMQ" 5672; then
            echo "✅ RabbitMQ started successfully"
        else
            echo "❌ Failed to start RabbitMQ"
            echo "   You may need to install RabbitMQ or start it manually"
            exit 1
        fi
    else
        echo "❌ RabbitMQ is not installed"
        echo "   Install it with: sudo apt-get install rabbitmq-server"
        exit 1
    fi
fi

# Create database tables
echo "🗄️  Setting up database..."
python -c "from app.core.database import create_tables; create_tables()"
if [ $? -eq 0 ]; then
    echo "✅ Database tables created"
else
    echo "❌ Failed to create database tables"
    exit 1
fi

# Start Celery worker
echo "🔄 Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > pids/celery.pid
sleep 3

# Check if Celery started successfully
if kill -0 $CELERY_PID 2>/dev/null; then
    echo "✅ Celery worker started with PID $CELERY_PID"
else
    echo "❌ Failed to start Celery worker"
    exit 1
fi

# Start FastAPI server
echo "🔄 Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > pids/fastapi.pid
sleep 3

# Check if FastAPI started successfully
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "✅ FastAPI server started with PID $FASTAPI_PID"
else
    echo "❌ Failed to start FastAPI server"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

if check_service "FastAPI" 8000; then
    echo "✅ FastAPI server is responding"
else
    echo "❌ FastAPI server is not responding"
    exit 1
fi

echo ""
echo "🎉 Content Recommendation System is now running!"
echo "=============================================="
echo "📊 Services Status:"
echo "   - FastAPI Server: http://localhost:8000 (PID: $FASTAPI_PID)"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo "   - RabbitMQ: localhost:5672"
echo "   - Celery Worker: Running (PID: $CELERY_PID)"
echo ""
echo "🧪 Test the API:"
echo "   python test_content_api.py"
echo ""
echo "📝 Logs are available in the 'logs' directory"
echo "🛑 To stop all services, run: ./stop_content_system.sh"
echo ""
echo "💡 Services are running in the background."
echo "   Use 'tail -f logs/*.log' to monitor logs"
echo "   Use './check_services.sh' to check status"
echo ""
echo "Happy coding! 🚀"

# Keep the script running and monitor processes
echo ""
echo "🔍 Monitoring services... (Press Ctrl+C to stop)"
echo "=============================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ -f "pids/fastapi.pid" ]; then
        FASTAPI_PID=$(cat pids/fastapi.pid)
        if kill -0 $FASTAPI_PID 2>/dev/null; then
            kill $FASTAPI_PID
            echo "✅ Stopped FastAPI server"
        fi
    fi
    
    if [ -f "pids/celery.pid" ]; then
        CELERY_PID=$(cat pids/celery.pid)
        if kill -0 $CELERY_PID 2>/dev/null; then
            kill $CELERY_PID
            echo "✅ Stopped Celery worker"
        fi
    fi
    
    echo "🎉 All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Monitor processes
while true; do
    # Check if processes are still running
    if [ -f "pids/fastapi.pid" ]; then
        FASTAPI_PID=$(cat pids/fastapi.pid)
        if ! kill -0 $FASTAPI_PID 2>/dev/null; then
            echo "❌ FastAPI server stopped unexpectedly"
            break
        fi
    fi
    
    if [ -f "pids/celery.pid" ]; then
        CELERY_PID=$(cat pids/celery.pid)
        if ! kill -0 $CELERY_PID 2>/dev/null; then
            echo "❌ Celery worker stopped unexpectedly"
            break
        fi
    fi
    
    # Show status every 30 seconds
    sleep 30
    echo "✅ Services still running... (FastAPI: $FASTAPI_PID, Celery: $CELERY_PID)"
done

# If we get here, something went wrong
echo "❌ One or more services stopped unexpectedly"
cleanup 
#!/bin/bash

# StuckAI for Travel - Content Recommendation System
# Daemon Startup Script (runs in background and stays alive)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Content Recommendation System (Daemon Mode)...${NC}"
echo "=============================================="

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if sudo lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${GREEN}✅ $service_name is already running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not running on port $port${NC}"
        return 1
    fi
}

# Create necessary directories
mkdir -p logs pids

echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

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
    echo -e "${RED}❌ PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    echo "   You can start it with: sudo systemctl start postgresql"
    exit 1
fi

# Check Redis
if ! check_service "Redis" 6379; then
    echo -e "${YELLOW}🔄 Starting Redis...${NC}"
    redis-server > logs/redis.log 2>&1 &
    echo $! > pids/redis.pid
    sleep 2
    if check_service "Redis" 6379; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
fi

# Check RabbitMQ
if ! check_service "RabbitMQ" 5672; then
    echo -e "${YELLOW}🔄 Starting RabbitMQ...${NC}"
    if command -v rabbitmq-server &> /dev/null; then
        rabbitmq-server > logs/rabbitmq.log 2>&1 &
        echo $! > pids/rabbitmq.pid
        sleep 5
        if check_service "RabbitMQ" 5672; then
            echo -e "${GREEN}✅ RabbitMQ started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start RabbitMQ${NC}"
            echo "   You may need to install RabbitMQ or start it manually"
            exit 1
        fi
    else
        echo -e "${RED}❌ RabbitMQ is not installed${NC}"
        echo "   Install it with: sudo apt-get install rabbitmq-server"
        exit 1
    fi
fi

# Create database tables
echo "🗄️  Setting up database..."
python -c "from app.core.database import create_tables; create_tables()"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database tables created${NC}"
else
    echo -e "${RED}❌ Failed to create database tables${NC}"
    exit 1
fi

# Start Celery worker
echo -e "${BLUE}🔍 Starting Celery worker...${NC}"
celery -A app.tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > pids/celery.pid
sleep 3

# Check if Celery started successfully
if kill -0 $CELERY_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Celery worker started with PID $CELERY_PID${NC}"
else
    echo -e "${RED}❌ Failed to start Celery worker${NC}"
    exit 1
fi

# Start FastAPI server
echo -e "${BLUE}🚀 Starting FastAPI server...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > pids/fastapi.pid
sleep 3

# Check if FastAPI started successfully
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${GREEN}✅ FastAPI server started with PID $FASTAPI_PID${NC}"
else
    echo -e "${RED}❌ Failed to start FastAPI server${NC}"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

if check_service "FastAPI" 8000; then
    echo -e "${GREEN}✅ FastAPI server is responding${NC}"
else
    echo -e "${RED}❌ FastAPI server is not responding${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Content Recommendation System is now running!${NC}"
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
echo -e "${YELLOW}💡 Services are running in the background.${NC}"
echo "   Use 'tail -f logs/*.log' to monitor logs"
echo "   Use './check_services.sh' to check status"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

# Keep the script running and monitor processes
echo ""
echo -e "${BLUE}🔍 Monitoring services... (Press Ctrl+C to stop)${NC}"
echo "=============================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
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
    
    if [ -f "pids/redis.pid" ]; then
        REDIS_PID=$(cat pids/redis.pid)
        if kill -0 $REDIS_PID 2>/dev/null; then
            kill $REDIS_PID
            echo "✅ Stopped Redis"
        fi
    fi
    
    if [ -f "pids/rabbitmq.pid" ]; then
        RABBITMQ_PID=$(cat pids/rabbitmq.pid)
        if kill -0 $RABBITMQ_PID 2>/dev/null; then
            kill $RABBITMQ_PID
            echo "✅ Stopped RabbitMQ"
        fi
    fi
    
    echo -e "${GREEN}🎉 All services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Monitor processes and keep alive
while true; do
    # Check if processes are still running
    if [ -f "pids/fastapi.pid" ]; then
        FASTAPI_PID=$(cat pids/fastapi.pid)
        if ! kill -0 $FASTAPI_PID 2>/dev/null; then
            echo -e "${RED}❌ FastAPI server stopped unexpectedly${NC}"
            break
        fi
    fi
    
    if [ -f "pids/celery.pid" ]; then
        CELERY_PID=$(cat pids/celery.pid)
        if ! kill -0 $CELERY_PID 2>/dev/null; then
            echo -e "${RED}❌ Celery worker stopped unexpectedly${NC}"
            break
        fi
    fi
    
    # Show status every 60 seconds
    sleep 60
    echo -e "${GREEN}✅ Services still running... (FastAPI: $FASTAPI_PID, Celery: $CELERY_PID)${NC}"
done

# If we get here, something went wrong
echo -e "${RED}❌ One or more services stopped unexpectedly${NC}"
cleanup 
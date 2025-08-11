#!/bin/bash

# StuckAI for Travel - Content Recommendation System
# Foreground Startup Script (for debugging and development)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Content Recommendation System (Foreground Mode)...${NC}"
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

echo ""
echo -e "${GREEN}🎉 Prerequisites ready!${NC}"
echo "=============================================="
echo "📊 Services Status:"
echo "   - PostgreSQL: localhost:5432 ✅"
echo "   - Redis: localhost:6379 ✅"
echo "   - RabbitMQ: localhost:5672 ✅"
echo ""
echo -e "${YELLOW}💡 Starting services in foreground mode...${NC}"
echo "   This will keep the terminal open and show live logs."
echo "   Press Ctrl+C to stop all services."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    
    # Stop background services
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

echo -e "${BLUE}🔍 Starting Celery worker in background...${NC}"
celery -A app.tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > pids/celery.pid
echo -e "${GREEN}✅ Celery worker started with PID $CELERY_PID${NC}"

echo ""
echo -e "${BLUE}🚀 Starting FastAPI server in foreground...${NC}"
echo "   API will be available at: http://localhost:8000"
echo "   Documentation at: http://localhost:8000/docs"
echo "   Health check at: http://localhost:8000/smart_recommender/content/health"
echo ""
echo -e "${YELLOW}💡 FastAPI logs will appear below. Press Ctrl+C to stop.${NC}"
echo "=============================================="

# Start FastAPI in foreground (this will keep the script running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 
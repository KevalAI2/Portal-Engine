#!/bin/bash

# StuckAI for Travel - Complete System Startup Script
# This script starts all required services in the background and exits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting StuckAI for Travel - Complete System${NC}"
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

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    local pid_file="pids/${service_name}.pid"
    
    echo -e "${BLUE}🔄 Starting $service_name...${NC}"
    
    # Kill existing process if running
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if kill -0 $old_pid 2>/dev/null; then
            echo "   Stopping existing $service_name process..."
            kill $old_pid
            sleep 2
        fi
    fi
    
    # Start new process
    nohup $command > logs/${service_name}.log 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait for service to start
    echo "   Waiting for $service_name to start..."
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if check_service $service_name $port >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    echo -e "${RED}❌ Failed to start $service_name${NC}"
    return 1
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
pip install -r requirements.txt > logs/pip_install.log 2>&1

# Check PostgreSQL
if ! check_service "PostgreSQL" 5432; then
    echo -e "${RED}❌ PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    echo "   You can start it with: sudo systemctl start postgresql"
    exit 1
fi

# Start Redis if not running
if ! check_service "Redis" 6379; then
    echo -e "${YELLOW}🔄 Starting Redis...${NC}"
    if command -v redis-server &> /dev/null; then
        nohup redis-server > logs/redis.log 2>&1 &
        echo $! > pids/redis.pid
        sleep 3
        if check_service "Redis" 6379; then
            echo -e "${GREEN}✅ Redis started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Redis${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Redis is not installed${NC}"
        echo "   Install it with: sudo apt-get install redis-server"
        exit 1
    fi
fi

# Start RabbitMQ if not running
if ! check_service "RabbitMQ" 5672; then
    echo -e "${YELLOW}🔄 Starting RabbitMQ...${NC}"
    if command -v rabbitmq-server &> /dev/null; then
        nohup rabbitmq-server > logs/rabbitmq.log 2>&1 &
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
python -c "from app.core.database import create_tables; create_tables()" > logs/db_setup.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database tables created${NC}"
else
    echo -e "${RED}❌ Failed to create database tables${NC}"
    exit 1
fi

# Start Celery worker
echo -e "${BLUE}🔍 Starting Celery worker...${NC}"
nohup celery -A app.tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
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

# Check if port 8000 is already in use and kill existing processes
if sudo lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port 8000 is in use, killing existing processes..."
    sudo lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9
    sleep 2
fi

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/fastapi.log 2>&1 &
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

# Final status check
echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
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
echo "🔍 To check status, run: ./check_services.sh"
echo ""
echo -e "${YELLOW}💡 All services are running in the background.${NC}"
echo "   The script will now exit. Services will continue running."
echo "   Use 'tail -f logs/*.log' to monitor logs"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

# Exit successfully - services continue running in background
exit 0 
#!/bin/bash

# StuckAI for Travel - Service Check Script
# This script checks the status of all required services

echo "🔍 StuckAI for Travel - Service Status Check"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local description=$3
    
    echo -n "Checking $service_name... "
    
    if sudo lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        echo "   Port: $port"
        echo "   Description: $description"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        echo "   Port: $port"
        echo "   Description: $description"
        return 1
    fi
}

# Function to check system service
check_system_service() {
    local service_name=$1
    local port=$2
    local description=$3
    
    echo -n "Checking $service_name... "
    
    if systemctl is-active --quiet $service_name; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        echo "   Port: $port"
        echo "   Description: $description"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        echo "   Port: $port"
        echo "   Description: $description"
        return 1
    fi
}

# Function to check database connection
check_database() {
    echo -n "Checking PostgreSQL database... "
    
    if command -v psql &> /dev/null; then
        # Try to connect to database
        if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ CONNECTED${NC}"
            echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
            echo "   Database: $POSTGRES_DB"
            return 0
        else
            echo -e "${RED}❌ CONNECTION FAILED${NC}"
            echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
            echo "   Database: $POSTGRES_DB"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  PSQL NOT FOUND${NC}"
        return 1
    fi
}

# Function to check Redis connection
check_redis() {
    echo -n "Checking Redis connection... "
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping >/dev/null 2>&1; then
            echo -e "${GREEN}✅ CONNECTED${NC}"
            echo "   Host: localhost:6379"
            
            # Check Redis info
            redis_info=$(redis-cli info server | grep "redis_version\|uptime_in_seconds\|connected_clients" | head -3)
            echo "   Info: $redis_info"
            return 0
        else
            echo -e "${RED}❌ CONNECTION FAILED${NC}"
            echo "   Host: localhost:6379"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  REDIS-CLI NOT FOUND${NC}"
        return 1
    fi
}

# Function to check RabbitMQ connection
check_rabbitmq() {
    echo -n "Checking RabbitMQ connection... "
    
    if command -v rabbitmqctl &> /dev/null; then
        if rabbitmqctl status >/dev/null 2>&1; then
            echo -e "${GREEN}✅ RUNNING${NC}"
            echo "   Host: localhost:5672"
            
            # Check management interface
            if curl -s http://localhost:15672 >/dev/null 2>&1; then
                echo "   Management: http://localhost:15672"
            fi
            return 0
        else
            echo -e "${RED}❌ NOT RUNNING${NC}"
            echo "   Host: localhost:5672"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  RABBITMQ-CTL NOT FOUND${NC}"
        return 1
    fi
}

# Function to check Python environment
check_python() {
    echo -n "Checking Python environment... "
    
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        echo -e "${GREEN}✅ FOUND${NC}"
        echo "   Version: $python_version"
        
        # Check if virtual environment is active
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            echo -e "   ${GREEN}Virtual Environment: ACTIVE${NC}"
            echo "   Path: $VIRTUAL_ENV"
        else
            echo -e "   ${YELLOW}Virtual Environment: NOT ACTIVE${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        return 1
    fi
}

# Function to check required Python packages
check_python_packages() {
    echo -n "Checking Python packages... "
    
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        # Check key packages
        packages=("fastapi" "sqlalchemy" "redis" "celery" "psycopg2")
        missing_packages=()
        
        for package in "${packages[@]}"; do
            if ! python3 -c "import $package" >/dev/null 2>&1; then
                missing_packages+=("$package")
            fi
        done
        
        if [ ${#missing_packages[@]} -eq 0 ]; then
            echo -e "${GREEN}✅ ALL REQUIRED PACKAGES INSTALLED${NC}"
        else
            echo -e "${RED}❌ MISSING PACKAGES${NC}"
            echo "   Missing: ${missing_packages[*]}"
            echo "   Run: pip install -r requirements.txt"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  VIRTUAL ENVIRONMENT NOT ACTIVE${NC}"
        return 1
    fi
}

# Function to check application status
check_application() {
    echo -n "Checking FastAPI application... "
    
    if curl -s http://localhost:8000/smart_recommender/content/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        echo "   URL: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        echo "   URL: http://localhost:8000"
        return 1
    fi
}

# Function to check Celery workers
check_celery() {
    echo -n "Checking Celery workers... "
    
    if command -v celery &> /dev/null; then
        # Try to inspect active workers
        if celery -A app.tasks.celery_app inspect active >/dev/null 2>&1; then
            echo -e "${GREEN}✅ WORKERS ACTIVE${NC}"
            
            # Get worker count
            worker_count=$(celery -A app.tasks.celery_app inspect active | grep -c "celery@" || echo "0")
            echo "   Active Workers: $worker_count"
            return 0
        else
            echo -e "${RED}❌ NO WORKERS ACTIVE${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  CELERY NOT FOUND${NC}"
        return 1
    fi
}

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  .env file not found, using defaults${NC}"
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=""
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_DB=smart_recommender
fi

echo ""
echo "📋 System Services"
echo "------------------"

# Check system services
check_system_service "postgresql" "5432" "PostgreSQL Database Server"
check_system_service "redis-server" "6379" "Redis Cache Server"
check_system_service "rabbitmq-server" "5672" "RabbitMQ Message Broker"

echo ""
echo "🔌 Network Services"
echo "-------------------"

# Check network services
check_service "FastAPI" "8000" "FastAPI Application Server"
check_service "PostgreSQL" "5432" "PostgreSQL Database"
check_service "Redis" "6379" "Redis Cache"
check_service "RabbitMQ" "5672" "RabbitMQ Message Broker"
check_service "RabbitMQ Management" "15672" "RabbitMQ Management Interface"

echo ""
echo "🐍 Python Environment"
echo "--------------------"

# Check Python environment
check_python
check_python_packages

echo ""
echo "🗄️  Database Connections"
echo "------------------------"

# Check database connections
check_database
check_redis
check_rabbitmq

echo ""
echo "🚀 Application Status"
echo "--------------------"

# Check application status
check_application
check_celery

echo ""
echo "📊 Summary"
echo "----------"

# Count services
total_services=0
running_services=0

# Count system services
for service in "postgresql" "redis-server" "rabbitmq-server"; do
    total_services=$((total_services + 1))
    if systemctl is-active --quiet $service; then
        running_services=$((running_services + 1))
    fi
done

# Count network services
for port in "8000" "5432" "6379" "5672"; do
    total_services=$((total_services + 1))
    if sudo lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        running_services=$((running_services + 1))
    fi
done

echo "Services Running: $running_services/$total_services"

if [ $running_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test the API: python test_content_api.py"
    echo "2. View API docs: http://localhost:8000/docs"
    echo "3. Monitor logs: tail -f logs/*.log"
else
    echo -e "${RED}⚠️  Some services are not running${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check service logs: sudo journalctl -u <service-name>"
    echo "2. Start services: ./start_content_system.sh"
    echo "3. Check configuration: cat .env"
fi

echo ""
echo "🔧 Quick Commands"
echo "-----------------"
echo "Start all services: ./start_content_system.sh"
echo "Stop all services:  ./stop_content_system.sh"
echo "View API docs:      http://localhost:8000/docs"
echo "Test API:           python test_content_api.py"
echo "Check logs:         tail -f logs/*.log"

echo ""
echo "=============================================="
echo "Service check completed! 🚀" 
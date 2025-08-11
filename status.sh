#!/bin/bash

# Quick status check for all services
echo "🔍 StuckAI for Travel - Quick Status"
echo "===================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check each service
services=(
    "FastAPI:8000"
    "PostgreSQL:5432"
    "Redis:6379"
    "RabbitMQ:5672"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if sudo lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
    else
        echo -e "${RED}❌ $name${NC}"
    fi
done

# Check Celery worker
if [ -f "pids/celery.pid" ]; then
    CELERY_PID=$(cat pids/celery.pid)
    if kill -0 $CELERY_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Celery Worker (PID: $CELERY_PID)${NC}"
    else
        echo -e "${RED}❌ Celery Worker${NC}"
    fi
else
    echo -e "${RED}❌ Celery Worker${NC}"
fi

echo ""
echo "📝 For detailed status: ./check_services.sh"
echo "📊 For logs: tail -f logs/*.log" 
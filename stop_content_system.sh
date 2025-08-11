#!/bin/bash

# Content Recommendation System Stop Script
# This script stops all services for the content recommendation system

echo "🛑 Stopping Content Recommendation System..."
echo "=============================================="

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="pids/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 Stopping $service_name (PID: $pid)..."
            kill $pid
            sleep 2
            
            # Check if process is still running
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚠️  $service_name is still running, force killing..."
                kill -9 $pid
                sleep 1
            fi
            
            if ! ps -p $pid > /dev/null 2>&1; then
                echo "✅ $service_name stopped"
                rm -f "$pid_file"
            else
                echo "❌ Failed to stop $service_name"
            fi
        else
            echo "ℹ️  $service_name is not running"
            rm -f "$pid_file"
        fi
    else
        echo "ℹ️  No PID file found for $service_name"
    fi
}

# Stop services in reverse order
echo "🔄 Stopping FastAPI server..."
stop_service "fastapi"

echo "🔄 Stopping Celery worker..."
stop_service "celery"

echo "🔄 Stopping RabbitMQ..."
stop_service "rabbitmq"

echo "🔄 Stopping Redis..."
stop_service "redis"

# Clean up PID files
echo "🧹 Cleaning up..."
rm -f pids/*.pid

echo ""
echo "✅ All services stopped!"
echo "=============================================="
echo "📝 Logs are still available in the 'logs' directory"
echo "🚀 To start again, run: ./start_content_system.sh" 
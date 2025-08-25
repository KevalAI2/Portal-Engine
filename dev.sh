#!/bin/bash

# Portal Engine Development Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    ! nc -z localhost $1 2>/dev/null
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to start development environment
start_dev() {
    print_status "Starting Portal Engine in development mode..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    # Check if Redis is running
    if ! command_exists redis-server; then
        print_warning "Redis not found. Please install Redis:"
        print_status "Ubuntu/Debian: sudo apt-get install redis-server"
        print_status "macOS: brew install redis"
        exit 1
    elif port_available 6379; then
        print_status "Starting Redis..."
        redis-server --daemonize yes
        sleep 2
    else
        print_status "Redis is already running on port 6379"
    fi
    
    # Check if RabbitMQ is running
    if ! command_exists rabbitmq-server; then
        print_warning "RabbitMQ not found. Please install RabbitMQ:"
        print_status "Ubuntu/Debian: sudo apt-get install rabbitmq-server"
        print_status "macOS: brew install rabbitmq"
        exit 1
    elif port_available 5672; then
        print_status "Starting RabbitMQ..."
        rabbitmq-server --daemonize
        sleep 5
    else
        print_status "RabbitMQ is already running on port 5672"
    fi
    
    # Wait for services to be ready
    wait_for_service 6379 "Redis"
    wait_for_service 5672 "RabbitMQ"
    
    # Start Celery worker in background
    print_status "Starting Celery worker..."
    celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 &
    CELERY_PID=$!
    
    # Start Celery beat in background (optional)
    print_status "Starting Celery beat scheduler..."
    celery -A app.workers.celery_app beat --loglevel=info &
    BEAT_PID=$!
    
    # Start FastAPI application
    print_status "Starting FastAPI application..."
    print_success "Portal Engine is starting..."
    print_status "API will be available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/api/v1/health/"
    
    # Trap to cleanup background processes
    trap "echo 'Shutting down...'; kill $CELERY_PID $BEAT_PID 2>/dev/null; exit" INT TERM
    
    # Start the API
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Install test dependencies if needed
    pip install -r requirements.txt
    
    # Run tests
    pytest -v --cov=app --cov-report=term-missing
}

# Function to show help
show_help() {
    echo "Portal Engine Development Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     Start in development mode (local services)"
    echo "  test    Run tests"
    echo "  help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Start development environment"
    echo "  $0 test     # Run test suite"
}

# Main script logic
case "${1:-help}" in
    dev)
        start_dev
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

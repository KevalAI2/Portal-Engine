# Portal Engine

A production-grade, modular recommendation system built with FastAPI, Celery, RabbitMQ, and Redis. The Portal Engine provides personalized recommendations by integrating with external services and using LLM-powered prompt generation.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │   Celery Worker │    │   Redis Cache   │
│                 │    │                 │    │                 │
│ • REST Endpoints│    │ • Background    │    │ • Store Results │
│ • Health Checks │    │   Tasks         │    │ • Cache TTL     │
│ • Request Logging│   │ • Task Status   │    │ • Namespaced    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  RabbitMQ       │    │  External       │    │  Prompt Builder │
│  Message Broker │    │  Services       │    │                 │
│                 │    │                 │    │                 │
│ • Task Queue    │    │ • User Profile  │    │ • Dynamic       │
│ • Task Results  │    │ • LIE (Location)│    │   Prompts       │
│ • Task Status   │    │ • CIS (Customer)│    │ • Context       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

- **Modular Architecture**: Clean separation of concerns with layered architecture
- **Background Processing**: Celery workers for async recommendation generation
- **Caching**: Redis-based caching with TTL and namespaced keys
- **Dynamic Prompts**: LLM-powered prompt generation based on user context
- **Health Monitoring**: Comprehensive health checks for all services
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Real-time Notifications**: WebSocket-based distributed notification service with Redis Streams and Pub/Sub
- **Testing**: Comprehensive async-aware test suite with mocking
- **Local Development**: Easy setup for local development
- **Production Ready**: Structured logging, error handling, and monitoring

## 📋 Prerequisites

- Python 3.12+
- Redis
- RabbitMQ

## 🛠️ Installation

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up external services**
   - Start Redis: `redis-server`
   - Start RabbitMQ: `rabbitmq-server`

4. **Set up external services**
   - Start Redis: `redis-server`
   - Start RabbitMQ: `rabbitmq-server`

5. **Run the application**
   ```bash
   # Start the API
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start Celery worker (in another terminal)
   celery -A app.workers.celery_app worker --loglevel=info
   
   # Start Celery beat (optional, for scheduled tasks)
   celery -A app.workers.celery_app beat --loglevel=info
   ```

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Core Endpoints

#### Recommendations

```http
# Get recommendations for a specific type
GET /api/v1/recommendations/{type}?user_id={user_id}

# Refresh recommendations for a user
POST /api/v1/recommendations/refresh/{user_id}
{
  "user_id": "user123",
  "force": false
}

# Get supported recommendation types
GET /api/v1/recommendations/types

# Delete cached recommendations
DELETE /api/v1/recommendations/{type}?user_id={user_id}

# Get task status
GET /api/v1/recommendations/status/{task_id}
```

#### Health Checks

```http
# Overall health check
GET /api/v1/health/

# Readiness check (Kubernetes)
GET /api/v1/health/ready

# Liveness check (Kubernetes)
GET /api/v1/health/live
```

### Notification Service Endpoints

```http
# WebSocket connection (server-side notification stream)
GET /ws/{user_id}  (WebSocket)

# Service health (includes Redis stream status)
GET /health

# Service statistics (local and distributed)
GET /stats
GET /stats/distributed

# Send notifications
POST /notify/stream/{user_id}    (via Redis Streams)
POST /notify/direct/{user_id}    (direct to socket or stored as pending)

# Debug (only when ENABLE_DEBUG=true at import time)
GET /debug/pending/{user_id}
```

## 🔧 Configuration

The application uses environment-based configuration. Key settings in `.env`:

```env
# Application Settings
APP_NAME=Portal Engine
DEBUG=false
ENVIRONMENT=production

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_NAMESPACE=recommendations

# RabbitMQ Settings
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

# External Services
USER_PROFILE_SERVICE_URL=http://user-profile-service:8000
LIE_SERVICE_URL=http://lie-service:8000
CIS_SERVICE_URL=http://cis-service:8000
PREFETCH_SERVICE_URL=http://prefetch-service:8000
```

## 🧪 Testing

The project includes a comprehensive async-aware test suite with high coverage across components, including the WebSocket notification service (Redis Streams consumer, Pub/Sub listeners, fanout, and background tasks). Tests are organized by category and include unit tests, integration tests, and performance tests.

### Quick Start

Run all tests with a single command:

```bash
# Run all tests
python run_all_tests.py

# Run with coverage reporting
python run_all_tests.py --coverage

# Run with verbose output
python run_all_tests.py --verbose

# Run tests in parallel for faster execution
python run_all_tests.py --parallel
```

### Test Categories

#### Unit Tests
Test individual components in isolation with mocked dependencies:

```bash
# Run only unit tests
python run_all_tests.py --unit

# Run unit tests with coverage
python run_all_tests.py --unit --coverage
```

#### Integration Tests
Test component interactions and external service integrations:

```bash
# Run only integration tests
python run_all_tests.py --integration

# Run integration tests with coverage
python run_all_tests.py --integration --coverage
```

#### Performance Tests
Test performance characteristics and load handling:

```bash
# Run only performance tests
python run_all_tests.py --performance

# Run performance tests with coverage
python run_all_tests.py --performance --coverage
```

### Test Runner Options

The `run_all_tests.py` script provides comprehensive testing capabilities:

```bash
# Basic usage
python run_all_tests.py                    # Run all tests
python run_all_tests.py --unit            # Run only unit tests
python run_all_tests.py --integration     # Run only integration tests
python run_all_tests.py --performance     # Run only performance tests

# Coverage and reporting
python run_all_tests.py --coverage        # Run with coverage reporting
python run_all_tests.py --report          # Generate comprehensive test report

# Output and performance
python run_all_tests.py --verbose         # Verbose output
python run_all_tests.py --parallel        # Run tests in parallel

# Specific tests
python run_all_tests.py --file test_main_app.py                    # Run specific test file
python run_all_tests.py --file test_main_app.py --function test_app_creation  # Run specific test function

# Utility commands
python run_all_tests.py --list            # List all available tests
python run_all_tests.py --check-deps      # Check if dependencies are installed
python run_all_tests.py --install-deps    # Install required dependencies
```

### Manual Testing Commands

If you prefer to use pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run notification service tests with coverage
pytest tests/test_notification_service.py --cov=notification_service --cov-report=term-missing -v

# Run specific test file
pytest tests/test_main_app.py

# Run specific test function
pytest tests/test_main_app.py::TestMainApp::test_app_creation

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Run tests with specific markers
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m performance   # Run only performance tests

# Run tests with coverage and generate reports
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
```

### Test Coverage

The test suite provides comprehensive coverage for:

- **Core Components**: Configuration, constants, logging
- **Services**: User profile, LIE, CIS, LLM, and results services
- **API Layer**: All endpoints, dependencies, and routers
- **Workers**: Celery tasks and configuration
- **Models**: All Pydantic schemas and data models
- **Utilities**: Prompt builder and helper functions
- **Main Application**: FastAPI app, middleware, and error handling
- **Notification Service**: WebSocket endpoints, Redis Streams consumer, Pub/Sub listeners, fanout, background tasks

### Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_main_app.py              # Main FastAPI application tests
├── test_health_router.py          # Health check endpoint tests
├── test_users_router.py           # Users API endpoint tests
├── test_core_config.py            # Configuration tests
├── test_core_constants.py         # Constants tests
├── test_core_logging.py           # Logging tests
├── test_services_base.py          # Base service tests
├── test_services_user_profile.py  # User profile service tests
├── test_services_lie_service.py   # LIE service tests
├── test_services_cis_service.py   # CIS service tests
├── test_services_llm_service.py   # LLM service tests
├── test_services_results_service.py # Results service tests
├── test_api_dependencies.py       # API dependencies tests
├── test_workers_tasks.py          # Celery workers tests
├── test_workers_celery_app.py     # Celery app configuration tests
├── test_models_schemas.py         # Data models tests
├── test_utils_prompt_builder.py   # Prompt builder utility tests
└── README.md                      # Test documentation
```

### Test Fixtures

The test suite includes comprehensive fixtures for:

- **Mock Services**: All external services are mocked for unit tests
- **Test Data**: Sample user profiles, location data, and interaction data
- **Test Client**: FastAPI test client for API testing
- **Mock Responses**: Predefined responses for external service calls

### Running Tests in Different Environments

#### Development Environment
```bash
# Install dependencies
python run_all_tests.py --install-deps

# Run all tests
python run_all_tests.py --verbose
```

#### CI/CD Environment
```bash
# Run tests with coverage and generate reports
python run_all_tests.py --coverage --report

# Run tests in parallel for faster execution
python run_all_tests.py --parallel --coverage
```

#### Production Environment
```bash
# Run tests to verify deployment
python run_all_tests.py --unit --coverage
```

### Test Reports

The test runner generates comprehensive reports:

- **HTML Coverage Report**: `htmlcov/index.html`
- **Terminal Coverage Report**: Coverage summary in terminal
- **XML Coverage Report**: `coverage.xml` for CI/CD integration
- **JUnit XML Report**: `test-results.xml` for test result tracking
- **HTML Test Report**: `test-report.html` for detailed test results

### Troubleshooting Tests

#### Common Issues

1. **Missing Dependencies**
   ```bash
   python run_all_tests.py --install-deps
   ```

2. **Test Failures**
   ```bash
   # Run with verbose output to see detailed error messages
   python run_all_tests.py --verbose
   
   # Run specific failing test
   python run_all_tests.py --file test_main_app.py --function test_app_creation
   ```

3. **Coverage Issues**
   ```bash
   # Check coverage for specific files
   python run_all_tests.py --coverage --file test_main_app.py
   ```

4. **Performance Issues**
   ```bash
   # Run tests in parallel
   python run_all_tests.py --parallel
   ```

#### Test Environment Setup

Ensure the following services are running for integration tests:

- **Redis**: `redis-server`
- **RabbitMQ**: `rabbitmq-server`
- **Celery**: `celery -A app.workers.celery_app worker --loglevel=info`

Note: Unit tests use mocked services and don't require external dependencies.

### Test Best Practices

1. **Run Tests Frequently**: Run tests after each code change
2. **Check Coverage**: Ensure new code is covered by tests
3. **Use Appropriate Test Types**: Use unit tests for isolated components, integration tests for service interactions
4. **Mock External Dependencies**: Use mocks for external services in unit tests
5. **Test Edge Cases**: Include tests for error conditions and edge cases
6. **Performance Testing**: Use performance tests for critical paths
7. **Maintain Test Data**: Keep test data realistic and comprehensive

## 📊 Monitoring

### Celery Monitoring (Flower)

To monitor Celery tasks, install Flower:
```bash
pip install flower
```

Then start Flower:
```bash
celery -A app.workers.celery_app flower --port=5555
```

Access Flower dashboard at: http://localhost:5555

- Monitor task execution
- View task history
- Check worker status
- Inspect task results

### RabbitMQ Management

If RabbitMQ management plugin is enabled, access at: http://localhost:15672

- Default credentials: guest/guest
- Monitor queues and exchanges
- Check message rates
- View connection status

To enable RabbitMQ management plugin:
```bash
rabbitmq-plugins enable rabbitmq_management
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/api/v1/health/

# Check Redis
redis-cli ping

# Check RabbitMQ
rabbitmq-diagnostics ping
```

## 🔄 Workflow

### Recommendation Generation Process

1. **Trigger**: Manual refresh or scheduled task
2. **Data Fetch**: Collect user data from external services
3. **Prompt Building**: Generate dynamic prompts using user context
4. **LLM Call**: Send prompts to Prefetch Service
5. **Caching**: Store results in Redis with TTL
6. **Response**: Serve recommendations from cache

### Task Flow

```
User Request → API → Celery Task → External Services → LLM → Cache → Response
```

## 🏗️ Project Structure

```
portal-engine/
├── app/
│   ├── api/                    # FastAPI routers and endpoints
│   │   ├── dependencies.py     # Dependency injection
│   │   └── routers/           # API route modules
│   ├── core/                  # Core configuration and utilities
│   │   ├── config.py          # Settings and configuration
│   │   ├── constants.py       # Constants and enums
│   │   └── logging.py         # Logging configuration
│   ├── models/                # Data models and schemas
│   │   └── schemas.py         # Pydantic models
│   ├── services/              # External service integrations
│   │   ├── base.py           # Base service class
│   │   ├── cache_service.py  # Redis cache service
│   │   ├── user_profile.py   # User Profile Service
│   │   ├── lie_service.py    # LIE Service
│   │   ├── cis_service.py    # CIS Service
│   │   └── prefetch_service.py # Prefetch Service
│   ├── utils/                 # Utility functions
│   │   └── prompt_builder.py # Dynamic prompt generation
│   ├── workers/               # Celery workers and tasks
│   │   ├── celery_app.py     # Celery configuration
│   │   └── tasks.py          # Background tasks
│   ├── notification_service.py # Distributed WebSocket notification service (FastAPI app)
│   └── main.py               # FastAPI application entry point
├── tests/                    # Test suite
│   ├── conftest.py           # Pytest configuration
│   └── test_recommendations_api.py
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment variables
   export ENVIRONMENT=production
   export DEBUG=false
   ```

2. **Service Setup**
   ```bash
   # Install and configure Redis
   sudo apt-get install redis-server
   sudo systemctl enable redis-server
   
   # Install and configure RabbitMQ
   sudo apt-get install rabbitmq-server
   sudo systemctl enable rabbitmq-server
   ```

3. **Application Deployment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Start Celery workers
   celery -A app.workers.celery_app worker --loglevel=info --concurrency=4 &
   
   # Start Celery beat (for scheduled tasks)
   celery -A app.workers.celery_app beat --loglevel=info &
   
   # Start FastAPI application with production server
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Monitoring and Logging

- **Structured Logging**: JSON format logs for production
- **Health Checks**: Service health endpoints
- **Process Management**: Use systemd or supervisor for process management
- **Metrics**: Prometheus metrics (can be added)
- **Tracing**: Distributed tracing support (can be added)

### Notes for Notification Service

- The `/debug/pending/{user_id}` endpoint is only registered when `ENABLE_DEBUG=true` at import time (environment variable read during module import). In tests, reload the module with the flag set to expose the route.
- WebSocket endpoint: `/ws/{user_id}` supports heartbeats (server-initiated) and client `ping`/server `pong` messages.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health check endpoint at `/api/v1/health/`

## 🔮 Future Enhancements

- [ ] Add Prometheus metrics
- [ ] Implement distributed tracing
- [ ] Add rate limiting
- [ ] Implement authentication/authorization
- [ ] Add database persistence
- [ ] Implement A/B testing framework
- [ ] Add recommendation analytics
- [ ] Implement real-time notifications

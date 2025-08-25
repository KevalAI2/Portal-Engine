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
- **Testing**: Comprehensive test suite with mocking
- **Local Development**: Easy setup for local development
- **Production Ready**: Structured logging, error handling, and monitoring

## 📋 Prerequisites

- Python 3.11+
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

#### Notifications

```http
# Get user notifications
GET /api/v1/notifications/?user_id={user_id}&limit=10

# Mark notification as read
POST /api/v1/notifications/{notification_id}/read?user_id={user_id}

# Delete notification
DELETE /api/v1/notifications/{notification_id}?user_id={user_id}
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

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_recommendations_api.py

# Run with verbose output
pytest -v
```

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

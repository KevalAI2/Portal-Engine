"""
Pytest configuration and fixtures for the FastAPI test suite
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any, Generator
import json
import os
import sys
from app.api.dependencies import (
    get_user_profile_service,
    get_lie_service,
    get_cis_service,
    get_llm_service,
)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.main import app
from app.core.config import settings
from app.api.routers import users as users_router_module
from app.models.schemas import UserProfile, LocationData, InteractionData


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client(mock_user_profile_service, mock_lie_service, mock_cis_service, mock_llm_service):
    # ✅ Correct: override with function references, not strings
    app.dependency_overrides[get_user_profile_service] = lambda: mock_user_profile_service
    app.dependency_overrides[get_lie_service] = lambda: mock_lie_service
    app.dependency_overrides[get_cis_service] = lambda: mock_cis_service
    # Ensure LLM service DI returns the same mock used by assertions in tests
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    # Some routers bind the dependency reference at import time; override that reference too
    app.dependency_overrides[users_router_module.get_llm_service] = lambda: mock_llm_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_profile():
    """Mock user profile data."""
    return UserProfile(
        user_id="test_user_1",
        name="Test User",
        email="test@example.com",
        preferences={
            "language": "en",
            "theme": "dark",
            "notifications": True
        },
        interests=["technology", "travel", "music"],
        age=25,
        location="Barcelona"
    )


@pytest.fixture
def mock_location_data():
    """Mock location data."""
    return LocationData(
        user_id="test_user_1",
        current_location="Barcelona",
        home_location="Madrid",
        work_location="Barcelona",
        travel_history=["Paris", "London", "Rome"],
        location_preferences={
            "preferred_cities": ["Barcelona", "Madrid"],
            "avoid_cities": ["Berlin"]
        }
    )


@pytest.fixture
def mock_interaction_data():
    """Mock interaction data."""
    return InteractionData(
        user_id="test_user_1",
        recent_interactions=[
            {"type": "view", "item_id": "movie_1", "timestamp": "2024-01-01T10:00:00Z"},
            {"type": "like", "item_id": "place_1", "timestamp": "2024-01-01T11:00:00Z"},
            {"type": "save", "item_id": "event_1", "timestamp": "2024-01-01T12:00:00Z"}
        ],
        interaction_history=[
            {"type": "view", "item_id": "movie_2", "timestamp": "2023-12-31T10:00:00Z"},
            {"type": "ignore", "item_id": "place_2", "timestamp": "2023-12-31T11:00:00Z"}
        ],
        preferences={
            "preferred_categories": ["movies", "places"],
            "avoid_categories": ["events"]
        },
        engagement_score=0.75
    )


@pytest.fixture
def mock_recommendations():
    """Mock recommendations data."""
    return {
        "success": True,
        "prompt": "Barcelona recommendations",
        "user_id": "test_user_1",
        "current_city": "Barcelona",
        "generated_at": 1640995200.0,
        "processing_time": 1.5,
        "recommendations": {
            "movies": [
                {
                    "title": "Vicky Cristina Barcelona",
                    "year": "2008",
                    "genre": "Romance/Drama",
                    "description": "A passionate tale of love, desire, and artistic inspiration in vibrant Barcelona",
                    "director": "Woody Allen",
                    "rating": "7.1",
                    "ranking_score": 0.8,
                    "why_would_you_like_this": "Based on your interest in Barcelona, this Romance/Drama offers compelling storytelling"
                }
            ],
            "music": [
                {
                    "title": "Barcelona",
                    "artist": "Freddie Mercury & Montserrat Caballé",
                    "genre": "Opera-Rock",
                    "description": "An epic fusion of rock and opera celebrating the Olympic spirit",
                    "ranking_score": 0.9,
                    "why_would_you_like_this": "This Opera-Rock matches your musical taste with its triumphant energy"
                }
            ],
            "places": [
                {
                    "name": "Sagrada Família",
                    "type": "tourist_attraction",
                    "rating": 4.7,
                    "ranking_score": 0.85,
                    "why_would_you_like_this": "Located in Barcelona, this tourist_attraction offers the perfect morning experience"
                }
            ],
            "events": [
                {
                    "name": "La Mercè Festival",
                    "date": "2024-09-20T10:00:00Z",
                    "description": "Barcelona's biggest street festival celebrating the city's patron saint",
                    "venue": "Various locations across Barcelona",
                    "ranking_score": 0.7,
                    "why_would_you_like_this": "This cultural happening in Barcelona perfectly matches your cultural interests"
                }
            ]
        },
        "metadata": {
            "total_recommendations": 4,
            "categories": ["movies", "music", "places", "events"],
            "model": "demo-llm-v1.0",
            "ranking_enabled": True
        }
    }


@pytest.fixture
def mock_ranked_results():
    """Mock ranked results data."""
    return {
        "success": True,
        "user_id": "test_user_1",
        "ranked_recommendations": {
            "movies": [
                {
                    "title": "Vicky Cristina Barcelona",
                    "genre": "Romance/Drama",
                    "ranking_score": 0.8,
                    "freshness_score": 0.6,
                    "diversity_penalty": 0.0
                }
            ],
            "places": [
                {
                    "name": "Sagrada Família",
                    "type": "tourist_attraction",
                    "ranking_score": 0.85,
                    "freshness_score": 0.7,
                    "diversity_penalty": 0.0
                }
            ]
        },
        "metadata": {
            "total_recommendations": 2,
            "categories": ["movies", "places"],
            "filters_applied": {
                "category": None,
                "limit": 5,
                "min_score": 0.0
            },
            "processing_time": 0.05,
            "data_source": "redis_cache"
        }
    }


@pytest.fixture
def sample_recommendation_response():
    """Sample recommendation response used by recommendations API tests."""
    return {
        "user_id": "test_user_123",
        "type": "music",
        "recommendations": [
            {"title": "Test Music", "ranking_score": 0.9}
        ]
    }



@pytest.fixture(autouse=True)
def _expose_sample_recommendation_response(request, sample_recommendation_response):
    """Expose sample_recommendation_response as a module-level name for tests that reference it directly."""
    try:
        module = request.module
        if module and module.__name__.endswith("test_recommendations_api"):
            setattr(module, "sample_recommendation_response", sample_recommendation_response)
    except Exception:
        pass


@pytest.fixture
def mock_celery_task():
    """Mock Celery task result."""
    return {
        "success": True,
        "user_id": "test_user_1",
        "task_id": "test_task_123",
        "comprehensive_data": {
            "user_profile": {
                "user_id": "test_user_1",
                "name": "Test User",
                "email": "test@example.com"
            },
            "location_data": {
                "user_id": "test_user_1",
                "current_location": "Barcelona"
            },
            "interaction_data": {
                "user_id": "test_user_1",
                "engagement_score": 0.75
            }
        },
        "message": "User processed comprehensively",
        "status": "completed"
    }


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.keys.return_value = []
    mock_redis.publish.return_value = 1
    return mock_redis


@pytest.fixture
def mock_user_profile_service(mock_external_services):
    service = Mock()
    service.get_user_profile = AsyncMock()
    service.health_check = AsyncMock(return_value=True)
    mock_external_services['user_profile_service'].return_value = service
    return service


@pytest.fixture
def mock_lie_service(mock_external_services):
    service = Mock()
    service.get_location_data = AsyncMock()
    service.health_check = AsyncMock(return_value=True)
    mock_external_services['lie_service'].return_value = service
    return service


@pytest.fixture
def mock_cis_service(mock_external_services):
    service = Mock()
    service.get_interaction_data = AsyncMock()
    service.health_check = AsyncMock(return_value=True)
    mock_external_services['cis_service'].return_value = service
    return service



@pytest.fixture
def mock_llm_service():
    """Mock LLMService used by DI and assertions.
    Returns the patched LLMService() instance so DI and tests share the same object.
    """
    from app.services.llm_service import LLMService  # patched by mock_external_services
    service = LLMService()  # this returns mock_llm.return_value
    # Ensure awaited call works and is tracked
    service.generate_recommendations = AsyncMock()
    if not hasattr(service, 'get_recommendations_from_redis'):
        service.get_recommendations_from_redis = Mock()
    if not hasattr(service, 'clear_recommendations'):
        service.clear_recommendations = Mock()
    return service


@pytest.fixture
def mock_results_service():
    """Mock ResultsService."""
    service = Mock()
    service.get_ranked_results = Mock()
    return service


@pytest.fixture
def mock_celery_app():
    """Mock Celery app."""
    app = Mock()
    app.AsyncResult = Mock()
    return app


@pytest.fixture
def mock_process_user_comprehensive():
    """Mock process_user_comprehensive task."""
    task = Mock()
    task.apply_async = Mock()
    task.delay = Mock()
    return task


@pytest.fixture
def sample_request_data():
    """Sample request data for testing."""
    return {
        "prompt": "Barcelona recommendations",
        "user_id": "test_user_1",
        "category": "movies",
        "limit": 5,
        "min_score": 0.5
    }


@pytest.fixture
def sample_error_response():
    """Sample error response for testing."""
    return {
        "success": False,
        "message": "Test error message",
        "data": None,
        "error": "Test error details"
    }


@pytest.fixture
def sample_success_response():
    """Sample success response for testing."""
    return {
        "success": True,
        "message": "Operation completed successfully",
        "data": {"test": "data"},
        "error": None
    }


# Environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield
    # Cleanup after test
    for key in ["ENVIRONMENT", "DEBUG", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]


# Database and external service mocking
@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services to avoid actual API calls during testing."""
    with patch('app.services.user_profile.UserProfileService') as mock_ups, \
         patch('app.services.lie_service.LIEService') as mock_lie, \
         patch('app.services.cis_service.CISService') as mock_cis, \
         patch('app.services.llm_service.LLMService') as mock_llm, \
         patch('app.services.results_service.ResultsService') as mock_results, \
         patch('app.workers.celery_app.celery_app') as mock_celery, \
         patch('redis.Redis') as mock_redis:
        
        # Configure mocks
        mock_ups.return_value.get_user_profile = AsyncMock()
        mock_ups.return_value.health_check = AsyncMock(return_value=True)
        
        mock_lie.return_value.get_location_data = AsyncMock()
        mock_lie.return_value.health_check = AsyncMock(return_value=True)
        
        mock_cis.return_value.get_interaction_data = AsyncMock()
        mock_cis.return_value.health_check = AsyncMock(return_value=True)
        
        # Ensure awaited calls in endpoints work with AsyncMock
        mock_llm.return_value.generate_recommendations = AsyncMock()
        mock_llm.return_value.get_recommendations_from_redis = Mock()
        mock_llm.return_value.clear_recommendations = Mock()
        
        mock_results.return_value.get_ranked_results = Mock()
        
        mock_celery.AsyncResult = Mock()
        
        mock_redis.return_value.get = Mock(return_value=None)
        mock_redis.return_value.setex = Mock(return_value=True)
        mock_redis.return_value.delete = Mock(return_value=1)
        mock_redis.return_value.keys = Mock(return_value=[])
        mock_redis.return_value.publish = Mock(return_value=1)
        
        yield {
            'user_profile_service': mock_ups,
            'lie_service': mock_lie,
            'cis_service': mock_cis,
            'llm_service': mock_llm,
            'results_service': mock_results,
            'celery_app': mock_celery,
            'redis': mock_redis
        }


# Test data generators
@pytest.fixture
def generate_test_users():
    """Generate test user data."""
    def _generate_users(count: int = 5) -> list:
        users = []
        for i in range(count):
            users.append({
                "user_id": f"test_user_{i+1}",
                "name": f"Test User {i+1}",
                "email": f"test{i+1}@example.com",
                "preferences": {"language": "en", "theme": "light"},
                "interests": ["technology", "travel"],
                "age": 25 + i,
                "location": "Barcelona"
            })
        return users
    return _generate_users


@pytest.fixture
def generate_test_recommendations():
    """Generate test recommendation data."""
    def _generate_recommendations(category: str, count: int = 3) -> list:
        recommendations = []
        for i in range(count):
            if category == "movies":
                recommendations.append({
                    "title": f"Test Movie {i+1}",
                    "year": f"202{4-i}",
                    "genre": "Drama",
                    "description": f"Test movie description {i+1}",
                    "ranking_score": 0.8 - (i * 0.1),
                    "why_would_you_like_this": f"Test reason {i+1}"
                })
            elif category == "places":
                recommendations.append({
                    "name": f"Test Place {i+1}",
                    "type": "restaurant",
                    "rating": 4.5 - (i * 0.1),
                    "ranking_score": 0.85 - (i * 0.1),
                    "why_would_you_like_this": f"Test reason {i+1}"
                })
        return recommendations
    return _generate_recommendations


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Data for performance testing."""
    return {
        "large_user_list": [{"user_id": f"user_{i}", "name": f"User {i}"} for i in range(1000)],
        "large_recommendation_list": [{"title": f"Item {i}", "score": 0.5} for i in range(500)],
        "complex_preferences": {
            "categories": ["movies", "music", "places", "events"],
            "filters": ["rating", "price", "location"],
            "sorting": ["relevance", "popularity", "date"]
        }
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Add any cleanup logic here if needed
    pass


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )
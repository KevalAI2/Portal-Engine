"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import settings
from app.services.cache_service import CacheService
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.prefetch_service import PrefetchService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    mock_service = AsyncMock(spec=CacheService)
    
    # Mock successful cache operations
    mock_service.get_recommendations.return_value = None  # No cached data
    mock_service.store_recommendations.return_value = True
    mock_service.delete_recommendations.return_value = True
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture
def mock_user_profile_service():
    """Mock user profile service for testing."""
    mock_service = AsyncMock(spec=UserProfileService)
    
    # Mock user profile data
    mock_profile = {
        "user_id": "test_user_123",
        "name": "Test User",
        "email": "test@example.com",
        "preferences": {"music": {"genre": "rock"}, "movies": {"genre": "action"}},
        "interests": ["music", "movies", "travel"],
        "age": 30,
        "location": "New York"
    }
    
    mock_service.get_user_profile.return_value = mock_profile
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture
def mock_lie_service():
    """Mock LIE service for testing."""
    mock_service = AsyncMock(spec=LIEService)
    
    # Mock location data
    mock_location = {
        "user_id": "test_user_123",
        "current_location": "New York, NY",
        "home_location": "New York, NY",
        "work_location": "Manhattan, NY",
        "travel_history": ["Los Angeles", "Chicago", "Miami"],
        "location_preferences": {"radius": 10, "type": "urban"}
    }
    
    mock_service.get_location_data.return_value = mock_location
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture
def mock_cis_service():
    """Mock CIS service for testing."""
    mock_service = AsyncMock(spec=CISService)
    
    # Mock interaction data
    mock_interaction = {
        "user_id": "test_user_123",
        "recent_interactions": [
            {"action": "viewed_music", "timestamp": "2024-01-01T10:00:00Z"},
            {"action": "watched_movie", "timestamp": "2024-01-01T09:00:00Z"}
        ],
        "interaction_history": [],
        "preferences": {"engagement": "high"},
        "engagement_score": 0.85
    }
    
    mock_service.get_interaction_data.return_value = mock_interaction
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture
def mock_prefetch_service():
    """Mock prefetch service for testing."""
    mock_service = AsyncMock(spec=PrefetchService)
    
    # Mock LLM recommendations
    mock_recommendations = [
        {
            "id": "rec_1",
            "title": "Test Music Recommendation",
            "description": "A great music recommendation",
            "score": 0.95,
            "metadata": {"genre": "rock", "artist": "Test Artist"},
            "url": "https://example.com/music/1"
        },
        {
            "id": "rec_2",
            "title": "Test Movie Recommendation",
            "description": "A great movie recommendation",
            "score": 0.88,
            "metadata": {"genre": "action", "year": 2023},
            "url": "https://example.com/movie/1"
        }
    ]
    
    mock_service.generate_recommendations.return_value = mock_recommendations
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture
def sample_recommendation_response():
    """Sample recommendation response for testing."""
    from app.models.schemas import RecommendationResponse, RecommendationItem
    from datetime import datetime, timedelta
    
    return RecommendationResponse(
        user_id="test_user_123",
        type="music",
        recommendations=[
            RecommendationItem(
                id="rec_1",
                title="Test Music",
                description="A test music recommendation",
                score=0.95,
                metadata={"genre": "rock"},
                url="https://example.com/music/1"
            )
        ],
        generated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        total_count=1
    )

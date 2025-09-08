"""
API dependencies for dependency injection
"""
from typing import Generator
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.results_service import ResultsService
from app.workers.celery_app import celery_app

# The timeout parameter is correctly handled by the service classes now.
# These functions are used by FastAPI's dependency injection system
# to provide instantiated services to API endpoints.

def get_user_profile_service() -> UserProfileService:
    """Returns an instance of the UserProfileService with a 30-second timeout."""
    return UserProfileService(timeout=30)

def get_lie_service() -> LIEService:
    """Returns an instance of the LIEService with a 30-second timeout."""
    return LIEService(timeout=30)

def get_cis_service() -> CISService:
    """Returns an instance of the CISService with a 30-second timeout."""
    return CISService(timeout=30)

def get_results_service() -> ResultsService:
    """Returns an instance of the ResultsService with a 30-second timeout."""
    return ResultsService(timeout=30)

def get_celery_app():
    """Returns the Celery application instance."""
    return celery_app

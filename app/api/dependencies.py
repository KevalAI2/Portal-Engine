"""
API dependencies for dependency injection
"""
from typing import Generator, Optional
from functools import lru_cache
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.results_service import ResultsService
from app.services.llm_service import LLMService
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import safe_model_dump
from fastapi import Depends, HTTPException

logger = get_logger("dependencies")

# Service instances cache
_service_cache = {}


def get_user_profile_service() -> UserProfileService:
    """Returns an instance of the UserProfileService with configured timeout."""
    try:
        service = UserProfileService(timeout=30)
        logger.debug("UserProfileService dependency created")
        return service
    except Exception as e:
        logger.error(f"Failed to create UserProfileService: {e}")
        raise


def get_lie_service() -> LIEService:
    """Returns an instance of the LIEService with configured timeout."""
    try:
        service = LIEService(timeout=30)
        logger.debug("LIEService dependency created")
        return service
    except Exception as e:
        logger.error(f"Failed to create LIEService: {e}")
        raise


def get_cis_service() -> CISService:
    """Returns an instance of the CISService with configured timeout."""
    try:
        service = CISService(timeout=30)
        logger.debug("CISService dependency created")
        return service
    except Exception as e:
        logger.error(f"Failed to create CISService: {e}")
        raise


def get_results_service() -> ResultsService:
    """Returns an instance of the ResultsService with configured timeout."""
    try:
        service = ResultsService(timeout=30)
        logger.debug("ResultsService dependency created")
        return service
    except Exception as e:
        logger.error(f"Failed to create ResultsService: {e}")
        raise


def get_llm_service() -> LLMService:
    """Returns an instance of the LLMService."""
    try:
        service = LLMService(timeout=120)
        logger.debug("LLMService dependency created")
        return service
    except Exception as e:
        logger.error(f"Failed to create LLMService: {e}")
        raise


def get_celery_app():
    """Returns the Celery application instance."""
    try:
        logger.debug("Celery app dependency provided")
        return celery_app
    except Exception as e:
        logger.error(f"Failed to get Celery app: {e}")
        raise


def get_cache_service():
    """Returns a cache service instance (placeholder for future implementation)."""
    # This is a placeholder for a future cache service implementation
    # Currently returns None as the cache functionality is handled within services
    return None


# Optional service dependencies for graceful degradation
async def get_user_profile(user_id: str, service: UserProfileService = Depends(get_user_profile_service)):
    """Get user profile with recursion protection."""
    try:
        profile = await service.get_user_profile(user_id)
        if profile:
            # Convert to simple dict to avoid recursion
            return safe_model_dump(profile)
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user profile")

def get_optional_user_profile_service() -> Optional[UserProfileService]:
    """Returns UserProfileService or None if unavailable (for graceful degradation)."""
    try:
        return get_user_profile_service()
    except Exception as e:
        logger.warning(f"UserProfileService unavailable: {e}")
        return None

def get_optional_lie_service() -> Optional[LIEService]:
    """Returns LIEService or None if unavailable (for graceful degradation)."""
    try:
        return get_lie_service()
    except Exception as e:
        logger.warning(f"LIEService unavailable: {e}")
        return None


def get_optional_cis_service() -> Optional[CISService]:
    """Returns CISService or None if unavailable (for graceful degradation)."""
    try:
        return get_cis_service()
    except Exception as e:
        logger.warning(f"CISService unavailable: {e}")
        return None

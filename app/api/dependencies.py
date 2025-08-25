"""
API dependencies for dependency injection
"""
from typing import Generator
from app.services.cache_service import CacheService
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.services.prefetch_service import PrefetchService
from app.workers.celery_app import celery_app


def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return CacheService()


def get_user_profile_service() -> UserProfileService:
    """Get user profile service instance"""
    return UserProfileService()


def get_lie_service() -> LIEService:
    """Get LIE service instance"""
    return LIEService()


def get_cis_service() -> CISService:
    """Get CIS service instance"""
    return CISService()


def get_prefetch_service() -> PrefetchService:
    """Get prefetch service instance"""
    return PrefetchService()


def get_celery_app():
    """Get Celery app instance"""
    return celery_app

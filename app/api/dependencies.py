"""
API dependencies for dependency injection
"""
from typing import Generator
from services.user_profile import UserProfileService
from services.lie_service import LIEService
from services.cis_service import CISService
from workers.celery_app import celery_app


def get_user_profile_service() -> UserProfileService:
    """Get user profile service instance"""
    return UserProfileService()


def get_lie_service() -> LIEService:
    """Get LIE service instance"""
    return LIEService()


def get_cis_service() -> CISService:
    """Get CIS service instance"""
    return CISService()


def get_celery_app():
    """Get Celery app instance"""
    return celery_app

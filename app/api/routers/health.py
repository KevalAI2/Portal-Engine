"""
Health check API router
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from app.core.logging import get_logger
from app.core.config import settings
from app.models.schemas import HealthCheckResponse
from app.services.user_profile import UserProfileService
from app.services.lie_service import LIEService
from app.services.cis_service import CISService
from app.api.dependencies import (
    get_user_profile_service,
    get_lie_service,
    get_cis_service
)

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("health_router")


@router.get("/", response_model=HealthCheckResponse)
async def health_check(
    user_profile_service: UserProfileService = Depends(get_user_profile_service),
    lie_service: LIEService = Depends(get_lie_service),
    cis_service: CISService = Depends(get_cis_service)
):
    """
    Health check endpoint to verify service status and dependencies
    """
    try:
        logger.info("Health check requested")
        
        # Check service health
        services_status = {}
        
        # Check external services (these might fail in development)
        try:
            user_profile_healthy = await user_profile_service.health_check()
            services_status["user_profile_service"] = "healthy" if user_profile_healthy else "unhealthy"
        except Exception:
            services_status["user_profile_service"] = "unavailable"
        
        try:
            lie_healthy = await lie_service.health_check()
            services_status["lie_service"] = "healthy" if lie_healthy else "unhealthy"
        except Exception:
            services_status["lie_service"] = "unavailable"
        
        try:
            cis_healthy = await cis_service.health_check()
            services_status["cis_service"] = "healthy" if cis_healthy else "unhealthy"
        except Exception:
            services_status["cis_service"] = "unavailable"
        
        # Determine overall status
        if all(status == "healthy" for status in services_status.values()):
            overall_status = "healthy"
        elif any(status == "healthy" for status in services_status.values()):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        response = HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            environment=settings.environment,
            services=services_status
        )
        
        logger.info("Health check completed", status=overall_status, services=services_status)
        
        return response
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            environment=settings.environment,
            services={"error": str(e)}
        )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes
    """
    try:
        # Check if the service is ready to handle requests
        # This could include checking database connections, cache, etc.
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not_ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes
    """
    try:
        # Simple check to see if the service is alive
        return {"status": "alive"}
        
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        return {"status": "dead", "error": str(e)}

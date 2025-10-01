"""
API Versioning and Backward Compatibility Management

This module provides comprehensive API versioning support with backward
compatibility, deprecation warnings, and version-specific routing.
"""
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from fastapi.routing import APIRouter
from app.core.logging import get_logger

logger = get_logger("api_versioning")


class APIVersion(str, Enum):
    """Supported API versions"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    LATEST = V3


class VersionStatus(str, Enum):
    """Version status types"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    RETIRED = "retired"


class VersionInfo:
    """Version information container"""
    
    def __init__(
        self,
        version: str,
        status: VersionStatus,
        release_date: datetime,
        deprecation_date: Optional[datetime] = None,
        sunset_date: Optional[datetime] = None,
        retirement_date: Optional[datetime] = None,
        breaking_changes: Optional[List[str]] = None,
        migration_guide: Optional[str] = None
    ):
        self.version = version
        self.status = status
        self.release_date = release_date
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
        self.retirement_date = retirement_date
        self.breaking_changes = breaking_changes or []
        self.migration_guide = migration_guide
    
    def is_active(self) -> bool:
        """Check if version is currently active"""
        return self.status == VersionStatus.ACTIVE
    
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        return self.status == VersionStatus.DEPRECATED
    
    def is_sunset(self) -> bool:
        """Check if version is in sunset period"""
        return self.status == VersionStatus.SUNSET
    
    def is_retired(self) -> bool:
        """Check if version is retired"""
        return self.status == VersionStatus.RETIRED
    
    def get_warning_message(self) -> Optional[str]:
        """Get deprecation warning message"""
        if self.is_deprecated():
            return f"API version {self.version} is deprecated. Please upgrade to the latest version."
        elif self.is_sunset():
            return f"API version {self.version} will be retired soon. Please migrate to the latest version."
        return None


class APIVersionManager:
    """API version management system"""
    
    def __init__(self):
        self.versions: Dict[str, VersionInfo] = {}
        self.default_version = APIVersion.V1
        self.latest_version = APIVersion.LATEST
        self._setup_default_versions()
    
    def _setup_default_versions(self):
        """Setup default version information"""
        now = datetime.now()
        
        # V1 - Stable and active
        self.versions[APIVersion.V1] = VersionInfo(
            version=APIVersion.V1,
            status=VersionStatus.ACTIVE,
            release_date=now - timedelta(days=365),
            migration_guide="https://docs.example.com/migration/v1-to-v2"
        )
        
        # V2 - Active with some deprecated features
        self.versions[APIVersion.V2] = VersionInfo(
            version=APIVersion.V2,
            status=VersionStatus.ACTIVE,
            release_date=now - timedelta(days=180),
            migration_guide="https://docs.example.com/migration/v2-to-v3"
        )
        
        # V3 - Latest version
        self.versions[APIVersion.V3] = VersionInfo(
            version=APIVersion.V3,
            status=VersionStatus.ACTIVE,
            release_date=now - timedelta(days=30)
        )
    
    def register_version(self, version_info: VersionInfo):
        """Register a new API version"""
        self.versions[version_info.version] = version_info
        logger.info("API version registered", version=version_info.version, status=version_info.status)
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """Get version information"""
        return self.versions.get(version)
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported versions"""
        return [v for v in self.versions.keys() if not self.versions[v].is_retired()]
    
    def get_active_versions(self) -> List[str]:
        """Get list of active versions"""
        return [v for v in self.versions.keys() if self.versions[v].is_active()]
    
    def get_latest_version(self) -> str:
        """Get latest version"""
        return self.latest_version
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported"""
        version_info = self.get_version_info(version)
        return version_info is not None and not version_info.is_retired()
    
    def validate_version(self, version: str) -> str:
        """Validate and normalize version string"""
        if not version:
            return self.default_version
        
        # Normalize version string
        version = version.lower().strip()
        if version.startswith('v'):
            version = version[1:]
        
        full_version = f"v{version}"
        
        if not self.is_version_supported(full_version):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. Supported versions: {', '.join(self.get_supported_versions())}"
            )
        
        return full_version


# Global version manager instance
version_manager = APIVersionManager()


def get_api_version(request: Request) -> str:
    """
    Extract API version from request.
    
    Priority:
    1. URL path parameter
    2. Accept header
    3. Query parameter
    4. Default version
    """
    # Check URL path parameter
    if hasattr(request, 'path_params') and 'version' in request.path_params:
        version = request.path_params['version']
        return version_manager.validate_version(version)
    
    # Check Accept header
    accept_header = request.headers.get('Accept', '')
    if 'version=' in accept_header:
        try:
            version = accept_header.split('version=')[1].split(',')[0].strip()
            return version_manager.validate_version(version)
        except (IndexError, ValueError):
            pass
    
    # Check query parameter
    version = request.query_params.get('version')
    if version:
        return version_manager.validate_version(version)
    
    # Return default version
    return version_manager.default_version


def get_version_info(version: str = Depends(get_api_version)) -> VersionInfo:
    """Dependency to get version information"""
    version_info = version_manager.get_version_info(version)
    if not version_info:
        raise HTTPException(status_code=400, detail=f"Invalid API version: {version}")
    return version_info


def check_version_status(version_info: VersionInfo = Depends(get_version_info)) -> VersionInfo:
    """Dependency to check version status and add warnings"""
    if version_info.is_retired():
        raise HTTPException(
            status_code=410,
            detail=f"API version {version_info.version} has been retired"
        )
    
    return version_info


def add_version_headers(response, version_info: VersionInfo):
    """Add version-related headers to response"""
    response.headers["API-Version"] = version_info.version
    response.headers["API-Latest-Version"] = version_manager.get_latest_version()
    
    if version_info.is_deprecated():
        response.headers["API-Deprecation-Warning"] = version_info.get_warning_message()
        response.headers["Sunset"] = version_info.sunset_date.isoformat() if version_info.sunset_date else ""
    
    if version_info.migration_guide:
        response.headers["API-Migration-Guide"] = version_info.migration_guide


class VersionedRouter:
    """Version-aware API router"""
    
    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routers: Dict[str, APIRouter] = {}
        self._setup_routers()
    
    def _setup_routers(self):
        """Setup versioned routers"""
        for version in version_manager.get_supported_versions():
            router = APIRouter(
                prefix=f"/api/{version}{self.prefix}",
                tags=[f"{tag} ({version})" for tag in self.tags]
            )
            self.routers[version] = router
    
    def get_router(self, version: str) -> APIRouter:
        """Get router for specific version"""
        return self.routers.get(version)
    
    def add_endpoint(
        self,
        path: str,
        endpoint: Callable,
        methods: List[str],
        versions: Optional[List[str]] = None,
        **kwargs
    ):
        """Add endpoint to specified versions"""
        target_versions = versions or version_manager.get_active_versions()
        
        for version in target_versions:
            if version in self.routers:
                router = self.routers[version]
                router.add_api_route(
                    path=path,
                    endpoint=endpoint,
                    methods=methods,
                    **kwargs
                )
    
    def get_all_routers(self) -> List[APIRouter]:
        """Get all versioned routers"""
        return list(self.routers.values())


def create_versioned_response(
    data: Any,
    version: str,
    message: str = "Success",
    status_code: int = 200
) -> Dict[str, Any]:
    """Create version-specific response format"""
    response = {
        "success": True,
        "message": message,
        "status_code": status_code,
        "data": data,
        "version": version
    }
    
    # Add version-specific formatting
    if version == APIVersion.V1:
        # V1 uses simple format
        pass
    elif version == APIVersion.V2:
        # V2 adds metadata
        response["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "version": version
        }
    elif version == APIVersion.V3:
        # V3 adds comprehensive metadata
        response["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "request_id": "generated_request_id",  # Would be from request context
            "pagination": None  # Would be populated if applicable
        }
    
    return response


def handle_version_migration(
    old_version: str,
    new_version: str,
    data: Any
) -> Any:
    """Handle data migration between versions"""
    if old_version == APIVersion.V1 and new_version == APIVersion.V2:
        # V1 to V2 migration
        if isinstance(data, dict):
            # Add new fields for V2
            data["migrated_from_v1"] = True
            data["version"] = APIVersion.V2
        return data
    
    elif old_version == APIVersion.V2 and new_version == APIVersion.V3:
        # V2 to V3 migration
        if isinstance(data, dict):
            # Add new fields for V3
            data["migrated_from_v2"] = True
            data["version"] = APIVersion.V3
            # Add any breaking changes
            if "old_field" in data:
                data["new_field"] = data.pop("old_field")
        return data
    
    return data


def get_version_compatibility_matrix() -> Dict[str, Dict[str, bool]]:
    """Get version compatibility matrix"""
    return {
        APIVersion.V1: {
            "backward_compatible": True,
            "forward_compatible": False,
            "deprecated": False
        },
        APIVersion.V2: {
            "backward_compatible": True,
            "forward_compatible": False,
            "deprecated": False
        },
        APIVersion.V3: {
            "backward_compatible": True,
            "forward_compatible": True,
            "deprecated": False
        }
    }


def validate_version_compatibility(
    client_version: str,
    server_version: str
) -> bool:
    """Validate version compatibility"""
    compatibility_matrix = get_version_compatibility_matrix()
    
    client_info = compatibility_matrix.get(client_version, {})
    server_info = compatibility_matrix.get(server_version, {})
    
    # Check if versions are compatible
    if client_version == server_version:
        return True
    
    # Check backward compatibility
    if client_info.get("backward_compatible") and server_info.get("forward_compatible"):
        return True
    
    return False
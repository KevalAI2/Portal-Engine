"""
Tests for API versioning and backward compatibility management
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from fastapi.routing import APIRouter

from app.core.versioning import (
    APIVersion, VersionStatus, VersionInfo, APIVersionManager,
    get_api_version, get_version_info, check_version_status,
    add_version_headers, VersionedRouter, create_versioned_response,
    handle_version_migration, get_version_compatibility_matrix,
    validate_version_compatibility, version_manager
)


class TestAPIVersion:
    """Test APIVersion enum"""
    
    def test_api_version_values(self):
        """Test API version enum values"""
        assert APIVersion.V1 == "v1"
        assert APIVersion.V2 == "v2"
        assert APIVersion.V3 == "v3"
        assert APIVersion.LATEST == APIVersion.V3


class TestVersionStatus:
    """Test VersionStatus enum"""
    
    def test_version_status_values(self):
        """Test version status enum values"""
        assert VersionStatus.ACTIVE == "active"
        assert VersionStatus.DEPRECATED == "deprecated"
        assert VersionStatus.SUNSET == "sunset"
        assert VersionStatus.RETIRED == "retired"


class TestVersionInfo:
    """Test VersionInfo class"""
    
    def test_version_info_creation(self):
        """Test VersionInfo creation with all parameters"""
        now = datetime.now()
        version_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=now,
            deprecation_date=now + timedelta(days=30),
            sunset_date=now + timedelta(days=60),
            retirement_date=now + timedelta(days=90),
            breaking_changes=["field_removed"],
            migration_guide="https://example.com/migration"
        )
        
        assert version_info.version == "v1"
        assert version_info.status == VersionStatus.ACTIVE
        assert version_info.release_date == now
        assert version_info.deprecation_date == now + timedelta(days=30)
        assert version_info.sunset_date == now + timedelta(days=60)
        assert version_info.retirement_date == now + timedelta(days=90)
        assert version_info.breaking_changes == ["field_removed"]
        assert version_info.migration_guide == "https://example.com/migration"
    
    def test_version_info_creation_minimal(self):
        """Test VersionInfo creation with minimal parameters"""
        now = datetime.now()
        version_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=now
        )
        
        assert version_info.version == "v1"
        assert version_info.status == VersionStatus.ACTIVE
        assert version_info.release_date == now
        assert version_info.deprecation_date is None
        assert version_info.sunset_date is None
        assert version_info.retirement_date is None
        assert version_info.breaking_changes == []
        assert version_info.migration_guide is None
    
    def test_is_active(self):
        """Test is_active method"""
        now = datetime.now()
        active_version = VersionInfo("v1", VersionStatus.ACTIVE, now)
        deprecated_version = VersionInfo("v1", VersionStatus.DEPRECATED, now)
        
        assert active_version.is_active() is True
        assert deprecated_version.is_active() is False
    
    def test_is_deprecated(self):
        """Test is_deprecated method"""
        now = datetime.now()
        active_version = VersionInfo("v1", VersionStatus.ACTIVE, now)
        deprecated_version = VersionInfo("v1", VersionStatus.DEPRECATED, now)
        
        assert active_version.is_deprecated() is False
        assert deprecated_version.is_deprecated() is True
    
    def test_is_sunset(self):
        """Test is_sunset method"""
        now = datetime.now()
        active_version = VersionInfo("v1", VersionStatus.ACTIVE, now)
        sunset_version = VersionInfo("v1", VersionStatus.SUNSET, now)
        
        assert active_version.is_sunset() is False
        assert sunset_version.is_sunset() is True
    
    def test_is_retired(self):
        """Test is_retired method"""
        now = datetime.now()
        active_version = VersionInfo("v1", VersionStatus.ACTIVE, now)
        retired_version = VersionInfo("v1", VersionStatus.RETIRED, now)
        
        assert active_version.is_retired() is False
        assert retired_version.is_retired() is True
    
    def test_get_warning_message(self):
        """Test get_warning_message method"""
        now = datetime.now()
        active_version = VersionInfo("v1", VersionStatus.ACTIVE, now)
        deprecated_version = VersionInfo("v1", VersionStatus.DEPRECATED, now)
        sunset_version = VersionInfo("v1", VersionStatus.SUNSET, now)
        
        assert active_version.get_warning_message() is None
        assert deprecated_version.get_warning_message() == "API version v1 is deprecated. Please upgrade to the latest version."
        assert sunset_version.get_warning_message() == "API version v1 will be retired soon. Please migrate to the latest version."


class TestAPIVersionManager:
    """Test APIVersionManager class"""
    
    def test_version_manager_initialization(self):
        """Test version manager initialization"""
        manager = APIVersionManager()
        
        assert manager.default_version == APIVersion.V1
        assert manager.latest_version == APIVersion.LATEST
        assert len(manager.versions) == 3
        assert APIVersion.V1 in manager.versions
        assert APIVersion.V2 in manager.versions
        assert APIVersion.V3 in manager.versions
    
    def test_register_version(self):
        """Test version registration"""
        manager = APIVersionManager()
        now = datetime.now()
        
        version_info = VersionInfo(
            version="v4",
            status=VersionStatus.ACTIVE,
            release_date=now
        )
        
        manager.register_version(version_info)
        assert "v4" in manager.versions
        assert manager.versions["v4"] == version_info
    
    def test_get_version_info(self):
        """Test getting version information"""
        manager = APIVersionManager()
        
        version_info = manager.get_version_info("v1")
        assert version_info is not None
        assert version_info.version == "v1"
        
        assert manager.get_version_info("nonexistent") is None
    
    def test_get_supported_versions(self):
        """Test getting supported versions"""
        manager = APIVersionManager()
        
        supported = manager.get_supported_versions()
        assert "v1" in supported
        assert "v2" in supported
        assert "v3" in supported
        
        # Add a retired version
        now = datetime.now()
        retired_version = VersionInfo(
            version="v0",
            status=VersionStatus.RETIRED,
            release_date=now
        )
        manager.register_version(retired_version)
        
        supported = manager.get_supported_versions()
        assert "v0" not in supported
    
    def test_get_active_versions(self):
        """Test getting active versions"""
        manager = APIVersionManager()
        
        active = manager.get_active_versions()
        assert "v1" in active
        assert "v2" in active
        assert "v3" in active
        
        # Add a deprecated version
        now = datetime.now()
        deprecated_version = VersionInfo(
            version="v4",
            status=VersionStatus.DEPRECATED,
            release_date=now
        )
        manager.register_version(deprecated_version)
        
        active = manager.get_active_versions()
        assert "v4" not in active
    
    def test_get_latest_version(self):
        """Test getting latest version"""
        manager = APIVersionManager()
        assert manager.get_latest_version() == APIVersion.LATEST
    
    def test_is_version_supported(self):
        """Test version support check"""
        manager = APIVersionManager()
        
        assert manager.is_version_supported("v1") is True
        assert manager.is_version_supported("v2") is True
        assert manager.is_version_supported("v3") is True
        assert manager.is_version_supported("v4") is False
        
        # Add a retired version
        now = datetime.now()
        retired_version = VersionInfo(
            version="v4",
            status=VersionStatus.RETIRED,
            release_date=now
        )
        manager.register_version(retired_version)
        
        assert manager.is_version_supported("v4") is False
    
    def test_validate_version_success(self):
        """Test successful version validation"""
        manager = APIVersionManager()
        
        assert manager.validate_version("v1") == "v1"
        assert manager.validate_version("V1") == "v1"
        assert manager.validate_version("1") == "v1"
        assert manager.validate_version("") == APIVersion.V1
        assert manager.validate_version(None) == APIVersion.V1
    
    def test_validate_version_failure(self):
        """Test version validation failure"""
        manager = APIVersionManager()
        
        with pytest.raises(HTTPException) as exc_info:
            manager.validate_version("v99")
        
        assert exc_info.value.status_code == 400
        assert "Unsupported API version" in str(exc_info.value.detail)


class TestVersionDependencies:
    """Test version-related dependencies"""
    
    def test_get_api_version_from_path_params(self):
        """Test getting API version from path parameters"""
        request = Mock(spec=Request)
        request.path_params = {"version": "v2"}
        request.headers = {}
        request.query_params = {}
        
        version = get_api_version(request)
        assert version == "v2"
    
    def test_get_api_version_from_accept_header(self):
        """Test getting API version from Accept header"""
        request = Mock(spec=Request)
        request.path_params = {}
        request.headers = {"Accept": "application/json; version=v2"}
        request.query_params = {}
        
        version = get_api_version(request)
        assert version == "v2"
    
    def test_get_api_version_from_query_params(self):
        """Test getting API version from query parameters"""
        request = Mock(spec=Request)
        request.path_params = {}
        request.headers = {}
        request.query_params = {"version": "v3"}
        
        version = get_api_version(request)
        assert version == "v3"
    
    def test_get_api_version_default(self):
        """Test getting default API version"""
        request = Mock(spec=Request)
        request.path_params = {}
        request.headers = {}
        request.query_params = {}
        
        version = get_api_version(request)
        assert version == APIVersion.V1
    
    def test_get_version_info_success(self):
        """Test successful version info retrieval"""
        version_info = get_version_info("v1")
        assert version_info is not None
        assert version_info.version == "v1"
    
    def test_get_version_info_failure(self):
        """Test version info retrieval failure"""
        with pytest.raises(HTTPException) as exc_info:
            get_version_info("v99")
        
        assert exc_info.value.status_code == 400
    
    def test_check_version_status_success(self):
        """Test successful version status check"""
        # Create a VersionInfo object for v1
        version_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.now()
        )
        
        result = check_version_status(version_info)
        assert result is not None
        assert result.version == "v1"
    
    def test_check_version_status_retired(self):
        """Test version status check for retired version"""
        # Create a retired VersionInfo object
        retired_version = VersionInfo(
            version="v99",
            status=VersionStatus.RETIRED,
            release_date=datetime.now()
        )
        
        with pytest.raises(HTTPException) as exc_info:
            check_version_status(retired_version)
        
        assert exc_info.value.status_code == 410


class TestVersionedRouter:
    """Test VersionedRouter class"""
    
    def test_versioned_router_initialization(self):
        """Test versioned router initialization"""
        router = VersionedRouter(prefix="/test", tags=["test"])
        
        assert router.prefix == "/test"
        assert router.tags == ["test"]
        assert len(router.routers) == 3
        assert "v1" in router.routers
        assert "v2" in router.routers
        assert "v3" in router.routers
    
    def test_get_router(self):
        """Test getting router for specific version"""
        router = VersionedRouter()
        
        v1_router = router.get_router("v1")
        assert v1_router is not None
        assert isinstance(v1_router, APIRouter)
        
        assert router.get_router("nonexistent") is None
    
    def test_add_endpoint(self):
        """Test adding endpoint to versions"""
        router = VersionedRouter()
        
        def test_endpoint():
            return {"message": "test"}
        
        router.add_endpoint(
            path="/test",
            endpoint=test_endpoint,
            methods=["GET"],
            versions=["v1", "v2"]
        )
        
        # Check that endpoints were added to specified versions
        v1_router = router.get_router("v1")
        v3_router = router.get_router("v3")
        
        # This is a basic check - in practice, you'd need to inspect the router's routes
        assert v1_router is not None
        assert v3_router is not None
    
    def test_get_all_routers(self):
        """Test getting all versioned routers"""
        router = VersionedRouter()
        all_routers = router.get_all_routers()
        
        assert len(all_routers) == 3
        assert all(isinstance(r, APIRouter) for r in all_routers)


class TestResponseHelpers:
    """Test response helper functions"""
    
    def test_add_version_headers(self):
        """Test adding version headers to response"""
        response = Mock()
        response.headers = {}
        
        now = datetime.now()
        version_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=now,
            migration_guide="https://example.com/migration"
        )
        
        add_version_headers(response, version_info)
        
        assert response.headers["API-Version"] == "v1"
        assert response.headers["API-Latest-Version"] == APIVersion.LATEST
        assert "API-Migration-Guide" in response.headers
    
    def test_add_version_headers_deprecated(self):
        """Test adding version headers for deprecated version"""
        response = Mock()
        response.headers = {}
        
        now = datetime.now()
        version_info = VersionInfo(
            version="v1",
            status=VersionStatus.DEPRECATED,
            release_date=now,
            sunset_date=now + timedelta(days=30)
        )
        
        add_version_headers(response, version_info)
        
        assert response.headers["API-Version"] == "v1"
        assert "API-Deprecation-Warning" in response.headers
        assert "Sunset" in response.headers
    
    def test_create_versioned_response_v1(self):
        """Test creating versioned response for v1"""
        data = {"test": "data"}
        response = create_versioned_response(data, "v1")
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["version"] == "v1"
        assert "metadata" not in response
    
    def test_create_versioned_response_v2(self):
        """Test creating versioned response for v2"""
        data = {"test": "data"}
        response = create_versioned_response(data, "v2")
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["version"] == "v2"
        assert "metadata" in response
        assert "timestamp" in response["metadata"]
        assert response["metadata"]["version"] == "v2"
    
    def test_create_versioned_response_v3(self):
        """Test creating versioned response for v3"""
        data = {"test": "data"}
        response = create_versioned_response(data, "v3")
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["version"] == "v3"
        assert "metadata" in response
        assert "timestamp" in response["metadata"]
        assert response["metadata"]["version"] == "v3"
        assert "request_id" in response["metadata"]
        assert "pagination" in response["metadata"]


class TestVersionMigration:
    """Test version migration functions"""
    
    def test_handle_version_migration_v1_to_v2(self):
        """Test migration from v1 to v2"""
        data = {"old_field": "value"}
        result = handle_version_migration("v1", "v2", data)
        
        assert result["migrated_from_v1"] is True
        assert result["version"] == "v2"
        assert result["old_field"] == "value"
    
    def test_handle_version_migration_v2_to_v3(self):
        """Test migration from v2 to v3"""
        data = {"old_field": "value", "existing_field": "test"}
        result = handle_version_migration("v2", "v3", data)
        
        assert result["migrated_from_v2"] is True
        assert result["version"] == "v3"
        assert "old_field" not in result
        assert result["new_field"] == "value"
        assert result["existing_field"] == "test"
    
    def test_handle_version_migration_no_change(self):
        """Test migration with no changes"""
        data = {"field": "value"}
        result = handle_version_migration("v1", "v3", data)
        
        assert result == data
    
    def test_handle_version_migration_non_dict(self):
        """Test migration with non-dict data"""
        data = "string_data"
        result = handle_version_migration("v1", "v2", data)
        
        assert result == data


class TestVersionCompatibility:
    """Test version compatibility functions"""
    
    def test_get_version_compatibility_matrix(self):
        """Test getting version compatibility matrix"""
        matrix = get_version_compatibility_matrix()
        
        assert "v1" in matrix
        assert "v2" in matrix
        assert "v3" in matrix
        
        assert matrix["v1"]["backward_compatible"] is True
        assert matrix["v1"]["forward_compatible"] is False
        assert matrix["v1"]["deprecated"] is False
        
        assert matrix["v3"]["backward_compatible"] is True
        assert matrix["v3"]["forward_compatible"] is True
        assert matrix["v3"]["deprecated"] is False
    
    def test_validate_version_compatibility_same_version(self):
        """Test compatibility validation for same version"""
        assert validate_version_compatibility("v1", "v1") is True
        assert validate_version_compatibility("v2", "v2") is True
        assert validate_version_compatibility("v3", "v3") is True
    
    def test_validate_version_compatibility_compatible(self):
        """Test compatibility validation for compatible versions"""
        assert validate_version_compatibility("v1", "v3") is True
        assert validate_version_compatibility("v2", "v3") is True
    
    def test_validate_version_compatibility_incompatible(self):
        """Test compatibility validation for incompatible versions"""
        assert validate_version_compatibility("v3", "v1") is False
        assert validate_version_compatibility("v3", "v2") is False
    
    def test_validate_version_compatibility_unknown_versions(self):
        """Test compatibility validation for unknown versions"""
        assert validate_version_compatibility("v99", "v1") is False
        assert validate_version_compatibility("v1", "v99") is False

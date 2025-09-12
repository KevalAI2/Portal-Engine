"""
Comprehensive test suite for API dependencies module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.api.dependencies import (
    get_user_profile_service,
    get_lie_service,
    get_cis_service,
    get_results_service,
    get_celery_app,
    get_llm_service
)


@pytest.mark.unit
class TestAPIDependencies:
    """Test the API dependencies functionality."""

    def test_get_user_profile_service(self):
        """Test user profile service dependency."""
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_user_profile_service()
            
            assert result == mock_service
            mock_service_class.assert_called_once()
    def test_get_cache_service(self):
        """Test cache service dependency."""
        from app.api.dependencies import get_cache_service
        
        result = get_cache_service()
        
        assert result is None
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self):
        """Test get_user_profile dependency success case."""
        from app.api.dependencies import get_user_profile
        
        mock_profile = {"user_id": "123", "name": "Test User"}
        mock_service = AsyncMock()
        mock_service.get_user_profile.return_value = mock_profile
        
        # Mock the service parameter directly since get_user_profile uses Depends
        with patch('app.api.dependencies.safe_model_dump', return_value=mock_profile) as mock_safe_dump:
            result = await get_user_profile(user_id="123", service=mock_service)
            
            assert result == mock_profile
            mock_service.get_user_profile.assert_awaited_once_with("123")
            mock_safe_dump.assert_called_once_with(mock_profile)

    @pytest.mark.asyncio
    async def test_get_user_profile_none(self):
        """Test get_user_profile dependency when profile is None."""
        from app.api.dependencies import get_user_profile
        
        mock_service = AsyncMock()
        mock_service.get_user_profile.return_value = None
        
        # Mock the service parameter directly since get_user_profile uses Depends
        result = await get_user_profile(user_id="123", service=mock_service)
        
        assert result is None
        mock_service.get_user_profile.assert_awaited_once_with("123")

    @pytest.mark.asyncio
    async def test_get_user_profile_error(self):
        """Test get_user_profile dependency error handling."""
        from app.api.dependencies import get_user_profile
        from fastapi import HTTPException
        
        mock_service = AsyncMock()
        mock_service.get_user_profile.side_effect = Exception("Profile fetch failed")
        
        # Mock the service parameter directly since get_user_profile uses Depends
        with patch('app.api.dependencies.logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await get_user_profile(user_id="123", service=mock_service)
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Error retrieving user profile"
            mock_logger.error.assert_called_once_with("Error getting user profile: Profile fetch failed")

    def test_get_optional_user_profile_service_success(self):
        """Test optional user profile service dependency success case."""
        from app.api.dependencies import get_optional_user_profile_service
        mock_service = Mock()
        
        with patch('app.api.dependencies.get_user_profile_service', return_value=mock_service):
            result = get_optional_user_profile_service()
            
            assert result == mock_service

    def test_get_optional_user_profile_service_failure(self):
        """Test optional user profile service dependency failure case."""
        from app.api.dependencies import get_optional_user_profile_service
        
        with patch('app.api.dependencies.get_user_profile_service') as mock_get_service:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_get_service.side_effect = Exception("Service unavailable")
                
                result = get_optional_user_profile_service()
                
                assert result is None
                mock_logger.warning.assert_called_once_with("UserProfileService unavailable: Service unavailable")

    def test_get_optional_lie_service_success(self):
        """Test optional LIE service dependency success case."""
        from app.api.dependencies import get_optional_lie_service
        mock_service = Mock()
        
        with patch('app.api.dependencies.get_lie_service', return_value=mock_service):
            result = get_optional_lie_service()
            
            assert result == mock_service

    def test_get_optional_lie_service_failure(self):
        """Test optional LIE service dependency failure case."""
        from app.api.dependencies import get_optional_lie_service
        
        with patch('app.api.dependencies.get_lie_service') as mock_get_service:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_get_service.side_effect = Exception("Service unavailable")
                
                result = get_optional_lie_service()
                
                assert result is None
                mock_logger.warning.assert_called_once_with("LIEService unavailable: Service unavailable")

    def test_get_optional_cis_service_success(self):
        """Test optional CIS service dependency success case."""
        from app.api.dependencies import get_optional_cis_service
        mock_service = Mock()
        
        with patch('app.api.dependencies.get_cis_service', return_value=mock_service):
            result = get_optional_cis_service()
            
            assert result == mock_service

    def test_get_optional_cis_service_failure(self):
        """Test optional CIS service dependency failure case."""
        from app.api.dependencies import get_optional_cis_service
        
        with patch('app.api.dependencies.get_cis_service') as mock_get_service:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_get_service.side_effect = Exception("Service unavailable")
                
                result = get_optional_cis_service()
                
                assert result is None
                mock_logger.warning.assert_called_once_with("CISService unavailable: Service unavailable")
    
    def test_get_user_profile_service_configuration(self):
        """Test user profile service dependency configuration."""
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_user_profile_service()
            
            # Verify service was created with correct parameters
            mock_service_class.assert_called_once()
            call_args = mock_service_class.call_args
            print("CALL ARGS:", call_args)

            assert call_args[1].get('timeout', None) == 30


    def test_get_user_profile_service_multiple_calls(self):
        """Test user profile service dependency multiple calls."""
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result1 = get_user_profile_service()
            result2 = get_user_profile_service()
            
            # Should create new instances each time
            assert result1 == mock_service
            assert result2 == mock_service
            assert mock_service_class.call_count == 2

    def test_get_lie_service(self):
        """Test LIE service dependency."""
        with patch('app.api.dependencies.LIEService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_lie_service()
            
            assert result == mock_service
            mock_service_class.assert_called_once()

    def test_get_lie_service_configuration(self):
        """Test LIE service dependency configuration."""
        with patch('app.api.dependencies.LIEService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_lie_service()
            
            # Verify service was created with correct parameters
            mock_service_class.assert_called_once()
            call_args = mock_service_class.call_args
            print("CALL ARGS:", call_args)

            assert call_args[1].get('timeout', None) == 30
    def test_get_lie_service_error_handling(self):
        """Test LIE service dependency error handling."""
        with patch('app.api.dependencies.LIEService') as mock_service_class:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_service_class.side_effect = Exception("LIE service creation failed")
                
                with pytest.raises(Exception, match="LIE service creation failed"):
                    get_lie_service()
                
                mock_logger.error.assert_called_once_with("Failed to create LIEService: LIE service creation failed")

    def test_get_cis_service_error_handling(self):
        """Test CIS service dependency error handling."""
        with patch('app.api.dependencies.CISService') as mock_service_class:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_service_class.side_effect = Exception("CIS service creation failed")
                
                with pytest.raises(Exception, match="CIS service creation failed"):
                    get_cis_service()
                
                mock_logger.error.assert_called_once_with("Failed to create CISService: CIS service creation failed")

    def test_get_results_service_error_handling(self):
        """Test Results service dependency error handling."""
        with patch('app.api.dependencies.ResultsService') as mock_service_class:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_service_class.side_effect = Exception("Results service creation failed")
                
                with pytest.raises(Exception, match="Results service creation failed"):
                    get_results_service()
                
                mock_logger.error.assert_called_once_with("Failed to create ResultsService: Results service creation failed")

    def test_get_llm_service_error_handling(self):
        """Test LLM service dependency error handling."""
        with patch('app.api.dependencies.LLMService') as mock_service_class:
            with patch('app.api.dependencies.logger') as mock_logger:
                mock_service_class.side_effect = Exception("LLM service creation failed")
                
                with pytest.raises(Exception, match="LLM service creation failed"):
                    get_llm_service()
                
                mock_logger.error.assert_called_once_with("Failed to create LLMService: LLM service creation failed")

    def test_get_celery_app_error_handling(self):
        """Test Celery app dependency error handling."""
        # Since celery_app is imported at module level and the function is simple,
        # we'll test that the function works correctly and logs appropriately
        with patch('app.api.dependencies.celery_app') as mock_celery_app:
            with patch('app.api.dependencies.logger') as mock_logger:
                # Test normal operation
                result = get_celery_app()
                assert result == mock_celery_app
                mock_logger.debug.assert_called_once_with("Celery app dependency provided")
                
                # Test multiple calls to ensure consistency
                result2 = get_celery_app()
                assert result2 == mock_celery_app
                assert result == result2

    def test_get_lie_service_multiple_calls(self):
        """Test LIE service dependency multiple calls."""
        with patch('app.api.dependencies.LIEService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result1 = get_lie_service()
            result2 = get_lie_service()
            
            # Should create new instances each time
            assert result1 == mock_service
            assert result2 == mock_service
            assert mock_service_class.call_count == 2

    def test_get_cis_service(self):
        """Test CIS service dependency."""
        with patch('app.api.dependencies.CISService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_cis_service()
            
            assert result == mock_service
            mock_service_class.assert_called_once()

    # tests/test_api_dependencies.py
    def test_get_cis_service_configuration(self):
        """Test CIS service dependency configuration."""
        with patch('app.api.dependencies.CISService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_cis_service()
            
            # Verify service was created with correct parameters
            mock_service_class.assert_called_once()
            call_args = mock_service_class.call_args  # Corrected from .call.arg
            print("CALL ARGS:", call_args)  # For debugging
            assert call_args[1].get('timeout', None) == 30


    def test_get_cis_service_multiple_calls(self):
        """Test CIS service dependency multiple calls."""
        with patch('app.api.dependencies.CISService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result1 = get_cis_service()
            result2 = get_cis_service()
            
            # Should create new instances each time
            assert result1 == mock_service
            assert result2 == mock_service
            assert mock_service_class.call_count == 2

    def test_get_results_service(self):
        """Test results service dependency."""
        with patch('app.api.dependencies.ResultsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_results_service()
            
            assert result == mock_service
            mock_service_class.assert_called_once()

    def test_get_results_service_configuration(self):
        """Test results service dependency configuration."""
        with patch('app.api.dependencies.ResultsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result = get_results_service()
            
            # Verify service was created with correct parameters
            mock_service_class.assert_called_once()
            call_args = mock_service_class.call_args
            print("CALL ARGS:", call_args)

            assert call_args[1].get('timeout', None) == 30


    def test_get_results_service_multiple_calls(self):
        """Test results service dependency multiple calls."""
        with patch('app.api.dependencies.ResultsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            result1 = get_results_service()
            result2 = get_results_service()
            
            # Should create new instances each time
            assert result1 == mock_service
            assert result2 == mock_service
            assert mock_service_class.call_count == 2

    def test_get_celery_app(self):
        """Test Celery app dependency."""
        with patch('app.api.dependencies.celery_app') as mock_celery_app:
            result = get_celery_app()
            
            assert result == mock_celery_app

    def test_get_celery_app_multiple_calls(self):
        """Test Celery app dependency multiple calls."""
        with patch('app.api.dependencies.celery_app') as mock_celery_app:
            result1 = get_celery_app()
            result2 = get_celery_app()
            
            # Should return same instance
            assert result1 == mock_celery_app
            assert result2 == mock_celery_app
            assert result1 == result2

    def test_dependencies_import(self):
        """Test dependencies import."""
        from app.api.dependencies import (
            get_user_profile_service,
            get_lie_service,
            get_cis_service,
            get_results_service,
            get_celery_app
        )
        
        # All functions should be callable
        assert callable(get_user_profile_service)
        assert callable(get_lie_service)
        assert callable(get_cis_service)
        assert callable(get_results_service)
        assert callable(get_celery_app)

    def test_dependencies_function_signatures(self):
        """Test dependencies function signatures."""
        import inspect
        
        # All functions should have no parameters
        assert len(inspect.signature(get_user_profile_service).parameters) == 0
        assert len(inspect.signature(get_lie_service).parameters) == 0
        assert len(inspect.signature(get_cis_service).parameters) == 0
        assert len(inspect.signature(get_results_service).parameters) == 0
        assert len(inspect.signature(get_celery_app).parameters) == 0

    def test_dependencies_return_types(self):
        """Test dependencies return types."""
        with patch('app.api.dependencies.UserProfileService') as mock_user_service:
            with patch('app.api.dependencies.LIEService') as mock_lie_service:
                with patch('app.api.dependencies.CISService') as mock_cis_service:
                    with patch('app.api.dependencies.ResultsService') as mock_results_service:
                        with patch('app.api.dependencies.celery_app') as mock_celery_app:
                            mock_user_service.return_value = Mock()
                            mock_lie_service.return_value = Mock()
                            mock_cis_service.return_value = Mock()
                            mock_results_service.return_value = Mock()
                            
                            # All should return Mock objects
                            assert isinstance(get_user_profile_service(), Mock)
                            assert isinstance(get_lie_service(), Mock)
                            assert isinstance(get_cis_service(), Mock)
                            assert isinstance(get_results_service(), Mock)
                            assert isinstance(get_celery_app(), Mock)

    def test_dependencies_error_handling(self):
        """Test dependencies error handling."""
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service_class.side_effect = Exception("Service creation failed")
            
            with pytest.raises(Exception):
                get_user_profile_service()

    def test_dependencies_thread_safety(self):
        """Test dependencies thread safety."""
        import threading
        import time
        
        results = []
        
        def test_dependency():
            try:
                with patch('app.api.dependencies.UserProfileService') as mock_service_class:
                    mock_service = Mock()
                    mock_service_class.return_value = mock_service
                    
                    result = get_user_profile_service()
                    results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_dependency, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_dependencies_performance(self):
        """Test dependencies performance."""
        import time
        
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            start_time = time.time()
            for _ in range(1000):
                get_user_profile_service()
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 1.0  # 1 second for 1000 calls

    def test_dependencies_memory_usage(self):
        """Test dependencies memory usage."""
        import gc
        
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Create multiple service instances
            services = []
            for _ in range(100):
                service = get_user_profile_service()
                services.append(service)
            
            # Check memory usage
            assert len(services) == 100
            
            # Clean up
            del services
            gc.collect()

    def test_dependencies_configuration_consistency(self):
        """Test dependencies configuration consistency."""
        with patch('app.api.dependencies.UserProfileService') as mock_user_service:
            with patch('app.api.dependencies.LIEService') as mock_lie_service:
                with patch('app.api.dependencies.CISService') as mock_cis_service:
                    with patch('app.api.dependencies.ResultsService') as mock_results_service:
                        mock_user_service.return_value = Mock()
                        mock_lie_service.return_value = Mock()
                        mock_cis_service.return_value = Mock()
                        mock_results_service.return_value = Mock()
                        
                        # All services should be created with same timeout
                        get_user_profile_service()
                        get_lie_service()
                        get_cis_service()
                        get_results_service()
                        
                        # Verify all services were created with timeout=30
                        for mock_service in [mock_user_service, mock_lie_service, mock_cis_service, mock_results_service]:
                            call_args = mock_service.call_args
                            print("CALL ARGS:", call_args)

                            assert call_args[1].get('timeout', None) == 30


    def test_dependencies_service_isolation(self):
        """Test dependencies service isolation."""
        with patch('app.api.dependencies.UserProfileService') as mock_user_service:
            with patch('app.api.dependencies.LIEService') as mock_lie_service:
                mock_user_service.return_value = Mock()
                mock_lie_service.return_value = Mock()
                
                user_service = get_user_profile_service()
                lie_service = get_lie_service()
                
                # Services should be different instances
                assert user_service != lie_service
                assert mock_user_service.call_count == 1
                assert mock_lie_service.call_count == 1

    def test_dependencies_celery_app_singleton(self):
        """Test dependencies Celery app singleton behavior."""
        with patch('app.api.dependencies.celery_app') as mock_celery_app:
            app1 = get_celery_app()
            app2 = get_celery_app()
            
            # Should return same instance
            assert app1 == app2
            assert app1 == mock_celery_app

    def test_dependencies_import_error_handling(self):
        """Test dependencies import error handling."""
        # Test that imports work correctly
        try:
            from app.api.dependencies import get_user_profile_service
            assert callable(get_user_profile_service)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_dependencies_module_structure(self):
        """Test dependencies module structure."""
        import app.api.dependencies as deps_module
        
        # Check that module has expected attributes
        assert hasattr(deps_module, 'get_user_profile_service')
        assert hasattr(deps_module, 'get_lie_service')
        assert hasattr(deps_module, 'get_cis_service')
        assert hasattr(deps_module, 'get_results_service')
        assert hasattr(deps_module, 'get_celery_app')
        
        # Check that all attributes are callable
        assert callable(deps_module.get_user_profile_service)
        assert callable(deps_module.get_lie_service)
        assert callable(deps_module.get_cis_service)
        assert callable(deps_module.get_results_service)
        assert callable(deps_module.get_celery_app)

    def test_dependencies_fastapi_integration(self):
        """Test dependencies FastAPI integration."""
        from fastapi import Depends
        
        # Test that dependencies can be used with FastAPI Depends
        with patch('app.api.dependencies.UserProfileService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Should work with Depends
            dependency = Depends(get_user_profile_service)
            assert dependency is not None

    def test_dependencies_concurrent_access(self):
        """Test dependencies concurrent access."""
        import asyncio
        
        async def test_dependency():
            with patch('app.api.dependencies.UserProfileService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                result = get_user_profile_service()
                return result
        
        # Create multiple concurrent tasks and run them properly
        tasks = [test_dependency() for _ in range(10)]
        async def _runner():
            return await asyncio.gather(*tasks)
        results = asyncio.run(_runner())
        
        # All should complete successfully
        assert len(results) == 10
        assert all(isinstance(result, Mock) for result in results)

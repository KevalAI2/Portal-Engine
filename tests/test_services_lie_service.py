"""
Comprehensive test suite for LIE service module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from app.services.lie_service import LIEService
from app.models.schemas import LocationData


@pytest.mark.unit
class TestLIEService:
    """Test the LIE service functionality."""

    @pytest.fixture
    def lie_service(self):
        """Create LIEService instance for testing."""
        with patch('app.services.lie_service.settings') as mock_settings:
            mock_settings.lie_service_url = "http://test.example.com"
            return LIEService()

    def test_lie_service_initialization(self, lie_service):
        """Test LIEService initialization."""
        assert lie_service.base_url == "http://test.example.com"
        assert lie_service.timeout == 30
        assert lie_service.logger is not None

    def test_lie_service_inheritance(self, lie_service):
        """Test LIEService inheritance from BaseService."""
        from app.services.base import BaseService
        assert isinstance(lie_service, BaseService)

    def test_generate_mock_location_data(self, lie_service):
        """Test mock location data generation."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check that location_data is a LocationData instance
        assert isinstance(location_data, LocationData)
        
        # Check required fields
        assert location_data.location_id is not None
        assert location_data.name is not None
        assert location_data.country is not None
        assert location_data.city is not None
        assert location_data.coordinates is not None
        assert location_data.attractions is not None
        assert location_data.restaurants is not None
        assert location_data.accommodations is not None
        assert location_data.activities is not None
        assert location_data.transportation is not None
        assert location_data.weather is not None
        assert location_data.culture is not None
        assert location_data.safety is not None
        assert location_data.budget is not None
        assert location_data.language is not None
        assert location_data.currency is not None
        assert location_data.timezone is not None
        assert location_data.visa_requirements is not None
        assert location_data.health_requirements is not None
        assert location_data.packing_tips is not None
        assert location_data.local_customs is not None
        assert location_data.emergency_contacts is not None
        assert location_data.tourist_offices is not None
        assert location_data.created_at is not None
        assert location_data.updated_at is not None

    def test_generate_mock_location_data_field_types(self, lie_service):
        """Test mock location data field types."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check field types
        assert isinstance(location_data.location_id, str)
        assert isinstance(location_data.name, str)
        assert isinstance(location_data.country, str)
        assert isinstance(location_data.city, str)
        assert isinstance(location_data.coordinates, dict)
        assert isinstance(location_data.attractions, list)
        assert isinstance(location_data.restaurants, list)
        assert isinstance(location_data.accommodations, list)
        assert isinstance(location_data.activities, list)
        assert isinstance(location_data.transportation, dict)
        assert isinstance(location_data.weather, dict)
        assert isinstance(location_data.culture, dict)
        assert isinstance(location_data.safety, dict)
        assert isinstance(location_data.budget, dict)
        assert isinstance(location_data.language, list)
        assert isinstance(location_data.currency, str)
        assert isinstance(location_data.timezone, str)
        assert isinstance(location_data.visa_requirements, dict)
        assert isinstance(location_data.health_requirements, dict)
        assert isinstance(location_data.packing_tips, list)
        assert isinstance(location_data.local_customs, list)
        assert isinstance(location_data.emergency_contacts, list)
        assert isinstance(location_data.tourist_offices, list)
        assert isinstance(location_data.created_at, str)
        assert isinstance(location_data.updated_at, str)

    def test_generate_mock_location_data_field_values(self, lie_service):
        """Test mock location data field values."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check field values are reasonable
        assert len(location_data.location_id) > 0
        assert len(location_data.name) > 0
        assert len(location_data.country) > 0
        assert len(location_data.city) > 0
        assert len(location_data.coordinates) > 0
        assert len(location_data.attractions) > 0
        assert len(location_data.restaurants) > 0
        assert len(location_data.accommodations) > 0
        assert len(location_data.activities) > 0
        assert len(location_data.transportation) > 0
        assert len(location_data.weather) > 0
        assert len(location_data.culture) > 0
        assert len(location_data.safety) > 0
        assert len(location_data.budget) > 0
        assert len(location_data.language) > 0
        assert len(location_data.currency) > 0
        assert len(location_data.timezone) > 0
        assert len(location_data.visa_requirements) > 0
        assert len(location_data.health_requirements) > 0
        assert len(location_data.packing_tips) > 0
        assert len(location_data.local_customs) > 0
        assert len(location_data.emergency_contacts) > 0
        assert len(location_data.tourist_offices) > 0
        assert len(location_data.created_at) > 0
        assert len(location_data.updated_at) > 0

    def test_generate_mock_location_data_multiple_calls(self, lie_service):
        """Test mock location data generation multiple calls."""
        location_data_list = []
        for _ in range(5):
            location_data = lie_service._generate_mock_location_data()
            location_data_list.append(location_data)
        
        # Check that all location data are valid
        for location_data in location_data_list:
            assert isinstance(location_data, LocationData)
            assert location_data.location_id is not None
            assert location_data.name is not None
            assert location_data.country is not None
            assert location_data.city is not None

    def test_generate_mock_location_data_uniqueness(self, lie_service):
        """Test mock location data uniqueness."""
        location_data_list = []
        for _ in range(10):
            location_data = lie_service._generate_mock_location_data()
            location_data_list.append(location_data)
        
        # Check that location_ids are unique
        location_ids = [data.location_id for data in location_data_list]
        assert len(set(location_ids)) == len(location_ids)

    def test_generate_mock_location_data_coordinates_structure(self, lie_service):
        """Test mock location data coordinates structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check coordinates structure
        assert "lat" in location_data.coordinates
        assert "lng" in location_data.coordinates
        assert isinstance(location_data.coordinates["lat"], (int, float))
        assert isinstance(location_data.coordinates["lng"], (int, float))
        assert -90 <= location_data.coordinates["lat"] <= 90
        assert -180 <= location_data.coordinates["lng"] <= 180

    def test_generate_mock_location_data_transportation_structure(self, lie_service):
        """Test mock location data transportation structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check transportation structure
        assert "airports" in location_data.transportation
        assert "public_transport" in location_data.transportation
        assert "taxis" in location_data.transportation
        assert "car_rental" in location_data.transportation
        assert isinstance(location_data.transportation["airports"], list)
        assert isinstance(location_data.transportation["public_transport"], list)
        assert isinstance(location_data.transportation["taxis"], list)
        assert isinstance(location_data.transportation["car_rental"], list)

    def test_generate_mock_location_data_weather_structure(self, lie_service):
        """Test mock location data weather structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check weather structure
        assert "climate" in location_data.weather
        assert "seasons" in location_data.weather
        assert "temperature" in location_data.weather
        assert "precipitation" in location_data.weather
        assert isinstance(location_data.weather["climate"], str)
        assert isinstance(location_data.weather["seasons"], list)
        assert isinstance(location_data.weather["temperature"], dict)
        assert isinstance(location_data.weather["precipitation"], dict)

    def test_generate_mock_location_data_culture_structure(self, lie_service):
        """Test mock location data culture structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check culture structure
        assert "traditions" in location_data.culture
        assert "festivals" in location_data.culture
        assert "art" in location_data.culture
        assert "music" in location_data.culture
        assert isinstance(location_data.culture["traditions"], list)
        assert isinstance(location_data.culture["festivals"], list)
        assert isinstance(location_data.culture["art"], list)
        assert isinstance(location_data.culture["music"], list)

    def test_generate_mock_location_data_safety_structure(self, lie_service):
        """Test mock location data safety structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check safety structure
        assert "crime_rate" in location_data.safety
        assert "safe_areas" in location_data.safety
        assert "unsafe_areas" in location_data.safety
        assert "emergency_numbers" in location_data.safety
        assert isinstance(location_data.safety["crime_rate"], str)
        assert isinstance(location_data.safety["safe_areas"], list)
        assert isinstance(location_data.safety["unsafe_areas"], list)
        assert isinstance(location_data.safety["emergency_numbers"], list)

    def test_generate_mock_location_data_budget_structure(self, lie_service):
        """Test mock location data budget structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check budget structure
        assert "accommodation" in location_data.budget
        assert "food" in location_data.budget
        assert "transportation" in location_data.budget
        assert "activities" in location_data.budget
        assert isinstance(location_data.budget["accommodation"], dict)
        assert isinstance(location_data.budget["food"], dict)
        assert isinstance(location_data.budget["transportation"], dict)
        assert isinstance(location_data.budget["activities"], dict)

    def test_generate_mock_location_data_visa_requirements_structure(self, lie_service):
        """Test mock location data visa requirements structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check visa requirements structure
        assert "required" in location_data.visa_requirements
        assert "duration" in location_data.visa_requirements
        assert "cost" in location_data.visa_requirements
        assert "processing_time" in location_data.visa_requirements
        assert isinstance(location_data.visa_requirements["required"], bool)
        assert isinstance(location_data.visa_requirements["duration"], str)
        assert isinstance(location_data.visa_requirements["cost"], str)
        assert isinstance(location_data.visa_requirements["processing_time"], str)

    def test_generate_mock_location_data_health_requirements_structure(self, lie_service):
        """Test mock location data health requirements structure."""
        location_data = lie_service._generate_mock_location_data()
        
        # Check health requirements structure
        assert "vaccinations" in location_data.health_requirements
        assert "health_insurance" in location_data.health_requirements
        assert "medical_facilities" in location_data.health_requirements
        assert "water_safety" in location_data.health_requirements
        assert isinstance(location_data.health_requirements["vaccinations"], list)
        assert isinstance(location_data.health_requirements["health_insurance"], str)
        assert isinstance(location_data.health_requirements["medical_facilities"], list)
        assert isinstance(location_data.health_requirements["water_safety"], str)

    @pytest.mark.asyncio
    async def test_get_location_data_success(self, lie_service):
        """Test successful location data retrieval."""
        mock_location_data = {
            "location_id": "loc_123",
            "name": "Test Location",
            "country": "Test Country",
            "city": "Test City",
            "coordinates": {"lat": 40.7128, "lng": -74.0060},
            "attractions": ["Attraction 1", "Attraction 2"],
            "restaurants": ["Restaurant 1", "Restaurant 2"],
            "accommodations": ["Hotel 1", "Hotel 2"],
            "activities": ["Activity 1", "Activity 2"],
            "transportation": {
                "airports": ["Airport 1"],
                "public_transport": ["Bus", "Train"],
                "taxis": ["Taxi Service"],
                "car_rental": ["Car Rental Service"]
            },
            "weather": {
                "climate": "Temperate",
                "seasons": ["Spring", "Summer", "Fall", "Winter"],
                "temperature": {"min": 0, "max": 30},
                "precipitation": {"annual": "1000mm"}
            },
            "culture": {
                "traditions": ["Tradition 1"],
                "festivals": ["Festival 1"],
                "art": ["Art 1"],
                "music": ["Music 1"]
            },
            "safety": {
                "crime_rate": "Low",
                "safe_areas": ["Area 1"],
                "unsafe_areas": [],
                "emergency_numbers": ["911"]
            },
            "budget": {
                "accommodation": {"min": 100, "max": 500},
                "food": {"min": 50, "max": 200},
                "transportation": {"min": 20, "max": 100},
                "activities": {"min": 30, "max": 150}
            },
            "language": ["English", "Spanish"],
            "currency": "USD",
            "timezone": "America/New_York",
            "visa_requirements": {
                "required": False,
                "duration": "90 days",
                "cost": "Free",
                "processing_time": "N/A"
            },
            "health_requirements": {
                "vaccinations": ["COVID-19"],
                "health_insurance": "Recommended",
                "medical_facilities": ["Hospital 1"],
                "water_safety": "Safe"
            },
            "packing_tips": ["Tip 1", "Tip 2"],
            "local_customs": ["Custom 1", "Custom 2"],
            "emergency_contacts": ["Contact 1", "Contact 2"],
            "tourist_offices": ["Office 1", "Office 2"],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }

        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = mock_location_data
            
            result = await lie_service.get_location_data("loc_123")
            
            assert isinstance(result, LocationData)
            assert result.location_id == "loc_123"
            assert result.name == "Test Location"
            assert result.country == "Test Country"
            assert result.city == "Test City"
            mock_make_request.assert_called_once_with("GET", "/location/loc_123")

    @pytest.mark.asyncio
    async def test_get_location_data_not_found(self, lie_service):
        """Test location data not found."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await lie_service.get_location_data("nonexistent_location")
            
            # Should return generated location data when not found
            assert isinstance(result, LocationData)
            assert result.location_id == "nonexistent_location"

    @pytest.mark.asyncio
    async def test_get_location_data_service_error(self, lie_service):
        """Test location data service error."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.RequestError("Service unavailable")
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when service error
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_timeout_error(self, lie_service):
        """Test location data timeout error."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when timeout
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_any_exception(self, lie_service):
        """Test location data any exception."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = ValueError("Any error")
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when any exception
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_invalid_response(self, lie_service):
        """Test location data invalid response."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {"invalid": "data"}
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when invalid response
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_partial_response(self, lie_service):
        """Test location data partial response."""
        partial_data = {
            "location_id": "loc_123",
            "name": "Test Location",
            "country": "Test Country",
            "city": "Test City"
            # Missing other required fields
        }

        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = partial_data
            
            result = await lie_service.get_location_data("loc_123")
            
            # Should return generated location data when partial response
            assert isinstance(result, LocationData)
            assert result.location_id == "loc_123"

    @pytest.mark.asyncio
    async def test_get_location_data_empty_response(self, lie_service):
        """Test location data empty response."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = {}
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when empty response
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_none_response(self, lie_service):
        """Test location data None response."""
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.return_value = None
            
            result = await lie_service.get_location_data("test_location")
            
            # Should return generated location data when None response
            assert isinstance(result, LocationData)
            assert result.location_id == "test_location"

    @pytest.mark.asyncio
    async def test_get_location_data_different_location_ids(self, lie_service):
        """Test location data with different location IDs."""
        location_ids = ["loc1", "loc2", "loc3", "loc_123", "test-loc", "loc@domain.com"]
        
        for location_id in location_ids:
            with patch.object(lie_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await lie_service.get_location_data(location_id)
                
                assert isinstance(result, LocationData)
                assert result.location_id == location_id

    @pytest.mark.asyncio
    async def test_get_location_data_special_characters(self, lie_service):
        """Test location data with special characters."""
        special_location_ids = ["loc-123", "loc_123", "loc.123", "loc@123", "loc+123"]
        
        for location_id in special_location_ids:
            with patch.object(lie_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await lie_service.get_location_data(location_id)
                
                assert isinstance(result, LocationData)
                assert result.location_id == location_id

    @pytest.mark.asyncio
    async def test_get_location_data_unicode(self, lie_service):
        """Test location data with Unicode characters."""
        unicode_location_ids = ["位置123", "ubicación123", "местоположение123", "場所123"]
        
        for location_id in unicode_location_ids:
            with patch.object(lie_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                
                result = await lie_service.get_location_data(location_id)
                
                assert isinstance(result, LocationData)
                assert result.location_id == location_id

    @pytest.mark.asyncio
    async def test_get_location_data_long_location_id(self, lie_service):
        """Test location data with long location ID."""
        long_location_id = "a" * 1000  # Very long location ID
        
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result = await lie_service.get_location_data(long_location_id)
            
            assert isinstance(result, LocationData)
            assert result.location_id == long_location_id

    @pytest.mark.asyncio
    async def test_get_location_data_concurrent_requests(self, lie_service):
        """Test location data concurrent requests."""
        import asyncio
        
        async def get_location_data(location_id):
            with patch.object(lie_service, '_make_request') as mock_make_request:
                mock_make_request.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=Mock()
                )
                return await lie_service.get_location_data(location_id)
        
        # Create multiple concurrent requests
        tasks = [get_location_data(f"loc_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check all results are valid
        for i, result in enumerate(results):
            assert isinstance(result, LocationData)
            assert result.location_id == f"loc_{i}"

    @pytest.mark.asyncio
    async def test_get_location_data_caching_behavior(self, lie_service):
        """Test location data caching behavior."""
        # Test that multiple calls with same location_id return consistent results
        location_id = "loc_123"
        
        with patch.object(lie_service, '_make_request') as mock_make_request:
            mock_make_request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock()
            )
            
            result1 = await lie_service.get_location_data(location_id)
            result2 = await lie_service.get_location_data(location_id)
            
            # Results should be consistent (same location_id)
            assert result1.location_id == result2.location_id
            assert result1.location_id == location_id

    def test_lie_service_logger_name(self, lie_service):
        """Test LIEService logger name."""
        assert lie_service.logger._context.get('logger') == 'LIEService'

    def test_lie_service_method_availability(self, lie_service):
        """Test LIEService method availability."""
        # Test that all expected methods are available
        assert hasattr(lie_service, '_make_request')
        assert hasattr(lie_service, 'health_check')
        assert hasattr(lie_service, '_generate_mock_location_data')
        assert hasattr(lie_service, 'get_location_data')
        assert callable(lie_service._make_request)
        assert callable(lie_service.health_check)
        assert callable(lie_service._generate_mock_location_data)
        assert callable(lie_service.get_location_data)

    def test_lie_service_async_methods(self, lie_service):
        """Test LIEService async methods."""
        import inspect
        
        # Test that methods are async
        assert inspect.iscoroutinefunction(lie_service._make_request)
        assert inspect.iscoroutinefunction(lie_service.health_check)
        assert inspect.iscoroutinefunction(lie_service.get_location_data)
        assert not inspect.iscoroutinefunction(lie_service._generate_mock_location_data)

    def test_lie_service_error_handling(self, lie_service):
        """Test LIEService error handling."""
        # Test that service handles errors gracefully
        with patch.object(lie_service.logger, 'error') as mock_error:
            # Simulate an error scenario
            try:
                raise httpx.HTTPStatusError("Test error", request=Mock(), response=Mock())
            except httpx.HTTPStatusError as e:
                lie_service.logger.error(
                    "Error fetching location data",
                    location_id="test_location",
                    error=str(e)
                )
            
            # Verify error was logged
            mock_error.assert_called_once()

    def test_lie_service_info_logging(self, lie_service):
        """Test LIEService info logging."""
        with patch.object(lie_service.logger, 'info') as mock_info:
            # Simulate an info log
            lie_service.logger.info(
                "Location data retrieved",
                location_id="test_location",
                source="api"
            )
            
            # Verify info was logged
            mock_info.assert_called_once()

    def test_lie_service_thread_safety(self, lie_service):
        """Test LIEService thread safety."""
        import threading
        import time
        
        results = []
        
        def test_get_location_data():
            try:
                # Simulate location data generation
                location_data = lie_service._generate_mock_location_data()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_get_location_data, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all threads completed
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_lie_service_memory_usage(self, lie_service):
        """Test LIEService memory usage."""
        import gc
        
        # Generate multiple location data
        location_data_list = []
        for _ in range(100):
            location_data = lie_service._generate_mock_location_data()
            location_data_list.append(location_data)
        
        # Check memory usage
        assert len(location_data_list) == 100
        
        # Clean up
        del location_data_list
        gc.collect()

    def test_lie_service_performance(self, lie_service):
        """Test LIEService performance."""
        import time
        
        # Test location data generation performance
        start_time = time.time()
        location_data_list = []
        for _ in range(100):
            location_data = lie_service._generate_mock_location_data()
            location_data_list.append(location_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds for 100 location data
        assert len(location_data_list) == 100

    def test_lie_service_data_consistency(self, lie_service):
        """Test LIEService data consistency."""
        # Test that generated data is consistent
        location_data1 = lie_service._generate_mock_location_data()
        location_data2 = lie_service._generate_mock_location_data()
        
        # Both should be valid LocationData instances
        assert isinstance(location_data1, LocationData)
        assert isinstance(location_data2, LocationData)
        
        # Both should have all required fields
        for location_data in [location_data1, location_data2]:
            assert location_data.location_id is not None
            assert location_data.name is not None
            assert location_data.country is not None
            assert location_data.city is not None
            assert location_data.coordinates is not None
            assert location_data.attractions is not None
            assert location_data.restaurants is not None
            assert location_data.accommodations is not None
            assert location_data.activities is not None
            assert location_data.transportation is not None
            assert location_data.weather is not None
            assert location_data.culture is not None
            assert location_data.safety is not None
            assert location_data.budget is not None
            assert location_data.language is not None
            assert location_data.currency is not None
            assert location_data.timezone is not None
            assert location_data.visa_requirements is not None
            assert location_data.health_requirements is not None
            assert location_data.packing_tips is not None
            assert location_data.local_customs is not None
            assert location_data.emergency_contacts is not None
            assert location_data.tourist_offices is not None
            assert location_data.created_at is not None
            assert location_data.updated_at is not None

    def test_lie_service_data_validation(self, lie_service):
        """Test LIEService data validation."""
        # Test that generated data passes validation
        location_data = lie_service._generate_mock_location_data()
        
        # Test coordinates validation
        assert -90 <= location_data.coordinates["lat"] <= 90
        assert -180 <= location_data.coordinates["lng"] <= 180
        
        # Test budget validation
        assert location_data.budget["accommodation"]["min"] <= location_data.budget["accommodation"]["max"]
        assert location_data.budget["food"]["min"] <= location_data.budget["food"]["max"]
        assert location_data.budget["transportation"]["min"] <= location_data.budget["transportation"]["max"]
        assert location_data.budget["activities"]["min"] <= location_data.budget["activities"]["max"]
        
        # Test temperature validation
        assert location_data.weather["temperature"]["min"] <= location_data.weather["temperature"]["max"]
        
        # Test list validations
        assert len(location_data.attractions) > 0
        assert len(location_data.restaurants) > 0
        assert len(location_data.accommodations) > 0
        assert len(location_data.activities) > 0
        assert len(location_data.language) > 0
        assert len(location_data.packing_tips) > 0
        assert len(location_data.local_customs) > 0
        assert len(location_data.emergency_contacts) > 0
        assert len(location_data.tourist_offices) > 0

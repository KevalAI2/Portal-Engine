"""
Tests for app/models/requests.py
"""
import pytest
from pydantic import ValidationError
from app.models.requests import (
    RecommendationRequest,
    UserProfileRequest,
    ProcessingRequest,
    RefreshRequest,
    ResultsFilterRequest,
    TaskStatusRequest,
    LocationPayload,
    DateRangePayload
)


class TestRecommendationRequest:
    """Test cases for RecommendationRequest model"""
    
    def test_valid_prompt(self):
        """Test valid prompt string"""
        request = RecommendationRequest(prompt="I like concerts")
        assert request.prompt == "I like concerts"
    
    def test_none_prompt(self):
        """Test None prompt (default)"""
        request = RecommendationRequest()
        assert request.prompt is None
    
    def test_empty_string_prompt(self):
        """Test empty string prompt gets converted to None"""
        request = RecommendationRequest(prompt="")
        assert request.prompt is None
    
    def test_whitespace_only_prompt(self):
        """Test whitespace-only prompt gets converted to None"""
        request = RecommendationRequest(prompt="   \n\t  ")
        assert request.prompt is None
    
    def test_stripped_prompt(self):
        """Test prompt gets stripped of whitespace"""
        request = RecommendationRequest(prompt="  I like concerts  ")
        assert request.prompt == "I like concerts"
    
    def test_invalid_prompt_type(self):
        """Test invalid prompt type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            RecommendationRequest(prompt=123)
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_json_schema_extra(self):
        """Test that json_schema_extra is properly configured"""
        schema = RecommendationRequest.model_json_schema()
        assert "example" in schema
        assert "prompt" in schema["example"]
        assert "location" in schema["example"]
        assert "date_range" in schema["example"]
    
    def test_recommendation_request_with_location(self):
        """Test RecommendationRequest with location payload"""
        location = LocationPayload(lat=41.3851, lng=2.1734, city="Barcelona")
        request = RecommendationRequest(
            prompt="I like concerts",
            location=location
        )
        assert request.prompt == "I like concerts"
        assert request.location.lat == 41.3851
        assert request.location.lng == 2.1734
        assert request.location.city == "Barcelona"
        assert request.date_range is None
    
    def test_recommendation_request_with_date_range(self):
        """Test RecommendationRequest with date range payload"""
        date_range = DateRangePayload(
            start="2024-01-01T00:00:00Z",
            end="2024-12-31T23:59:59Z"
        )
        request = RecommendationRequest(
            prompt="I like concerts",
            date_range=date_range
        )
        assert request.prompt == "I like concerts"
        assert request.date_range.start == "2024-01-01T00:00:00Z"
        assert request.date_range.end == "2024-12-31T23:59:59Z"
        assert request.location is None
    
    def test_recommendation_request_with_all_fields(self):
        """Test RecommendationRequest with all fields"""
        location = LocationPayload(lat=41.3851, lng=2.1734, city="Barcelona")
        date_range = DateRangePayload(
            start="2024-01-01T00:00:00Z",
            end="2024-12-31T23:59:59Z"
        )
        request = RecommendationRequest(
            prompt="I like concerts",
            location=location,
            date_range=date_range
        )
        assert request.prompt == "I like concerts"
        assert request.location.lat == 41.3851
        assert request.date_range.start == "2024-01-01T00:00:00Z"
    
    def test_recommendation_request_empty_fields(self):
        """Test RecommendationRequest with all fields as None"""
        request = RecommendationRequest(
            prompt=None,
            location=None,
            date_range=None
        )
        assert request.prompt is None
        assert request.location is None
        assert request.date_range is None


class TestUserProfileRequest:
    """Test cases for UserProfileRequest model"""
    
    def test_valid_user_id(self):
        """Test valid user ID"""
        request = UserProfileRequest(user_id="user123")
        assert request.user_id == "user123"
    
    def test_stripped_user_id(self):
        """Test user ID gets stripped of whitespace"""
        request = UserProfileRequest(user_id="  user123  ")
        assert request.user_id == "user123"
    
    def test_empty_user_id(self):
        """Test empty user ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileRequest(user_id="")
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_whitespace_only_user_id(self):
        """Test whitespace-only user ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileRequest(user_id="   ")
        assert "User ID cannot be empty" in str(exc_info.value)
    
    def test_invalid_user_id_type(self):
        """Test invalid user ID type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileRequest(user_id=123)
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_missing_user_id(self):
        """Test missing user ID raises ValidationError"""
        with pytest.raises(ValidationError):
            UserProfileRequest()


class TestProcessingRequest:
    """Test cases for ProcessingRequest model"""
    
    def test_valid_request_with_default_priority(self):
        """Test valid request with default priority"""
        request = ProcessingRequest(user_id="user123")
        assert request.user_id == "user123"
        assert request.priority == 5
    
    def test_valid_request_with_custom_priority(self):
        """Test valid request with custom priority"""
        request = ProcessingRequest(user_id="user123", priority=8)
        assert request.user_id == "user123"
        assert request.priority == 8
    
    def test_stripped_user_id(self):
        """Test user ID gets stripped of whitespace"""
        request = ProcessingRequest(user_id="  user123  ", priority=3)
        assert request.user_id == "user123"
        assert request.priority == 3
    
    def test_empty_user_id(self):
        """Test empty user ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingRequest(user_id="")
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_invalid_user_id_type(self):
        """Test invalid user ID type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingRequest(user_id=123)
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_priority_too_low(self):
        """Test priority below 1 raises ValidationError"""
        with pytest.raises(ValidationError):
            ProcessingRequest(user_id="user123", priority=0)
    
    def test_priority_too_high(self):
        """Test priority above 10 raises ValidationError"""
        with pytest.raises(ValidationError):
            ProcessingRequest(user_id="user123", priority=11)
    
    def test_priority_boundary_values(self):
        """Test priority boundary values (1 and 10)"""
        request1 = ProcessingRequest(user_id="user123", priority=1)
        assert request1.priority == 1
        
        request10 = ProcessingRequest(user_id="user123", priority=10)
        assert request10.priority == 10
    
    def test_missing_user_id(self):
        """Test missing user ID raises ValidationError"""
        with pytest.raises(ValidationError):
            ProcessingRequest(priority=5)


class TestRefreshRequest:
    """Test cases for RefreshRequest model"""
    
    def test_valid_request_with_default_force(self):
        """Test valid request with default force=False"""
        request = RefreshRequest(user_id="user123")
        assert request.user_id == "user123"
        assert request.force is False
    
    def test_valid_request_with_force_true(self):
        """Test valid request with force=True"""
        request = RefreshRequest(user_id="user123", force=True)
        assert request.user_id == "user123"
        assert request.force is True
    
    def test_stripped_user_id(self):
        """Test user ID gets stripped of whitespace"""
        request = RefreshRequest(user_id="  user123  ", force=True)
        assert request.user_id == "user123"
        assert request.force is True
    
    def test_empty_user_id(self):
        """Test empty user ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            RefreshRequest(user_id="")
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_invalid_user_id_type(self):
        """Test invalid user ID type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            RefreshRequest(user_id=123)
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_missing_user_id(self):
        """Test missing user ID raises ValidationError"""
        with pytest.raises(ValidationError):
            RefreshRequest(force=True)


class TestResultsFilterRequest:
    """Test cases for ResultsFilterRequest model"""
    
    def test_valid_request_with_defaults(self):
        """Test valid request with default values"""
        request = ResultsFilterRequest()
        assert request.category is None
        assert request.limit == 5
        assert request.min_score == 0.0
    
    def test_valid_request_with_all_params(self):
        """Test valid request with all parameters"""
        request = ResultsFilterRequest(
            category="music",
            limit=10,
            min_score=0.5
        )
        assert request.category == "music"
        assert request.limit == 10
        assert request.min_score == 0.5
    
    def test_valid_categories(self):
        """Test all valid categories"""
        valid_categories = ['music', 'movie', 'place', 'event']
        for category in valid_categories:
            request = ResultsFilterRequest(category=category)
            assert request.category == category
    
    def test_case_insensitive_categories(self):
        """Test case insensitive category validation"""
        request = ResultsFilterRequest(category="MUSIC")
        assert request.category == "MUSIC"
    
    def test_invalid_category(self):
        """Test invalid category raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ResultsFilterRequest(category="invalid")
        assert "Category must be one of: music, movie, place, event" in str(exc_info.value)
    
    def test_none_category(self):
        """Test None category is valid"""
        request = ResultsFilterRequest(category=None)
        assert request.category is None
    
    def test_limit_too_low(self):
        """Test limit below 1 raises ValidationError"""
        with pytest.raises(ValidationError):
            ResultsFilterRequest(limit=0)
    
    def test_limit_too_high(self):
        """Test limit above 100 raises ValidationError"""
        with pytest.raises(ValidationError):
            ResultsFilterRequest(limit=101)
    
    def test_limit_boundary_values(self):
        """Test limit boundary values (1 and 100)"""
        request1 = ResultsFilterRequest(limit=1)
        assert request1.limit == 1
        
        request100 = ResultsFilterRequest(limit=100)
        assert request100.limit == 100
    
    def test_min_score_too_low(self):
        """Test min_score below 0.0 raises ValidationError"""
        with pytest.raises(ValidationError):
            ResultsFilterRequest(min_score=-0.1)
    
    def test_min_score_too_high(self):
        """Test min_score above 1.0 raises ValidationError"""
        with pytest.raises(ValidationError):
            ResultsFilterRequest(min_score=1.1)
    
    def test_min_score_boundary_values(self):
        """Test min_score boundary values (0.0 and 1.0)"""
        request0 = ResultsFilterRequest(min_score=0.0)
        assert request0.min_score == 0.0
        
        request1 = ResultsFilterRequest(min_score=1.0)
        assert request1.min_score == 1.0


class TestTaskStatusRequest:
    """Test cases for TaskStatusRequest model"""
    
    def test_valid_task_id(self):
        """Test valid task ID"""
        request = TaskStatusRequest(task_id="task123")
        assert request.task_id == "task123"
    
    def test_stripped_task_id(self):
        """Test task ID gets stripped of whitespace"""
        request = TaskStatusRequest(task_id="  task123  ")
        assert request.task_id == "task123"
    
    def test_empty_task_id(self):
        """Test empty task ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TaskStatusRequest(task_id="")
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_whitespace_only_task_id(self):
        """Test whitespace-only task ID raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TaskStatusRequest(task_id="   ")
        assert "Task ID cannot be empty" in str(exc_info.value)
    
    def test_invalid_task_id_type(self):
        """Test invalid task ID type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TaskStatusRequest(task_id=123)
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_missing_task_id(self):
        """Test missing task ID raises ValidationError"""
        with pytest.raises(ValidationError):
            TaskStatusRequest()
    
    def test_long_task_id(self):
        """Test task ID at maximum length"""
        long_task_id = "a" * 100  # Max length is 100
        request = TaskStatusRequest(task_id=long_task_id)
        assert request.task_id == long_task_id
    
    def test_too_long_task_id(self):
        """Test task ID exceeding maximum length raises ValidationError"""
        with pytest.raises(ValidationError):
            TaskStatusRequest(task_id="a" * 101)  # Exceeds max length of 100


class TestLocationPayload:
    """Test cases for LocationPayload model"""
    
    def test_valid_location_payload(self):
        """Test valid location payload with all fields"""
        payload = LocationPayload(
            lat=41.3851,
            lng=2.1734,
            city="Barcelona",
            country="Spain",
            timezone="Europe/Madrid"
        )
        assert payload.lat == 41.3851
        assert payload.lng == 2.1734
        assert payload.city == "Barcelona"
        assert payload.country == "Spain"
        assert payload.timezone == "Europe/Madrid"
    
    def test_location_payload_minimal(self):
        """Test location payload with only required fields"""
        payload = LocationPayload(lat=0.0, lng=0.0)
        assert payload.lat == 0.0
        assert payload.lng == 0.0
        assert payload.city is None
        assert payload.country is None
        assert payload.timezone is None
    
    def test_location_payload_lat_out_of_range_high(self):
        """Test latitude exceeding maximum value raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(lat=91.0, lng=0.0)
    
    def test_location_payload_lat_out_of_range_low(self):
        """Test latitude below minimum value raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(lat=-91.0, lng=0.0)
    
    def test_location_payload_lng_out_of_range_high(self):
        """Test longitude exceeding maximum value raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(lat=0.0, lng=181.0)
    
    def test_location_payload_lng_out_of_range_low(self):
        """Test longitude below minimum value raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(lat=0.0, lng=-181.0)
    
    def test_location_payload_city_too_long(self):
        """Test city name exceeding maximum length raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(
                lat=0.0, 
                lng=0.0, 
                city="a" * 121  # Exceeds max length of 120
            )
    
    def test_location_payload_country_too_long(self):
        """Test country name exceeding maximum length raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(
                lat=0.0, 
                lng=0.0, 
                country="a" * 121  # Exceeds max length of 120
            )
    
    def test_location_payload_timezone_too_long(self):
        """Test timezone exceeding maximum length raises ValidationError"""
        with pytest.raises(ValidationError):
            LocationPayload(
                lat=0.0, 
                lng=0.0, 
                timezone="a" * 65  # Exceeds max length of 64
            )


class TestDateRangePayload:
    """Test cases for DateRangePayload model"""
    
    def test_valid_date_range_payload(self):
        """Test valid date range payload with ISO8601 dates"""
        payload = DateRangePayload(
            start="2024-01-01T00:00:00Z",
            end="2024-12-31T23:59:59Z"
        )
        assert payload.start == "2024-01-01T00:00:00Z"
        assert payload.end == "2024-12-31T23:59:59Z"
    
    def test_date_range_payload_date_only(self):
        """Test date range payload with date-only ISO8601 format"""
        payload = DateRangePayload(
            start="2024-01-01",
            end="2024-12-31"
        )
        assert payload.start == "2024-01-01"
        assert payload.end == "2024-12-31"
    
    def test_date_range_payload_with_timezone(self):
        """Test date range payload with timezone information"""
        payload = DateRangePayload(
            start="2024-01-01T00:00:00+01:00",
            end="2024-12-31T23:59:59+01:00"
        )
        assert payload.start == "2024-01-01T00:00:00+01:00"
        assert payload.end == "2024-12-31T23:59:59+01:00"
    
    def test_date_range_payload_none_values(self):
        """Test date range payload with None values"""
        payload = DateRangePayload(start=None, end=None)
        assert payload.start is None
        assert payload.end is None
    
    def test_date_range_payload_partial_values(self):
        """Test date range payload with only start or end"""
        payload_start = DateRangePayload(start="2024-01-01", end=None)
        assert payload_start.start == "2024-01-01"
        assert payload_start.end is None
        
        payload_end = DateRangePayload(start=None, end="2024-12-31")
        assert payload_end.start is None
        assert payload_end.end == "2024-12-31"
    
    def test_date_range_payload_invalid_start_format(self):
        """Test invalid start date format raises ValidationError"""
        with pytest.raises(ValidationError):
            DateRangePayload(start="2024-01-01T00:00:00", end="2024-12-31T23:59:59Z")
    
    def test_date_range_payload_invalid_end_format(self):
        """Test invalid end date format raises ValidationError"""
        with pytest.raises(ValidationError):
            DateRangePayload(start="2024-01-01T00:00:00Z", end="2024-12-31T23:59:59")
    
    def test_date_range_payload_invalid_date_string(self):
        """Test invalid date string raises ValidationError"""
        with pytest.raises(ValidationError):
            DateRangePayload(start="not-a-date", end="2024-12-31T23:59:59Z")
    
    def test_date_range_payload_invalid_datetime_string(self):
        """Test invalid datetime string raises ValidationError"""
        with pytest.raises(ValidationError):
            DateRangePayload(start="2024-01-01T25:00:00Z", end="2024-12-31T23:59:59Z")
    
    def test_date_range_payload_empty_string(self):
        """Test empty string raises ValidationError"""
        with pytest.raises(ValidationError):
            DateRangePayload(start="", end="2024-12-31T23:59:59Z")

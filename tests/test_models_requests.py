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
    TaskStatusRequest
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
        assert schema["example"] == {"prompt": "I like concerts"}


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

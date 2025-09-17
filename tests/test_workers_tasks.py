import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.workers.tasks import (
    fetch_user_data,
    build_prompt,
    call_llm,
    cache_results,
    generate_recommendations,
    process_user,
    get_users,
    process_user_comprehensive,
    generate_user_prompt
)
from app.core.constants import RecommendationType
from app.models.schemas import UserProfile, LocationData, InteractionData

@pytest.mark.unit
class TestCeleryTasks:
    """Test suite for Celery tasks in tasks.py."""

    @pytest.fixture
    def mock_user_profile(self):
        """Fixture to create a valid UserProfile."""
        return UserProfile(
            user_id="123",
            name="John Doe", 
            email="john@example.com", 
            age=30, 
            location="New York", 
            interests=["travel"], 
            preferences={}
        )

    @pytest.fixture
    def mock_location_data(self):
        """Fixture to create a valid LocationData."""
        return LocationData(
            user_id="123",
            current_location="New York", 
            home_location="Boston", 
            work_location="NYC", 
            travel_history=["Paris"], 
            location_preferences={"hotel": 1}
        )

    @pytest.fixture
    def mock_interaction_data(self):
        """Fixture to create a valid InteractionData."""
        return InteractionData(
            user_id="123",
            engagement_score=0.8, 
            recent_interactions=[], 
            interaction_history=[], 
            preferences={}
        )

    def test_fetch_user_data_success(self, mock_user_profile, mock_location_data, mock_interaction_data):
        """Test fetch_user_data task success case."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            with patch('app.workers.tasks.LIEService') as mock_lie_service_cls:
                with patch('app.workers.tasks.CISService') as mock_cis_service_cls:
                    mock_user_service = mock_user_service_cls.return_value
                    mock_lie_service = mock_lie_service_cls.return_value
                    mock_cis_service = mock_cis_service_cls.return_value
                    
                    # Use AsyncMock for async methods
                    mock_user_service.get_user_profile = AsyncMock(return_value=mock_user_profile)
                    mock_lie_service.get_location_data = AsyncMock(return_value=mock_location_data)
                    mock_cis_service.get_interaction_data = AsyncMock(return_value=mock_interaction_data)
                    
                    result = fetch_user_data("123")
        
        assert result["success"] is True
        assert result["user_data"]["user_profile"]["user_id"] == "123"

    def test_fetch_user_data_failure(self):
        """Test fetch_user_data task failure case."""
        with patch('app.workers.tasks.UserProfileService', side_effect=Exception("Service failure")):
            result = fetch_user_data("123")
        
        assert result["success"] is False
        assert "Service failure" in result["error"]

    def test_build_prompt_success_standard(self):
        """Test build_prompt task success case with standard prompt."""
        user_data = {
            "user_profile": {"user_id": "123", "name": "John", "email": "john@example.com", "age": 30, "location": "New York", "interests": ["travel"], "preferences": {}},
            "location_data": {"user_id": "123", "current_location": "New York", "home_location": "Boston", "work_location": "NYC", "travel_history": ["Paris"], "location_preferences": {"hotel": 1}},
            "interaction_data": {"user_id": "123", "engagement_score": 0.8, "recent_interactions": [], "interaction_history": [], "preferences": {}}
        }
        
        with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder_cls:
            mock_prompt_builder = mock_prompt_builder_cls.return_value
            mock_prompt_builder.build_recommendation_prompt.return_value = "Standard prompt"
            
            result = build_prompt(user_data, RecommendationType.PLACE.value)
        
        assert result["success"] is True
        assert result["prompt"] == "Standard prompt"

    def test_build_prompt_success_fallback(self):
        """Test build_prompt task success case with fallback prompt."""
        user_data = {}
        
        with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder_cls:
            mock_prompt_builder = mock_prompt_builder_cls.return_value
            mock_prompt_builder.build_fallback_prompt.return_value = "Fallback prompt"
            
            result = build_prompt(user_data, RecommendationType.PLACE.value)
        
        assert result["success"] is True
        assert result["prompt"] == "Fallback prompt"

    def test_build_prompt_invalid_recommendation_type(self):
        """Test build_prompt task with invalid recommendation type."""
        user_data = {
            "user_profile": {"user_id": "123", "name": "John", "email": "john@example.com"}
        }
        
        result = build_prompt(user_data, "INVALID_TYPE")
        
        assert result["success"] is False
        assert "Invalid recommendation type" in result["error"]

    def test_call_llm_success(self):
        """Test call_llm task success case."""
        recommendations = [{"id": 1, "name": "Place1"}]
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.generate_recommendations = AsyncMock(return_value=recommendations)
            
            result = call_llm("Test prompt", {"user_id": "123"}, RecommendationType.PLACE.value)
        
        assert result["success"] is True
        assert result["recommendations"] == recommendations

    def test_call_llm_no_recommendations(self):
        """Test call_llm task when no recommendations are generated."""
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.generate_recommendations = AsyncMock(return_value=[])
            
            result = call_llm("Test prompt", {"user_id": "123"}, RecommendationType.PLACE.value)
        
        assert result["success"] is False
        assert result["error"] == "No recommendations generated by LLM"

    def test_cache_results_success(self):
        """Test cache_results task success case."""
        recommendations = [{"id": 1, "name": "Place1"}]
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.store_recommendations = AsyncMock(return_value=True)
            
            result = cache_results("123", recommendations, RecommendationType.PLACE.value)
        
        assert result["success"] is True
        assert result["user_id"] == "123"

    def test_cache_results_failure(self):
        """Test cache_results task failure case."""
        recommendations = [{"id": 1, "name": "Place1"}]
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.store_recommendations = AsyncMock(return_value=False)
            
            result = cache_results("123", recommendations, RecommendationType.PLACE.value)
        
        assert result["success"] is False
        assert result["error"] == "Failed to store recommendations in cache"

    def test_generate_recommendations_success_cached(self):
        """Test generate_recommendations task success case with cached results."""
        cached_recommendations = Mock(model_dump=lambda: [{"id": 1, "name": "Place1"}])
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.get_recommendations = AsyncMock(return_value=cached_recommendations)
            
            result = generate_recommendations("123", RecommendationType.PLACE.value, force_refresh=False)
        
        assert result["success"] is True
        assert result["source"] == "cache"
        assert result["recommendations"] == [{"id": 1, "name": "Place1"}]

    @patch('app.workers.tasks.cache_results')
    @patch('app.workers.tasks.call_llm')
    @patch('app.workers.tasks.build_prompt')
    @patch('app.workers.tasks.fetch_user_data')
    def test_generate_recommendations_success_generated(self, mock_fetch_user_data, mock_build_prompt, mock_call_llm, mock_cache_results):
        """Test generate_recommendations task success case with generated results."""
        # Mock the .delay and .result for Celery tasks
        mock_fetch_result = Mock()
        mock_fetch_result.result = {"success": True, "user_data": {"user_profile": {}}}
        mock_fetch_user_data.delay.return_value = mock_fetch_result

        mock_build_result = Mock()
        mock_build_result.result = {"success": True, "prompt": "Test prompt"}
        mock_build_prompt.delay.return_value = mock_build_result

        mock_call_result = Mock()
        mock_call_result.result = {"success": True, "recommendations": [{"id": 1, "name": "Place1"}]}
        mock_call_llm.delay.return_value = mock_call_result

        mock_cache_result = Mock()
        mock_cache_result.result = {"success": True, "cached_count": 1}
        mock_cache_results.delay.return_value = mock_cache_result
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.get_recommendations = AsyncMock(return_value=None)
            
            result = generate_recommendations("123", RecommendationType.PLACE.value, force_refresh=True)
        
        assert result["success"] is True
        assert result["source"] == "generated"
        assert result["recommendations"] == [{"id": 1, "name": "Place1"}]

    @patch('app.workers.tasks.fetch_user_data')
    def test_generate_recommendations_failure(self, mock_fetch_user_data):
        """Test generate_recommendations task failure case."""
        mock_fetch_result = Mock()
        mock_fetch_result.result = {"success": False, "error": "Fetch failed"}
        mock_fetch_user_data.delay.return_value = mock_fetch_result
        
        with patch('app.workers.tasks.llm_service') as mock_llm_service:
            mock_llm_service.get_recommendations = AsyncMock(return_value=None)
            
            result = generate_recommendations("123", RecommendationType.PLACE.value)
        
        assert result["success"] is False
        assert "Fetch failed" in result["error"]

    def test_process_user_success(self):
        """Test process_user task success case."""
        user = {"id": "123", "name": "John Doe", "priority": 1}
        
        with patch('os.getpid', return_value=12345):
            with patch('app.workers.tasks.time.sleep'):
                result = process_user(user)
        
        assert result["success"] is True
        assert result["user_id"] == "123"
        assert result["user_name"] == "John Doe"

    def test_process_user_failure(self):
        """Test process_user task failure case."""
        user = {"id": "123", "name": "John Doe"}
        
        # Raise exception in time.sleep instead to avoid logging interference
        with patch('app.workers.tasks.time.sleep', side_effect=Exception("Processing error")):
            result = process_user(user)
        
        assert result["success"] is False
        assert result["error"] == "Processing error"

    def test_get_users_success(self):
        """Test get_users task success case."""
        with patch('app.workers.tasks.process_user_comprehensive.apply_async'):
            with patch('app.workers.tasks.time.sleep'):
                result = get_users(count=3, delay=1)
        
        assert result["success"] is True
        assert result["generated_count"] == 3

    def test_process_user_comprehensive_success(self, mock_user_profile, mock_location_data, mock_interaction_data):
        """Test process_user_comprehensive task success case."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            with patch('app.workers.tasks.LIEService') as mock_lie_service_cls:
                with patch('app.workers.tasks.CISService') as mock_cis_service_cls:
                    with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder_cls:
                        mock_user_service = mock_user_service_cls.return_value
                        mock_lie_service = mock_lie_service_cls.return_value
                        mock_cis_service = mock_cis_service_cls.return_value
                        mock_prompt_builder = mock_prompt_builder_cls.return_value
                        
                        # Use AsyncMock for async methods
                        mock_user_service.get_user_profile = AsyncMock(return_value=mock_user_profile)
                        mock_lie_service.get_location_data = AsyncMock(return_value=mock_location_data)
                        mock_cis_service.get_interaction_data = AsyncMock(return_value=mock_interaction_data)
                        mock_prompt_builder.build_recommendation_prompt.return_value = "Test prompt"
                        
                        with patch('os.getpid', return_value=12345):
                            with patch('app.workers.tasks.time.time', return_value=1234567890.0):
                                result = process_user_comprehensive("123")
        
        assert result["success"] is True
        assert result["user_id"] == "123"
        assert result["generated_prompt"] == "Test prompt"

    def test_process_user_comprehensive_failure(self):
        """Test process_user_comprehensive task failure case."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            mock_user_service = mock_user_service_cls.return_value
            mock_user_service.get_user_profile = AsyncMock(side_effect=Exception("Profile fetch failed"))
            
            result = process_user_comprehensive("123")
        
        assert result["success"] is False
        assert "Profile fetch failed" in result["error"]

    def test_generate_user_prompt_success(self, mock_user_profile, mock_location_data, mock_interaction_data):
        """Test generate_user_prompt task success case."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            with patch('app.workers.tasks.LIEService') as mock_lie_service_cls:
                with patch('app.workers.tasks.CISService') as mock_cis_service_cls:
                    with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder_cls:
                        with patch('app.workers.tasks.llm_service') as mock_llm_service:
                            mock_user_service = mock_user_service_cls.return_value
                            mock_lie_service = mock_lie_service_cls.return_value
                            mock_cis_service = mock_cis_service_cls.return_value
                            mock_prompt_builder = mock_prompt_builder_cls.return_value
                            
                            # Use AsyncMock for async methods
                            mock_user_service.get_user_profile = AsyncMock(return_value=mock_user_profile)
                            mock_lie_service.get_location_data = AsyncMock(return_value=mock_location_data)
                            mock_cis_service.get_interaction_data = AsyncMock(return_value=mock_interaction_data)
                            mock_prompt_builder.build_recommendation_prompt.return_value = "Test prompt"
                            mock_llm_service.generate_recommendations = AsyncMock(return_value={"success": True, "metadata": {"total_recommendations": 1, "categories": ["place"]}})
                            
                            with patch('os.getpid', return_value=12345):
                                result = generate_user_prompt("123", "PLACE", 5)
        
        assert result["success"] is True
        assert result["user_id"] == "123"
        assert result["generated_prompt"] == "Test prompt"

    def test_generate_user_prompt_invalid_recommendation_type(self, mock_user_profile, mock_location_data, mock_interaction_data):
        """Test generate_user_prompt task with invalid recommendation type."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            with patch('app.workers.tasks.LIEService') as mock_lie_service_cls:
                with patch('app.workers.tasks.CISService') as mock_cis_service_cls:
                    with patch('app.workers.tasks.PromptBuilder') as mock_prompt_builder_cls:
                        with patch('app.workers.tasks.llm_service') as mock_llm_service:
                            mock_user_service = mock_user_service_cls.return_value
                            mock_lie_service = mock_lie_service_cls.return_value
                            mock_cis_service = mock_cis_service_cls.return_value
                            mock_prompt_builder = mock_prompt_builder_cls.return_value
                            
                            # Use AsyncMock for async methods
                            mock_user_service.get_user_profile = AsyncMock(return_value=mock_user_profile)
                            mock_lie_service.get_location_data = AsyncMock(return_value=mock_location_data)
                            mock_cis_service.get_interaction_data = AsyncMock(return_value=mock_interaction_data)
                            mock_prompt_builder.build_recommendation_prompt.return_value = "Test prompt"
                            mock_llm_service.generate_recommendations = AsyncMock(return_value={"success": True, "metadata": {"total_recommendations": 1, "categories": ["place"]}})
                            
                            with patch('os.getpid', return_value=12345):
                                result = generate_user_prompt("123", "INVALID_TYPE", 5)
        
        assert result["success"] is True  # Falls back to PLACE
        assert result["generated_prompt"] == "Test prompt"

    def test_generate_user_prompt_failure(self):
        """Test generate_user_prompt task failure case."""
        with patch('app.workers.tasks.UserProfileService') as mock_user_service_cls:
            mock_user_service = mock_user_service_cls.return_value
            mock_user_service.get_user_profile = AsyncMock(side_effect=Exception("Profile fetch failed"))
            
            result = generate_user_prompt("123", "PLACE", 5)
        
        assert result["success"] is False
        assert "Profile fetch failed" in result["error"]
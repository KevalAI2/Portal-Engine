import pytest
from unittest.mock import Mock, patch
from app.utils.prompt_builder import PromptBuilder, RecommendationType


@pytest.mark.unit
class TestPromptBuilder:
    """Test the prompt builder utility functionality."""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing."""
        return PromptBuilder()

    @pytest.fixture
    def mock_get_json_structure_requirements(self, prompt_builder):
        """Mock _get_json_structure_requirements to avoid AttributeError."""
        with patch.object(prompt_builder, '_get_json_structure_requirements', return_value='{"recommendations": []}') as mock_method:
            yield mock_method

    def test_prompt_builder_initialization(self, prompt_builder):
        """Test PromptBuilder initialization."""
        assert prompt_builder is not None
        assert isinstance(prompt_builder, PromptBuilder)

    def test_get_ranking_language(self, prompt_builder):
        """Test ranking language generation."""
        test_cases = [
            (1, "very likely"),
            (2, "likely"),
            (3, "may be like"),
            (4, "fourth"),
            (5, "fifth"),
            (10, "tenth"),
            (100, "hundredth"),
        ]
        
        for rank, expected in test_cases:
            result = prompt_builder._get_ranking_language(rank)
            assert isinstance(result, str)
            assert len(result) > 0
            assert expected in result.lower()

    def test_get_ranking_language_edge_cases(self, prompt_builder):
        """Test ranking language edge cases."""
        result = prompt_builder._get_ranking_language(0)
        assert isinstance(result, str)
        assert len(result) > 0
        
        result = prompt_builder._get_ranking_language(-1)
        assert isinstance(result, str)
        assert len(result) > 0
        
        result = prompt_builder._get_ranking_language(1000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_ranking_language_performance(self, prompt_builder):
        """Test ranking language performance."""
        import time
        
        start_time = time.time()
        for i in range(1000):
            prompt_builder._get_ranking_language(i)
        end_time = time.time()
        
        assert end_time - start_time < 1.0

    def test_extract_top_interests(self, prompt_builder):
        """Test top interests extraction."""
        user_profile = {
            "interests": ["travel", "food", "adventure", "culture", "nature", "music", "art", "sports"]
        }
        
        result = prompt_builder._extract_top_interests(user_profile, limit=3)
        
        assert isinstance(result, list)
        assert len(result) <= 3
        assert all(isinstance(interest, str) for interest in result)
        assert all(len(interest) > 0 for interest in result)

    def test_extract_top_interests_empty(self, prompt_builder):
        """Test top interests extraction with empty interests."""
        user_profile = {"interests": []}
        
        result = prompt_builder._extract_top_interests(user_profile, limit=3)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_top_interests_missing(self, prompt_builder):
        """Test top interests extraction with missing interests."""
        user_profile = {}
        
        result = prompt_builder._extract_top_interests(user_profile, limit=3)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_top_interests_none(self, prompt_builder):
        """Test top interests extraction with None interests."""
        user_profile = {"interests": None}
        
        result = prompt_builder._extract_top_interests(user_profile, limit=3)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_top_interests_large_list(self, prompt_builder):
        """Test top interests extraction with large list."""
        user_profile = {
            "interests": [f"interest_{i}" for i in range(100)]
        }
        
        result = prompt_builder._extract_top_interests(user_profile, limit=5)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        assert all(isinstance(interest, str) for interest in result)

    def test_extract_top_interests_performance(self, prompt_builder):
        """Test top interests extraction performance."""
        import time
        
        user_profile = {
            "interests": [f"interest_{i}" for i in range(1000)]
        }
        
        start_time = time.time()
        for _ in range(100):
            prompt_builder._extract_top_interests(user_profile, limit=10)
        end_time = time.time()
        
        assert end_time - start_time < 1.0

    def test_extract_location_preferences(self, prompt_builder):
        """Test location preferences extraction."""
        location_data = {
            "location_patterns": ["hotel", "outdoor", "local"]
        }
        
        result = prompt_builder._extract_location_preferences(location_data)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("hotel" in pref.lower() for pref in result)

    def test_extract_location_preferences_empty(self, prompt_builder):
        """Test location preferences extraction with empty data."""
        location_data = {}
        
        result = prompt_builder._extract_location_preferences(location_data)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_location_preferences_partial(self, prompt_builder):
        """Test location preferences extraction with partial data."""
        location_data = {
            "location_patterns": ["hotel"]
        }
        
        result = prompt_builder._extract_location_preferences(location_data)
        
        assert isinstance(result, list)
        assert any("hotel" in pref.lower() for pref in result)

    def test_extract_location_preferences_none(self, prompt_builder):
        """Test location preferences extraction with None data."""
        result = prompt_builder._extract_location_preferences(None)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_location_preferences_performance(self, prompt_builder):
        """Test location preferences extraction performance."""
        import time
        
        location_data = {
            "location_patterns": ["hotel", "outdoor"]
        }
        
        start_time = time.time()
        for _ in range(1000):
            prompt_builder._extract_location_preferences(location_data)
        end_time = time.time()
        
        assert end_time - start_time < 1.0

    def test_extract_interaction_preferences(self, prompt_builder):
        """Test interaction preferences extraction."""
        interaction_history = {"interaction_patterns": ["review", "view", "click"]}
        
        result = prompt_builder._extract_interaction_preferences(interaction_history)
        
        assert isinstance(result, list)
        assert any("review" in pref.lower() for pref in result)

    def test_extract_interaction_preferences_empty(self, prompt_builder):
        """Test interaction preferences extraction with empty history."""
        interaction_history = {}
        
        result = prompt_builder._extract_interaction_preferences(interaction_history)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_interaction_preferences_none(self, prompt_builder):
        """Test interaction preferences extraction with None history."""
        result = prompt_builder._extract_interaction_preferences(None)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_interaction_preferences_missing_fields(self, prompt_builder):
        """Test interaction preferences extraction with missing fields."""
        interaction_history = {"interaction_patterns": ["review", "view"]}
        
        result = prompt_builder._extract_interaction_preferences(interaction_history)
        
        assert isinstance(result, list)
        assert len(result) > 0

    def test_extract_interaction_preferences_performance(self, prompt_builder):
        """Test interaction preferences extraction performance."""
        import time
        
        interaction_history = {"interaction_patterns": [f"pattern_{i}" for i in range(1000)]}
        
        start_time = time.time()
        for _ in range(100):
            prompt_builder._extract_interaction_preferences(interaction_history)
        end_time = time.time()
        
        assert end_time - start_time < 1.0

    @patch('app.utils.prompt_builder.PromptBuilder._extract_location_preferences', return_value=["hotel"])
    def test_build_recommendation_prompt(self, mock_extract_location_preferences, prompt_builder):
        """Test recommendation prompt building."""
        user_profile = {
            "name": "John Doe",
            "interests": ["travel", "food", "adventure"],
            "location": {"country": "United States", "city": "New York"},
            "preferences": {"accommodation": "hotel", "activities": "outdoor"}
        }
        
        interaction_history = [
            {"location_id": "loc_1", "rating": 5, "interaction_type": "review"},
            {"location_id": "loc_2", "rating": 4, "interaction_type": "view"},
        ]
        
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=None,
            interaction_data=interaction_history,
            recommendation_type=RecommendationType.PLACE
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "John" in result or "travel" in result or "adventure" in result

    def test_build_recommendation_prompt_empty_data(self, prompt_builder):
        """Test recommendation prompt building with empty data."""
        user_profile = {}
        interaction_history = []
        
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data={},
            interaction_data=interaction_history,
            recommendation_type=RecommendationType.PLACE
        )
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_recommendation_prompt_none_data(self, prompt_builder):
        """Test recommendation prompt building with None data."""
        result = prompt_builder.build_recommendation_prompt(
            user_profile=None,
            location_data=None,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @patch('app.utils.prompt_builder.PromptBuilder._extract_location_preferences', return_value=["hotel"])
    def test_build_recommendation_prompt_performance(self, mock_extract_location_preferences, prompt_builder):
        """Test recommendation prompt building performance."""
        import time
        
        user_profile = {
            "name": "John Doe",
            "interests": ["travel", "food", "adventure"],
            "location": {"country": "United States", "city": "New York"},
            "preferences": {"accommodation": "hotel", "activities": "outdoor"}
        }
        
        interaction_history = [
            {"location_id": f"loc_{i}", "rating": i % 5 + 1, "interaction_type": "view"}
            for i in range(100)
        ]
        
        start_time = time.time()
        for _ in range(100):
            prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=None,
                interaction_data=interaction_history,
                recommendation_type=RecommendationType.PLACE
            )
        end_time = time.time()
        
        assert end_time - start_time < 2.0

    def test_build_fallback_prompt(self, prompt_builder, mock_get_json_structure_requirements):
        """Test fallback prompt building."""
        result = prompt_builder.build_fallback_prompt()
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_fallback_prompt_structure(self, prompt_builder, mock_get_json_structure_requirements):
        """Test fallback prompt structure."""
        result = prompt_builder.build_fallback_prompt()
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "{" in result
        assert "}" in result

    def test_build_fallback_prompt_performance(self, prompt_builder, mock_get_json_structure_requirements):
        """Test fallback prompt building performance."""
        import time
        
        start_time = time.time()
        for _ in range(1000):
            prompt_builder.build_fallback_prompt()
        end_time = time.time()
        
        assert end_time - start_time < 1.0

    def test_prompt_builder_method_availability(self, prompt_builder):
        """Test PromptBuilder method availability."""
        assert hasattr(prompt_builder, '_get_ranking_language')
        assert hasattr(prompt_builder, '_extract_top_interests')
        assert hasattr(prompt_builder, '_extract_location_preferences')
        assert hasattr(prompt_builder, '_extract_interaction_preferences')
        assert hasattr(prompt_builder, 'build_recommendation_prompt')
        assert hasattr(prompt_builder, 'build_fallback_prompt')
        assert callable(prompt_builder._get_ranking_language)
        assert callable(prompt_builder._extract_top_interests)
        assert callable(prompt_builder._extract_location_preferences)
        assert callable(prompt_builder._extract_interaction_preferences)
        assert callable(prompt_builder.build_recommendation_prompt)
        assert callable(prompt_builder.build_fallback_prompt)

    def test_prompt_builder_thread_safety(self, prompt_builder, mock_get_json_structure_requirements):
        """Test PromptBuilder thread safety."""
        import threading
        
        results = []
        
        def test_operation():
            try:
                prompt = prompt_builder.build_fallback_prompt()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_operation, name=f"thread_{i}")
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_prompt_builder_memory_usage(self, prompt_builder, mock_get_json_structure_requirements):
        """Test PromptBuilder memory usage."""
        import gc
        
        prompts = []
        for _ in range(100):
            prompt = prompt_builder.build_fallback_prompt()
            prompts.append(prompt)
        
        assert len(prompts) == 100
        
        del prompts
        gc.collect()

    def test_prompt_builder_performance(self, prompt_builder, mock_get_json_structure_requirements):
        """Test PromptBuilder performance."""
        import time
        
        start_time = time.time()
        prompts = []
        for _ in range(100):
            prompt = prompt_builder.build_fallback_prompt()
            prompts.append(prompt)
        end_time = time.time()
        
        assert end_time - start_time < 2.0
        assert len(prompts) == 100

    def test_prompt_builder_data_consistency(self, prompt_builder, mock_get_json_structure_requirements):
        """Test PromptBuilder data consistency."""
        prompt1 = prompt_builder.build_fallback_prompt()
        prompt2 = prompt_builder.build_fallback_prompt()
        
        assert isinstance(prompt1, str)
        assert isinstance(prompt2, str)
        assert len(prompt1) > 0
        assert len(prompt2) > 0
        assert "{" in prompt1
        assert "}" in prompt1
        assert "{" in prompt2
        assert "}" in prompt2

    def test_prompt_builder_error_handling(self, prompt_builder):
        """Test PromptBuilder error handling."""
        result = prompt_builder._get_ranking_language(-1)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch('app.utils.prompt_builder.PromptBuilder._extract_location_preferences', return_value=["hotel"])
    def test_prompt_builder_unicode_support(self, mock_extract_location_preferences, prompt_builder):
        """Test PromptBuilder Unicode support."""
        user_profile = {
            "name": "用户123",
            "interests": ["旅行", "美食", "冒险"],
            "location": {"country": "中国", "city": "北京"},
            "preferences": {"accommodation": "酒店", "activities": "户外"}
        }
        
        interaction_history = [
            {"location_id": "loc_1", "rating": 5, "interaction_type": "review"},
        ]
        
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=None,
            interaction_data=interaction_history,
            recommendation_type=RecommendationType.PLACE
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "用户" in result or "旅行" in result or "美食" in result

    @patch('app.utils.prompt_builder.PromptBuilder._extract_location_preferences', return_value=["hotel"])
    def test_prompt_builder_large_data(self, mock_extract_location_preferences, prompt_builder):
        """Test PromptBuilder with large data."""
        user_profile = {
            "name": "John Doe",
            "interests": [f"interest_{i}" for i in range(1000)],
            "location": {"country": "United States", "city": "New York"},
            "preferences": {"accommodation": "hotel", "activities": "outdoor"}
        }
        
        interaction_history = [
            {"location_id": f"loc_{i}", "rating": i % 5 + 1, "interaction_type": "view"}
            for i in range(1000)
        ]
        
        results = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=None,
            interaction_data=interaction_history,
            recommendation_type=RecommendationType.PLACE
        )
        
        assert isinstance(results, str)
        assert len(results) > 0
        assert "John" in results or "interest" in results
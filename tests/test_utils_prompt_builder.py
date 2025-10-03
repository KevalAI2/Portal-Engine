import pytest
from unittest.mock import Mock, patch
from app.utils.prompt_builder import PromptBuilder, RecommendationType
from app.models.schemas import UserProfile, LocationData, InteractionData
import time
import threading
import gc

@pytest.mark.unit
class TestPromptBuilder:
    """Test suite for PromptBuilder utility functionality."""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing."""
        return PromptBuilder()

    def test_prompt_builder_initialization(self, prompt_builder):
        """Test PromptBuilder initialization."""
        assert isinstance(prompt_builder, PromptBuilder)
        assert prompt_builder.logger is not None

    def test_get_ranking_language_integer(self, prompt_builder):
        """Test _get_ranking_language with integer inputs."""
        test_cases = [
            (1, "very likely"),
            (2, "likely"),
            (3, "somewhat likely"),
            (4, "fourth"),
            (10, "tenth"),
            (0, "unknown rank"),
            (-1, "unknown rank"),
        ]
        for rank, expected in test_cases:
            result = prompt_builder._get_ranking_language(rank)
            assert isinstance(result, str)
            assert result == expected

    def test_get_ranking_language_float(self, prompt_builder):
        """Test _get_ranking_language with float inputs."""
        test_cases = [
            (0.95, "very likely"),
            (0.85, "likely"),
            (0.75, "somewhat likely"),
            (0.65, "somewhat interested in"),
            (0.55, "not very interested in"),
            (0.45, "not like"),
        ]
        for score, expected in test_cases:
            result = prompt_builder._get_ranking_language(score)
            assert isinstance(result, str)
            assert result == expected

    def test_get_ranking_language_invalid(self, prompt_builder):
        """Test _get_ranking_language with invalid inputs."""
        result = prompt_builder._get_ranking_language(0.1)
        assert isinstance(result, str)
        assert result == "not like"  # Default for unhandled types

    def test_get_ranking_language_performance(self, prompt_builder):
        """Test _get_ranking_language performance."""
        start_time = time.time()
        for i in range(1000):
            prompt_builder._get_ranking_language(i % 5 + 0.5)
        end_time = time.time()
        assert end_time - start_time < 1.0

    def test_extract_top_interests_simple(self, prompt_builder):
        """Test _extract_top_interests with simple interests list."""
        profile_data = {
            "interests": ["travel", "food", "adventure", "culture"]
        }
        result = prompt_builder._extract_top_interests(profile_data, limit=3)
        assert result == ["very likely travel", "very likely food", "very likely adventure"]

    def test_extract_top_interests_preferences(self, prompt_builder):
        """Test _extract_top_interests with structured preferences."""
        profile_data = {
            "preferences": {
                "Keywords (legacy)": {
                    "example_values": [
                        {"value": "hiking", "similarity_score": 0.9},
                        {"value": "museums", "similarity_score": 0.8}
                    ]
                },
                "Archetypes (legacy)": {
                    "example_values": [
                        {"value": "explorer", "similarity_score": 0.7}
                    ]
                },
                "Music Genres": {
                    "example_values": [
                        {"value": "jazz", "similarity_score": 0.6}
                    ]
                },
                "Dining preferences (cuisine)": {
                    "example_values": [
                        {"value": "Italian", "similarity_score": 0.95}
                    ]
                }
            }
        }
        result = prompt_builder._extract_top_interests(profile_data, limit=5)
        assert result == [
            "very likely hiking",
            "likely museums",
            "somewhat likely explorer",
            "somewhat interested in jazz",
            "very likely Italian"
        ]

    def test_extract_top_interests_empty(self, prompt_builder):
        """Test _extract_top_interests with empty or invalid data."""
        test_cases = [
            ({"interests": []}, []),
            ({}, []),
            ({"interests": None}, []),
            ({"preferences": {}}, []),
        ]
        for profile_data, expected in test_cases:
            result = prompt_builder._extract_top_interests(profile_data)
            assert result == expected

    def test_extract_top_interests_malformed(self, prompt_builder):
        """Test _extract_top_interests with malformed preferences."""
        profile_data = {
            "preferences": {
                "Keywords (legacy)": {
                    "example_values": [{"value": "hiking"}]  # Missing similarity_score
                }
            }
        }
        result = prompt_builder._extract_top_interests(profile_data)
        assert result == []

    def test_extract_top_interests_performance(self, prompt_builder):
        """Test _extract_top_interests performance."""
        profile_data = {
            "interests": [f"interest_{i}" for i in range(1000)],
            "preferences": {
                "Keywords (legacy)": {
                    "example_values": [{"value": f"keyword_{i}", "similarity_score": 0.9} for i in range(500)]
                }
            }
        }
        start_time = time.time()
        for _ in range(100):
            prompt_builder._extract_top_interests(profile_data, limit=10)
        end_time = time.time()
        assert end_time - start_time < 1.0

    def test_extract_location_preferences_simple(self, prompt_builder):
        """Test _extract_location_preferences with simple location_patterns."""
        location_data = {
            "location_patterns": ["hotel", "outdoor", "cafe"]
        }
        result = prompt_builder._extract_location_preferences(location_data)
        assert result == ["very likely hotel", "very likely outdoor", "very likely cafe"]

    def test_extract_location_preferences_structured(self, prompt_builder):
        """Test _extract_location_preferences with structured location_patterns."""
        location_data = {
            "location_patterns": [
                {"venue_type": "restaurant", "similarity": 0.9},
                {"venue_type": "park", "similarity": 0.8}
            ]
        }
        result = prompt_builder._extract_location_preferences(location_data)
        assert result == ["very likely restaurant", "likely park"]

    def test_extract_location_preferences_empty(self, prompt_builder):
        """Test _extract_location_preferences with empty or invalid data."""
        test_cases = [
            ({}, []),
            ({"location_patterns": []}, []),
            (None, []),
        ]
        for location_data, expected in test_cases:
            result = prompt_builder._extract_location_preferences(location_data)
            assert result == expected

    def test_extract_location_preferences_malformed(self, prompt_builder):
        """Test _extract_location_preferences with malformed data."""
        location_data = {
            "location_patterns": [{"venue_type": "restaurant"}]  # Missing similarity
        }
        result = prompt_builder._extract_location_preferences(location_data)
        assert result == []

    def test_extract_location_preferences_performance(self, prompt_builder):
        """Test _extract_location_preferences performance."""
        location_data = {
            "location_patterns": [{"venue_type": f"venue_{i}", "similarity": 0.9} for i in range(1000)]
        }
        start_time = time.time()
        for _ in range(100):
            prompt_builder._extract_location_preferences(location_data)
        end_time = time.time()
        assert end_time - start_time < 1.0

    def test_extract_interaction_preferences_simple(self, prompt_builder):
        """Test _extract_interaction_preferences with simple interaction_patterns."""
        interaction_data = {
            "interaction_patterns": ["review", "view", "click"]
        }
        result = prompt_builder._extract_interaction_preferences(interaction_data)
        assert result == ["very likely review", "very likely view", "very likely click"]

    def test_extract_interaction_preferences_structured(self, prompt_builder):
        """Test _extract_interaction_preferences with structured interaction_patterns."""
        interaction_data = {
            "interaction_patterns": [
                {"content_type": "article", "similarity": 0.9},
                {"content_type": "video", "similarity": 0.7}
            ]
        }
        result = prompt_builder._extract_interaction_preferences(interaction_data)
        assert result == ["very likely article", "somewhat likely video"]

    def test_extract_interaction_preferences_empty(self, prompt_builder):
        """Test _extract_interaction_preferences with empty or invalid data."""
        test_cases = [
            ({}, []),
            ({"interaction_patterns": []}, []),
            (None, []),
        ]
        for interaction_data, expected in test_cases:
            result = prompt_builder._extract_interaction_preferences(interaction_data)
            assert result == expected

    def test_extract_interaction_preferences_malformed(self, prompt_builder):
        """Test _extract_interaction_preferences with malformed data."""
        interaction_data = {
            "interaction_patterns": [{"content_type": "article"}]  # Missing similarity
        }
        result = prompt_builder._extract_interaction_preferences(interaction_data)
        assert result == []

    def test_extract_interaction_preferences_performance(self, prompt_builder):
        """Test _extract_interaction_preferences performance."""
        interaction_data = {
            "interaction_patterns": [{"content_type": f"content_{i}", "similarity": 0.9} for i in range(1000)]
        }
        start_time = time.time()
        for _ in range(100):
            prompt_builder._extract_interaction_preferences(interaction_data)
        end_time = time.time()
        assert end_time - start_time < 1.0

    def test_get_complete_json_structure(self, prompt_builder):
        """Test _get_complete_json_structure with different cities."""
        result = prompt_builder._get_complete_json_structure(current_city="Paris")
        assert isinstance(result, str)
        assert len(result) > 0
        assert '"movies": [' in result
        assert '"music": [' in result
        assert '"places": [' in result
        assert '"events": [' in result

    def test_get_complete_json_structure_performance(self, prompt_builder):
        """Test _get_complete_json_structure performance."""
        start_time = time.time()
        for _ in range(1000):
            prompt_builder._get_complete_json_structure()
        end_time = time.time()
        assert end_time - start_time < 1.0

    def test_build_recommendation_prompt_with_models(self, prompt_builder):
        """Test build_recommendation_prompt with Pydantic models."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", age=30, location="New York", interests=["travel"], preferences={}, email="john@example.com"
        )
        location_data = LocationData(
            user_id="123", current_location="New York", home_location="Boston", location_preferences={"hotel": 1}
        )
        interaction_data = InteractionData(
            user_id="123", engagement_score=0.8, interaction_patterns=["review"]
        )
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=location_data,
            interaction_data=interaction_data,
            recommendation_type=RecommendationType.PLACE,
            max_results=5
        )
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "New York" in result
        assert "very likely travel" in result
        assert "0.80" in result

    def test_build_recommendation_prompt_none_data(self, prompt_builder):
        """Test build_recommendation_prompt with None data."""
        result = prompt_builder.build_recommendation_prompt(
            user_profile=None,
            location_data=None,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert isinstance(result, str)
        assert "Unknown User" in result
        assert "Barcelona" in result
        assert "General entertainment preferences" in result

    def test_build_recommendation_prompt_malformed_location(self, prompt_builder):
        """Test build_recommendation_prompt with malformed location data."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", age=30, location="New York", interests=["travel"], preferences={}, email="john@example.com"
        )
        location_data = {"current_location": {"invalid": "data"}}  # Malformed dict
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=location_data,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "Barcelona" in result  # Falls back to default

    def test_build_recommendation_prompt_performance(self, prompt_builder):
        """Test build_recommendation_prompt performance."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", interests=[f"interest_{i}" for i in range(50)], preferences={}, email="john@example.com"
        )
        start_time = time.time()
        for _ in range(100):
            prompt_builder.build_recommendation_prompt(
                user_profile=user_profile,
                location_data=None,
                interaction_data=None,
                recommendation_type=RecommendationType.PLACE
            )
        end_time = time.time()
        assert end_time - start_time < 2.0

    def test_build_fallback_prompt_full_data(self, prompt_builder):
        """Test build_fallback_prompt with full data."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", age=30, home_location="Boston", interests=["travel"], preferences={}, email="john@example.com"
        )
        location_data = LocationData(
            user_id="123", current_location="New York", home_location="Boston", location_preferences={"hotel": 1}
        )
        interaction_data = InteractionData(
            user_id="123", engagement_score=0.8, interaction_patterns=["review"]
        )
        result = prompt_builder.build_fallback_prompt(
            user_profile=user_profile,
            location_data=location_data,
            interaction_data=interaction_data,
            recommendation_type=RecommendationType.PLACE,
            max_results=5
        )
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "New York" in result
        assert "very likely travel" in result
        assert "0.80" in result
        assert "Available data: user profile, location data, interaction data" in result

    def test_build_fallback_prompt_partial_data(self, prompt_builder):
        """Test build_fallback_prompt with partial data."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", interests=["travel"], preferences={}, email="john@example.com"
        )
        result = prompt_builder.build_fallback_prompt(
            user_profile=user_profile,
            location_data=None,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "Barcelona" in result
        assert "Available data: user profile" in result

    def test_build_fallback_prompt_invalid_inputs(self, prompt_builder, caplog):
        """Test build_fallback_prompt with invalid max_results and recommendation_type."""
        result = prompt_builder.build_fallback_prompt(
            user_profile=None,
            location_data=None,
            interaction_data=None,
            recommendation_type="INVALID",
            max_results=-1
        )
        assert isinstance(result, str)
        assert "Barcelona" in result
        assert "Friend" in result
        assert "Invalid max_results -1, defaulting to 10" in caplog.text
        assert "Invalid recommendation_type INVALID, defaulting to PLACE" in caplog.text

    def test_build_fallback_prompt_error_handling(self, prompt_builder, caplog):
        """Test build_fallback_prompt with error in data extraction."""
        user_profile = Mock()
        user_profile.model_dump.side_effect = Exception("'Mock' object is not subscriptable")
        result = prompt_builder.build_fallback_prompt(
            user_profile=user_profile,
            location_data=None,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert isinstance(result, str)
        assert "Friend" in result
        assert "Error extracting user profile: 'Mock' object is not subscriptable" in caplog.text

    def test_build_fallback_prompt_performance(self, prompt_builder):
        """Test build_fallback_prompt performance."""
        user_profile = UserProfile(
            user_id="123", name="John Doe", interests=[f"interest_{i}" for i in range(50)], preferences={}, email="john@example.com"
        )
        start_time = time.time()
        for _ in range(100):
            prompt_builder.build_fallback_prompt(
                user_profile=user_profile,
                location_data=None,
                interaction_data=None,
                recommendation_type=RecommendationType.PLACE
            )
        end_time = time.time()
        assert end_time - start_time < 2.0

    def test_prompt_builder_unicode_support(self, prompt_builder):
        """Test PromptBuilder Unicode support."""
        user_profile = UserProfile(
            user_id="123", name="用户123", interests=["旅行", "美食"], preferences={}, email="user@example.com"
        )
        location_data = LocationData(
            user_id="123", current_location="北京", location_preferences={"酒店": 1}
        )
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=location_data,
            interaction_data=None,
            recommendation_type=RecommendationType.PLACE
        )
        assert "用户123" in result
        assert "北京" in result
        assert "very likely 旅行" in result

    def test_prompt_builder_thread_safety(self, prompt_builder):
        """Test PromptBuilder thread safety."""
        results = []
        def test_operation():
            try:
                prompt = prompt_builder.build_fallback_prompt()
                results.append(f"success_{threading.current_thread().name}")
            except Exception as e:
                results.append(f"error_{threading.current_thread().name}: {e}")
        threads = [threading.Thread(target=test_operation, name=f"thread_{i}") for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(results) == 5
        assert all(result.startswith("success_") for result in results)

    def test_prompt_builder_memory_usage(self, prompt_builder):
        """Test PromptBuilder memory usage."""
        prompts = []
        for _ in range(100):
            prompt = prompt_builder.build_fallback_prompt()
            prompts.append(prompt)
        
        assert len(prompts) == 100
        
        del prompts
        gc.collect()

    def test_prompt_builder_performance(self, prompt_builder):
        """Test PromptBuilder performance."""
        start_time = time.time()
        prompts = []
        for _ in range(100):
            prompt = prompt_builder.build_fallback_prompt()
            prompts.append(prompt)
        end_time = time.time()
        
        assert end_time - start_time < 2.0
        assert len(prompts) == 100

    def test_prompt_builder_data_consistency(self, prompt_builder):
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
        try:
            result = prompt_builder._get_ranking_language(-1)
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            assert False, f"Unexpected exception: {e}"

    def test_prompt_builder_large_data(self, prompt_builder):
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
        
        result = prompt_builder.build_recommendation_prompt(
            user_profile=user_profile,
            location_data=None,  # Matches implementation expectation
            interaction_data=interaction_history,
            recommendation_type=RecommendationType.PLACE
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "John" in result or "interest" in result
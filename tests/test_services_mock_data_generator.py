"""
Tests for mock data generator service
"""
import pytest
from datetime import datetime
from unittest.mock import patch, Mock

from app.services.mock_data_generator import (
    DataQuality, MockDataConfig, MockDataGenerator, mock_data_generator
)


class TestDataQuality:
    """Test DataQuality enum"""
    
    def test_data_quality_values(self):
        """Test data quality enum values"""
        assert DataQuality.BASIC == "basic"
        assert DataQuality.REALISTIC == "realistic"
        assert DataQuality.PREMIUM == "premium"


class TestMockDataConfig:
    """Test MockDataConfig dataclass"""
    
    def test_mock_data_config_defaults(self):
        """Test MockDataConfig with default values"""
        config = MockDataConfig()
        
        assert config.quality == DataQuality.REALISTIC
        assert config.locale == "en_US"
        assert config.seed is None
        assert config.include_optional_fields is True
        assert config.realistic_relationships is True
        assert config.data_consistency is True
    
    def test_mock_data_config_custom(self):
        """Test MockDataConfig with custom values"""
        config = MockDataConfig(
            quality=DataQuality.PREMIUM,
            locale="es_ES",
            seed=12345,
            include_optional_fields=False,
            realistic_relationships=False,
            data_consistency=False
        )
        
        assert config.quality == DataQuality.PREMIUM
        assert config.locale == "es_ES"
        assert config.seed == 12345
        assert config.include_optional_fields is False
        assert config.realistic_relationships is False
        assert config.data_consistency is False


class TestMockDataGenerator:
    """Test MockDataGenerator class"""
    
    @pytest.fixture
    def generator(self):
        """Create MockDataGenerator instance"""
        return MockDataGenerator()
    
    @pytest.fixture
    def premium_generator(self):
        """Create MockDataGenerator with premium quality"""
        config = MockDataConfig(quality=DataQuality.PREMIUM, seed=12345)
        return MockDataGenerator(config)
    
    def test_generator_initialization(self, generator):
        """Test generator initialization"""
        assert generator.config is not None
        assert generator.config.quality == DataQuality.REALISTIC
        assert generator.logger is not None
        assert isinstance(generator._user_consistency, dict)
        assert isinstance(generator._location_consistency, dict)
        assert isinstance(generator._interaction_consistency, dict)
        assert len(generator.cities) > 0
        assert len(generator.venue_types) > 0
        assert len(generator.content_types) > 0
        assert len(generator.interaction_types) > 0
        assert isinstance(generator.genres, dict)
    
    def test_generator_with_seed(self, premium_generator):
        """Test generator with seed for reproducible data"""
        assert premium_generator.config.seed == 12345
        assert premium_generator.config.quality == DataQuality.PREMIUM
    
    def test_generate_user_profile_data_basic(self, generator):
        """Test generating basic user profile data"""
        user_id = "test_user_123"
        profile_data = generator.generate_user_profile_data(user_id)
        
        assert profile_data["user_id"] == user_id
        assert "name" in profile_data
        assert "email" in profile_data
        assert "age" in profile_data
        assert "location" in profile_data
        assert "preferences" in profile_data
        assert "interests" in profile_data
        assert "generated_at" in profile_data
        assert "profile_completeness" in profile_data
        assert "data_quality" in profile_data
        
        assert isinstance(profile_data["age"], int)
        assert 18 <= profile_data["age"] <= 65
        assert isinstance(profile_data["interests"], list)
        assert len(profile_data["interests"]) >= 3
        assert isinstance(profile_data["profile_completeness"], float)
        assert 0 <= profile_data["profile_completeness"] <= 1
    
    def test_generate_user_profile_data_premium(self, premium_generator):
        """Test generating premium user profile data"""
        user_id = "test_user_456"
        profile_data = premium_generator.generate_user_profile_data(user_id)
        
        assert profile_data["user_id"] == user_id
        assert profile_data["data_quality"] == "premium"
        assert "phone" in profile_data
        assert "gender" in profile_data
        assert "occupation" in profile_data
        assert "education_level" in profile_data
        assert "income_range" in profile_data
        assert "marital_status" in profile_data
        assert "languages" in profile_data
        assert "timezone" in profile_data
        assert "created_at" in profile_data
    
    def test_generate_user_profile_data_without_optional_fields(self, generator):
        """Test generating user profile data without optional fields"""
        config = MockDataConfig(include_optional_fields=False)
        generator = MockDataGenerator(config)
        
        user_id = "test_user_789"
        profile_data = generator.generate_user_profile_data(user_id)
        
        assert "phone" not in profile_data
        assert "gender" not in profile_data
        assert "occupation" not in profile_data
    
    def test_generate_location_data(self, generator):
        """Test generating location data"""
        user_id = "test_user_location"
        location_data = generator.generate_location_data(user_id)
        
        assert location_data["user_id"] == user_id
        assert "current_location" in location_data
        assert "home_location" in location_data
        assert "work_location" in location_data
        assert "travel_history" in location_data
        assert "location_preferences" in location_data
        assert "generated_at" in location_data
        assert "data_confidence" in location_data
        
        assert isinstance(location_data["travel_history"], list)
        assert isinstance(location_data["location_preferences"], dict)
        assert "preferred_neighborhoods" in location_data["location_preferences"]
        assert "avoided_areas" in location_data["location_preferences"]
        assert "favorite_venue_types" in location_data["location_preferences"]
        assert "travel_frequency" in location_data["location_preferences"]
        assert isinstance(location_data["data_confidence"], float)
        assert 0 <= location_data["data_confidence"] <= 1
    
    def test_generate_interaction_data(self, generator):
        """Test generating interaction data"""
        user_id = "test_user_interaction"
        interaction_data = generator.generate_interaction_data(user_id)
        
        assert interaction_data["user_id"] == user_id
        assert "recent_interactions" in interaction_data
        assert "interaction_history" in interaction_data
        assert "preferences" in interaction_data
        assert "engagement_score" in interaction_data
        assert "generated_at" in interaction_data
        assert "data_confidence" in interaction_data
        
        assert isinstance(interaction_data["recent_interactions"], list)
        assert len(interaction_data["recent_interactions"]) >= 15
        assert isinstance(interaction_data["interaction_history"], list)
        assert isinstance(interaction_data["preferences"], dict)
        assert "preferred_content_types" in interaction_data["preferences"]
        assert "preferred_interaction_types" in interaction_data["preferences"]
        assert "interaction_frequency" in interaction_data["preferences"]
        assert "engagement_style" in interaction_data["preferences"]
        assert isinstance(interaction_data["engagement_score"], float)
        assert 0 <= interaction_data["engagement_score"] <= 1
    
    def test_generate_recommendations_data(self, generator):
        """Test generating recommendations data"""
        user_id = "test_user_recommendations"
        categories = ["movies", "music", "places"]
        
        recommendations_data = generator.generate_recommendations_data(user_id, categories)
        
        assert recommendations_data["success"] is True
        assert recommendations_data["user_id"] == user_id
        assert "recommendations" in recommendations_data
        assert "metadata" in recommendations_data
        
        recommendations = recommendations_data["recommendations"]
        assert "movies" in recommendations
        assert "music" in recommendations
        assert "places" in recommendations
        
        # Check movie recommendations
        movies = recommendations["movies"]
        assert isinstance(movies, list)
        assert len(movies) >= 3
        for movie in movies:
            assert "title" in movie
            assert "description" in movie
            assert "genre" in movie
            assert "rating" in movie
            assert "ranking_score" in movie
            assert "why_would_you_like_this" in movie
            assert isinstance(movie["rating"], float)
            assert 3.0 <= movie["rating"] <= 5.0
            assert isinstance(movie["ranking_score"], float)
            assert 0.6 <= movie["ranking_score"] <= 0.95
    
    def test_generate_recommendations_data_default_categories(self, generator):
        """Test generating recommendations data with default categories"""
        user_id = "test_user_default"
        recommendations_data = generator.generate_recommendations_data(user_id)
        
        recommendations = recommendations_data["recommendations"]
        assert "movies" in recommendations
        assert "music" in recommendations
        assert "places" in recommendations
        assert "events" in recommendations
    
    def test_generate_realistic_age(self, generator):
        """Test realistic age generation"""
        ages = [generator._generate_realistic_age() for _ in range(100)]
        
        # Check that ages are within expected range
        assert all(18 <= age <= 65 for age in ages)
        
        # Check distribution (more users in 25-45 range)
        age_25_45 = sum(1 for age in ages if 25 <= age <= 45)
        assert age_25_45 > 50  # Should be majority
    
    def test_generate_realistic_interests(self, generator):
        """Test realistic interests generation"""
        # Test with different ages
        young_interests = generator._generate_realistic_interests(22)
        middle_interests = generator._generate_realistic_interests(35)
        older_interests = generator._generate_realistic_interests(55)
        
        assert isinstance(young_interests, list)
        assert isinstance(middle_interests, list)
        assert isinstance(older_interests, list)
        
        assert 3 <= len(young_interests) <= 8
        assert 3 <= len(middle_interests) <= 8
        assert 3 <= len(older_interests) <= 8
        
        # Check that interests are from expected list
        all_interests = [
            "technology", "travel", "music", "movies", "sports", "cooking",
            "photography", "art", "fitness", "reading", "gaming", "fashion",
            "gardening", "dancing", "writing", "volunteering", "investing",
            "parenting", "career_development", "health_wellness"
        ]
        
        for interest in young_interests + middle_interests + older_interests:
            assert interest in all_interests
    
    def test_generate_consistent_location(self, generator):
        """Test consistent location generation"""
        user_id = "test_consistency"
        
        # Generate location twice
        location1 = generator._generate_consistent_location(user_id)
        location2 = generator._generate_consistent_location(user_id)
        
        # Should be consistent when data_consistency is True
        assert location1 == location2
        
        # Check location structure
        assert "current_location" in location1
        assert "home_location" in location1
        assert "work_location" in location1
        assert "timezone" in location1
        assert "country" in location1
        assert "coordinates" in location1
        assert "lat" in location1["coordinates"]
        assert "lng" in location1["coordinates"]
    
    def test_generate_realistic_preferences(self, generator):
        """Test realistic preferences generation"""
        interests = ["technology", "music", "fitness"]
        
        young_prefs = generator._generate_realistic_preferences(25, interests)
        middle_prefs = generator._generate_realistic_preferences(40, interests)
        older_prefs = generator._generate_realistic_preferences(60, interests)
        
        # Check basic structure
        for prefs in [young_prefs, middle_prefs, older_prefs]:
            assert "language" in prefs
            assert "theme" in prefs
            assert "notifications" in prefs
            assert "privacy_level" in prefs
            assert "content_filters" in prefs
            assert "accessibility" in prefs
        
        # Check age-based preferences
        assert young_prefs.get("social_sharing") is True
        assert young_prefs.get("push_notifications") is True
        assert young_prefs.get("location_tracking") is True
        
        assert older_prefs.get("social_sharing") is False
        assert older_prefs.get("push_notifications") is False
        assert older_prefs.get("location_tracking") is False
    
    def test_calculate_profile_completeness(self, generator):
        """Test profile completeness calculation"""
        # Test with different ages and interest counts
        completeness1 = generator._calculate_profile_completeness(25, ["tech", "music"])
        completeness2 = generator._calculate_profile_completeness(25, ["tech", "music", "fitness", "travel"])
        completeness3 = generator._calculate_profile_completeness(70, ["reading"])
        
        assert isinstance(completeness1, float)
        assert 0 <= completeness1 <= 1
        assert completeness2 > completeness1  # More interests = higher completeness
        assert completeness3 < completeness1  # Age outside range = lower completeness
    
    def test_generate_occupation(self, generator):
        """Test occupation generation based on age"""
        young_occupation = generator._generate_occupation(22)
        middle_occupation = generator._generate_occupation(35)
        older_occupation = generator._generate_occupation(55)
        
        assert isinstance(young_occupation, str)
        assert isinstance(middle_occupation, str)
        assert isinstance(older_occupation, str)
        
        # Check age-appropriate occupations
        young_occupations = ["Student", "Intern", "Entry-level", "Freelancer"]
        older_occupations = ["Executive", "Consultant", "Advisor", "Retired"]
        
        assert young_occupation in young_occupations or young_occupation == "Professional"
        assert older_occupation in older_occupations or older_occupation == "Professional"
    
    def test_generate_education_level(self, generator):
        """Test education level generation based on age"""
        young_education = generator._generate_education_level(20)
        middle_education = generator._generate_education_level(28)
        older_education = generator._generate_education_level(45)
        
        assert isinstance(young_education, str)
        assert isinstance(middle_education, str)
        assert isinstance(older_education, str)
        
        # Check age-appropriate education levels
        young_levels = ["High School", "Some College", "Associate's"]
        middle_levels = ["Bachelor's", "Master's", "Some Graduate"]
        older_levels = ["Bachelor's", "Master's", "Doctorate", "Professional"]
        
        assert young_education in young_levels
        assert middle_education in middle_levels
        assert older_education in older_levels
    
    def test_generate_income_range(self, generator):
        """Test income range generation based on age"""
        young_income = generator._generate_income_range(22)
        middle_income = generator._generate_income_range(35)
        older_income = generator._generate_income_range(55)
        
        assert isinstance(young_income, str)
        assert isinstance(middle_income, str)
        assert isinstance(older_income, str)
        
        # Check age-appropriate income ranges
        young_ranges = ["$20k-40k", "$40k-60k"]
        middle_ranges = ["$60k-80k", "$80k-100k", "$100k-150k"]
        older_ranges = ["$100k-150k", "$150k+", "Retired"]
        
        assert young_income in young_ranges
        assert middle_income in middle_ranges
        assert older_income in older_ranges
    
    def test_generate_marital_status(self, generator):
        """Test marital status generation based on age"""
        young_status = generator._generate_marital_status(22)
        middle_status = generator._generate_marital_status(30)
        older_status = generator._generate_marital_status(50)
        
        assert isinstance(young_status, str)
        assert isinstance(middle_status, str)
        assert isinstance(older_status, str)
        
        # Check age-appropriate marital statuses
        young_statuses = ["Single", "In a relationship"]
        middle_statuses = ["Single", "In a relationship", "Married"]
        older_statuses = ["Married", "Divorced", "Widowed", "Single"]
        
        assert young_status in young_statuses
        assert middle_status in middle_statuses
        assert older_status in older_statuses
    
    def test_generate_languages(self, generator):
        """Test language generation"""
        languages = generator._generate_languages()
        
        assert isinstance(languages, list)
        assert "English" in languages  # Should always include English
        assert len(languages) >= 1
        assert len(languages) <= 3  # Max 3 languages
        
        # Check that additional languages are from expected list
        additional_languages = ["Spanish", "French", "German", "Chinese", "Japanese", "Portuguese", "Italian"]
        for lang in languages[1:]:  # Skip English
            assert lang in additional_languages
    
    def test_data_consistency_tracking(self, generator):
        """Test data consistency tracking"""
        user_id = "consistency_test"
        
        # Generate profile data
        profile_data = generator.generate_user_profile_data(user_id)
        
        # Check that data was stored for consistency
        assert user_id in generator._user_consistency
        consistency_data = generator._user_consistency[user_id]
        
        assert "age" in consistency_data
        assert "interests" in consistency_data
        assert "location" in consistency_data
        assert "preferences" in consistency_data
        
        assert consistency_data["age"] == profile_data["age"]
        assert consistency_data["interests"] == profile_data["interests"]
    
    def test_generate_interaction_history(self, generator):
        """Test interaction history generation"""
        user_id = "history_test"
        history = generator._generate_interaction_history(user_id)
        
        assert isinstance(history, list)
        assert 50 <= len(history) <= 150
        
        for interaction in history:
            assert "id" in interaction
            assert "content_type" in interaction
            assert "interaction_type" in interaction
            assert "content_title" in interaction
            assert "timestamp" in interaction
            assert "engagement_score" in interaction
            assert "category" in interaction
            
            assert interaction["content_type"] in generator.content_types
            assert interaction["interaction_type"] in generator.interaction_types
            assert isinstance(interaction["engagement_score"], float)
            assert 0 <= interaction["engagement_score"] <= 1


class TestGlobalGenerator:
    """Test global mock data generator instance"""
    
    def test_global_generator_exists(self):
        """Test that global generator instance exists"""
        assert mock_data_generator is not None
        assert isinstance(mock_data_generator, MockDataGenerator)
    
    def test_global_generator_initialization(self):
        """Test global generator initialization"""
        assert mock_data_generator.config is not None
        assert mock_data_generator.config.quality == DataQuality.REALISTIC
        assert mock_data_generator.logger is not None

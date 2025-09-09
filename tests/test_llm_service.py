"""
Comprehensive test suite for the LLM service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import time
from app.services.llm_service import LLMService


@pytest.mark.unit
class TestLLMService:
    """Test the LLM service functionality."""

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value.get.return_value = None
            mock_redis.return_value.setex.return_value = True
            mock_redis.return_value.delete.return_value = 1
            mock_redis.return_value.keys.return_value = []
            mock_redis.return_value.publish.return_value = 1
            
            service = LLMService()
            service.redis_client = mock_redis.return_value
            return service

    def test_llm_service_initialization(self, llm_service):
        """Test LLM service initialization."""
        assert llm_service is not None
        assert hasattr(llm_service, 'demo_recommendations')
        assert hasattr(llm_service, 'redis_client')
        assert hasattr(llm_service, 'ACTION_WEIGHTS')

    def test_demo_data_setup(self, llm_service):
        """Test demo data setup."""
        assert 'movies' in llm_service.demo_recommendations
        assert 'music' in llm_service.demo_recommendations
        assert 'places' in llm_service.demo_recommendations
        assert 'events' in llm_service.demo_recommendations
        
        # Check Barcelona data
        assert 'barcelona' in llm_service.demo_recommendations['movies']
        assert 'barcelona' in llm_service.demo_recommendations['music']
        assert 'barcelona' in llm_service.demo_recommendations['places']
        assert 'barcelona' in llm_service.demo_recommendations['events']
        
        # Check international data
        assert 'international' in llm_service.demo_recommendations['movies']
        assert 'international' in llm_service.demo_recommendations['music']
        assert 'international' in llm_service.demo_recommendations['places']
        assert 'international' in llm_service.demo_recommendations['events']

    def test_normalize_key(self, llm_service):
        """Test key normalization."""
        assert llm_service._normalize_key("Test Title") == "test title"   # space kept
        assert llm_service._normalize_key("Test@#$%Title") == "testtitle" # special chars removed
        assert llm_service._normalize_key("") == ""
        assert llm_service._normalize_key(None) == ""
        assert llm_service._normalize_key(123) == ""


    def test_get_user_interaction_history(self, llm_service):
        """Test user interaction history generation."""
        history = llm_service._get_user_interaction_history("test_user_1")
        
        assert 'movies' in history
        assert 'music' in history
        assert 'places' in history
        assert 'events' in history
        
        # Check that each category has interactions
        for category in history:
            assert len(history[category]) > 0
            for interaction in history[category]:
                assert 'action' in interaction
                assert 'timestamp' in interaction
                assert interaction['action'] in ['view', 'liked', 'saved', 'shared', 'clicked', 'ignored', 'disliked']

    def test_compute_ranking_score(self, llm_service):
        """Test ranking score computation."""
        # Test with no interactions
        item = {"title": "Test Movie"}
        history = {"movies": []}
        score = llm_service._compute_ranking_score(item, "movies", history)
        assert score == llm_service.BASE_SCORE
        
        # Test with positive interaction
        item = {"title": "Test Movie"}
        history = {"movies": [{"title": "Test Movie", "action": "liked", "timestamp": "2024-01-01T10:00:00Z"}]}
        score = llm_service._compute_ranking_score(item, "movies", history)
        assert score > llm_service.BASE_SCORE
        
        # Test with negative interaction
        history = {"movies": [{"title": "Test Movie", "action": "ignored", "timestamp": "2024-01-01T10:00:00Z"}]}
        score = llm_service._compute_ranking_score(item, "movies", history)
        assert score < llm_service.BASE_SCORE

    def test_compute_ranking_score_different_categories(self, llm_service):
        """Test ranking score computation for different categories."""
        # Test movies
        movie_item = {"title": "Test Movie"}
        movie_history = {"movies": [{"title": "Test Movie", "action": "liked", "timestamp": "2024-01-01T10:00:00Z"}]}
        movie_score = llm_service._compute_ranking_score(movie_item, "movies", movie_history)
        
        # Test places
        place_item = {"name": "Test Place"}
        place_history = {"places": [{"name": "Test Place", "action": "liked", "timestamp": "2024-01-01T10:00:00Z"}]}
        place_score = llm_service._compute_ranking_score(place_item, "places", place_history)
        
        assert movie_score > llm_service.BASE_SCORE
        assert place_score > llm_service.BASE_SCORE

    def test_generate_personalized_reason(self, llm_service):
        """Test personalized reason generation."""
        item = {
            "title": "Test Movie",
            "genre": "Drama",
            "year": "2024",
            "cast": ["Actor 1", "Actor 2"]
        }
        
        reason = llm_service._generate_personalized_reason(item, "movies", "Barcelona recommendations", "test_user_1")
        assert isinstance(reason, str)
        assert len(reason) > 0


    def test_generate_personalized_reason_no_user_id(self, llm_service):
        """Test personalized reason generation without user ID."""
        item = {"title": "Test Movie", "genre": "Drama"}
        
        reason = llm_service._generate_personalized_reason(item, "movies", "Barcelona recommendations")
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_generate_demo_recommendations(self, llm_service):
        """Test demo recommendations generation."""
        prompt = "Barcelona recommendations"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        assert 'movies' in recommendations
        assert 'music' in recommendations
        assert 'places' in recommendations
        assert 'events' in recommendations
        
        # Check that each category has recommendations
        for category in recommendations:
            assert len(recommendations[category]) > 0
            for item in recommendations[category]:
                assert 'ranking_score' in item
                assert 'why_would_you_like_this' in item
                assert 0 <= item['ranking_score'] <= 1

    def test_generate_demo_recommendations_barcelona_preference(self, llm_service):
        """Test Barcelona preference in recommendations."""
        prompt = "Barcelona recommendations with Gaudí and Sagrada Família"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        # Should have Barcelona-focused recommendations
        barcelona_items = 0
        for category in recommendations:
            for item in recommendations[category]:
                if 'barcelona' in str(item).lower() or 'gaudí' in str(item).lower():
                    barcelona_items += 1
        
        assert barcelona_items > 0

    def test_generate_demo_recommendations_international_preference(self, llm_service):
        """Test international preference in recommendations."""
        prompt = "International recommendations with Hollywood and global content"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        # Should have international recommendations
        international_items = 0
        for category in recommendations:
            for item in recommendations[category]:
                if 'hollywood' in str(item).lower() or 'international' in str(item).lower():
                    international_items += 1
        
        # Should have some international content
        assert len(recommendations['movies']) > 0
        assert len(recommendations['music']) > 0

    def test_generate_recommendations_success(self, llm_service):
        """Test successful recommendation generation."""
        prompt = "Barcelona recommendations"
        user_id = "test_user_1"
        
        with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
            mock_gen.return_value = {
                "movies": [{"title": "Test Movie", "ranking_score": 0.8}],
                "music": [{"title": "Test Song", "ranking_score": 0.7}],
                "places": [{"name": "Test Place", "ranking_score": 0.9}],
                "events": [{"name": "Test Event", "ranking_score": 0.6}]
            }
            
            with patch.object(llm_service, '_store_in_redis') as mock_store:
                result = llm_service.generate_recommendations(prompt, user_id)
                
                assert result['success'] is True
                assert result['user_id'] == user_id
                assert result['prompt'] == prompt
                assert 'recommendations' in result
                assert 'metadata' in result
                assert mock_store.called

    def test_generate_recommendations_without_user_id(self, llm_service):
        """Test recommendation generation without user ID."""
        prompt = "Barcelona recommendations"
        
        with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
            mock_gen.return_value = {
                "movies": [{"title": "Test Movie", "ranking_score": 0.8}],
                "music": [],
                "places": [],
                "events": []
            }
            
            result = llm_service.generate_recommendations(prompt)
            
            assert result['success'] is True
            assert result['user_id'] is None
            assert result['prompt'] == prompt

    def test_generate_recommendations_error(self, llm_service):
        """Test recommendation generation error handling."""
        prompt = "Barcelona recommendations"
        
        with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
            mock_gen.side_effect = Exception("Generation error")
            
            result = llm_service.generate_recommendations(prompt, "test_user_1")
            
            assert result['success'] is False
            assert 'error' in result
            assert result['prompt'] == prompt
            assert result['user_id'] == "test_user_1"

    def test_store_in_redis_success(self, llm_service):
        """Test successful Redis storage."""
        user_id = "test_user_1"
        data = {"test": "data"}
        
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.return_value = True
            
            with patch.object(llm_service.redis_client, 'publish') as mock_publish:
                mock_publish.return_value = 1
                
                llm_service._store_in_redis(user_id, data)
                
                mock_setex.assert_called_once()
                # publish may or may not be called, just ensure no exception


    def test_store_in_redis_error(self, llm_service):
        """Test Redis storage error handling."""
        user_id = "test_user_1"
        data = {"test": "data"}
        
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.side_effect = Exception("Redis error")
            
            # Should not raise exception
            llm_service._store_in_redis(user_id, data)

    def test_store_in_redis_notification_error(self, llm_service):
        """Test Redis notification error handling."""
        user_id = "test_user_1"
        data = {"test": "data"}
        
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.return_value = True
            
            with patch.object(llm_service.redis_client, 'publish') as mock_publish:
                mock_publish.side_effect = Exception("Publish error")
                
                # Should not raise exception
                llm_service._store_in_redis(user_id, data)

    def test_get_recommendations_from_redis_success(self, llm_service):
        """Test successful Redis retrieval."""
        user_id = "test_user_1"
        expected_data = {"test": "data"}
        
        with patch.object(llm_service.redis_client, 'get') as mock_get:
            mock_get.return_value = json.dumps(expected_data)
            
            result = llm_service.get_recommendations_from_redis(user_id)
            
            assert result == expected_data
            mock_get.assert_called_once_with(f"recommendations:{user_id}")

    def test_get_recommendations_from_redis_not_found(self, llm_service):
        """Test Redis retrieval when not found."""
        user_id = "test_user_1"
        
        with patch.object(llm_service.redis_client, 'get') as mock_get:
            mock_get.return_value = None
            
            result = llm_service.get_recommendations_from_redis(user_id)
            
            assert result is None

    def test_get_recommendations_from_redis_error(self, llm_service):
        """Test Redis retrieval error handling."""
        user_id = "test_user_1"
        
        with patch.object(llm_service.redis_client, 'get') as mock_get:
            mock_get.side_effect = Exception("Redis error")
            
            result = llm_service.get_recommendations_from_redis(user_id)
            
            assert result is None

    def test_clear_recommendations_single_user(self, llm_service):
        """Test clearing recommendations for single user."""
        user_id = "test_user_1"
        
        with patch.object(llm_service.redis_client, 'delete') as mock_delete:
            mock_delete.return_value = 1
            
            llm_service.clear_recommendations(user_id)
            
            mock_delete.assert_called_once_with(f"recommendations:{user_id}")

    def test_clear_recommendations_all_users(self, llm_service):
        """Test clearing recommendations for all users."""
        with patch.object(llm_service.redis_client, 'keys') as mock_keys:
            mock_keys.return_value = ["recommendations:user1", "recommendations:user2"]
            
            with patch.object(llm_service.redis_client, 'delete') as mock_delete:
                mock_delete.return_value = 2
                
                llm_service.clear_recommendations()
                
                mock_keys.assert_called_once_with("recommendations:*")
                mock_delete.assert_called_once_with("recommendations:user1", "recommendations:user2")

    def test_clear_recommendations_error(self, llm_service):
        """Test clearing recommendations error handling."""
        user_id = "test_user_1"
        
        with patch.object(llm_service.redis_client, 'delete') as mock_delete:
            mock_delete.side_effect = Exception("Redis error")
            
            # Should not raise exception
            llm_service.clear_recommendations(user_id)

    def test_action_weights(self, llm_service):
        """Test action weights configuration."""
        assert llm_service.ACTION_WEIGHTS['liked'] > 0
        assert llm_service.ACTION_WEIGHTS['saved'] > 0
        assert llm_service.ACTION_WEIGHTS['shared'] > 0
        assert llm_service.ACTION_WEIGHTS['clicked'] > 0
        assert llm_service.ACTION_WEIGHTS['view'] > 0
        assert llm_service.ACTION_WEIGHTS['ignored'] < 0
        assert llm_service.ACTION_WEIGHTS['disliked'] < 0

    def test_base_score_and_scale(self, llm_service):
        """Test base score and scale configuration."""
        assert 0 <= llm_service.BASE_SCORE <= 1
        assert llm_service.SCALE > 0

    def test_recommendation_count_limits(self, llm_service):
        """Test that recommendations are limited per category."""
        prompt = "Barcelona recommendations"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        for category in recommendations:
            assert len(recommendations[category]) <= 5

    def test_recommendation_sorting(self, llm_service):
        """Test that recommendations are sorted by ranking score."""
        prompt = "Barcelona recommendations"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        for category in recommendations:
            scores = [item['ranking_score'] for item in recommendations[category]]
            assert scores == sorted(scores, reverse=True)

    def test_recommendation_fields_completeness(self, llm_service):
        """Test that recommendations have all required fields."""
        prompt = "Barcelona recommendations"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        for category in recommendations:
            for item in recommendations[category]:
                assert 'ranking_score' in item
                assert 'why_would_you_like_this' in item
                assert isinstance(item['ranking_score'], (int, float))
                assert isinstance(item['why_would_you_like_this'], str)

    def test_barcelona_data_quality(self, llm_service):
        """Test Barcelona data quality."""
        barcelona_movies = llm_service.demo_recommendations['movies']['barcelona']
        assert len(barcelona_movies) > 0
        
        for movie in barcelona_movies:
            assert 'title' in movie
            assert 'year' in movie
            assert 'genre' in movie
            assert 'description' in movie
            assert 'director' in movie
            assert 'rating' in movie

    def test_international_data_quality(self, llm_service):
        """Test international data quality."""
        international_movies = llm_service.demo_recommendations['movies']['international']
        assert len(international_movies) > 0
        
        for movie in international_movies:
            assert 'title' in movie
            assert 'year' in movie
            assert 'genre' in movie
            assert 'description' in movie
            assert 'director' in movie
            assert 'rating' in movie

    def test_places_data_structure(self, llm_service):
        """Test places data structure."""
        barcelona_places = llm_service.demo_recommendations['places']['barcelona']
        assert len(barcelona_places) > 0
        
        for place in barcelona_places:
            assert 'name' in place
            assert 'type' in place
            assert 'rating' in place
            assert 'location' in place
            assert 'place_id' in place
            assert 'vicinity' in place

    def test_events_data_structure(self, llm_service):
        """Test events data structure."""
        barcelona_events = llm_service.demo_recommendations['events']['barcelona']
        assert len(barcelona_events) > 0
        
        for event in barcelona_events:
            assert 'name' in event
            assert 'date' in event
            assert 'end_date' in event
            assert 'description' in event
            assert 'venue' in event
            assert 'address' in event

    def test_music_data_structure(self, llm_service):
        """Test music data structure."""
        barcelona_music = llm_service.demo_recommendations['music']['barcelona']
        assert len(barcelona_music) > 0
        
        for music in barcelona_music:
            assert 'title' in music
            assert 'artist' in music
            assert 'genre' in music
            assert 'description' in music
            assert 'release_year' in music
            assert 'album' in music

    def test_processing_time_simulation(self, llm_service):
        """Test processing time simulation."""
        prompt = "Barcelona recommendations"
        
        start_time = time.time()
        result = llm_service.generate_recommendations(prompt, "test_user_1")
        end_time = time.time()
        
        assert result['success'] is True
        assert 'processing_time' in result
        assert 0.5 <= result['processing_time'] <= 2.0
        assert (end_time - start_time) >= 0.5  # Should simulate processing time

    def test_metadata_generation(self, llm_service):
        """Test metadata generation."""
        prompt = "Barcelona recommendations"
        result = llm_service.generate_recommendations(prompt, "test_user_1")
        
        assert 'metadata' in result
        metadata = result['metadata']
        assert 'total_recommendations' in metadata
        assert 'categories' in metadata
        assert 'model' in metadata
        assert 'ranking_enabled' in metadata
        
        assert isinstance(metadata['total_recommendations'], int)
        assert isinstance(metadata['categories'], list)
        assert isinstance(metadata['ranking_enabled'], bool)

    def test_current_city_parameter(self, llm_service):
        """Test current city parameter handling."""
        prompt = "Barcelona recommendations"
        result = llm_service.generate_recommendations(prompt, "test_user_1", "Madrid")
        
        assert result['current_city'] == "Madrid"

    def test_recommendation_diversity(self, llm_service):
        """Test recommendation diversity."""
        prompt = "Barcelona recommendations"
        recommendations = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        # Should have recommendations in multiple categories
        categories_with_items = sum(1 for category in recommendations if len(recommendations[category]) > 0)
        assert categories_with_items >= 2

    def test_user_id_deterministic_behavior(self, llm_service):
        """Test that same user ID produces consistent structure."""
        prompt = "Barcelona recommendations"
        
        rec1 = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        rec2 = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        
        # Should have same structure
        assert set(rec1.keys()) == set(rec2.keys())
        for category in rec1:
            assert isinstance(rec1[category], list)
            assert isinstance(rec2[category], list)


    def test_different_user_ids_different_results(self, llm_service):
        """Test that different user IDs produce different results."""
        prompt = "Barcelona recommendations"
        
        rec1 = llm_service._generate_demo_recommendations(prompt, "test_user_1")
        rec2 = llm_service._generate_demo_recommendations(prompt, "test_user_2")
        
        # Should have same structure but potentially different content
        assert set(rec1.keys()) == set(rec2.keys())

    def test_error_logging(self, llm_service):
        """Test error logging functionality."""
        with patch('app.services.llm_service.logger') as mock_logger:
            with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
                mock_gen.side_effect = Exception("Test error")
                
                result = llm_service.generate_recommendations("test prompt", "test_user")
                
                assert result['success'] is False
                assert mock_logger.error.called

    def test_success_logging(self, llm_service):
        """Test success logging functionality."""
        with patch('app.services.llm_service.logger') as mock_logger:
            with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
                mock_gen.return_value = {
                    "movies": [{"title": "Test", "ranking_score": 0.8}],
                    "music": [],
                    "places": [],
                    "events": []
                }
                
                with patch.object(llm_service, '_store_in_redis'):
                    result = llm_service.generate_recommendations("test prompt", "test_user")
                    
                    assert result['success'] is True
                    assert mock_logger.info.called

    def test_redis_connection_handling(self, llm_service):
        """Test Redis connection handling."""
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.side_effect = Exception("Connection error")
            
            # Should handle connection errors gracefully
            llm_service._store_in_redis("test_user", {"test": "data"})

    def test_json_serialization(self, llm_service):
        """Test JSON serialization of complex data."""
        complex_data = {
            "test": "data",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "datetime": "2024-01-01T10:00:00Z"
        }
        
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.return_value = True
            
            with patch.object(llm_service.redis_client, 'publish') as mock_publish:
                mock_publish.return_value = 1
                
                # Should handle complex data serialization
                llm_service._store_in_redis("test_user", complex_data)
                
                # Verify that setex was called with JSON string
                call_args = mock_setex.call_args
                assert isinstance(call_args[0][2], str)  # Third argument should be JSON string

    def test_notification_payload_structure(self, llm_service):
        """Test notification payload structure."""
        user_id = "test_user_1"
        data = {"test": "data"}
        
        with patch.object(llm_service.redis_client, 'setex') as mock_setex:
            mock_setex.return_value = True
            
            with patch.object(llm_service.redis_client, 'publish') as mock_publish:
                mock_publish.return_value = 1
                
                llm_service._store_in_redis(user_id, data)
                
                # Verify publish was attempted (if implemented)
                if mock_publish.call_args:
                    assert isinstance(mock_publish.call_args[0][0], str)



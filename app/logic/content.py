import redis
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.model.content import UserProfile, ContentRecommendation, ContentInteraction
from app.schema.content import (
    ContentType, InteractionType, UserProfileCreate, UserProfileUpdate,
    ContentRecommendationCreate, ContentInteractionCreate,
    RecommendationRequest, RecommendationResponse
)
from app.core.database import get_db


# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


class ContentRecommendationService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def create_or_update_user_profile(self, user_id: int, profile_data: UserProfileCreate) -> UserProfile:
        """Create or update user profile"""
        profile = self.get_user_profile(user_id)
        
        if profile:
            # Update existing profile
            for key, value in profile_data.dict(exclude_unset=True).items():
                setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile = UserProfile(user_id=user_id, **profile_data.dict())
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_cached_recommendations(self, user_id: int, content_types: List[ContentType]) -> List[ContentRecommendation]:
        """Get cached recommendations from Redis"""
        cached_recommendations = []
        
        for content_type in content_types:
            cache_key = f"prefetch:{user_id}:{content_type.value}"
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    # Convert cached data back to ContentRecommendation objects
                    for item in data:
                        recommendation = ContentRecommendation(
                            user_id=user_id,
                            content_type=content_type,
                            content_id=item["content_id"],
                            title=item["title"],
                            description=item.get("description"),
                            content_metadata=item.get("content_metadata", {}),
                            relevance_score=item.get("relevance_score", 0.0),
                            ranking_position=item.get("ranking_position", 0),
                            is_cached=True,
                            cache_key=cache_key
                        )
                        cached_recommendations.append(recommendation)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return cached_recommendations

    def get_database_recommendations(self, user_id: int, content_types: List[ContentType], limit: int = 10) -> List[ContentRecommendation]:
        """Get recommendations from database"""
        query = self.db.query(ContentRecommendation).filter(
            ContentRecommendation.user_id == user_id,
            ContentRecommendation.content_type.in_([ct.value for ct in content_types]),
            ContentRecommendation.expires_at > datetime.utcnow()
        ).order_by(ContentRecommendation.ranking_position.asc()).limit(limit)
        
        return query.all()

    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get recommendations for a user"""
        # First try to get from cache
        cached_recommendations = self.get_cached_recommendations(request.user_id, request.content_types)
        
        if cached_recommendations:
            return RecommendationResponse(
                recommendations=cached_recommendations,
                cache_hit=True,
                generated_at=datetime.utcnow()
            )
        
        # If no cache, get from database
        db_recommendations = self.get_database_recommendations(request.user_id, request.content_types)
        
        # If no database recommendations, trigger async generation
        if not db_recommendations:
            self.trigger_recommendation_generation(request)
            # Return empty response for now
            return RecommendationResponse(
                recommendations=[],
                cache_hit=False,
                generated_at=datetime.utcnow()
            )
        
        return RecommendationResponse(
            recommendations=db_recommendations,
            cache_hit=False,
            generated_at=datetime.utcnow()
        )

    def trigger_recommendation_generation(self, request: RecommendationRequest):
        """Trigger async recommendation generation"""
        # Lazy import to avoid circular dependency
        from app.tasks.celery_app import celery_app
        
        # Send task to Celery for async processing
        celery_app.send_task(
            'app.tasks.recommendation_tasks.generate_recommendations',
            args=[request.dict()]
        )

    def log_interaction(self, user_id: int, interaction_data: ContentInteractionCreate) -> ContentInteraction:
        """Log user interaction with content"""
        interaction = ContentInteraction(
            user_id=user_id,
            content_id=interaction_data.content_id,
            interaction_type=interaction_data.interaction_type,
            interaction_data=interaction_data.interaction_data,
            device_info=interaction_data.device_info,
            location=interaction_data.location
        )
        
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        
        return interaction

    def cache_recommendations(self, user_id: int, content_type: ContentType, recommendations: List[Dict[str, Any]], ttl: int = 1800):
        """Cache recommendations in Redis"""
        cache_key = f"prefetch:{user_id}:{content_type.value}"
        
        # Convert recommendations to serializable format
        cache_data = []
        for rec in recommendations:
            cache_data.append({
                "content_id": rec["content_id"],
                "title": rec["title"],
                "description": rec.get("description"),
                "content_metadata": rec.get("content_metadata", {}),
                "relevance_score": rec.get("relevance_score", 0.0),
                "ranking_position": rec.get("ranking_position", 0)
            })
        
        # Store in Redis with TTL
        redis_client.setex(cache_key, ttl, json.dumps(cache_data))

    def save_recommendations_to_db(self, user_id: int, recommendations: List[Dict[str, Any]]):
        """Save recommendations to database"""
        for rec_data in recommendations:
            recommendation = ContentRecommendation(
                user_id=user_id,
                content_type=rec_data["content_type"],
                content_id=rec_data["content_id"],
                title=rec_data["title"],
                description=rec_data.get("description"),
                content_metadata=rec_data.get("content_metadata", {}),
                relevance_score=rec_data.get("relevance_score", 0.0),
                ranking_position=rec_data.get("ranking_position", 0),
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
            )
            self.db.add(recommendation)
        
        self.db.commit()


# Mock recommendation generator for demo purposes
class MockRecommendationGenerator:
    """Mock recommendation generator for demo purposes"""
    
    @staticmethod
    def generate_music_recommendations(user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate mock music recommendations"""
        recommendations = [
            {
                "content_type": ContentType.MUSIC,
                "content_id": "music_001",
                "title": "Chill Vibes Playlist",
                "description": "Perfect for relaxing evenings",
                "content_metadata": {"genre": "chill", "duration": "2h 15m"},
                "relevance_score": 0.85,
                "ranking_position": 1
            },
            {
                "content_type": ContentType.MUSIC,
                "content_id": "music_002",
                "title": "Workout Beats",
                "description": "High energy tracks for your workout",
                "content_metadata": {"genre": "electronic", "duration": "1h 30m"},
                "relevance_score": 0.75,
                "ranking_position": 2
            }
        ]
        return recommendations

    @staticmethod
    def generate_movie_recommendations(user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate mock movie recommendations"""
        recommendations = [
            {
                "content_type": ContentType.MOVIE,
                "content_id": "movie_001",
                "title": "The Great Adventure",
                "description": "An epic journey through unknown lands",
                "content_metadata": {"genre": "adventure", "rating": "PG-13", "duration": "2h 15m"},
                "relevance_score": 0.90,
                "ranking_position": 1
            },
            {
                "content_type": ContentType.MOVIE,
                "content_id": "movie_002",
                "title": "Romantic Comedy Night",
                "description": "Perfect for date night",
                "content_metadata": {"genre": "romance", "rating": "PG-13", "duration": "1h 45m"},
                "relevance_score": 0.80,
                "ranking_position": 2
            }
        ]
        return recommendations

    @staticmethod
    def generate_event_recommendations(user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate mock event recommendations"""
        recommendations = [
            {
                "content_type": ContentType.EVENT,
                "content_id": "event_001",
                "title": "Wellness Workshop",
                "description": "Mindfulness and meditation session",
                "content_metadata": {"category": "wellness", "duration": "2h", "price": "$25"},
                "relevance_score": 0.88,
                "ranking_position": 1
            },
            {
                "content_type": ContentType.EVENT,
                "content_id": "event_002",
                "title": "Food Festival",
                "description": "Local cuisine and live music",
                "content_metadata": {"category": "food", "duration": "4h", "price": "$15"},
                "relevance_score": 0.82,
                "ranking_position": 2
            }
        ]
        return recommendations

    @staticmethod
    def generate_place_recommendations(user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate mock place recommendations"""
        recommendations = [
            {
                "content_type": ContentType.PLACE,
                "content_id": "place_001",
                "title": "Cozy Coffee Shop",
                "description": "Perfect spot for remote work",
                "content_metadata": {"category": "cafe", "rating": 4.5, "price_range": "$$"},
                "relevance_score": 0.87,
                "ranking_position": 1
            },
            {
                "content_type": ContentType.PLACE,
                "content_id": "place_002",
                "title": "Rooftop Restaurant",
                "description": "Amazing views and great food",
                "content_metadata": {"category": "restaurant", "rating": 4.8, "price_range": "$$$"},
                "relevance_score": 0.85,
                "ranking_position": 2
            }
        ]
        return recommendations 
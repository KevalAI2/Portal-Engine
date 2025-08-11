from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.logic.content import ContentRecommendationService, MockRecommendationGenerator
from app.schema.content import RecommendationRequest, ContentType
from typing import Dict, Any


@shared_task
def generate_recommendations(request_data: Dict[str, Any]):
    """Generate recommendations asynchronously"""
    try:
        # Convert request data back to RecommendationRequest
        request = RecommendationRequest(**request_data)
        
        # Get database session
        db = next(get_db())
        service = ContentRecommendationService(db)
        
        # Get user profile
        user_profile = service.get_user_profile(request.user_id)
        
        if not user_profile:
            # Create default profile if none exists
            from app.schema.content import UserProfileCreate
            default_profile = UserProfileCreate(
                interests=["music", "movies", "events", "places"],
                keywords=["entertainment"],
                archetypes=["explorer"]
            )
            user_profile = service.create_or_update_user_profile(request.user_id, default_profile)
        
        # Generate recommendations for each content type
        all_recommendations = []
        
        for content_type in request.content_types:
            if content_type == ContentType.MUSIC:
                recommendations = MockRecommendationGenerator.generate_music_recommendations(user_profile)
            elif content_type == ContentType.MOVIE:
                recommendations = MockRecommendationGenerator.generate_movie_recommendations(user_profile)
            elif content_type == ContentType.EVENT:
                recommendations = MockRecommendationGenerator.generate_event_recommendations(user_profile)
            elif content_type == ContentType.PLACE:
                recommendations = MockRecommendationGenerator.generate_place_recommendations(user_profile)
            else:
                continue
            
            all_recommendations.extend(recommendations)
        
        # Save recommendations to database
        service.save_recommendations_to_db(request.user_id, all_recommendations)
        
        # Cache recommendations in Redis
        for content_type in request.content_types:
            type_recommendations = [r for r in all_recommendations if r["content_type"] == content_type]
            if type_recommendations:
                service.cache_recommendations(request.user_id, content_type, type_recommendations)
        
        print(f"Generated {len(all_recommendations)} recommendations for user {request.user_id}")
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        raise
    finally:
        db.close()


@shared_task
def refresh_user_recommendations(user_id: int):
    """Refresh recommendations for a specific user"""
    try:
        db = next(get_db())
        service = ContentRecommendationService(db)
        
        # Get user profile
        user_profile = service.get_user_profile(user_id)
        
        if not user_profile:
            print(f"No profile found for user {user_id}")
            return
        
        # Generate recommendations for all content types
        content_types = [ContentType.MUSIC, ContentType.MOVIE, ContentType.EVENT, ContentType.PLACE]
        
        all_recommendations = []
        
        for content_type in content_types:
            if content_type == ContentType.MUSIC:
                recommendations = MockRecommendationGenerator.generate_music_recommendations(user_profile)
            elif content_type == ContentType.MOVIE:
                recommendations = MockRecommendationGenerator.generate_movie_recommendations(user_profile)
            elif content_type == ContentType.EVENT:
                recommendations = MockRecommendationGenerator.generate_event_recommendations(user_profile)
            elif content_type == ContentType.PLACE:
                recommendations = MockRecommendationGenerator.generate_place_recommendations(user_profile)
            else:
                continue
            
            all_recommendations.extend(recommendations)
        
        # Save to database
        service.save_recommendations_to_db(user_id, all_recommendations)
        
        # Cache in Redis
        for content_type in content_types:
            type_recommendations = [r for r in all_recommendations if r["content_type"] == content_type]
            if type_recommendations:
                service.cache_recommendations(user_id, content_type, type_recommendations)
        
        print(f"Refreshed {len(all_recommendations)} recommendations for user {user_id}")
        
    except Exception as e:
        print(f"Error refreshing recommendations for user {user_id}: {str(e)}")
        raise
    finally:
        db.close()


@shared_task
def cleanup_expired_recommendations():
    """Clean up expired recommendations from database"""
    try:
        from datetime import datetime
        from app.model.content import ContentRecommendation
        
        db = next(get_db())
        
        # Delete expired recommendations
        expired_count = db.query(ContentRecommendation).filter(
            ContentRecommendation.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        
        print(f"Cleaned up {expired_count} expired recommendations")
        
    except Exception as e:
        print(f"Error cleaning up expired recommendations: {str(e)}")
        raise
    finally:
        db.close() 
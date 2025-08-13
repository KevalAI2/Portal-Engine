from sqlalchemy.orm import Session
from app.model.user_profile import UserProfile as UserProfileModel, UserProfileHistory
from app.schema.user_profile import UserProfileCreate, UserProfileUpdate, ProfileValue
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


def get_user_profile(db: Session, user_id: int) -> Optional[UserProfileModel]:
    """Get user profile by user ID"""
    return db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()


def create_user_profile(db: Session, user_id: int, profile_data: UserProfileCreate) -> UserProfileModel:
    """Create a new user profile"""
    
    # Convert ProfileValue objects to dictionaries for JSON storage
    def convert_profile_values(values):
        if values is None:
            return []
        return [value.dict() if hasattr(value, 'dict') else value for value in values]
    
    db_profile = UserProfileModel(
        user_id=user_id,
        keywords=convert_profile_values(profile_data.keywords),
        archetypes=convert_profile_values(profile_data.archetypes),
        demographics=profile_data.demographics,
        home_location=profile_data.home_location,
        trips_taken=convert_profile_values(profile_data.trips_taken),
        living_situation=profile_data.living_situation,
        profession=profile_data.profession,
        education=profile_data.education,
        key_relationships=convert_profile_values(profile_data.key_relationships),
        children=convert_profile_values(profile_data.children),
        relationship_goals=convert_profile_values(profile_data.relationship_goals),
        cultural_language_preferences=convert_profile_values(profile_data.cultural_language_preferences),
        aesthetic_preferences=convert_profile_values(profile_data.aesthetic_preferences),
        dining_preferences_cuisine=convert_profile_values(profile_data.dining_preferences_cuisine),
        dining_preferences_other=convert_profile_values(profile_data.dining_preferences_other),
        indoor_activity_preferences=convert_profile_values(profile_data.indoor_activity_preferences),
        outdoor_activity_preferences=convert_profile_values(profile_data.outdoor_activity_preferences),
        at_home_activity_preferences=convert_profile_values(profile_data.at_home_activity_preferences),
        favorite_neighborhoods=convert_profile_values(profile_data.favorite_neighborhoods),
        tv_movie_genres=convert_profile_values(profile_data.tv_movie_genres),
        music_genres=convert_profile_values(profile_data.music_genres),
        podcast_genres=convert_profile_values(profile_data.podcast_genres),
        favorite_creators=convert_profile_values(profile_data.favorite_creators),
        accommodation_preferences=convert_profile_values(profile_data.accommodation_preferences),
        travel_style=convert_profile_values(profile_data.travel_style),
        vehicle_ownership=convert_profile_values(profile_data.vehicle_ownership),
        fitness_level=profile_data.fitness_level,
        medical_conditions=convert_profile_values(profile_data.medical_conditions),
        health_goals=convert_profile_values(profile_data.health_goals),
        career_goals=convert_profile_values(profile_data.career_goals),
        financial_goals=convert_profile_values(profile_data.financial_goals),
        social_goals=convert_profile_values(profile_data.social_goals),
        learning_goals=convert_profile_values(profile_data.learning_goals),
        travel_goals=convert_profile_values(profile_data.travel_goals),
        recent_searches=convert_profile_values(profile_data.recent_searches),
        recent_content_likes=convert_profile_values(profile_data.recent_content_likes),
        recent_plan_discussions=convert_profile_values(profile_data.recent_plan_discussions),
        recently_visited_venues=convert_profile_values(profile_data.recently_visited_venues),
        recent_media_consumption=convert_profile_values(profile_data.recent_media_consumption),
        user_mood=profile_data.user_mood,
        user_energy=profile_data.user_energy,
        user_stress=profile_data.user_stress,
        typical_outing_times=convert_profile_values(profile_data.typical_outing_times),
        wake_sleep_time=profile_data.wake_sleep_time,
        meal_times=profile_data.meal_times,
        exercise_time=profile_data.exercise_time,
        weekly_routines=convert_profile_values(profile_data.weekly_routines),
        productivity_windows=convert_profile_values(profile_data.productivity_windows),
        commute_patterns=convert_profile_values(profile_data.commute_patterns),
        preferred_budget=profile_data.preferred_budget,
        preferred_vibe=convert_profile_values(profile_data.preferred_vibe),
        content_discovery_sources=convert_profile_values(profile_data.content_discovery_sources),
        typical_group_size=profile_data.typical_group_size,
        current_location=profile_data.current_location,
        time_of_day=profile_data.time_of_day,
        day_of_week=profile_data.day_of_week,
        weather=profile_data.weather,
        device_type_usage_mode=profile_data.device_type_usage_mode,
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_user_profile(db: Session, user_id: int, profile_update: UserProfileUpdate) -> Optional[UserProfileModel]:
    """Update user profile with partial data"""
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        return None
    
    # Save current state to history before updating
    save_profile_history(db, user_id, "Profile updated")
    
    # Update only provided fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_profile)
    return db_profile


def save_profile_history(db: Session, user_id: int, change_description: str):
    """Save current profile state to history"""
    profile = get_user_profile(db, user_id)
    if profile:
        # Convert profile to dict for snapshot
        profile_dict = {
            'keywords': profile.keywords,
            'archetypes': profile.archetypes,
            'demographics': profile.demographics,
            'home_location': profile.home_location,
            'trips_taken': profile.trips_taken,
            'living_situation': profile.living_situation,
            'profession': profile.profession,
            'education': profile.education,
            'key_relationships': profile.key_relationships,
            'children': profile.children,
            'relationship_goals': profile.relationship_goals,
            'cultural_language_preferences': profile.cultural_language_preferences,
            'aesthetic_preferences': profile.aesthetic_preferences,
            'dining_preferences_cuisine': profile.dining_preferences_cuisine,
            'dining_preferences_other': profile.dining_preferences_other,
            'indoor_activity_preferences': profile.indoor_activity_preferences,
            'outdoor_activity_preferences': profile.outdoor_activity_preferences,
            'at_home_activity_preferences': profile.at_home_activity_preferences,
            'favorite_neighborhoods': profile.favorite_neighborhoods,
            'tv_movie_genres': profile.tv_movie_genres,
            'music_genres': profile.music_genres,
            'podcast_genres': profile.podcast_genres,
            'favorite_creators': profile.favorite_creators,
            'accommodation_preferences': profile.accommodation_preferences,
            'travel_style': profile.travel_style,
            'vehicle_ownership': profile.vehicle_ownership,
            'fitness_level': profile.fitness_level,
            'medical_conditions': profile.medical_conditions,
            'health_goals': profile.health_goals,
            'career_goals': profile.career_goals,
            'financial_goals': profile.financial_goals,
            'social_goals': profile.social_goals,
            'learning_goals': profile.learning_goals,
            'travel_goals': profile.travel_goals,
            'recent_searches': profile.recent_searches,
            'recent_content_likes': profile.recent_content_likes,
            'recent_plan_discussions': profile.recent_plan_discussions,
            'recently_visited_venues': profile.recently_visited_venues,
            'recent_media_consumption': profile.recent_media_consumption,
            'user_mood': profile.user_mood,
            'user_energy': profile.user_energy,
            'user_stress': profile.user_stress,
            'typical_outing_times': profile.typical_outing_times,
            'wake_sleep_time': profile.wake_sleep_time,
            'meal_times': profile.meal_times,
            'exercise_time': profile.exercise_time,
            'weekly_routines': profile.weekly_routines,
            'productivity_windows': profile.productivity_windows,
            'commute_patterns': profile.commute_patterns,
            'preferred_budget': profile.preferred_budget,
            'preferred_vibe': profile.preferred_vibe,
            'content_discovery_sources': profile.content_discovery_sources,
            'typical_group_size': profile.typical_group_size,
            'current_location': profile.current_location,
            'time_of_day': profile.time_of_day,
            'day_of_week': profile.day_of_week,
            'weather': profile.weather,
            'device_type_usage_mode': profile.device_type_usage_mode,
        }
        
        history_entry = UserProfileHistory(
            user_id=user_id,
            profile_snapshot=profile_dict,
            change_description=change_description
        )
        db.add(history_entry)
        db.commit()


def add_recent_search(db: Session, user_id: int, search_query: str, similarity_score: float = 0.9):
    """Add a recent search to user profile"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return None
    
    new_search = ProfileValue(value=search_query, similarity_score=similarity_score)
    
    # Keep only last 10 searches
    recent_searches = profile.recent_searches or []
    recent_searches.append(new_search.dict())
    if len(recent_searches) > 10:
        recent_searches = recent_searches[-10:]
    
    profile.recent_searches = recent_searches
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def add_recent_venue_visit(db: Session, user_id: int, venue_name: str, similarity_score: float = 0.9):
    """Add a recently visited venue to user profile"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return None
    
    new_venue = ProfileValue(value=venue_name, similarity_score=similarity_score)
    
    # Keep only last 10 venues
    recent_venues = profile.recently_visited_venues or []
    recent_venues.append(new_venue.dict())
    if len(recent_venues) > 10:
        recent_venues = recent_venues[-10:]
    
    profile.recently_visited_venues = recent_venues
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def update_user_context(db: Session, user_id: int, context_data: Dict[str, Any]):
    """Update environmental context (location, time, weather, etc.)"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return None
    
    # Update context fields
    if 'current_location' in context_data:
        profile.current_location = context_data['current_location']
    if 'time_of_day' in context_data:
        profile.time_of_day = context_data['time_of_day']
    if 'day_of_week' in context_data:
        profile.day_of_week = context_data['day_of_week']
    if 'weather' in context_data:
        profile.weather = context_data['weather']
    if 'device_type_usage_mode' in context_data:
        profile.device_type_usage_mode = context_data['device_type_usage_mode']
    if 'user_mood' in context_data:
        profile.user_mood = context_data['user_mood']
    if 'user_energy' in context_data:
        profile.user_energy = context_data['user_energy']
    if 'user_stress' in context_data:
        profile.user_stress = context_data['user_stress']
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def get_profile_insights(db: Session, user_id: int) -> Dict[str, Any]:
    """Analyze user profile and return insights"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return {}
    
    insights = {
        'primary_archetype': None,
        'travel_style': None,
        'budget_preference': profile.preferred_budget,
        'top_activity_preferences': [],
        'top_dining_preferences': [],
        'top_music_genres': [],
        'confidence_scores': {},
        'recent_activity': {}
    }
    
    # Determine primary archetype
    if profile.archetypes:
        sorted_archetypes = sorted(profile.archetypes, key=lambda x: x.get('similarity_score', 0), reverse=True)
        insights['primary_archetype'] = sorted_archetypes[0].get('value') if sorted_archetypes else None
    
    # Determine travel style
    if profile.travel_style:
        sorted_travel_styles = sorted(profile.travel_style, key=lambda x: x.get('similarity_score', 0), reverse=True)
        insights['travel_style'] = sorted_travel_styles[0].get('value') if sorted_travel_styles else None
    
    # Get top activity preferences
    if profile.outdoor_activity_preferences:
        insights['top_activity_preferences'].extend([p.get('value') for p in profile.outdoor_activity_preferences[:3]])
    if profile.indoor_activity_preferences:
        insights['top_activity_preferences'].extend([p.get('value') for p in profile.indoor_activity_preferences[:3]])
    
    # Get top dining preferences
    if profile.dining_preferences_cuisine:
        insights['top_dining_preferences'] = [p.get('value') for p in profile.dining_preferences_cuisine[:5]]
    
    # Get top music genres
    if profile.music_genres:
        insights['top_music_genres'] = [p.get('value') for p in profile.music_genres[:5]]
    
    # Calculate confidence scores
    insights['confidence_scores'] = {
        'archetypes': len(profile.archetypes) * 0.1 if profile.archetypes else 0,
        'activities': len(profile.outdoor_activity_preferences or []) + len(profile.indoor_activity_preferences or []) * 0.05,
        'dining': len(profile.dining_preferences_cuisine or []) * 0.1,
        'travel_history': len(profile.trips_taken or []) * 0.1
    }
    
    # Recent activity
    insights['recent_activity'] = {
        'recent_searches': len(profile.recent_searches or []),
        'recent_venues': len(profile.recently_visited_venues or []),
        'current_mood': profile.user_mood,
        'current_location': profile.current_location
    }
    
    return insights 
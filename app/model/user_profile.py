from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Long-term memory characteristics
    keywords = Column(JSON, default=list)  # List of keyword objects with similarity scores
    archetypes = Column(JSON, default=list)  # List of archetype objects
    demographics = Column(JSON, default=dict)  # Age, ethnicity, health, etc.
    home_location = Column(String, nullable=True)
    trips_taken = Column(JSON, default=list)  # List of past trips
    living_situation = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    education = Column(String, nullable=True)
    key_relationships = Column(JSON, default=list)
    children = Column(JSON, default=list)
    relationship_goals = Column(JSON, default=list)
    cultural_language_preferences = Column(JSON, default=list)
    aesthetic_preferences = Column(JSON, default=list)
    dining_preferences_cuisine = Column(JSON, default=list)
    dining_preferences_other = Column(JSON, default=list)
    indoor_activity_preferences = Column(JSON, default=list)
    outdoor_activity_preferences = Column(JSON, default=list)
    at_home_activity_preferences = Column(JSON, default=list)
    favorite_neighborhoods = Column(JSON, default=list)
    tv_movie_genres = Column(JSON, default=list)
    music_genres = Column(JSON, default=list)
    podcast_genres = Column(JSON, default=list)
    favorite_creators = Column(JSON, default=list)
    accommodation_preferences = Column(JSON, default=list)
    travel_style = Column(JSON, default=list)
    vehicle_ownership = Column(JSON, default=list)
    fitness_level = Column(String, nullable=True)
    medical_conditions = Column(JSON, default=list)
    health_goals = Column(JSON, default=list)
    career_goals = Column(JSON, default=list)
    financial_goals = Column(JSON, default=list)
    social_goals = Column(JSON, default=list)
    learning_goals = Column(JSON, default=list)
    travel_goals = Column(JSON, default=list)
    
    # Short-term memory characteristics
    recent_searches = Column(JSON, default=list)
    recent_content_likes = Column(JSON, default=list)
    recent_plan_discussions = Column(JSON, default=list)
    recently_visited_venues = Column(JSON, default=list)
    recent_media_consumption = Column(JSON, default=list)
    user_mood = Column(String, nullable=True)
    user_energy = Column(String, nullable=True)
    user_stress = Column(String, nullable=True)
    
    # Behavioral & preference patterns
    typical_outing_times = Column(JSON, default=list)
    wake_sleep_time = Column(JSON, default=dict)
    meal_times = Column(JSON, default=dict)
    exercise_time = Column(String, nullable=True)
    weekly_routines = Column(JSON, default=list)
    productivity_windows = Column(JSON, default=list)
    commute_patterns = Column(JSON, default=list)
    preferred_budget = Column(String, nullable=True)
    preferred_vibe = Column(JSON, default=list)
    content_discovery_sources = Column(JSON, default=list)
    typical_group_size = Column(String, nullable=True)
    
    # Environmental context
    current_location = Column(String, nullable=True)
    time_of_day = Column(String, nullable=True)
    day_of_week = Column(String, nullable=True)
    weather = Column(String, nullable=True)
    device_type_usage_mode = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("UserInDB", back_populates="profile")


class UserProfileHistory(Base):
    __tablename__ = "user_profile_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_snapshot = Column(JSON, nullable=False)  # Complete profile state
    change_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("UserInDB") 
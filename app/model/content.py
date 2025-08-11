from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)
    
    # Preferences
    interests = Column(JSON, default=[])  # ["music", "movies", "events", "places"]
    keywords = Column(JSON, default=[])   # ["date night", "wellness", "adventure"]
    archetypes = Column(JSON, default=[]) # ["wellness", "foodie", "adventurer"]
    
    # Demographics
    age_group = Column(String(50), nullable=True)  # "20s", "30s", "40s"
    relationship_status = Column(String(50), nullable=True)  # "single", "partnered"
    
    # Travel history
    travel_history = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UserInDB", back_populates="profile")


class ContentRecommendation(Base):
    __tablename__ = "content_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Content details
    content_type = Column(String(50), nullable=False)  # "music", "movie", "event", "place"
    content_id = Column(String(255), nullable=False)   # External ID or unique identifier
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Content metadata
    content_metadata = Column(JSON, default={})  # Genre, rating, location, etc.
    
    # Ranking and relevance
    relevance_score = Column(Float, default=0.0)
    ranking_position = Column(Integer, default=0)
    
    # Cache info
    is_cached = Column(Boolean, default=False)
    cache_key = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserInDB", back_populates="recommendations")
    interactions = relationship("ContentInteraction", back_populates="content")


class ContentInteraction(Base):
    __tablename__ = "content_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content_recommendations.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # "view", "click", "ignore", "like"
    interaction_data = Column(JSON, default={})  # Additional interaction metadata
    
    # Device and context
    device_info = Column(JSON, default={})
    location = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("UserInDB", back_populates="interactions")
    content = relationship("ContentRecommendation", back_populates="interactions") 
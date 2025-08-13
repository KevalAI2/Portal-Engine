from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


# UserProfile class moved to app/model/user_profile.py to avoid conflicts


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
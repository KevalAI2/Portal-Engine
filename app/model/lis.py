from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class LISPrompt(Base):
    """Database model for storing LIS prompts"""
    __tablename__ = "lis_prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prompt details
    prompt_type = Column(String(50), nullable=False)  # restaurant, activity, attraction, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    urgency = Column(String(20), nullable=False)  # low, medium, high, critical
    relevance_score = Column(Float, nullable=False)
    reasoning = Column(JSON, default=list)  # List of reasoning strings
    context_factors = Column(JSON, default=dict)  # Context factors that influenced the prompt
    
    # Location and context
    location = Column(String(255), nullable=False)
    location_context = Column(JSON, default=dict)  # Location context data
    user_context = Column(JSON, default=dict)  # User context data
    
    # Action and expiration
    action_url = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("UserInDB")
    interactions = relationship("LISInteraction", back_populates="prompt")


class LISInteraction(Base):
    """Database model for storing user interactions with LIS prompts"""
    __tablename__ = "lis_interactions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(String(255), ForeignKey("lis_prompts.prompt_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # view, click, dismiss, like
    interaction_data = Column(JSON, default=dict)  # Additional interaction context
    
    # Device and location context
    device_info = Column(JSON, default=dict)  # Device type, browser, etc.
    location_at_interaction = Column(JSON, default=dict)  # Location when interaction occurred
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prompt = relationship("LISPrompt", back_populates="interactions")
    user = relationship("UserInDB")


class LISAnalytics(Base):
    """Database model for storing LIS analytics and insights"""
    __tablename__ = "lis_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Analytics data
    total_prompts_generated = Column(Integer, default=0)
    prompts_by_type = Column(JSON, default=dict)  # Count by prompt type
    average_relevance_score = Column(Float, default=0.0)
    top_interaction_types = Column(JSON, default=dict)  # Interaction counts by type
    location_effectiveness = Column(JSON, default=dict)  # Effectiveness by location
    user_engagement_rate = Column(Float, default=0.0)
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("UserInDB")


class LISLocationData(Base):
    """Database model for storing location-specific data and recommendations"""
    __tablename__ = "lis_location_data"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(255), nullable=False, index=True)
    
    # Location details
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Location data
    restaurants = Column(JSON, default=list)  # Restaurant data for this location
    activities = Column(JSON, default=list)  # Activity data for this location
    attractions = Column(JSON, default=list)  # Attraction data for this location
    events = Column(JSON, default=list)  # Event data for this location
    
    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source = Column(String(100), nullable=True)  # Source of the data (API, manual, etc.)
    is_active = Column(Boolean, default=True)  # Whether this location data is active


class LISUserPreference(Base):
    """Database model for storing user preferences learned from LIS interactions"""
    __tablename__ = "lis_user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Preference categories
    cuisine_preferences = Column(JSON, default=dict)  # Cuisine preferences with weights
    activity_preferences = Column(JSON, default=dict)  # Activity preferences with weights
    location_preferences = Column(JSON, default=dict)  # Location preferences with weights
    time_preferences = Column(JSON, default=dict)  # Time-based preferences
    budget_preferences = Column(JSON, default=dict)  # Budget preferences
    
    # Interaction patterns
    preferred_prompt_types = Column(JSON, default=dict)  # Preferred prompt types
    interaction_patterns = Column(JSON, default=dict)  # Interaction patterns
    engagement_times = Column(JSON, default=dict)  # Times when user is most engaged
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("UserInDB") 
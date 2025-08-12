# models.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserInDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    
    # Relationships - using string references to avoid circular imports
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recommendations = relationship("ContentRecommendation", back_populates="user")
    interactions = relationship("ContentInteraction", back_populates="user")

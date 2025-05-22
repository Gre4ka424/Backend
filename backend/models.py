from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Add new fields for user profile
    birth_date = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    interests = Column(JSON, default=lambda: [], nullable=False)  # Stores list of interest IDs
    joined_groups = Column(JSON, default=lambda: [], nullable=False)  # Stores list of group IDs
    onboarding_completed = Column(Boolean, default=False)  # Flag for completing onboarding
    profile_photo = Column(String, nullable=True)  # URL to profile photo

class SiteContent(Base):
    __tablename__ = "site_content"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EventDB(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    location = Column(String)
    event_date = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    participants = Column(JSON, default=lambda: [], nullable=False)  # List of participant IDs
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Schema for user profile update
class UserProfileUpdate(BaseModel):
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    interests: Optional[List[str]] = None
    joined_groups: Optional[List[int]] = None
    onboarding_completed: Optional[bool] = None
    profile_photo: Optional[str] = None

# Schema for user profile data in response
class UserProfile(BaseModel):
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    interests: List[str] = []
    joined_groups: List[int] = []
    onboarding_completed: bool = False
    profile_photo: Optional[str] = None
    
    class Config:
        from_attributes = True

# Extended user schema that includes profile data
class UserWithProfile(User):
    profile: UserProfile
    
    class Config:
        from_attributes = True

class SiteContentBase(BaseModel):
    key: str
    value: str

class SiteContentCreate(SiteContentBase):
    pass

class SiteContentUpdate(BaseModel):
    value: str

class SiteContentOut(SiteContentBase):
    id: int
    updated_at: datetime
    class Config:
        from_attributes = True

# Schemas for events
class EventBase(BaseModel):
    title: str
    description: str
    location: str
    event_date: datetime
    max_participants: Optional[int] = None
    image_url: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    max_participants: Optional[int] = None
    image_url: Optional[str] = None

class Event(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    participants: List[int] = []
    
    class Config:
        from_attributes = True

# Schema for adding/removing event participant
class EventParticipantUpdate(BaseModel):
    user_id: int
    action: str  # "add" or "remove"
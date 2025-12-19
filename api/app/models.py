from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ChallengeType(str, Enum):
    SMS = "sms"
    EMAIL = "email"


# Auth Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ChallengeRequest(BaseModel):
    session_id: str
    code: str
    challenge_type: ChallengeType


class TwoFactorRequest(BaseModel):
    session_id: str
    code: str
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    requires_challenge: bool = False
    challenge_type: Optional[ChallengeType] = None
    session_id: Optional[str] = None
    access_token: Optional[str] = None
    user: Optional["UserProfile"] = None


# User Models
class UserProfile(BaseModel):
    ig_user_id: str
    username: str
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    media_count: Optional[int] = None
    is_private: Optional[bool] = None
    is_verified: Optional[bool] = None
    biography: Optional[str] = None


class InstagramUser(BaseModel):
    ig_id: str
    username: str
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    is_verified: bool = False
    is_private: bool = False


# Analytics Models
class AnalyticsOverview(BaseModel):
    total_followers: int
    total_following: int
    not_following_back: int
    not_followed_back: int
    mutual_friends: int
    new_followers: int = 0  # Since last sync
    lost_followers: int = 0  # Since last sync
    last_sync: Optional[datetime] = None


class DetailedAnalytics(BaseModel):
    overview: AnalyticsOverview
    followers: list[InstagramUser] = []  # All followers
    following: list[InstagramUser] = []  # All following
    not_following_back: list[InstagramUser] = []  # People who don't follow you back
    not_followed_back: list[InstagramUser] = []  # People you don't follow back
    mutual_friends: list[InstagramUser] = []
    new_followers: list[InstagramUser] = []
    lost_followers: list[InstagramUser] = []
    ghost_followers: list[InstagramUser] = []  # Follow but never engage


# TODO: Story viewer feature - not yet implemented
# class StoryViewerStats(BaseModel):
#     viewer: InstagramUser
#     view_count: int
#     last_viewed: datetime


class SyncStatus(BaseModel):
    is_syncing: bool
    progress: int  # 0-100
    current_task: str
    last_sync: Optional[datetime] = None


class ImageCacheStatus(BaseModel):
    is_caching: bool
    total: int
    completed: int
    failed: int
    current_user: Optional[str] = None
    started_at: Optional[str] = None


# Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


AuthResponse.model_rebuild()

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from databases import Database
from datetime import datetime
from .config import get_settings

settings = get_settings()

# Async database for queries
database = Database(settings.database_url)

# SQLAlchemy for table definitions
metadata = MetaData()

# Users table - stores app users and their Instagram sessions
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ig_user_id", String(50), unique=True, index=True),
    Column("ig_username", String(100), index=True),
    Column("ig_full_name", String(200), nullable=True),
    Column("ig_profile_pic_url", Text, nullable=True),
    Column("session_data", Text),  # Encrypted instagrapi session
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("last_sync_at", DateTime, nullable=True),
)

# Followers snapshot - stores follower data for comparison
followers_snapshot = Table(
    "followers_snapshot",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), index=True),
    Column("snapshot_date", DateTime, default=datetime.utcnow),
    Column("follower_ig_id", String(50)),
    Column("follower_username", String(100)),
    Column("follower_full_name", String(200), nullable=True),
    Column("follower_profile_pic_url", Text, nullable=True),
    Column("is_verified", Boolean, default=False),
    Column("is_private", Boolean, default=False),
)

# Following snapshot
following_snapshot = Table(
    "following_snapshot",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), index=True),
    Column("snapshot_date", DateTime, default=datetime.utcnow),
    Column("following_ig_id", String(50)),
    Column("following_username", String(100)),
    Column("following_full_name", String(200), nullable=True),
    Column("following_profile_pic_url", Text, nullable=True),
    Column("is_verified", Boolean, default=False),
    Column("is_private", Boolean, default=False),
)

# Story viewers - TODO: Feature not yet implemented
# story_viewers = Table(
#     "story_viewers",
#     metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("user_id", Integer, ForeignKey("users.id"), index=True),
#     Column("story_id", String(50)),
#     Column("story_date", DateTime),
#     Column("viewer_ig_id", String(50)),
#     Column("viewer_username", String(100)),
#     Column("viewed_at", DateTime, default=datetime.utcnow),
# )

# Analytics cache
analytics_cache = Table(
    "analytics_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), unique=True),
    Column("data", Text),  # JSON serialized analytics
    Column("computed_at", DateTime, default=datetime.utcnow),
)


async def init_db():
    """Initialize database tables."""
    # Use sync engine for table creation
    sync_url = settings.database_url.replace("+aiosqlite", "")
    engine = create_engine(sync_url)
    metadata.create_all(engine)
    engine.dispose()


async def connect_db():
    """Connect to database."""
    await database.connect()


async def disconnect_db():
    """Disconnect from database."""
    await database.disconnect()

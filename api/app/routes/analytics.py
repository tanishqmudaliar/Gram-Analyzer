from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..models import (
    DetailedAnalytics,
    AnalyticsOverview,
    InstagramUser,
    SyncStatus,
    UserProfile,
    ImageCacheStatus,
)
from ..auth import get_current_user, decrypt_session
from ..instagram_service import InstagramService, RATE_LIMITS, InstagramRateLimitError
from ..analytics_service import analytics_service
from ..database import database, users
from ..config import get_settings
from ..log_stream import log
from ..image_cache_service import (
    cache_profile_pictures,
    has_cached_pic,
    get_cached_pic_path,
    get_cache_status,
)

settings = get_settings()
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Track sync status per user (in production, use Redis)
sync_status: dict[str, SyncStatus] = {}


def can_sync(last_sync: Optional[datetime]) -> tuple[bool, Optional[int]]:
    """
    Check if user can sync based on cooldown.
    Returns (can_sync, seconds_until_next_sync)
    """
    if last_sync is None:
        return True, None

    # Make sure last_sync is timezone-aware
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    cooldown = timedelta(hours=settings.sync_cooldown_hours)
    next_sync_time = last_sync + cooldown

    if now >= next_sync_time:
        return True, None

    seconds_remaining = int((next_sync_time - now).total_seconds())
    return False, seconds_remaining


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(current_user: dict = Depends(get_current_user)):
    """Get analytics overview (quick summary)."""
    user_id = current_user["id"]

    # Try to get cached analytics
    cached = await analytics_service.get_cached_analytics(user_id)
    if cached:
        return cached.overview

    # No cached data - need to sync first
    raise HTTPException(
        status_code=404,
        detail="No analytics data available. Please sync your account first.",
    )


@router.get("/detailed", response_model=DetailedAnalytics)
async def get_detailed_analytics(current_user: dict = Depends(get_current_user)):
    """Get detailed analytics with all lists."""
    user_id = current_user["id"]

    # Try to get cached analytics
    cached = await analytics_service.get_cached_analytics(user_id)
    if cached:
        return cached

    # Return empty analytics instead of 404
    return DetailedAnalytics(
        overview=AnalyticsOverview(
            total_followers=0,
            total_following=0,
            not_following_back=0,
            not_followed_back=0,
            mutual_friends=0,
            new_followers=0,
            lost_followers=0,
            last_sync=None,
        ),
        followers=[],
        following=[],
        not_following_back=[],
        not_followed_back=[],
        mutual_friends=[],
        new_followers=[],
        lost_followers=[],
    )


@router.get("/not-following-back", response_model=list[InstagramUser])
async def get_not_following_back(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get list of people who don't follow you back."""
    user_id = current_user["id"]
    cached = await analytics_service.get_cached_analytics(user_id)

    if not cached:
        raise HTTPException(status_code=404, detail="Please sync your account first.")

    return cached.not_following_back[offset : offset + limit]


@router.get("/not-followed-back", response_model=list[InstagramUser])
async def get_not_followed_back(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get list of people you don't follow back."""
    user_id = current_user["id"]
    cached = await analytics_service.get_cached_analytics(user_id)

    if not cached:
        raise HTTPException(status_code=404, detail="Please sync your account first.")

    return cached.not_followed_back[offset : offset + limit]


@router.get("/mutual", response_model=list[InstagramUser])
async def get_mutual_friends(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get list of mutual friends (follow each other)."""
    user_id = current_user["id"]
    cached = await analytics_service.get_cached_analytics(user_id)

    if not cached:
        raise HTTPException(status_code=404, detail="Please sync your account first.")

    return cached.mutual_friends[offset : offset + limit]


@router.get("/new-followers", response_model=list[InstagramUser])
async def get_new_followers(current_user: dict = Depends(get_current_user)):
    """Get list of new followers since last sync."""
    user_id = current_user["id"]
    cached = await analytics_service.get_cached_analytics(user_id)

    if not cached:
        raise HTTPException(status_code=404, detail="Please sync your account first.")

    return cached.new_followers


@router.get("/lost-followers", response_model=list[InstagramUser])
async def get_lost_followers(current_user: dict = Depends(get_current_user)):
    """Get list of people who unfollowed you since last sync."""
    user_id = current_user["id"]
    cached = await analytics_service.get_cached_analytics(user_id)

    if not cached:
        raise HTTPException(status_code=404, detail="Please sync your account first.")

    return cached.lost_followers


@router.get("/can-sync")
async def check_can_sync(current_user: dict = Depends(get_current_user)):
    """Check if user can sync (based on 24-hour cooldown)."""
    last_sync = current_user.get("last_sync_at")
    allowed, seconds_remaining = can_sync(last_sync)

    return {
        "can_sync": allowed,
        "seconds_until_next_sync": seconds_remaining,
        "hours_until_next_sync": round(seconds_remaining / 3600, 1) if seconds_remaining else None,
        "last_sync": last_sync.isoformat() if last_sync else None,
        "cooldown_hours": settings.sync_cooldown_hours,
    }


@router.post("/sync")
async def sync_analytics(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    force: bool = False,  # Admin override (not exposed in UI)
):
    """
    Start syncing Instagram data.
    Enforces 24-hour cooldown between syncs.
    """
    user_id = current_user["id"]
    ig_user_id = current_user["ig_user_id"]
    last_sync = current_user.get("last_sync_at")

    log(f"[SYNC] Sync requested for user_id={user_id}, ig_user_id={ig_user_id}, last_sync={last_sync}")

    # Check cooldown (unless force is True - for admin/testing)
    if not force:
        allowed, seconds_remaining = can_sync(last_sync)
        if not allowed:
            hours_remaining = round(seconds_remaining / 3600, 1)
            log(f"[SYNC] Cooldown active - {hours_remaining} hours remaining")
            return {
                "success": False,
                "message": f"Please wait {hours_remaining} hours before syncing again.",
                "can_sync": False,
                "seconds_until_next_sync": seconds_remaining,
            }

    # Check if already syncing
    status_key = f"sync_{user_id}"
    if status_key in sync_status and sync_status[status_key].is_syncing:
        return {
            "success": False,
            "message": "Sync already in progress",
            "status": sync_status[status_key],
        }

    # Start sync
    sync_status[status_key] = SyncStatus(
        is_syncing=True,
        progress=0,
        current_task="Starting sync...",
    )

    # Run sync in background
    background_tasks.add_task(
        perform_sync,
        user_id,
        ig_user_id,
        current_user["session_data"],
        status_key,
    )

    return {
        "success": True,
        "message": "Sync started",
        "status": sync_status[status_key],
    }


@router.get("/sync/status", response_model=SyncStatus)
async def get_sync_status(current_user: dict = Depends(get_current_user)):
    """Get current sync status."""
    user_id = current_user["id"]
    status_key = f"sync_{user_id}"

    if status_key in sync_status:
        return sync_status[status_key]

    # Get last sync time from user record
    return SyncStatus(
        is_syncing=False,
        progress=100,
        current_task="Idle",
        last_sync=current_user.get("last_sync_at"),
    )


async def perform_sync(
    user_id: int,
    ig_user_id: str,
    encrypted_session: str,
    status_key: str,
):
    """Background task to fetch followers and following lists."""
    import asyncio
    import random
    import traceback

    async def human_delay(min_sec: int = 2, max_sec: int = 5):
        """Add human-like delay between operations."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    followers = []
    following = []

    try:
        # Initialize Instagram service
        ig_service = InstagramService()
        session_data = decrypt_session(encrypted_session)

        sync_status[status_key].current_task = "Restoring session..."
        sync_status[status_key].progress = 5

        if not ig_service.load_session(session_data):
            sync_status[status_key].is_syncing = False
            sync_status[status_key].current_task = "Session expired. Please login again."
            log("[SYNC] Failed to load session")
            return

        log(f"[SYNC] Session loaded for user_id={user_id}, ig_user_id={ig_user_id}")
        await human_delay(1, 3)

        if not ig_service.load_session(session_data):
            sync_status[status_key].is_syncing = False
            sync_status[status_key]. current_task = "Session expired.  Please login again."
            log("[SYNC] Failed to load session")
            return

        # ADD THIS: 
        sync_status[status_key].current_task = "Validating session..."
        sync_status[status_key].progress = 8

        if not await ig_service.validate_session():
            sync_status[status_key].is_syncing = False
            sync_status[status_key].current_task = "Session invalid. Please login again."
            log("[SYNC] Session validation failed")
            return

        # Get previous followers for comparison
        sync_status[status_key].current_task = "Loading previous data..."
        sync_status[status_key].progress = 10
        previous_followers = await analytics_service.get_previous_followers(user_id)
        log(f"[SYNC] Previous followers count: {len(previous_followers) if previous_followers else 0}")

        # Fetch followers
        sync_status[status_key].current_task = "Fetching followers..."
        sync_status[status_key].progress = 20
        log("[SYNC] Fetching followers...")

        try:
            def update_follower_progress(current, total):
                sync_status[status_key]. current_task = f"Fetching followers...  {current}/{total}"
                sync_status[status_key]. progress = 20 + int((current / total) * 25) if total > 0 else 20
            
            followers = await ig_service.get_followers(ig_user_id, progress_callback=update_follower_progress)
            log(f"[SYNC] Got {len(followers)} followers")
            sync_status[status_key].current_task = f"Found {len(followers)} followers"
            sync_status[status_key].progress = 45
        except InstagramRateLimitError as e:
            log(f"[SYNC ERROR] Instagram rate limit: {e}")
            sync_status[status_key].is_syncing = False
            sync_status[status_key].current_task = str(e)
            return
        except Exception as e:
            log(f"[SYNC ERROR] Failed to fetch followers: {e}")
            log(f"[SYNC ERROR] Traceback: {traceback.format_exc()}")
            # Continue with empty followers list

        await human_delay(3, 8)

        # Fetch following
        sync_status[status_key].current_task = "Fetching following..."
        sync_status[status_key].progress = 50
        log("[SYNC] Fetching following...")

        try:
            def update_following_progress(current, total):
                sync_status[status_key].current_task = f"Fetching following... {current}/{total}"
                sync_status[status_key].progress = 50 + int((current / total) * 25) if total > 0 else 50
            
            following = await ig_service.get_following(ig_user_id, progress_callback=update_following_progress)
            log(f"[SYNC] Got {len(following)} following")
            sync_status[status_key]. current_task = f"Found {len(following)} following"
            sync_status[status_key].progress = 75
        except InstagramRateLimitError as e: 
            log(f"[SYNC ERROR] Instagram rate limit: {e}")
            sync_status[status_key].is_syncing = False
            sync_status[status_key].current_task = str(e)
            return
        except Exception as e:
            log(f"[SYNC ERROR] Failed to fetch following: {e}")
            log(f"[SYNC ERROR] Traceback: {traceback.format_exc()}")
            # Continue with empty following list

        # Compute analytics (even if lists are empty or partial)
        sync_status[status_key].current_task = "Computing analytics..."
        sync_status[status_key].progress = 85
        log(f"[SYNC] Computing analytics with {len(followers)} followers, {len(following)} following")

        analytics = analytics_service.compute_analytics(
            followers=followers,
            following=following,
            previous_followers=previous_followers,
        )

        # Save snapshot
        sync_status[status_key].current_task = "Saving data..."
        sync_status[status_key].progress = 90
        await analytics_service.save_snapshot(user_id, followers, following)

        # Cache analytics
        await analytics_service.cache_analytics(user_id, analytics)

        # Update user's last sync time
        await database.execute(
            users.update()
            .where(users.c.id == user_id)
            .values(last_sync_at=datetime.utcnow())
        )

        # Done
        sync_status[status_key].is_syncing = False
        sync_status[status_key].progress = 100
        sync_status[status_key].current_task = "Sync complete!"
        sync_status[status_key].last_sync = datetime.utcnow()
        log(f"[SYNC] Complete! Followers: {len(followers)}, Following: {len(following)}")

        # Start background image caching (non-blocking)
        log("[SYNC] Starting background image caching...")

        # Get user's profile pic URL from the database
        user_row = await database.fetch_one(
            users.select().where(users.c.id == user_id)
        )
        user_profile_pic_url = user_row["ig_profile_pic_url"] if user_row else None

        # Run image caching in background
        asyncio.create_task(
            cache_profile_pictures(
                user_profile_pic_url=user_profile_pic_url,
                user_ig_id=ig_user_id,
                followers=followers,
                following=following,
            )
        )

    except Exception as e:
        log(f"[SYNC ERROR] Unexpected error: {e}")
        log(f"[SYNC ERROR] Traceback: {traceback.format_exc()}")
        sync_status[status_key].is_syncing = False
        sync_status[status_key].current_task = f"Error: {str(e)}"


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's Instagram profile."""
    ig_user_id = current_user["ig_user_id"]
    encrypted_session = current_user["session_data"]

    ig_service = InstagramService()
    session_data = decrypt_session(encrypted_session)

    if not ig_service.load_session(session_data):
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")

    return await ig_service.get_user_info(ig_user_id)


@router.get("/profile-pic/{ig_user_id}")
async def get_profile_pic(ig_user_id: str):
    """
    Get a cached profile picture by Instagram user ID.
    Returns the image file if cached, 404 otherwise.
    """
    if not has_cached_pic(ig_user_id):
        raise HTTPException(status_code=404, detail="Profile picture not cached")

    pic_path = get_cached_pic_path(ig_user_id)
    return FileResponse(
        pic_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
    )


@router.get("/image-cache/status", response_model=ImageCacheStatus)
async def get_image_cache_status():
    """Get the current status of background image caching."""
    return get_cache_status()


@router.get("/has-cached-pic/{ig_user_id}")
async def check_has_cached_pic(ig_user_id: str):
    """Check if a profile picture is cached for a user."""
    return {"has_cached_pic": has_cached_pic(ig_user_id)}

import os
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Set
from datetime import datetime
from .log_stream import log
from .config import get_settings

settings = get_settings()

# Directory to store cached profile pictures
PROFILE_PICS_DIR = Path(__file__).parent.parent / "profile_pics"

# Track caching status
image_cache_status = {
    "is_caching": False,
    "total": 0,
    "completed": 0,
    "failed": 0,
    "current_user": None,
    "started_at": None,
}


def ensure_profile_pics_dir():
    """Ensure the profile_pics directory exists."""
    PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)


def get_cached_pic_path(ig_user_id: str) -> Path:
    """Get the path for a cached profile picture."""
    return PROFILE_PICS_DIR / f"{ig_user_id}.jpg"


def has_cached_pic(ig_user_id: str) -> bool:
    """Check if a profile picture is already cached."""
    return get_cached_pic_path(ig_user_id).exists()


def get_all_cached_ids() -> Set[str]:
    """Get all Instagram user IDs that have cached profile pictures."""
    ensure_profile_pics_dir()
    cached = set()
    for file in PROFILE_PICS_DIR.glob("*.jpg"):
        cached.add(file.stem)
    return cached


async def download_profile_pic(ig_user_id:  str, profile_pic_url:  str) -> bool:
    """Download and cache a single profile picture."""
    if not profile_pic_url:
        return False
    
    # Skip Instagram default profile pics
    if "44884218_345707102882519_2446069589734326272_n" in profile_pic_url:
        return False

    ensure_profile_pics_dir()
    pic_path = get_cached_pic_path(ig_user_id)

    if pic_path.exists():
        return True

    try: 
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                profile_pic_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "image" in content_type and len(response.content) > 500:
                    pic_path.write_bytes(response.content)
                    return True
            
            return False

    except httpx.TimeoutException:
        log(f"[IMG CACHE] Timeout downloading {ig_user_id}")
        return False
    except Exception as e:
        log(f"[IMG CACHE] Error downloading {ig_user_id}: {e}")
        return False


async def cache_profile_pictures(
    user_profile_pic_url: Optional[str],
    user_ig_id: str,
    followers: list,
    following: list,
):
    """
    Background task to cache all profile pictures.
    Priority: User's own pic > Followers > Following
    Rate limited to 1 image per second.
    """
    global image_cache_status

    # Build unique list of users to cache (preserving priority order)
    users_to_cache = []
    seen_ids = set()

    # Get already cached IDs to skip them
    already_cached = get_all_cached_ids()

    # 1. User's own profile pic (highest priority)
    if user_ig_id and user_ig_id not in already_cached:
        users_to_cache.append({
            "ig_id": user_ig_id,
            "profile_pic_url": user_profile_pic_url,
            "username": "you",
        })
        seen_ids.add(user_ig_id)

    # 2. Followers
    for user in followers:
        ig_id = user.ig_id if hasattr(user, 'ig_id') else user.get('ig_id')
        if ig_id and ig_id not in seen_ids and ig_id not in already_cached:
            users_to_cache.append({
                "ig_id": ig_id,
                "profile_pic_url": user.profile_pic_url if hasattr(user, 'profile_pic_url') else user.get('profile_pic_url'),
                "username": user.username if hasattr(user, 'username') else user.get('username'),
            })
            seen_ids.add(ig_id)

    # 3. Following (only those not already in followers)
    for user in following:
        ig_id = user.ig_id if hasattr(user, 'ig_id') else user.get('ig_id')
        if ig_id and ig_id not in seen_ids and ig_id not in already_cached:
            users_to_cache.append({
                "ig_id": ig_id,
                "profile_pic_url": user.profile_pic_url if hasattr(user, 'profile_pic_url') else user.get('profile_pic_url'),
                "username": user.username if hasattr(user, 'username') else user.get('username'),
            })
            seen_ids.add(ig_id)

    total_to_cache = len(users_to_cache)

    if total_to_cache == 0:
        log("[IMG CACHE] All profile pictures already cached!")
        return

    # Update status
    image_cache_status = {
        "is_caching": True,
        "total": total_to_cache,
        "completed": 0,
        "failed": 0,
        "current_user": None,
        "started_at": datetime.utcnow().isoformat(),
    }

    log(f"[IMG CACHE] Starting to cache {total_to_cache} profile pictures (1 per second)")

    for i, user in enumerate(users_to_cache):
        ig_id = user["ig_id"]
        pic_url = user["profile_pic_url"]
        username = user["username"]

        image_cache_status["current_user"] = username

        if pic_url:
            success = await download_profile_pic(ig_id, pic_url)
            if success:
                image_cache_status["completed"] += 1
                log(f"[IMG CACHE] ({i+1}/{total_to_cache}) Cached @{username}")
            else:
                image_cache_status["failed"] += 1
                log(f"[IMG CACHE] ({i+1}/{total_to_cache}) Failed @{username}")
        else:
            image_cache_status["failed"] += 1
            log(f"[IMG CACHE] ({i+1}/{total_to_cache}) No URL for @{username}")

        # Rate limit: 1 image per second
        if i < total_to_cache - 1:
            await asyncio.sleep(1)

    # Done
    image_cache_status["is_caching"] = False
    image_cache_status["current_user"] = None

    completed = image_cache_status["completed"]
    failed = image_cache_status["failed"]
    log(f"[IMG CACHE] Complete! Cached: {completed}, Failed: {failed}")


def get_cache_status() -> dict:
    """Get the current image caching status."""
    return image_cache_status.copy()

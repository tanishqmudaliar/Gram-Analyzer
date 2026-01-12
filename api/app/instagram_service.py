import json
import asyncio
import uuid
import random
import hashlib
import time
from datetime import datetime
from typing import Optional, Callable
from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword,
    PleaseWaitFewMinutes,
    ClientError,
    ClientBadRequestError,
)


class InstagramRateLimitError(Exception):
    """Raised when Instagram temporarily restricts account access."""
    pass
from .config import get_settings
from .models import InstagramUser, UserProfile
from .log_stream import log

settings = get_settings()

# Store pending challenges (in production, use Redis)
# Challenges expire after 10 minutes
pending_challenges: dict[str, dict] = {}
CHALLENGE_EXPIRY_MINUTES = 10


def cleanup_expired_challenges():
    """Remove challenges older than CHALLENGE_EXPIRY_MINUTES."""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    expiry_threshold = timedelta(minutes=CHALLENGE_EXPIRY_MINUTES)

    expired = [
        session_id for session_id, data in pending_challenges.items()
        if now - data.get("created_at", now) > expiry_threshold
    ]
    for session_id in expired:
        del pending_challenges[session_id]


# Current Instagram app version as of December 2024
CURRENT_APP_VERSION = "410.1.0.63.71"
CURRENT_VERSION_CODE = "571304583"

# Realistic device pool - Instagram sees different devices for different users
DEVICE_POOL = [
    {
        "app_version": CURRENT_APP_VERSION,
        "android_version": 34,
        "android_release": "14",
        "dpi": "440dpi",
        "resolution": "1080x2340",
        "manufacturer": "samsung",
        "device": "SM-S928B",
        "model": "Galaxy S24 Ultra",
        "cpu": "qcom",
        "version_code": CURRENT_VERSION_CODE,
    },
    {
        "app_version": CURRENT_APP_VERSION,
        "android_version": 35,
        "android_release": "15",
        "dpi": "420dpi",
        "resolution": "1080x2400",
        "manufacturer": "Google",
        "device": "husky",
        "model": "Pixel 8 Pro",
        "cpu": "tensor",
        "version_code": CURRENT_VERSION_CODE,
    },
    {
        "app_version": CURRENT_APP_VERSION,
        "android_version": 34,
        "android_release": "14",
        "dpi": "480dpi",
        "resolution": "1312x2868",
        "manufacturer": "OnePlus",
        "device": "CPH2551",
        "model": "OnePlus 12",
        "cpu": "qcom",
        "version_code": CURRENT_VERSION_CODE,
    },
    {
        "app_version": CURRENT_APP_VERSION,
        "android_version": 34,
        "android_release": "14",
        "dpi": "400dpi",
        "resolution": "1080x2400",
        "manufacturer": "Xiaomi",
        "device": "2312DRA50G",
        "model": "Redmi Note 13 Pro",
        "cpu": "mt6877v",
        "version_code": CURRENT_VERSION_CODE,
    },
]

# Rate limiting config - CRITICAL for avoiding detection
RATE_LIMITS = {
    "followers_per_request": 100,
    "delay_between_pages": (4, 10),  # Increased for safety
    "delay_between_operations": (8, 20),  # Increased for safety
    "max_followers_per_sync": 5000,
    "delay_after_login": (3, 7),
    "delay_between_stories": (2, 5),
    "retry_base_delay": 60,  # Base delay for exponential backoff (seconds)
    "max_retries": 3,
}


def generate_device_id(username: str) -> str:
    """Generate consistent device ID per user based on machine UUID."""
    from .config import get_settings
    machine_uuid = get_settings().machine_uuid
    return hashlib.md5(f"{machine_uuid}_{username}_device".encode()).hexdigest()[:16]


def get_device_for_user(username: str) -> dict:
    """Get a consistent device for a user based on username hash."""
    index = int(hashlib.md5(username.encode()).hexdigest(), 16) % len(DEVICE_POOL)
    return DEVICE_POOL[index].copy()


async def human_delay(delay_range: tuple = (2, 5)):
    """Add human-like random delay."""
    delay = random.uniform(delay_range[0], delay_range[1])
    await asyncio.sleep(delay)


class InstagramService:
    def __init__(self):
        self.client: Optional[Client] = None
        self._username: Optional[str] = None

    def _create_client(self, username: str = None) -> Client:
        """Create Instagram client with realistic, per-user settings."""
        cl = Client()

        if username:
            device = get_device_for_user(username)
            device_id = generate_device_id(username)
            self._username = username
        else:
            device = random.choice(DEVICE_POOL)
            device_id = uuid.uuid4().hex[:16]

        cl.set_device(device)

        ua = (
            f"Instagram {device['app_version']} Android "
            f"({device['android_version']}/{device['android_release']}; "
            f"{device['dpi']}; {device['resolution']}; "
            f"{device['manufacturer']}/{device['manufacturer'].lower()}; "
            f"{device['model']}; {device['device']}; {device['cpu']}; "
            f"en_US; {device['version_code']})"
        )
        cl.set_user_agent(ua)

        cl.set_uuids({
            "phone_id": str(uuid.UUID(device_id + device_id)),
            "uuid": str(uuid.UUID(device_id[::-1] + device_id[::-1])),
            "client_session_id": str(uuid.uuid4()),
            "advertising_id": str(uuid.uuid4()),
            "android_device_id": f"android-{device_id}",
        })

        cl.delay_range = [2, 6]

        if settings.proxy_url:
            cl.set_proxy(settings.proxy_url)

        return cl

    async def login(self, username: str, password: str) -> dict:
        """Attempt to login to Instagram."""
        # Cleanup expired challenges to prevent memory leak
        cleanup_expired_challenges()

        self.client = self._create_client(username=username)
        self._username = username
        session_id = str(uuid.uuid4())

        try:
            self.client.login(username, password)
            await human_delay(RATE_LIMITS["delay_after_login"])

            user_info = self.client.user_info(self.client.user_id)
            session_data = self.client.get_settings()
            session_data["_gramanalyzer_username"] = username

            return {
                "success": True,
                "session_id": session_id,
                "session_data": json.dumps(session_data),
                "user": self._user_info_to_profile(user_info),
            }

        except TwoFactorRequired:
            pending_challenges[session_id] = {
                "client": self.client,
                "type": "2fa",
                "username": username,
                "password": password,
                "created_at": datetime.utcnow(),
            }
            return {
                "success": False,
                "requires_2fa": True,
                "session_id": session_id,
                "message": "Two-factor authentication required",
            }

        except ChallengeRequired:
            try:
                self.client.challenge_resolve(self.client.last_json)
                challenge_type = self._get_challenge_type()

                pending_challenges[session_id] = {
                    "client": self.client,
                    "type": "challenge",
                    "challenge_choice": challenge_type,
                    "username": username,
                    "created_at": datetime.utcnow(),
                }

                return {
                    "success": False,
                    "requires_challenge": True,
                    "challenge_type": challenge_type,
                    "session_id": session_id,
                    "message": f"Security code sent via {challenge_type}",
                }
            except Exception as ce:
                return {"success": False, "error": f"Challenge failed: {str(ce)}"}

        except BadPassword:
            return {"success": False, "error": "Invalid password"}

        except PleaseWaitFewMinutes:
            return {
                "success": False,
                "error": "Rate limited. Please wait a few minutes.",
                "retry_after": 300,
            }

        except ClientError as e:
            return {"success": False, "error": f"Instagram error: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}

    def _get_challenge_type(self) -> str:
        """Determine challenge type from client state."""
        try:
            last_json = self.client.last_json
            if "step_name" in last_json:
                step = last_json.get("step_name", "")
                if "email" in step.lower():
                    return "email"
                elif "phone" in step.lower() or "sms" in step.lower():
                    return "sms"
            return "email"
        except Exception:
            return "email"

    async def complete_2fa(self, session_id: str, code: str, username: str, password: str) -> dict:
        """Complete 2FA login."""
        if session_id not in pending_challenges:
            return {"success": False, "error": "Session expired."}

        challenge_data = pending_challenges[session_id]
        if challenge_data["type"] != "2fa":
            return {"success": False, "error": "Invalid challenge type"}

        client = challenge_data["client"]

        try:
            client.login(username, password, verification_code=code)
            await human_delay(RATE_LIMITS["delay_after_login"])

            user_info = client.user_info(client.user_id)
            session_data = client.get_settings()
            session_data["_gramanalyzer_username"] = username

            del pending_challenges[session_id]

            return {
                "success": True,
                "session_data": json.dumps(session_data),
                "user": self._user_info_to_profile(user_info),
            }

        except Exception as e:
            return {"success": False, "error": f"2FA failed: {str(e)}"}

    async def complete_challenge(self, session_id: str, code: str) -> dict:
        """Complete Instagram security challenge."""
        if session_id not in pending_challenges:
            return {"success": False, "error": "Session expired."}

        challenge_data = pending_challenges[session_id]
        if challenge_data["type"] != "challenge":
            return {"success": False, "error": "Invalid challenge type"}

        client = challenge_data["client"]
        username = challenge_data.get("username")

        try:
            client.challenge_code_handler = lambda u, choice: code
            result = client.challenge_resolve(client.last_json)

            if result:
                await human_delay(RATE_LIMITS["delay_after_login"])
                user_info = client.user_info(client.user_id)
                session_data = client.get_settings()
                session_data["_gramanalyzer_username"] = username

                del pending_challenges[session_id]

                return {
                    "success": True,
                    "session_data": json.dumps(session_data),
                    "user": self._user_info_to_profile(user_info),
                }
            else:
                return {"success": False, "error": "Challenge failed."}

        except Exception as e:
            return {"success": False, "error": f"Challenge failed: {str(e)}"}

    def load_session(self, session_data: str) -> bool:
        """Load a saved session with proper device restoration."""
        try:
            settings_dict = json.loads(session_data)
            username = settings_dict.get("_gramanalyzer_username")

            self.client = self._create_client(username=username)
            self._username = username
            self.client.set_settings(settings_dict)

            return True
        except Exception as e:
            log(f"[IG ERROR] Failed to load session: {e}")
            return False

    async def get_followers(
        self,
        user_id: str,
        amount: int = 0,
        progress_callback:  Callable[[int, int], None] = None
    ) -> list[InstagramUser]:
        """Get followers with rate limiting."""
        if not self.client:
            raise ValueError("Not logged in")

        try:
            # Determine how many to fetch (0 means all)
            max_amount = min(amount, RATE_LIMITS["max_followers_per_sync"]) if amount > 0 else 0
            
            log(f"[IG] Fetching followers for user {user_id} (max: {max_amount if max_amount > 0 else 'all'})")
            
            # instagrapi handles pagination internally - just call once
            # amount=0 means fetch all followers
            followers = self.client.user_followers(user_id, amount=max_amount)
            
            log(f"[IG] Got {len(followers)} followers from API")
            
            if progress_callback: 
                progress_callback(len(followers), len(followers))
            
            result = []
            for pk, user in followers.items():
                result.append(self._user_short_to_instagram_user(user))
            
            return result
            
        except ClientBadRequestError as e: 
            error_str = str(e).lower()
            log(f"[IG ERROR] Bad request getting followers: {e}")
            if "400" in str(e) or "bad request" in error_str:
                raise InstagramRateLimitError(
                    "Instagram temporarily restricted access to followers.  "
                    "Try again in 1-24 hours."
                )
            raise
        except PleaseWaitFewMinutes as e: 
            log(f"[IG ERROR] Rate limited: {e}")
            raise InstagramRateLimitError(
                "Instagram rate limit hit. Please wait a few minutes and try again."
            )
        except Exception as e:
            log(f"[IG ERROR] Error getting followers: {e}")
            raise


    async def get_following(
        self,
        user_id: str,
        amount: int = 0,
        progress_callback: Callable[[int, int], None] = None
    ) -> list[InstagramUser]:
        """Get following with rate limiting."""
        if not self.client:
            raise ValueError("Not logged in")

        try:
            max_amount = min(amount, RATE_LIMITS["max_followers_per_sync"]) if amount > 0 else 0
            
            log(f"[IG] Fetching following for user {user_id} (max: {max_amount if max_amount > 0 else 'all'})")
            
            # instagrapi handles pagination internally
            following = self.client.user_following(user_id, amount=max_amount)
            
            log(f"[IG] Got {len(following)} following from API")
            
            if progress_callback:
                progress_callback(len(following), len(following))
            
            result = []
            for pk, user in following.items():
                result.append(self._user_short_to_instagram_user(user))
            
            return result
            
        except ClientBadRequestError as e:
            error_str = str(e).lower()
            log(f"[IG ERROR] Bad request getting following: {e}")
            if "400" in str(e) or "bad request" in error_str: 
                raise InstagramRateLimitError(
                    "Instagram temporarily restricted access to following list."
                    "Try again in 1-24 hours."
                )
            raise
        except PleaseWaitFewMinutes as e:
            log(f"[IG ERROR] Rate limited:  {e}")
            raise InstagramRateLimitError(
                "Instagram rate limit hit. Please wait a few minutes and try again."
            )
        except Exception as e:
            log(f"[IG ERROR] Error getting following: {e}")
            raise

    # TODO: Story viewer feature - not yet implemented
    # async def get_story_viewers(self, story_pk: str) -> list[InstagramUser]:
    #     """Get story viewers with delay."""
    #     if not self.client:
    #         raise ValueError("Not logged in")
    #
    #     try:
    #         await human_delay(RATE_LIMITS["delay_between_stories"])
    #         viewers = self.client.story_viewers(story_pk)
    #         return [self._user_short_to_instagram_user(u) for u in viewers]
    #     except Exception as e:
    #         log(f"[IG ERROR] Error getting story viewers: {e}")
    #         raise
    #
    # async def get_user_stories(self, user_id: str) -> list[dict]:
    #     """Get user stories."""
    #     if not self.client:
    #         raise ValueError("Not logged in")
    #
    #     try:
    #         stories = self.client.user_stories(user_id)
    #         return [
    #             {
    #                 "pk": str(s.pk),
    #                 "taken_at": s.taken_at.isoformat() if s.taken_at else None,
    #                 "media_type": s.media_type,
    #                 "thumbnail_url": str(s.thumbnail_url) if s.thumbnail_url else None,
    #             }
    #             for s in stories
    #         ]
    #     except Exception as e:
    #         log(f"[IG ERROR] Error getting stories: {e}")
    #         raise

    async def get_user_info(self, user_id: str) -> UserProfile:
        """Get user info."""
        if not self.client:
            raise ValueError("Not logged in")

        user_info = self.client.user_info(user_id)
        return self._user_info_to_profile(user_info)

    async def validate_session(self) -> bool:
        """Check if the current session is still valid."""
        if not self.client:
            return False
        
        try: 
            # Try to get own user info as a session check
            self.client.user_info(self.client.user_id)
            return True
        except Exception as e:
            log(f"[IG] Session validation failed: {e}")
            return False

    def _user_info_to_profile(self, user_info) -> UserProfile:
        return UserProfile(
            ig_user_id=str(user_info.pk),
            username=user_info.username,
            full_name=user_info.full_name,
            profile_pic_url=str(user_info.profile_pic_url) if user_info.profile_pic_url else None,
            follower_count=user_info.follower_count,
            following_count=user_info.following_count,
            media_count=user_info.media_count,
            is_private=user_info.is_private,
            is_verified=user_info.is_verified,
            biography=user_info.biography,
        )

    def _user_short_to_instagram_user(self, user_short) -> InstagramUser:
        # Log raw data to WebSocket stream (json already imported at top)
        raw_data = {}
        for attr in ['pk', 'username', 'full_name', 'profile_pic_url', 'is_private', 'is_verified']:
            raw_data[attr] = getattr(user_short, attr, 'NOT_FOUND')
        log(f"[IG RAW] {json.dumps(raw_data, default=str)}")

        is_verified = getattr(user_short, "is_verified", None)
        is_private = getattr(user_short, "is_private", None)

        return InstagramUser(
            ig_id=str(user_short.pk),
            username=user_short.username,
            full_name=user_short.full_name,
            profile_pic_url=str(user_short.profile_pic_url) if user_short.profile_pic_url else None,
            is_verified=is_verified if is_verified is not None else False,
            is_private=is_private if is_private is not None else False,
        )


instagram_service = InstagramService()

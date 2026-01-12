from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import os
from pathlib import Path


def get_or_create_secret_key() -> str:
    """Get secret key from file or create a new one that persists."""
    secret_file = Path(__file__).parent.parent / ".secret_key"

    if secret_file.exists():
        return secret_file.read_text().strip()

    # Generate and save a new secret key
    new_key = secrets.token_urlsafe(32)
    secret_file.write_text(new_key)
    return new_key


def get_machine_uuid() -> str:
    """Get a persistent machine UUID for device identification."""
    import platform
    import subprocess

    try:
        system = platform.system()

        if system == "Windows":
            # Get Windows machine GUID
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                uuid = lines[1].strip()
                if uuid and uuid != "UUID":
                    return uuid

        elif system == "Darwin":  # macOS
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]

        elif system == "Linux":
            # Try machine-id first
            for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                if os.path.exists(path):
                    with open(path) as f:
                        return f.read().strip()
    except Exception:
        pass

    # Fallback: generate and persist a UUID
    uuid_file = Path(__file__).parent.parent / ".machine_uuid"
    if uuid_file.exists():
        return uuid_file.read_text().strip()

    import uuid
    new_uuid = str(uuid.uuid4())
    uuid_file.write_text(new_uuid)
    return new_uuid


class Settings(BaseSettings):
    # App
    app_name: str = "GramAnalyzer API"
    debug: bool = False

    # Security - use persistent secret key
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # Machine identification
    machine_uuid: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./gramanalyzer.db"

    # Instagram
    proxy_url: str | None = None
    max_followers_to_fetch: int = 1000  # ADD THIS
    max_following_to_fetch: int = 1000  # ADD THIS

    # Sync settings
    sync_cooldown_hours: int = 0  # Set to 0 for testing, 24 for production
    auto_sync_on_login: bool = True  # Auto-sync on first login

    # CORS
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set secret key if not provided via env
        if not self.secret_key:
            object.__setattr__(self, 'secret_key', get_or_create_secret_key())
        # Set machine UUID
        if not self.machine_uuid:
            object.__setattr__(self, 'machine_uuid', get_machine_uuid())


@lru_cache()
def get_settings() -> Settings:
    return Settings()

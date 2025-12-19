from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from ..models import (
    LoginRequest,
    ChallengeRequest,
    TwoFactorRequest,
    AuthResponse,
    UserProfile,
    ChallengeType,
)
from ..instagram_service import InstagramService
from ..auth import create_access_token, encrypt_session
from ..database import database, users
from ..log_stream import log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login to Instagram.
    May require additional steps like 2FA or challenge verification.
    """
    log(f"[AUTH] Login attempt for user: {request.username}")
    ig_service = InstagramService()
    result = await ig_service.login(request.username, request.password)
    log(f"[AUTH] Login result: {result}")

    if result.get("success"):
        # Save/update user in database
        user_profile: UserProfile = result["user"]
        encrypted_session = encrypt_session(result["session_data"])

        # Check if user exists
        existing = await database.fetch_one(
            users.select().where(users.c.ig_user_id == user_profile.ig_user_id)
        )

        if existing:
            # Update existing user
            await database.execute(
                users.update()
                .where(users.c.ig_user_id == user_profile.ig_user_id)
                .values(
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    updated_at=datetime.utcnow(),
                )
            )
        else:
            # Create new user
            await database.execute(
                users.insert().values(
                    ig_user_id=user_profile.ig_user_id,
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        # Create access token
        access_token = create_access_token(data={"sub": user_profile.ig_user_id})

        return AuthResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            user=user_profile,
        )

    elif result.get("requires_2fa"):
        return AuthResponse(
            success=False,
            message=result.get("message", "Two-factor authentication required"),
            requires_challenge=True,
            challenge_type=ChallengeType.SMS,  # 2FA is typically SMS/app
            session_id=result["session_id"],
        )

    elif result.get("requires_challenge"):
        challenge_type = ChallengeType.EMAIL
        if result.get("challenge_type") == "sms":
            challenge_type = ChallengeType.SMS

        return AuthResponse(
            success=False,
            message=result.get("message", "Security verification required"),
            requires_challenge=True,
            challenge_type=challenge_type,
            session_id=result["session_id"],
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Login failed"),
        )


@router.post("/verify-2fa", response_model=AuthResponse)
async def verify_2fa(request: TwoFactorRequest):
    """Complete 2FA verification."""
    ig_service = InstagramService()
    result = await ig_service.complete_2fa(
        request.session_id, request.code, request.username, request.password
    )

    if result.get("success"):
        user_profile: UserProfile = result["user"]
        encrypted_session = encrypt_session(result["session_data"])

        # Save user
        existing = await database.fetch_one(
            users.select().where(users.c.ig_user_id == user_profile.ig_user_id)
        )

        if existing:
            await database.execute(
                users.update()
                .where(users.c.ig_user_id == user_profile.ig_user_id)
                .values(
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    updated_at=datetime.utcnow(),
                )
            )
        else:
            await database.execute(
                users.insert().values(
                    ig_user_id=user_profile.ig_user_id,
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        access_token = create_access_token(data={"sub": user_profile.ig_user_id})

        return AuthResponse(
            success=True,
            message="2FA verification successful",
            access_token=access_token,
            user=user_profile,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=result.get("error", "2FA verification failed"),
    )


@router.post("/verify-challenge", response_model=AuthResponse)
async def verify_challenge(request: ChallengeRequest):
    """Complete Instagram security challenge."""
    ig_service = InstagramService()
    result = await ig_service.complete_challenge(request.session_id, request.code)

    if result.get("success"):
        user_profile: UserProfile = result["user"]
        encrypted_session = encrypt_session(result["session_data"])

        # Save user
        existing = await database.fetch_one(
            users.select().where(users.c.ig_user_id == user_profile.ig_user_id)
        )

        if existing:
            await database.execute(
                users.update()
                .where(users.c.ig_user_id == user_profile.ig_user_id)
                .values(
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    updated_at=datetime.utcnow(),
                )
            )
        else:
            await database.execute(
                users.insert().values(
                    ig_user_id=user_profile.ig_user_id,
                    ig_username=user_profile.username,
                    ig_full_name=user_profile.full_name,
                    ig_profile_pic_url=user_profile.profile_pic_url,
                    session_data=encrypted_session,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        access_token = create_access_token(data={"sub": user_profile.ig_user_id})

        return AuthResponse(
            success=True,
            message="Challenge verification successful",
            access_token=access_token,
            user=user_profile,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=result.get("error", "Challenge verification failed"),
    )


@router.post("/logout")
async def logout():
    """Logout - client should discard the token."""
    return {"success": True, "message": "Logged out successfully"}

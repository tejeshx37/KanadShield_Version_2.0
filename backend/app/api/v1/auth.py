from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_current_user, get_db
from app.core.audit import write_audit_log
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.users import RefreshToken, User
from app.repositories.entity_repositories import UserRepository
from app.schemas.auth import RefreshRequest, TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(user: User, db: AsyncSession, settings: Settings) -> TokenResponse:
    access = create_access_token(str(user.id), user.role.value, settings)
    raw_refresh, refresh_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.flush()
    return TokenResponse(access_token=access, refresh_token=raw_refresh)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def register(request: Request, payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.get_by_email(payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "email_taken", "message": "Email already registered"}},
        )
    user = await repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    await write_audit_log(
        db, user_id=user.id, action="register", resource_type="user", resource_id=str(user.id), result="success", request=request
    )
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def login(
    request: Request,
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "invalid_credentials", "message": "Incorrect email or password"}},
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        # Committed immediately: the request's exception path rolls back
        # the session, which would otherwise silently discard this
        # security-relevant audit entry.
        await write_audit_log(
            db, user_id=None, action="login", resource_type="user", resource_id=payload.email, result="failure", request=request
        )
        await db.commit()
        raise invalid
    if not user.is_active:
        raise invalid
    await write_audit_log(
        db, user_id=user.id, action="login", resource_type="user", resource_id=str(user.id), result="success", request=request
    )
    return await _issue_tokens(user, db, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    from sqlalchemy import select

    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "invalid_refresh_token", "message": "Refresh token invalid or expired"}},
    )
    if stored is None or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise invalid
    user = await UserRepository(db).get(stored.user_id)
    if user is None or not user.is_active:
        raise invalid
    stored.revoked = True
    await db.flush()
    return await _issue_tokens(user, db, settings)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user

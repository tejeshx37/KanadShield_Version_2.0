import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.users import User
from app.repositories.entity_repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_app_settings() -> Settings:
    return get_settings()


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "unauthorized", "message": "Not authenticated"}},
    )
    if not token:
        raise unauthorized
    try:
        payload = decode_token(token, settings)
    except ValueError:
        raise unauthorized
    if payload.get("type") != "access":
        raise unauthorized
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise unauthorized
    user = await UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(token, db, settings)
    except HTTPException:
        return None


def require_role(*roles: UserRole):
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "forbidden", "message": "Insufficient role"}},
            )
        return user

    return _checker

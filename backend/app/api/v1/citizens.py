import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_current_user, get_db
from app.core.config import Settings
from app.models.users import CitizenProfile, User

router = APIRouter(prefix="/citizens", tags=["citizens"])


class ProfileUpsertRequest(BaseModel):
    derived_attributes: dict


@router.put("/profile")
async def upsert_profile(
    payload: ProfileUpsertRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(CitizenProfile).where(CitizenProfile.user_id == user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        profile = CitizenProfile(
            user_id=user.id,
            derived_attributes=payload.derived_attributes,
            consent_given_at=datetime.now(timezone.utc),
        )
        db.add(profile)
    else:
        profile.derived_attributes = payload.derived_attributes
        profile.consent_given_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": profile.id, "derived_attributes": profile.derived_attributes}


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(CitizenProfile).where(CitizenProfile.user_id == user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "No citizen profile on file"}},
        )
    return {
        "id": profile.id,
        "derived_attributes": profile.derived_attributes,
        "digilocker_linked": profile.digilocker_linked,
        "consent_given_at": profile.consent_given_at,
    }


@router.post("/profile/revoke-consent")
async def revoke_consent(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(CitizenProfile).where(CitizenProfile.user_id == user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "No citizen profile on file"}},
        )
    profile.consent_given_at = None
    profile.digilocker_linked = False
    await db.flush()
    return {"status": "consent_revoked"}


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(CitizenProfile).where(CitizenProfile.user_id == user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is not None:
        await db.delete(profile)
        await db.flush()
    return None


@router.get("/digilocker/authorize")
async def digilocker_authorize(settings: Settings = Depends(get_app_settings), user: User = Depends(get_current_user)):
    if not settings.DIGILOCKER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "digilocker_disabled", "message": "DigiLocker integration is disabled"}},
        )
    from app.services.citizen_data.digilocker import DigiLockerProvider

    provider = DigiLockerProvider(settings)
    url = await provider.get_authorization_url(state=str(user.id))
    return {"authorization_url": url}

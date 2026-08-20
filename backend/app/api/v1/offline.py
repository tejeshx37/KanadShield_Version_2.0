import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.intelligence.factory import get_embedding_provider, get_llm_provider
from app.services.offline_bundle_service import build_offline_bundle

router = APIRouter(prefix="/offline", tags=["offline"])


class OfflineBundleRequest(BaseModel):
    document_ids: list[uuid.UUID]


@router.post("/bundle")
async def create_offline_bundle(
    payload: OfflineBundleRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    return await build_offline_bundle(
        db, settings, get_llm_provider(), get_embedding_provider(), payload.document_ids
    )

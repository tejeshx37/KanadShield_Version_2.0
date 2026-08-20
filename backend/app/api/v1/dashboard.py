from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.services.analytics_service import (
    corpus_health,
    department_insights,
    frequently_accessed_documents,
    trending_searches,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/trending-searches")
async def get_trending_searches(db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_app_settings)):
    return {"items": await trending_searches(db, settings)}


@router.get("/frequently-accessed-documents")
async def get_frequently_accessed_documents(db: AsyncSession = Depends(get_db)):
    return {"items": await frequently_accessed_documents(db)}


@router.get("/department-insights")
async def get_department_insights(db: AsyncSession = Depends(get_db)):
    return {"items": await department_insights(db)}


@router.get("/corpus-health")
async def get_corpus_health(db: AsyncSession = Depends(get_db)):
    return await corpus_health(db)

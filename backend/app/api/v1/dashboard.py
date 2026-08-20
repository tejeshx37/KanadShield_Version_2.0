from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_db
from app.core.cache import cached_json
from app.core.config import Settings
from app.services.analytics_service import (
    corpus_health,
    department_insights,
    frequently_accessed_documents,
    trending_searches,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Public, non-user-specific aggregates only — safe to cache across users.
# A short TTL keeps the dashboard reasonably fresh without hitting the
# aggregate queries on every request.
_DASHBOARD_CACHE_TTL_SECONDS = 60


@router.get("/trending-searches")
async def get_trending_searches(db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_app_settings)):
    async def _load():
        return {"items": await trending_searches(db, settings)}

    return await cached_json("dashboard:trending-searches", _DASHBOARD_CACHE_TTL_SECONDS, _load)


@router.get("/frequently-accessed-documents")
async def get_frequently_accessed_documents(db: AsyncSession = Depends(get_db)):
    async def _load():
        return {"items": await frequently_accessed_documents(db)}

    return await cached_json("dashboard:frequently-accessed-documents", _DASHBOARD_CACHE_TTL_SECONDS, _load)


@router.get("/department-insights")
async def get_department_insights(db: AsyncSession = Depends(get_db)):
    async def _load():
        return {"items": await department_insights(db)}

    return await cached_json("dashboard:department-insights", _DASHBOARD_CACHE_TTL_SECONDS, _load)


@router.get("/corpus-health")
async def get_corpus_health(db: AsyncSession = Depends(get_db)):
    async def _load():
        return await corpus_health(db)

    return await cached_json("dashboard:corpus-health", _DASHBOARD_CACHE_TTL_SECONDS, _load)

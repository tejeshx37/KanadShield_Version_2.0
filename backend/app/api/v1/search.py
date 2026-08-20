import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_current_user_optional, get_db
from app.core.config import Settings
from app.intelligence.factory import get_embedding_provider
from app.models.document import Act, Document
from app.models.enums import DocumentType, Jurisdiction
from app.models.organizations import Department, Ministry
from app.models.users import User
from app.search.service import HybridSearchService, SearchFilters

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = "",
    source: str | None = None,
    document_type: DocumentType | None = None,
    jurisdiction: Jurisdiction | None = None,
    ministry: uuid.UUID | None = None,
    department: uuid.UUID | None = None,
    court: uuid.UUID | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    language: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    user: User | None = Depends(get_current_user_optional),
):
    page_size = min(page_size or settings.SEARCH_DEFAULT_PAGE_SIZE, settings.SEARCH_MAX_PAGE_SIZE)
    filters = SearchFilters(
        source=source,
        document_type=document_type,
        jurisdiction=jurisdiction,
        ministry_id=ministry,
        department_id=department,
        court_id=court,
        year_from=year_from,
        year_to=year_to,
        language=language,
    )
    service = HybridSearchService(db, settings, get_embedding_provider())
    result = await service.search(q, filters, page=page, page_size=page_size, user_id=user.id if user else None)
    return {
        "items": [item.__dict__ for item in result.items],
        "total": result.total,
        "page": page,
        "page_size": page_size,
        "facets": result.facets,
        "search_time_ms": round(result.search_time_ms, 2),
    }


@router.get("/suggestions")
async def suggestions(q: str = "", limit: int = Query(10, ge=1, le=25), db: AsyncSession = Depends(get_db)):
    """Deterministic autocomplete from real entities/history — no LLM call."""
    if not q.strip():
        return {"suggestions": []}
    like = f"%{q}%"

    title_stmt = select(Document.title).where(Document.title.ilike(like)).distinct().limit(limit)
    act_stmt = select(Act.short_title).where(Act.short_title.ilike(like)).distinct().limit(limit)
    dept_stmt = select(Department.name).where(Department.name.ilike(like)).distinct().limit(limit)
    ministry_stmt = select(Ministry.name).where(Ministry.name.ilike(like)).distinct().limit(limit)

    results: set[str] = set()
    for stmt in (title_stmt, act_stmt, dept_stmt, ministry_stmt):
        rows = (await db.execute(stmt)).scalars().all()
        results.update(r for r in rows if r)

    return {"suggestions": sorted(results)[:limit]}

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.document import Document
from app.models.enums import UserRole
from app.models.ingestion import IngestionDeadLetter

router = APIRouter(prefix="/admin", tags=["admin"])

_LOW_CONFIDENCE_ROLES = (UserRole.ADMIN, UserRole.RESEARCHER)


@router.get("/review-queue", dependencies=[Depends(require_role(*_LOW_CONFIDENCE_ROLES))])
async def low_confidence_review_queue(
    threshold: float = Query(0.6, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Low-confidence classifications, visibly flagged rather than
    silently trusted (per the Document Categorization Module)."""
    stmt = (
        select(Document)
        .where(Document.classification_confidence.is_not(None), Document.classification_confidence < threshold)
        .order_by(Document.classification_confidence.asc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type.value,
                "classification_confidence": d.classification_confidence,
                "classification_method": d.classification_method.value if d.classification_method else None,
            }
            for d in rows
        ]
    }


@router.get("/dead-letters", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def list_dead_letters(
    resolved: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(IngestionDeadLetter).order_by(IngestionDeadLetter.created_at.desc())
    if resolved is not None:
        stmt = stmt.where(IngestionDeadLetter.resolved == resolved)
    stmt = stmt.limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": d.id,
                "source": d.source,
                "source_document_id": d.source_document_id,
                "error_message": d.error_message,
                "retry_count": d.retry_count,
                "resolved": d.resolved,
                "created_at": d.created_at,
            }
            for d in rows
        ]
    }

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.timeline_service import get_document_timeline

router = APIRouter(prefix="/documents", tags=["timeline"])


@router.get("/{document_id}/timeline")
async def document_timeline(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    events = await get_document_timeline(db, document_id)
    return {
        "events": [
            {
                "event_type": e.event_type,
                "date": e.date,
                "title": e.title,
                "document_id": str(e.document_id) if e.document_id else None,
                "detail": e.detail,
            }
            for e in events
        ]
    }

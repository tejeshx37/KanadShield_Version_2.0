import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.entity_repositories import ActRepository

router = APIRouter(prefix="/acts", tags=["acts"])


@router.get("/{act_id}")
async def get_act(act_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    act = await ActRepository(db).get(act_id)
    if act is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Act not found"}},
        )
    document = await DocumentRepository(db).get(act.document_id)
    return {
        "id": act.id,
        "document_id": act.document_id,
        "act_number": act.act_number,
        "year": act.year,
        "short_title": act.short_title,
        "long_title": act.long_title,
        "sections": [
            {"id": s.id, "section_number": s.section_number, "heading": s.heading, "text": s.text}
            for s in sorted(act.sections, key=lambda s: s.order_index)
        ],
        "document": {
            "id": document.id,
            "title": document.title,
            "source_url": document.source_url,
            "date": document.date,
        }
        if document
        else None,
    }

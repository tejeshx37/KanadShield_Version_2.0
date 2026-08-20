import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.entity_repositories import JudgmentRepository

router = APIRouter(prefix="/judgments", tags=["judgments"])


@router.get("/{judgment_id}")
async def get_judgment(judgment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    judgment = await JudgmentRepository(db).get(judgment_id)
    if judgment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Judgment not found"}},
        )
    document = await DocumentRepository(db).get(judgment.document_id)
    return {
        "id": judgment.id,
        "document_id": judgment.document_id,
        "case_number": judgment.case_number,
        "decision_date": judgment.decision_date,
        "citation": judgment.citation,
        "petitioner": judgment.petitioner,
        "respondent": judgment.respondent,
        "headnote": judgment.headnote,
        "document": {
            "id": document.id,
            "title": document.title,
            "source_url": document.source_url,
        }
        if document
        else None,
    }

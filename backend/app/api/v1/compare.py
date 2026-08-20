import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.intelligence.factory import get_llm_provider
from app.models.document import Document
from app.services.comparison_service import compare_texts, explain_diff

router = APIRouter(prefix="/documents", tags=["comparison"])


class CompareRequest(BaseModel):
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID
    explain: bool = False


@router.post("/compare")
async def compare_documents(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    doc_a = await db.get(Document, payload.document_id_a)
    doc_b = await db.get(Document, payload.document_id_b)
    if doc_a is None or doc_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "One or both documents not found"}},
        )
    if not doc_a.extracted_text or not doc_b.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "no_text", "message": "One or both documents have no extracted text to compare"}},
        )

    segments = compare_texts(doc_a.extracted_text, doc_b.extracted_text)
    response = {
        "document_a": {"id": str(doc_a.id), "title": doc_a.title},
        "document_b": {"id": str(doc_b.id), "title": doc_b.title},
        "segments": [
            {
                "change_type": s.change_type.value,
                "category": s.category.value,
                "old_text": s.old_text,
                "new_text": s.new_text,
            }
            for s in segments
        ],
    }
    if payload.explain:
        response["explanation"] = await explain_diff(segments, get_llm_provider())
    return response

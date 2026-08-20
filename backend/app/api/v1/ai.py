import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_current_user_optional, get_db
from app.core.audit import write_audit_log
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.intelligence.factory import get_embedding_provider, get_llm_provider
from app.models.users import User
from app.services.rag.ask_service import answer_question
from app.services.rag.summarize_service import SummarizationError, summarize_document

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    question: str
    document_id: uuid.UUID | None = None


@router.post("/summarize/{document_id}")
@limiter.limit(get_settings().RATE_LIMIT_AI)
async def summarize(
    request: Request,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    user: User | None = Depends(get_current_user_optional),
):
    try:
        summary = await summarize_document(
            db, settings, get_llm_provider(), get_embedding_provider(), document_id
        )
    except SummarizationError as exc:
        await write_audit_log(
            db,
            user_id=user.id if user else None,
            action="ai_summarize",
            resource_type="document",
            resource_id=str(document_id),
            result="insufficient_evidence",
            request=request,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "insufficient_evidence", "message": str(exc)}},
        )
    await write_audit_log(
        db,
        user_id=user.id if user else None,
        action="ai_summarize",
        resource_type="document",
        resource_id=str(document_id),
        result="success",
        request=request,
    )
    return summary


@router.post("/ask")
@limiter.limit(get_settings().RATE_LIMIT_AI)
async def ask(
    request: Request,
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    user: User | None = Depends(get_current_user_optional),
):
    answer = await answer_question(
        db,
        settings,
        get_llm_provider(),
        get_embedding_provider(),
        payload.question,
        document_id=payload.document_id,
    )
    await write_audit_log(
        db,
        user_id=user.id if user else None,
        action="ai_ask",
        resource_type="document",
        resource_id=str(payload.document_id) if payload.document_id else None,
        result="insufficient_evidence" if answer.insufficient_evidence else "success",
        request=request,
    )
    return answer

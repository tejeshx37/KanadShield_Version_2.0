import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, get_db
from app.core.audit import write_audit_log
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.document import Document
from app.models.users import User
from app.workers.ai_tasks import ask_question_task, summarize_document_task
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    question: str
    document_id: uuid.UUID | None = None


class JobAccepted(BaseModel):
    job_id: str
    status: str = "queued"


@router.post("/summarize/{document_id}", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(get_settings().RATE_LIMIT_AI)
async def summarize(
    request: Request,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Document not found"}},
        )
    task = summarize_document_task.delay(str(document_id))
    await write_audit_log(
        db,
        user_id=user.id if user else None,
        action="ai_summarize_requested",
        resource_type="document",
        resource_id=str(document_id),
        result="queued",
        request=request,
    )
    return JobAccepted(job_id=task.id)


@router.post("/ask", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(get_settings().RATE_LIMIT_AI)
async def ask(
    request: Request,
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    task = ask_question_task.delay(payload.question, str(payload.document_id) if payload.document_id else None)
    await write_audit_log(
        db,
        user_id=user.id if user else None,
        action="ai_ask_requested",
        resource_type="document",
        resource_id=str(payload.document_id) if payload.document_id else None,
        result="queued",
        request=request,
    )
    return JobAccepted(job_id=task.id)


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    result = celery_app.AsyncResult(job_id)
    if result.state == "PENDING":
        return {"status": "pending"}
    if result.state == "FAILURE":
        return {"status": "failed", "error": "The AI processing job failed unexpectedly"}
    if result.state == "SUCCESS":
        return result.result
    return {"status": result.state.lower()}

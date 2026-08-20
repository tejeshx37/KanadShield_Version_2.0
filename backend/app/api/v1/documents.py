import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, get_db
from app.core.config import Settings, get_settings
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction
from app.models.users import DocumentView, User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentDetailSchema, PaginatedDocuments

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=PaginatedDocuments)
async def list_documents(
    document_type: DocumentType | None = None,
    jurisdiction: Jurisdiction | None = None,
    state: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    if jurisdiction:
        stmt = stmt.where(Document.jurisdiction == jurisdiction)
    if state:
        stmt = stmt.where(Document.state == state)
    if year_from:
        stmt = stmt.where(Document.year >= year_from)
    if year_to:
        stmt = stmt.where(Document.year <= year_to)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Document.date.desc().nullslast()).limit(page_size).offset((page - 1) * page_size)
    items = list((await db.execute(stmt)).scalars().all())

    return PaginatedDocuments(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentDetailSchema)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    doc = await DocumentRepository(db).get(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Document not found"}},
        )
    db.add(DocumentView(document_id=doc.id, user_id=user.id if user else None))
    await db.flush()
    return doc

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.document import Document
from app.models.users import Annotation, Collection, CollectionItem, User
from app.services.export_service import render_markdown_notes

router = APIRouter(prefix="/research", tags=["research"])


class CollectionCreateRequest(BaseModel):
    name: str
    description: str | None = None


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection(payload: CollectionCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    collection = Collection(user_id=user.id, name=payload.name, description=payload.description)
    db.add(collection)
    await db.flush()
    return {"id": collection.id, "name": collection.name}


@router.get("/collections")
async def list_collections(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Collection).where(Collection.user_id == user.id)
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [{"id": c.id, "name": c.name, "description": c.description} for c in rows]}


class CollectionItemRequest(BaseModel):
    document_id: uuid.UUID
    note: str | None = None


@router.post("/collections/{collection_id}/items", status_code=status.HTTP_201_CREATED)
async def add_collection_item(
    collection_id: uuid.UUID, payload: CollectionItemRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    collection = await db.get(Collection, collection_id)
    if collection is None or collection.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Collection not found"}})
    item = CollectionItem(collection_id=collection_id, document_id=payload.document_id, note=payload.note)
    db.add(item)
    await db.flush()
    return {"id": item.id, "document_id": item.document_id, "note": item.note}


class AnnotationCreateRequest(BaseModel):
    document_id: uuid.UUID
    page: int | None = None
    quoted_text: str | None = None
    note: str


@router.post("/annotations", status_code=status.HTTP_201_CREATED)
async def create_annotation(payload: AnnotationCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    annotation = Annotation(
        user_id=user.id,
        document_id=payload.document_id,
        page=payload.page,
        quoted_text=payload.quoted_text,
        note=payload.note,
    )
    db.add(annotation)
    await db.flush()
    return {"id": annotation.id, "note": annotation.note}


@router.get("/collections/{collection_id}/export")
async def export_collection(collection_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    collection = await db.get(Collection, collection_id)
    if collection is None or collection.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Collection not found"}})

    items_stmt = (
        select(CollectionItem, Document)
        .join(Document, Document.id == CollectionItem.document_id)
        .where(CollectionItem.collection_id == collection_id)
    )
    rows = (await db.execute(items_stmt)).all()

    annotations: list[Annotation] = []
    if rows:
        annotations_stmt = select(Annotation).where(
            Annotation.user_id == user.id, Annotation.document_id.in_([d.id for _, d in rows])
        )
        annotations = (await db.execute(annotations_stmt)).scalars().all()
    annotations_by_doc: dict[uuid.UUID, list[Annotation]] = {}
    for a in annotations:
        annotations_by_doc.setdefault(a.document_id, []).append(a)

    sections = []
    for item, document in rows:
        body_lines = [f"- Source: {document.source_url or 'N/A'}"]
        if item.note:
            body_lines.append(f"- Note: {item.note}")
        for annotation in annotations_by_doc.get(document.id, []):
            body_lines.append(f"- Annotation: {annotation.note}")
        sections.append((document.title, "\n".join(body_lines)))

    markdown = render_markdown_notes(title=collection.name, sections=sections)
    return PlainTextResponse(content=markdown, media_type="text/markdown")

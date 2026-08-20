import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.users import Bookmark, SavedSearch, User

router = APIRouter(tags=["personalization"])


class BookmarkCreateRequest(BaseModel):
    document_id: uuid.UUID
    note: str | None = None


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED)
async def create_bookmark(payload: BookmarkCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    bookmark = Bookmark(user_id=user.id, document_id=payload.document_id, note=payload.note)
    db.add(bookmark)
    await db.flush()
    return {"id": bookmark.id, "document_id": bookmark.document_id, "note": bookmark.note}


@router.get("/bookmarks")
async def list_bookmarks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Bookmark).where(Bookmark.user_id == user.id).order_by(Bookmark.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [{"id": b.id, "document_id": b.document_id, "note": b.note, "created_at": b.created_at} for b in rows]}


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(bookmark_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    bookmark = await db.get(Bookmark, bookmark_id)
    if bookmark is None or bookmark.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Bookmark not found"}}
        )
    await db.delete(bookmark)
    await db.flush()
    return None


class SavedSearchCreateRequest(BaseModel):
    name: str | None = None
    query: str
    filters: dict = {}


@router.post("/saved-searches", status_code=status.HTTP_201_CREATED)
async def create_saved_search(payload: SavedSearchCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    saved = SavedSearch(user_id=user.id, name=payload.name, query=payload.query, filters=payload.filters)
    db.add(saved)
    await db.flush()
    return {"id": saved.id, "name": saved.name, "query": saved.query, "filters": saved.filters}


@router.get("/saved-searches")
async def list_saved_searches(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(SavedSearch).where(SavedSearch.user_id == user.id).order_by(SavedSearch.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [{"id": s.id, "name": s.name, "query": s.query, "filters": s.filters} for s in rows]}


@router.delete("/saved-searches/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(saved_search_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    saved = await db.get(SavedSearch, saved_search_id)
    if saved is None or saved.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Saved search not found"}}
        )
    await db.delete(saved)
    await db.flush()
    return None


@router.get("/search-history")
async def search_history(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.users import SearchHistory

    stmt = select(SearchHistory).where(SearchHistory.user_id == user.id).order_by(SearchHistory.created_at.desc()).limit(100)
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {"query": h.query, "filters": h.filters, "result_count": h.result_count, "created_at": h.created_at}
            for h in rows
        ]
    }

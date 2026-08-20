import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def get_by_natural_key(self, source: str, source_document_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.source == source,
                Document.source_document_id == source_document_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_type(self, document_type, *, limit: int = 50, offset: int = 0) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.document_type == document_type)
            .order_by(Document.date.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def upsert_by_natural_key(self, *, source: str, source_document_id: str, **fields) -> tuple[Document, bool]:
        """Idempotent ingestion entry point. Returns (document, was_created).
        Never creates a duplicate for an existing (source, source_document_id)."""
        existing = await self.get_by_natural_key(source, source_document_id)
        if existing is None:
            doc = Document(source=source, source_document_id=source_document_id, **fields)
            self.session.add(doc)
            await self.session.flush()
            return doc, True

        new_hash = fields.get("content_hash")
        if new_hash is not None and new_hash == existing.content_hash:
            return existing, False  # unchanged — skip reprocessing

        for key, value in fields.items():
            setattr(existing, key, value)
        await self.session.flush()
        return existing, False

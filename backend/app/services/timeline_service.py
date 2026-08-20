import uuid
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentVersion
from app.models.relationships import LegalEntity, LegalRelationship


@dataclass
class TimelineEvent:
    event_type: str  # "published" | "version" | relationship type
    date: date | datetime | None
    title: str
    document_id: uuid.UUID | None
    detail: str | None = None


async def get_document_timeline(db: AsyncSession, document_id: uuid.UUID) -> list[TimelineEvent]:
    """Builds a real chronological timeline from stored version history and
    graph relationships touching this document — never a fabricated
    sequence of events."""
    document = await db.get(Document, document_id)
    if document is None:
        return []

    events: list[TimelineEvent] = [
        TimelineEvent(event_type="published", date=document.date, title=document.title, document_id=document.id)
    ]

    version_rows = (
        (
            await db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.version_number)
            )
        )
        .scalars()
        .all()
    )
    for v in version_rows:
        events.append(
            TimelineEvent(
                event_type="version",
                date=v.created_at,
                title=f"{document.title} — revision {v.version_number}",
                document_id=document.id,
                detail=f"Detected content change (hash {v.content_hash[:12]}...)",
            )
        )

    entity_stmt = select(LegalEntity).where(LegalEntity.canonical_document_id == document_id)
    entity = (await db.execute(entity_stmt)).scalar_one_or_none()
    if entity is not None:
        rel_stmt = select(LegalRelationship, Document.date, Document.title).join(
            Document, Document.id == LegalRelationship.source_document_id, isouter=True
        ).where(
            (LegalRelationship.source_entity_id == entity.id) | (LegalRelationship.target_entity_id == entity.id)
        )
        for relationship, rel_date, rel_title in (await db.execute(rel_stmt)).all():
            events.append(
                TimelineEvent(
                    event_type=relationship.relationship_type.value,
                    date=rel_date,
                    title=rel_title or "Related document",
                    document_id=relationship.source_document_id,
                    detail=relationship.evidence_text,
                )
            )

    def _sort_key(event: TimelineEvent):
        if event.date is None:
            return (1, date.min)
        d = event.date.date() if isinstance(event.date, datetime) else event.date
        return (0, d)

    events.sort(key=_sort_key)
    return events

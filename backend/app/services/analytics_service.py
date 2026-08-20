from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.document import Document
from app.models.organizations import Department, Ministry
from app.models.users import DocumentView, SearchHistory


async def trending_searches(db: AsyncSession, settings: Settings, *, limit: int = 20) -> list[dict]:
    """Aggregated, anonymized query volume — grouped by query text only,
    never joined back to a user, so no per-user search behavior is
    exposed here."""
    since = datetime.now(timezone.utc) - timedelta(days=settings.ANALYTICS_TRENDING_WINDOW_DAYS)
    stmt = (
        select(SearchHistory.query, func.count().label("count"))
        .where(SearchHistory.created_at >= since)
        .group_by(SearchHistory.query)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [{"query": q, "count": c} for q, c in rows]


async def frequently_accessed_documents(db: AsyncSession, *, limit: int = 20) -> list[dict]:
    stmt = (
        select(DocumentView.document_id, func.count().label("views"), Document.title)
        .join(Document, Document.id == DocumentView.document_id)
        .group_by(DocumentView.document_id, Document.title)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [{"document_id": str(doc_id), "title": title, "views": views} for doc_id, views, title in rows]


async def department_insights(db: AsyncSession, *, limit: int = 50) -> list[dict]:
    stmt = (
        select(
            Department.id,
            Department.name,
            func.count(Document.id).label("document_count"),
            func.max(Document.updated_at).label("last_activity"),
        )
        .join(Document, Document.department_id == Department.id, isouter=True)
        .group_by(Department.id, Department.name)
        .order_by(func.count(Document.id).desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {"department_id": str(dept_id), "name": name, "document_count": count, "last_activity": last_activity}
        for dept_id, name, count, last_activity in rows
    ]


async def corpus_health(db: AsyncSession) -> dict:
    """Ingestion volume over time + classification/extraction confidence
    distribution — an honest trust signal about data quality, not a
    vanity metric."""
    volume_stmt = (
        select(func.date_trunc("month", Document.created_at).label("month"), func.count().label("count"))
        .group_by("month")
        .order_by("month")
    )
    volume_rows = (await db.execute(volume_stmt)).all()

    confidence_buckets_stmt = select(
        func.count().filter(Document.classification_confidence >= 0.8).label("high"),
        func.count().filter(
            Document.classification_confidence >= 0.5, Document.classification_confidence < 0.8
        ).label("medium"),
        func.count().filter(Document.classification_confidence < 0.5).label("low"),
        func.count().filter(Document.classification_confidence.is_(None)).label("unknown"),
    )
    classification_row = (await db.execute(confidence_buckets_stmt)).one()

    date_confidence_stmt = select(
        func.count().filter(Document.date_confidence >= 0.8).label("high"),
        func.count().filter(Document.date_confidence >= 0.5, Document.date_confidence < 0.8).label("medium"),
        func.count().filter(Document.date_confidence < 0.5).label("low"),
        func.count().filter(Document.date_confidence.is_(None)).label("unknown"),
    )
    date_row = (await db.execute(date_confidence_stmt)).one()

    total_stmt = select(func.count()).select_from(Document)
    total = (await db.execute(total_stmt)).scalar_one()

    return {
        "total_documents": total,
        "ingestion_volume_by_month": [{"month": str(m), "count": c} for m, c in volume_rows],
        "classification_confidence_distribution": {
            "high": classification_row.high,
            "medium": classification_row.medium,
            "low": classification_row.low,
            "unknown": classification_row.unknown,
        },
        "date_extraction_confidence_distribution": {
            "high": date_row.high,
            "medium": date_row.medium,
            "low": date_row.low,
            "unknown": date_row.unknown,
        },
    }

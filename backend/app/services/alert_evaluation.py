from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.users import Alert

_ALERT_FIELD_MAP = {
    "topic": None,  # matched against title/subject text below
    "act": "act_number",
    "department": "department_id",
    "ministry": "ministry_id",
    "court": "court_id",
    "document_type": "document_type",
}


async def evaluate_alert(db: AsyncSession, alert: Alert) -> list[Document]:
    """Evaluates one saved alert against documents created/updated since it
    was last checked — real query against real data, not a simulated
    trigger."""
    since = alert.last_checked_at or datetime.min.replace(tzinfo=timezone.utc)
    stmt = select(Document).where(Document.updated_at > since)

    target = alert.target or {}
    if alert.alert_type == "topic" and target.get("topic"):
        like = f"%{target['topic']}%"
        stmt = stmt.where(Document.title.ilike(like) | Document.subject.ilike(like))
    elif alert.alert_type in _ALERT_FIELD_MAP and _ALERT_FIELD_MAP[alert.alert_type]:
        column_name = _ALERT_FIELD_MAP[alert.alert_type]
        column = getattr(Document, column_name)
        value = target.get(alert.alert_type)
        if value is not None:
            stmt = stmt.where(column == value)

    matches = (await db.execute(stmt.order_by(Document.updated_at.desc()).limit(50))).scalars().all()
    alert.last_checked_at = datetime.now(timezone.utc)
    await db.flush()
    return matches

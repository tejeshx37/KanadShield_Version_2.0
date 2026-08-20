import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.enums import ImpactLevel
from app.models.ingestion import ChangeRadarReport

router = APIRouter(prefix="/change-radar", tags=["change-radar"])


@router.get("")
async def list_reports(
    impact_level: ImpactLevel | None = None,
    document_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChangeRadarReport).order_by(ChangeRadarReport.created_at.desc())
    if impact_level:
        stmt = stmt.where(ChangeRadarReport.impact_level == impact_level)
    if document_id:
        stmt = stmt.where(ChangeRadarReport.document_id == document_id)
    stmt = stmt.limit(limit)
    reports = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": r.id,
                "document_id": r.document_id,
                "change_type": r.change_type,
                "impact_level": r.impact_level.value,
                "affected_entities": r.affected_entities,
                "related_judgments": r.related_judgments,
                "evidence": r.evidence,
                "created_at": r.created_at,
            }
            for r in reports
        ]
    }

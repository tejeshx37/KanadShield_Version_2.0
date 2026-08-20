import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.enums import ImpactLevel
from app.models.ingestion import ChangeRadarReport
from app.models.relationships import LegalEntity, LegalRelationship
from app.services.comparison_service import DiffCategory, DiffChangeType, compare_texts

# Categories that, when changed, carry real-world consequence for someone
# relying on the document — used for both change_type labeling and impact
# scoring, never an arbitrary "everything is HIGH impact" default.
_HIGH_STAKES_CATEGORIES = {DiffCategory.ELIGIBILITY, DiffCategory.MONETARY_LIMITS, DiffCategory.PENALTIES}


async def _affected_entities(db: AsyncSession, document_id: uuid.UUID) -> dict:
    entity_stmt = select(LegalEntity).where(LegalEntity.canonical_document_id == document_id)
    entity = (await db.execute(entity_stmt)).scalar_one_or_none()
    if entity is None:
        return {}

    rel_stmt = (
        select(LegalRelationship, LegalEntity)
        .join(LegalEntity, LegalEntity.id == LegalRelationship.target_entity_id)
        .where(LegalRelationship.source_entity_id == entity.id)
    )
    rows = (await db.execute(rel_stmt)).all()

    grouped: dict[str, list[str]] = {}
    for relationship, target_entity in rows:
        grouped.setdefault(target_entity.entity_type, []).append(target_entity.name)
    return grouped


def _dominant_category(segments) -> DiffCategory:
    material = [s for s in segments if s.change_type != DiffChangeType.UNCHANGED]
    if not material:
        return DiffCategory.GENERAL
    for category in (
        DiffCategory.ELIGIBILITY,
        DiffCategory.MONETARY_LIMITS,
        DiffCategory.PENALTIES,
        DiffCategory.AUTHORITIES,
        DiffCategory.OBLIGATIONS,
        DiffCategory.DATES,
        DiffCategory.DEFINITIONS,
    ):
        if any(s.category == category for s in material):
            return category
    return DiffCategory.GENERAL


def _impact_level(segments, affected_entity_count: int) -> ImpactLevel:
    material = [s for s in segments if s.change_type != DiffChangeType.UNCHANGED]
    high_stakes_hits = sum(1 for s in material if s.category in _HIGH_STAKES_CATEGORIES)
    if not material:
        return ImpactLevel.LOW
    if high_stakes_hits >= 2 and affected_entity_count >= 2:
        return ImpactLevel.CRITICAL
    if high_stakes_hits >= 1:
        return ImpactLevel.HIGH
    if len(material) >= 3:
        return ImpactLevel.MEDIUM
    return ImpactLevel.LOW


async def generate_change_radar_report(
    db: AsyncSession, document: Document, old_text: str | None, new_text: str
) -> ChangeRadarReport | None:
    """Runs whenever a re-crawled document differs from the stored
    version — this IS the change-detection trigger, not a separate
    parallel system (per the ingestion pipeline's natural-key upsert)."""
    if not old_text or not new_text:
        return None

    segments = compare_texts(old_text, new_text)
    material = [s for s in segments if s.change_type != DiffChangeType.UNCHANGED]
    if not material:
        return None

    affected = await _affected_entities(db, document.id)
    related_judgments = affected.get("JUDGMENT", [])
    affected_count = sum(len(v) for k, v in affected.items() if k != "JUDGMENT")

    report = ChangeRadarReport(
        document_id=document.id,
        change_type=_dominant_category(segments).value,
        changed_sections={
            "segments": [
                {"change_type": s.change_type.value, "category": s.category.value, "old_text": s.old_text, "new_text": s.new_text}
                for s in material[:50]
            ]
        },
        affected_entities=affected,
        related_judgments={"judgments": related_judgments},
        impact_level=_impact_level(segments, affected_count),
        evidence={
            "note": (
                "This reflects a potential impact based on detected textual changes "
                "and known graph relationships — not a legal conclusion."
            ),
            "material_change_count": len(material),
        },
    )
    db.add(report)
    await db.flush()
    return report

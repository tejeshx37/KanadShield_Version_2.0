import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.enums import RelationshipType
from app.models.relationships import LegalEntity, LegalRelationship
from app.services.relationship_extraction import extract_relationships

_TARGET_ENTITY_TYPE_BY_RELATIONSHIP: dict[RelationshipType, str] = {
    RelationshipType.AMENDS: "ACT",
    RelationshipType.REPEALS: "ACT",
    RelationshipType.SUPERSEDES: "GR",
    RelationshipType.IMPLEMENTS: "ACT",
    RelationshipType.ISSUED_BY: "DEPARTMENT",
    RelationshipType.CITES: "JUDGMENT",
}


async def _get_or_create_entity(db: AsyncSession, *, entity_type: str, name: str, canonical_document_id=None) -> LegalEntity:
    stmt = select(LegalEntity).where(LegalEntity.entity_type == entity_type, LegalEntity.name == name)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    entity = LegalEntity(entity_type=entity_type, name=name, canonical_document_id=canonical_document_id)
    db.add(entity)
    await db.flush()
    return entity


async def extract_and_persist_relationships(db: AsyncSession, document: Document) -> list[LegalRelationship]:
    """Runs deterministic relationship extraction over a document's text
    and persists real graph edges — called from the ingestion pipeline so
    the graph grows with the corpus rather than being built separately."""
    if not document.extracted_text:
        return []

    source_entity = await _get_or_create_entity(
        db, entity_type=document.document_type.value, name=document.title, canonical_document_id=document.id
    )

    extracted = extract_relationships(document.extracted_text)
    persisted: list[LegalRelationship] = []
    for item in extracted:
        target_type = _TARGET_ENTITY_TYPE_BY_RELATIONSHIP.get(item.relationship_type, "OTHER")
        target_entity = await _get_or_create_entity(db, entity_type=target_type, name=item.target_text)

        relationship = LegalRelationship(
            source_entity_id=source_entity.id,
            target_entity_id=target_entity.id,
            relationship_type=item.relationship_type,
            source_document_id=document.id,
            confidence=item.confidence,
            evidence_text=item.evidence_text,
        )
        db.add(relationship)
        persisted.append(relationship)
    await db.flush()
    return persisted


async def get_entity_graph(db: AsyncSession, entity_id: uuid.UUID, *, depth: int = 1) -> dict:
    """Returns a small node/edge graph centered on one entity. depth=1
    (default) is direct relationships only — kept simple and fast rather
    than an unbounded traversal."""
    center = await db.get(LegalEntity, entity_id)
    if center is None:
        return {"nodes": [], "edges": []}

    stmt = select(LegalRelationship).where(
        (LegalRelationship.source_entity_id == entity_id) | (LegalRelationship.target_entity_id == entity_id)
    )
    edges = (await db.execute(stmt)).scalars().all()

    node_ids = {entity_id}
    for e in edges:
        node_ids.add(e.source_entity_id)
        node_ids.add(e.target_entity_id)

    nodes_stmt = select(LegalEntity).where(LegalEntity.id.in_(node_ids))
    nodes = (await db.execute(nodes_stmt)).scalars().all()

    return {
        "nodes": [{"id": str(n.id), "type": n.entity_type, "name": n.name} for n in nodes],
        "edges": [
            {
                "source": str(e.source_entity_id),
                "target": str(e.target_entity_id),
                "type": e.relationship_type.value,
                "confidence": e.confidence,
                "evidence_text": e.evidence_text,
            }
            for e in edges
        ],
    }

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import RelationshipType


class LegalEntity(Base, UUIDPKMixin, TimestampMixin):
    """A canonical node in the legal knowledge graph — an Act, Department,
    Court, Scheme, etc. — resolvable across many document mentions."""

    __tablename__ = "legal_entities"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    canonical_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), index=True
    )


class LegalRelationship(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "legal_relationships"

    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("legal_entities.id"), nullable=False, index=True)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("legal_entities.id"), nullable=False, index=True)
    relationship_type: Mapped[RelationshipType] = mapped_column(nullable=False, index=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    page: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence_text: Mapped[str | None] = mapped_column(Text)


class Citation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "citations"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    cited_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)

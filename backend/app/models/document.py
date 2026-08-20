import uuid
from datetime import date as date_type

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Computed, Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ChunkType, DocumentType, ExtractionMethod, Jurisdiction

_EMBEDDING_DIM = get_settings().EMBEDDING_DIMENSIONS


class Document(Base, UUIDPKMixin, TimestampMixin):
    """Common fields shared by every ingested document, regardless of type.
    Type-specific tables (Act, Judgment, GR, ...) hang off this by document_id."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("source", "source_document_id", name="uq_documents_source_natural_key"),
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_document_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(nullable=False, index=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float)
    classification_method: Mapped[ExtractionMethod | None] = mapped_column()

    jurisdiction: Mapped[Jurisdiction] = mapped_column(nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(String(100), index=True)

    source_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)
    language_confidence: Mapped[float | None] = mapped_column(Float)
    is_mixed_language: Mapped[bool] = mapped_column(default=False)

    date: Mapped[date_type | None] = mapped_column(Date, index=True)
    date_confidence: Mapped[float | None] = mapped_column(Float)
    date_extraction_method: Mapped[ExtractionMethod | None] = mapped_column()
    year: Mapped[int | None] = mapped_column(Integer, index=True)

    ministry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ministries.id"), index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), index=True)
    court_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courts.id"), index=True)

    case_number: Mapped[str | None] = mapped_column(String(200), index=True)
    act_number: Mapped[str | None] = mapped_column(String(200), index=True)

    subject: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))

    source_url: Mapped[str | None] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(Text)
    text_available: Mapped[bool] = mapped_column(default=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    # Generated column created by migration 0002_search_indexes.py — declared
    # here as Computed so SQLAlchemy never attempts to write to it directly.
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(subject, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(extracted_text, '')), 'C')",
            persisted=True,
        ),
        nullable=True,
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    translations: Mapped[list["DocumentTranslation"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    __table_args__ = __table_args__ + (
        Index("ix_documents_type_jurisdiction", "document_type", "jurisdiction"),
        Index("ix_documents_year_state", "year", "state"),
    )


class DocumentVersion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_number", name="uq_document_version"),)

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    diff_from_previous: Mapped[dict | None] = mapped_column(JSONB)
    detected_at: Mapped[str | None] = mapped_column(String(50))

    document: Mapped[Document] = relationship(back_populates="versions")


class DocumentChunk(Base, UUIDPKMixin, TimestampMixin):
    """Legal-aware chunk used for hybrid search: never blind fixed-char split."""

    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),)

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[ChunkType] = mapped_column(nullable=False, default=ChunkType.GENERIC)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer)
    section_ref: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_EMBEDDING_DIM))
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', coalesce(text, ''))", persisted=True), nullable=True
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class DocumentTranslation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "document_translations"
    __table_args__ = (UniqueConstraint("document_id", "language", name="uq_document_translation_lang"),)

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    generated_at: Mapped[str | None] = mapped_column(String(50))

    document: Mapped[Document] = relationship(back_populates="translations")


class Act(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "acts"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    act_number: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer)
    short_title: Mapped[str | None] = mapped_column(String(500))
    long_title: Mapped[str | None] = mapped_column(Text)

    sections: Mapped[list["Section"]] = relationship(back_populates="act", cascade="all, delete-orphan")


class Section(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "sections"

    act_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("acts.id"), nullable=False, index=True)
    parent_section_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id"))
    section_number: Mapped[str] = mapped_column(String(50), nullable=False)
    heading: Mapped[str | None] = mapped_column(String(500))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    act: Mapped[Act] = relationship(back_populates="sections")


class Judgment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "judgments"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    court_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courts.id"), index=True)
    case_number: Mapped[str | None] = mapped_column(String(200))
    decision_date: Mapped[date_type | None] = mapped_column(Date)
    citation: Mapped[str | None] = mapped_column(String(300))
    petitioner: Mapped[str | None] = mapped_column(Text)
    respondent: Mapped[str | None] = mapped_column(Text)
    headnote: Mapped[str | None] = mapped_column(Text)
    judge_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String(36)))


class GR(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "government_resolutions"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    gr_number: Mapped[str | None] = mapped_column(String(200))
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    subject: Mapped[str | None] = mapped_column(Text)


class Notification(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "notifications"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    notification_number: Mapped[str | None] = mapped_column(String(200))


class Circular(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "circulars"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    circular_number: Mapped[str | None] = mapped_column(String(200))


class Gazette(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "gazettes"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    gazette_number: Mapped[str | None] = mapped_column(String(200))
    part: Mapped[str | None] = mapped_column(String(100))
    section: Mapped[str | None] = mapped_column(String(100))


class Scheme(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "schemes"

    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    benefits: Mapped[str | None] = mapped_column(Text)
    required_documents: Mapped[list[str] | None] = mapped_column(JSONB)
    official_source: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

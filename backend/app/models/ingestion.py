import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ImpactLevel


class IngestionDeadLetter(Base, UUIDPKMixin, TimestampMixin):
    """Documents/fetches that failed processing — never silently dropped."""

    __tablename__ = "ingestion_dead_letters"

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_document_id: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class IngestionRun(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ingestion_runs"

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    documents_seen: Mapped[int] = mapped_column(Integer, default=0)
    documents_new: Mapped[int] = mapped_column(Integer, default=0)
    documents_updated: Mapped[int] = mapped_column(Integer, default=0)
    documents_unchanged: Mapped[int] = mapped_column(Integer, default=0)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")


class ChangeRadarReport(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "change_radar_reports"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document_versions.id"), index=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_sections: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    affected_entities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    related_judgments: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    impact_level: Mapped[ImpactLevel] = mapped_column(nullable=False, default=ImpactLevel.LOW)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

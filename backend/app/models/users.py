import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import AlertFrequency, UserRole


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(300))
    role: Mapped[UserRole] = mapped_column(nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")


class RefreshToken(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class SavedSearch(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "saved_searches"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(300))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Bookmark(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)


class Alert(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "alerts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    frequency: Mapped[AlertFrequency] = mapped_column(nullable=False, default=AlertFrequency.DAILY)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SearchHistory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "search_history"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(100), index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Collection(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "collections"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class CollectionItem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "collection_items"

    collection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)


class Annotation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "annotations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    page: Mapped[int | None] = mapped_column(Integer)
    quoted_text: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, nullable=False)


class DocumentView(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "document_views"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)


class AuditLog(Base, UUIDPKMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))


class CitizenProfile(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "citizen_profiles"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    derived_attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    digilocker_linked: Mapped[bool] = mapped_column(Boolean, default=False)

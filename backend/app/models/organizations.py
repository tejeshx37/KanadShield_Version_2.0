import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import CourtLevel


class Ministry(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ministries"

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(500))

    departments: Mapped[list["Department"]] = relationship(back_populates="ministry")


class Department(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "departments"

    ministry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ministries.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(500))
    jurisdiction: Mapped[str] = mapped_column(String(20), nullable=False, default="STATE")
    state: Mapped[str | None] = mapped_column(String(100), index=True)

    ministry: Mapped[Ministry | None] = relationship(back_populates="departments")


class Court(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "courts"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    level: Mapped[CourtLevel] = mapped_column(nullable=False)
    jurisdiction_state: Mapped[str | None] = mapped_column(String(100), index=True)

    judges: Mapped[list["Judge"]] = relationship(back_populates="court")


class Judge(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "judges"

    court_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courts.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    source_value: Mapped[str | None] = mapped_column(String(300))

    court: Mapped[Court | None] = relationship(back_populates="judges")

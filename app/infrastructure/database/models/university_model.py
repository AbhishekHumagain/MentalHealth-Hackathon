from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.University import University
from app.infrastructure.database.base import Base


class UniversityModel(Base):
    __tablename__ = "universities"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Fields ────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Audit fields ──────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Mapper methods ────────────────────────────────────────────────────────

    @classmethod
    def from_entity(cls, entity: University) -> "UniversityModel":
        return cls(
            id=uuid.UUID(entity.id),
            name=entity.name,
            domain=entity.domain,
            country=entity.country,
            is_active=entity.is_active,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
        )

    def to_entity(self) -> University:
        return University(
            id=str(self.id),
            name=self.name,
            domain=self.domain,
            country=self.country,
            is_active=self.is_active,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

    def apply_entity(self, entity: University) -> None:
        self.name = entity.name
        self.domain = entity.domain
        self.country = entity.country
        self.is_active = entity.is_active
        self.modified_at = entity.modified_at
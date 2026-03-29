from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.internship import Internship
from app.infrastructure.database.base import Base


class InternshipModel(Base):
    __tablename__ = "internships"
    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_internship_source_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    application_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    posted_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    majors: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    risk_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    risk_reasons: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_entity(self) -> Internship:
        return Internship(
            id=str(self.id),
            title=self.title,
            company=self.company,
            description=self.description,
            location=self.location,
            application_url=self.application_url,
            posted_by=self.posted_by,
            source_type=self.source_type,
            external_id=self.external_id,
            source_name=self.source_name,
            source_url=self.source_url,
            majors=list(self.majors),
            keywords=list(self.keywords),
            is_active=self.is_active,
            risk_score=self.risk_score,
            risk_level=self.risk_level,
            risk_reasons=list(self.risk_reasons),
            expires_at=self.expires_at,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            raw_payload=self.raw_payload,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

    @classmethod
    def from_entity(cls, entity: Internship) -> "InternshipModel":
        return cls(
            id=uuid.UUID(entity.id),
            title=entity.title,
            company=entity.company,
            description=entity.description,
            location=entity.location,
            application_url=entity.application_url,
            posted_by=entity.posted_by,
            source_type=entity.source_type,
            external_id=entity.external_id,
            source_name=entity.source_name,
            source_url=entity.source_url,
            majors=entity.majors,
            keywords=entity.keywords,
            is_active=entity.is_active,
            risk_score=entity.risk_score,
            risk_level=entity.risk_level,
            risk_reasons=entity.risk_reasons,
            expires_at=entity.expires_at,
            first_seen_at=entity.first_seen_at,
            last_seen_at=entity.last_seen_at,
            raw_payload=entity.raw_payload,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
        )

    def apply_entity(self, entity: Internship) -> None:
        self.title = entity.title
        self.company = entity.company
        self.description = entity.description
        self.location = entity.location
        self.application_url = entity.application_url
        self.posted_by = entity.posted_by
        self.source_type = entity.source_type
        self.external_id = entity.external_id
        self.source_name = entity.source_name
        self.source_url = entity.source_url
        self.majors = entity.majors
        self.keywords = entity.keywords
        self.is_active = entity.is_active
        self.risk_score = entity.risk_score
        self.risk_level = entity.risk_level
        self.risk_reasons = entity.risk_reasons
        self.expires_at = entity.expires_at
        self.first_seen_at = entity.first_seen_at
        self.last_seen_at = entity.last_seen_at
        self.raw_payload = entity.raw_payload
        self.modified_at = entity.modified_at

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.internship import Internship
from app.infrastructure.database.base import Base


class InternshipModel(Base):
    __tablename__ = "internships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    application_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    posted_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    majors: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
            majors=list(self.majors),
            keywords=list(self.keywords),
            is_active=self.is_active,
            expires_at=self.expires_at,
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
            majors=entity.majors,
            keywords=entity.keywords,
            is_active=entity.is_active,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
        )

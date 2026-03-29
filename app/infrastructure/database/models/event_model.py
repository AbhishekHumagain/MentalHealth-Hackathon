from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.event import Event
from app.infrastructure.database.base import Base


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hosted_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    host_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    organizer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    risk_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    risk_reasons: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    banner_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String(1000)), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_entity(self) -> Event:
        return Event(
            id=str(self.id),
            title=self.title,
            description=self.description,
            hosted_by=self.hosted_by,
            host_type=self.host_type,
            organizer_name=self.organizer_name,
            mode=self.mode,
            location=self.location,
            meeting_url=self.meeting_url,
            start_at=self.start_at,
            end_at=self.end_at,
            tags=list(self.tags),
            is_active=self.is_active,
            risk_score=self.risk_score,
            risk_level=self.risk_level,
            risk_reasons=list(self.risk_reasons),
            banner_url=self.banner_url,
            image_urls=list(self.image_urls or []),
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

    @classmethod
    def from_entity(cls, entity: Event) -> "EventModel":
        return cls(
            id=uuid.UUID(entity.id),
            title=entity.title,
            description=entity.description,
            hosted_by=entity.hosted_by,
            host_type=entity.host_type,
            organizer_name=entity.organizer_name,
            mode=entity.mode,
            location=entity.location,
            meeting_url=entity.meeting_url,
            start_at=entity.start_at,
            end_at=entity.end_at,
            tags=entity.tags,
            is_active=entity.is_active,
            risk_score=entity.risk_score,
            risk_level=entity.risk_level,
            risk_reasons=entity.risk_reasons,
            banner_url=entity.banner_url,
            image_urls=list(entity.image_urls),
            created_at=entity.created_at,
            modified_at=entity.modified_at,
        )

    def apply_entity(self, entity: Event) -> None:
        self.title = entity.title
        self.description = entity.description
        self.organizer_name = entity.organizer_name
        self.mode = entity.mode
        self.location = entity.location
        self.meeting_url = entity.meeting_url
        self.start_at = entity.start_at
        self.end_at = entity.end_at
        self.tags = entity.tags
        self.is_active = entity.is_active
        self.risk_score = entity.risk_score
        self.risk_level = entity.risk_level
        self.risk_reasons = entity.risk_reasons
        self.banner_url = entity.banner_url
        self.image_urls = list(entity.image_urls)
        self.modified_at = entity.modified_at

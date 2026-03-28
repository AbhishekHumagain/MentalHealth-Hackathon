from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.event_rsvp import EventRSVP
from app.infrastructure.database.base import Base


class EventRSVPModel(Base):
    __tablename__ = "event_rsvps"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_rsvp_event_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="going")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_entity(self) -> EventRSVP:
        return EventRSVP(
            id=str(self.id),
            event_id=str(self.event_id),
            user_id=self.user_id,
            status=self.status,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

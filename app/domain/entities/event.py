from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities.Base import BaseModel


@dataclass
class Event(BaseModel):
    title: str = ""
    description: str = ""
    hosted_by: str = ""
    host_type: str = ""
    organizer_name: str = ""
    mode: str = ""
    location: str | None = None
    meeting_url: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    is_active: bool = True

    def is_upcoming(self, now: datetime) -> bool:
        return self.is_active and self.start_at is not None and self.start_at >= now

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel


@dataclass(frozen=True)
class CreateEventDTO:
    title: str
    description: str
    hosted_by: str
    host_type: str
    organizer_name: str
    mode: str
    start_at: datetime
    end_at: datetime
    location: str | None = None
    meeting_url: str | None = None
    tags: list[str] = field(default_factory=list)
    is_active: bool = True
    risk_score: float = 0.0
    risk_level: str = "low"
    risk_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateEventDTO:
    event_id: str
    editor_user_id: str
    editor_is_admin: bool
    title: str | None = None
    description: str | None = None
    organizer_name: str | None = None
    mode: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    location: str | None = None
    meeting_url: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class EventResponseDTO(BaseModel):
    id: str
    title: str
    description: str
    hosted_by: str
    host_type: str
    organizer_name: str
    mode: str
    location: str | None
    meeting_url: str | None
    start_at: datetime
    end_at: datetime
    tags: list[str]
    is_active: bool
    risk_score: float
    risk_level: str
    risk_reasons: list[str]
    created_at: datetime
    modified_at: datetime

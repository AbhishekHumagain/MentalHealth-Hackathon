from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EventRSVPResponseDTO(BaseModel):
    event_id: str
    user_id: str
    status: str
    google_calendar_url: str
    created_at: datetime
    modified_at: datetime


class EventRSVPStatusDTO(BaseModel):
    event_id: str
    user_id: str
    status: str
    created_at: datetime
    modified_at: datetime


class EventAttendeeDTO(BaseModel):
    user_id: str
    status: str
    created_at: datetime
    modified_at: datetime


class EventAttendeeListDTO(BaseModel):
    event_id: str
    total: int
    attendees: list[EventAttendeeDTO]

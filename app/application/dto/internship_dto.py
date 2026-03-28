from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel


@dataclass(frozen=True)
class CreateInternshipDTO:
    title: str
    company: str
    description: str
    location: str
    application_url: str
    posted_by: str
    source_type: str = "manual"
    external_id: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    majors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    is_active: bool = True
    expires_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, object] | None = None


class InternshipResponseDTO(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str
    application_url: str
    posted_by: str
    source_type: str
    external_id: str | None
    source_name: str | None
    source_url: str | None
    majors: list[str]
    keywords: list[str]
    is_active: bool
    expires_at: datetime | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    raw_payload: dict[str, object] | None
    created_at: datetime
    modified_at: datetime

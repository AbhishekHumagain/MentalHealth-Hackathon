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
    majors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    is_active: bool = True
    expires_at: datetime | None = None


class InternshipResponseDTO(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str
    application_url: str
    posted_by: str
    source_type: str
    majors: list[str]
    keywords: list[str]
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    modified_at: datetime

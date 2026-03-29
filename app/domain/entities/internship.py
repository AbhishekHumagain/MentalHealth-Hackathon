from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.entities.Base import BaseModel


@dataclass
class Internship(BaseModel):
    title: str = ""
    company: str = ""
    description: str = ""
    location: str = ""
    application_url: str = ""
    posted_by: str = ""
    source_type: str = "manual"
    external_id: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    majors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    is_active: bool = True
    risk_score: float = 0.0
    risk_level: str = "low"
    risk_reasons: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, object] | None = None

    def is_available_on(self, target_date: date) -> bool:
        if not self.is_active:
            return False
        if self.expires_at is None:
            return True
        return self.expires_at.date() >= target_date

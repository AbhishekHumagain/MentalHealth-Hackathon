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
    risk_score: float = 0.0
    risk_level: str = "low"
    risk_reasons: list[str] = field(default_factory=list)
    banner_url: str | None = None
    image_urls: list[str] = field(default_factory=list)

    MAX_IMAGES: int = field(default=7, init=False, repr=False, compare=False)

    def add_image(self, url: str) -> None:
        if len(self.image_urls) >= 7:
            raise ValueError("Maximum of 7 images allowed per event.")
        self.image_urls.append(url)

    def remove_image(self, url: str) -> bool:
        if url in self.image_urls:
            self.image_urls.remove(url)
            return True
        return False

    def is_upcoming(self, now: datetime) -> bool:
        return self.is_active and self.start_at is not None and self.start_at >= now

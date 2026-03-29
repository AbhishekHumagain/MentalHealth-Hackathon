from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities.Base import BaseModel


@dataclass
class Apartment(BaseModel):
    title: str = ""
    description: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    monthly_rent: float = 0.0
    bedrooms: int = 1
    bathrooms: float = 1.0
    is_furnished: bool = False
    is_available: bool = True
    available_from: str | None = None
    images_urls: list[str] = field(default_factory=list)
    amenities: list[str] = field(default_factory=list)
    posted_by: str = ""
    source_type: str = "manual"
    external_id: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, object] | None = None

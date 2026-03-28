from __future__ import annotations

from dataclasses import dataclass, field

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
    contact_email: str = ""
    contact_phone: str | None = None
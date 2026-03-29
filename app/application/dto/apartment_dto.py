from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateApartmentDTO(BaseModel):
    title: str
    description: str
    address: str
    city: str
    state: str
    zip_code: str
    monthly_rent: float
    bedrooms: int = 1
    bathrooms: float = 1.0
    is_furnished: bool = False
    available_from: str | None = None
    images_urls: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
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


class ApartmentResponseDTO(BaseModel):
    id: str
    title: str
    description: str
    address: str
    city: str
    state: str
    zip_code: str
    monthly_rent: float
    bedrooms: int
    bathrooms: float
    is_furnished: bool
    is_available: bool
    available_from: str | None
    images_urls: list[str]
    amenities: list[str]
    posted_by: str
    source_type: str
    external_id: str | None
    source_name: str | None
    source_url: str | None
    contact_email: str | None
    contact_phone: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    raw_payload: dict[str, object] | None = None
    created_at: datetime
    modified_at: datetime

    model_config = {"from_attributes": True}

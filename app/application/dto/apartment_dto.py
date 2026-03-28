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
    contact_email: str = ""
    contact_phone: str | None = None


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
    contact_email: str
    contact_phone: str | None
    created_at: datetime
    modified_at: datetime

    model_config = {"from_attributes": True}
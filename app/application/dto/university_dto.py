from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel


##Create DTOs for University entity
@dataclass(frozen=True)
class CreateUniversityDTO:
    name: str
    domain: str
    country: str
    requesting_user_id: str | None = None


##Update DTO with optional fields for partial updates (PATCH)
@dataclass(frozen=True)
class UpdateUniversityDTO:
    university_id: str
    name: str | None = None
    domain: str | None = None
    country: str | None = None
    is_active: bool | None = None
    requesting_user_id: str | None = None


##Response DTO for returning university data in API responses
class UniversityResponseDTO(BaseModel):
    id: str
    name: str
    domain: str
    country: str
    is_active: bool
    created_at: datetime
    modified_at: datetime
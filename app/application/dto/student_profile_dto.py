from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel


@dataclass(frozen=True)
class CreateStudentProfileDTO:
    user_id: str
    university_id: str
    major: str
    skills: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    graduation_year: int | None = None
    preferred_locations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateStudentProfileDTO:
    user_id: str
    university_id: str | None = None
    major: str | None = None
    skills: list[str] | None = None
    interests: list[str] | None = None
    graduation_year: int | None = None
    preferred_locations: list[str] | None = None
    is_active: bool | None = None


class StudentProfileResponseDTO(BaseModel):
    id: str
    user_id: str
    university_id: str
    major: str
    skills: list[str]
    interests: list[str]
    graduation_year: int | None
    preferred_locations: list[str]
    is_active: bool
    created_at: datetime
    modified_at: datetime

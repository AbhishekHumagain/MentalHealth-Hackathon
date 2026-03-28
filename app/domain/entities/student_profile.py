from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.entities.Base import BaseModel


@dataclass
class StudentProfile(BaseModel):
    user_id: str = ""
    university_id: str = ""
    major: str = ""
    skills: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    graduation_year: int | None = None
    preferred_locations: list[str] = field(default_factory=list)
    is_active: bool = True

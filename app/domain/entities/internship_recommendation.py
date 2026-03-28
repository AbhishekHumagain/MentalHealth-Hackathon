from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.entities.Base import BaseModel


@dataclass
class InternshipRecommendation(BaseModel):
    student_profile_id: str = ""
    internship_id: str = ""
    score: float = 0.0
    reason: str = ""
    recommended_for_date: date = field(default_factory=date.today)

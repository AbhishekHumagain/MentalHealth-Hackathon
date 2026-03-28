from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class InternshipRecommendationResponseDTO(BaseModel):
    id: str
    student_profile_id: str
    internship_id: str
    score: float
    reason: str
    recommended_for_date: date
    created_at: datetime
    internship_title: str
    internship_company: str
    internship_location: str
    application_url: str

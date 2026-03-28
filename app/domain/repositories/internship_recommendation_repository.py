from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.internship_recommendation import InternshipRecommendation


class InternshipRecommendationRepository(ABC):
    @abstractmethod
    async def replace_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
        recommendations: list[InternshipRecommendation],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
    ) -> list[InternshipRecommendation]:
        raise NotImplementedError

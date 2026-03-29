from __future__ import annotations

from datetime import date

from app.application.dto.recommendation_dto import InternshipRecommendationResponseDTO
from app.domain.exceptions.student_profile import StudentProfileNotFoundError
from app.domain.repositories.internship_recommendation_repository import (
    InternshipRecommendationRepository,
)
from app.domain.repositories.internship_repository import InternshipRepository
from app.domain.repositories.student_profile_repository import StudentProfileRepository


class ListMyRecommendationsUseCase:
    def __init__(
        self,
        profiles: StudentProfileRepository,
        recommendations: InternshipRecommendationRepository,
        internships: InternshipRepository,
    ) -> None:
        self._profiles = profiles
        self._recommendations = recommendations
        self._internships = internships

    async def execute(
        self,
        user_id: str,
        target_date: date,
    ) -> list[InternshipRecommendationResponseDTO]:
        profile = await self._profiles.get_by_user_id(user_id)
        if profile is None:
            raise StudentProfileNotFoundError(user_id)

        recommendations = await self._recommendations.list_for_profile_on_date(profile.id, target_date)
        results: list[InternshipRecommendationResponseDTO] = []

        for recommendation in recommendations:
            internship = await self._internships.get_by_id(recommendation.internship_id)
            if internship is None:
                continue
            results.append(
                InternshipRecommendationResponseDTO(
                    id=recommendation.id,
                    student_profile_id=recommendation.student_profile_id,
                    internship_id=recommendation.internship_id,
                    score=recommendation.score,
                    reason=recommendation.reason,
                    recommended_for_date=recommendation.recommended_for_date,
                    created_at=recommendation.created_at,
                    internship_title=internship.title,
                    internship_company=internship.company,
                    internship_location=internship.location,
                    application_url=internship.application_url,
                    risk_score=internship.risk_score,
                    risk_level=internship.risk_level,
                    risk_reasons=internship.risk_reasons,
                )
            )

        return results

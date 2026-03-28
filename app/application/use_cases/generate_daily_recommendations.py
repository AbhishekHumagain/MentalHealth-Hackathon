from __future__ import annotations

from datetime import date

from app.application.services.internship_matching import InternshipMatchingService
from app.domain.entities.internship_recommendation import InternshipRecommendation
from app.domain.repositories.internship_recommendation_repository import (
    InternshipRecommendationRepository,
)
from app.domain.repositories.internship_repository import InternshipRepository
from app.domain.repositories.student_profile_repository import StudentProfileRepository


class GenerateDailyRecommendationsUseCase:
    def __init__(
        self,
        profiles: StudentProfileRepository,
        internships: InternshipRepository,
        recommendations: InternshipRecommendationRepository,
        matching_service: InternshipMatchingService | None = None,
    ) -> None:
        self._profiles = profiles
        self._internships = internships
        self._recommendations = recommendations
        self._matching_service = matching_service or InternshipMatchingService()

    async def execute(self, target_date: date) -> int:
        profiles = await self._profiles.list_active()
        internships = await self._internships.list_available(target_date)
        generated_count = 0

        for profile in profiles:
            matches = self._matching_service.score_profile(profile, internships, target_date)
            recommendations = [
                InternshipRecommendation(
                    student_profile_id=profile.id,
                    internship_id=match.internship.id,
                    score=match.score,
                    reason=match.reason,
                    recommended_for_date=target_date,
                )
                for match in matches
            ]
            await self._recommendations.replace_for_profile_on_date(
                profile.id,
                target_date,
                recommendations,
            )
            generated_count += len(recommendations)

        return generated_count

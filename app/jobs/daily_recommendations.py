from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.generate_daily_recommendations import (
    GenerateDailyRecommendationsUseCase,
)
from app.infrastructure.database.repositories.internship_recommendation_repository_impl import (
    SQLAlchemyInternshipRecommendationRepository,
)
from app.infrastructure.database.repositories.internship_repository_impl import (
    SQLAlchemyInternshipRepository,
)
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)


async def run_daily_recommendations(
    session: AsyncSession,
    target_date: date | None = None,
) -> int:
    effective_date = target_date or date.today()
    return await GenerateDailyRecommendationsUseCase(
        profiles=SQLAlchemyStudentProfileRepository(session),
        internships=SQLAlchemyInternshipRepository(session),
        recommendations=SQLAlchemyInternshipRecommendationRepository(session),
    ).execute(effective_date)

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.internship_recommendation import InternshipRecommendation
from app.domain.repositories.internship_recommendation_repository import (
    InternshipRecommendationRepository,
)
from app.infrastructure.database.models.internship_recommendation_model import (
    InternshipRecommendationModel,
)


class SQLAlchemyInternshipRecommendationRepository(InternshipRecommendationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
        recommendations: list[InternshipRecommendation],
    ) -> None:
        await self._session.execute(
            delete(InternshipRecommendationModel).where(
                InternshipRecommendationModel.student_profile_id == uuid.UUID(profile_id),
                InternshipRecommendationModel.recommended_for_date == target_date,
            )
        )
        if not recommendations:
            await self._session.flush()
            return

        models = [InternshipRecommendationModel.from_entity(item) for item in recommendations]
        self._session.add_all(models)
        await self._session.flush()

    async def list_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
    ) -> list[InternshipRecommendation]:
        result = await self._session.execute(
            select(InternshipRecommendationModel)
            .where(
                InternshipRecommendationModel.student_profile_id == uuid.UUID(profile_id),
                InternshipRecommendationModel.recommended_for_date == target_date,
            )
            .order_by(InternshipRecommendationModel.score.desc())
        )
        return [row.to_entity() for row in result.scalars().all()]

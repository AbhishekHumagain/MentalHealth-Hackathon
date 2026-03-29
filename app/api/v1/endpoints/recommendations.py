from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.application.dto.recommendation_dto import InternshipRecommendationResponseDTO
from app.application.use_cases.generate_daily_recommendations import (
    GenerateDailyRecommendationsUseCase,
)
from app.application.use_cases.list_my_recommendations import ListMyRecommendationsUseCase
from app.domain.exceptions.student_profile import StudentProfileNotFoundError
from app.infrastructure.database.repositories.internship_recommendation_repository_impl import (
    SQLAlchemyInternshipRecommendationRepository,
)
from app.infrastructure.database.repositories.internship_repository_impl import (
    SQLAlchemyInternshipRepository,
)
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


class RecommendationResponse(BaseModel):
    id: str
    student_profile_id: str
    internship_id: str
    score: float
    reason: str
    recommended_for_date: date
    internship_title: str
    internship_company: str
    internship_location: str
    application_url: str
    risk_score: float
    risk_level: str
    risk_reasons: list[str]


class RecommendationGenerationResponse(BaseModel):
    generated_count: int
    target_date: date


def get_profile_repo(session: DbSession) -> SQLAlchemyStudentProfileRepository:
    return SQLAlchemyStudentProfileRepository(session)


def get_internship_repo(session: DbSession) -> SQLAlchemyInternshipRepository:
    return SQLAlchemyInternshipRepository(session)


def get_recommendation_repo(session: DbSession) -> SQLAlchemyInternshipRecommendationRepository:
    return SQLAlchemyInternshipRecommendationRepository(session)


def _to_http(dto: InternshipRecommendationResponseDTO) -> RecommendationResponse:
    payload = dto.model_dump()
    payload.pop("created_at", None)
    return RecommendationResponse(**payload)


@router.get("/me", response_model=list[RecommendationResponse])
async def list_my_recommendations(
    current_user_id: CurrentUserId,
    target_date: date = Query(default_factory=date.today),
    profiles: SQLAlchemyStudentProfileRepository = Depends(get_profile_repo),
    internships: SQLAlchemyInternshipRepository = Depends(get_internship_repo),
    recommendations: SQLAlchemyInternshipRecommendationRepository = Depends(
        get_recommendation_repo
    ),
):
    try:
        results = await ListMyRecommendationsUseCase(
            profiles=profiles,
            recommendations=recommendations,
            internships=internships,
        ).execute(current_user_id, target_date)
        return [_to_http(item) for item in results]
    except StudentProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/generate", response_model=RecommendationGenerationResponse)
async def generate_recommendations(
    target_date: date = Query(default_factory=date.today),
    profiles: SQLAlchemyStudentProfileRepository = Depends(get_profile_repo),
    internships: SQLAlchemyInternshipRepository = Depends(get_internship_repo),
    recommendations: SQLAlchemyInternshipRecommendationRepository = Depends(
        get_recommendation_repo
    ),
):
    generated_count = await GenerateDailyRecommendationsUseCase(
        profiles=profiles,
        internships=internships,
        recommendations=recommendations,
    ).execute(target_date)
    return RecommendationGenerationResponse(
        generated_count=generated_count,
        target_date=target_date,
    )

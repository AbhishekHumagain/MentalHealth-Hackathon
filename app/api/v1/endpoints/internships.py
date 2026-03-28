from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.application.dto.internship_dto import CreateInternshipDTO, InternshipResponseDTO
from app.application.use_cases.create_internship import CreateInternshipUseCase
from app.application.use_cases.list_internships import ListInternshipsUseCase
from app.infrastructure.database.repositories.internship_repository_impl import (
    SQLAlchemyInternshipRepository,
)
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/internships", tags=["Internships"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


class InternshipCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1, max_length=255)
    application_url: HttpUrl
    source_type: str = Field(default="manual", max_length=50)
    majors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    is_active: bool = True
    expires_at: datetime | None = None


class InternshipResponse(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str
    application_url: str
    posted_by: str
    source_type: str
    majors: list[str]
    keywords: list[str]
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    modified_at: datetime


class InternshipListResponse(BaseModel):
    items: list[InternshipResponse]
    total: int
    skip: int
    limit: int


def get_repo(session: DbSession) -> SQLAlchemyInternshipRepository:
    return SQLAlchemyInternshipRepository(session)


def _to_http(dto: InternshipResponseDTO) -> InternshipResponse:
    return InternshipResponse(**dto.model_dump())


@router.post("/", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
async def create_internship(
    body: InternshipCreateRequest,
    current_user_id: CurrentUserId,
    repo: SQLAlchemyInternshipRepository = Depends(get_repo),
):
    dto = CreateInternshipDTO(
        posted_by=current_user_id,
        application_url=str(body.application_url),
        **body.model_dump(exclude={"application_url"}),
    )
    return _to_http(await CreateInternshipUseCase(repo).execute(dto))


@router.get("/", response_model=InternshipListResponse)
async def list_internships(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    repo: SQLAlchemyInternshipRepository = Depends(get_repo),
):
    results = await ListInternshipsUseCase(repo).execute(skip, limit)
    return InternshipListResponse(
        items=[_to_http(item) for item in results],
        total=len(results),
        skip=skip,
        limit=limit,
    )

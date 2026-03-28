from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.application.dto.student_profile_dto import (
    CreateStudentProfileDTO,
    StudentProfileResponseDTO,
    UpdateStudentProfileDTO,
)
from app.application.use_cases.create_student_profile import CreateStudentProfileUseCase
from app.application.use_cases.get_student_profile import GetStudentProfileUseCase
from app.application.use_cases.update_student_profile import UpdateStudentProfileUseCase
from app.domain.exceptions.student_profile import (
    StudentProfileAlreadyExistsError,
    StudentProfileNotFoundError,
)
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/student-profiles", tags=["Student Profiles"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


class StudentProfileCreateRequest(BaseModel):
    university_id: str
    major: str = Field(..., min_length=1, max_length=255)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    graduation_year: int | None = None
    preferred_locations: list[str] = Field(default_factory=list)


class StudentProfileUpdateRequest(BaseModel):
    university_id: str | None = None
    major: str | None = None
    skills: list[str] | None = None
    interests: list[str] | None = None
    graduation_year: int | None = None
    preferred_locations: list[str] | None = None
    is_active: bool | None = None


class StudentProfileResponse(BaseModel):
    id: str
    user_id: str
    university_id: str
    major: str
    skills: list[str]
    interests: list[str]
    graduation_year: int | None
    preferred_locations: list[str]
    is_active: bool
    created_at: datetime
    modified_at: datetime


def get_repo(session: DbSession) -> SQLAlchemyStudentProfileRepository:
    return SQLAlchemyStudentProfileRepository(session)


def _to_http(dto: StudentProfileResponseDTO) -> StudentProfileResponse:
    return StudentProfileResponse(**dto.model_dump())


@router.post("/", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_student_profile(
    body: StudentProfileCreateRequest,
    current_user_id: CurrentUserId,
    repo: SQLAlchemyStudentProfileRepository = Depends(get_repo),
):
    try:
        dto = CreateStudentProfileDTO(user_id=current_user_id, **body.model_dump())
        return _to_http(await CreateStudentProfileUseCase(repo).execute(dto))
    except StudentProfileAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_student_profile(
    current_user_id: CurrentUserId,
    repo: SQLAlchemyStudentProfileRepository = Depends(get_repo),
):
    try:
        return _to_http(await GetStudentProfileUseCase(repo).execute(current_user_id))
    except StudentProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/me", response_model=StudentProfileResponse)
async def update_my_student_profile(
    body: StudentProfileUpdateRequest,
    current_user_id: CurrentUserId,
    repo: SQLAlchemyStudentProfileRepository = Depends(get_repo),
):
    try:
        dto = UpdateStudentProfileDTO(user_id=current_user_id, **body.model_dump())
        return _to_http(await UpdateStudentProfileUseCase(repo).execute(dto))
    except StudentProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

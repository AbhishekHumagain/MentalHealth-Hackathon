from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.university_dto import (
    CreateUniversityDTO,
    UpdateUniversityDTO,
    UniversityResponseDTO,
)
from app.application.use_cases.create_university import CreateUniversityUseCase
from app.application.use_cases.delete_university import DeleteUniversityUseCase
from app.application.use_cases.get_university import GetUniversityUseCase
from app.application.use_cases.list_universities import ListUniversitiesUseCase
from app.application.use_cases.update_university import UpdateUniversityUseCase
from app.domain.exceptions.university import (
    UniversityAlreadyExistsError,
    UniversityNotFoundError,
)
from app.infrastructure.database.repositories.university_repository_impl import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.database.session import get_async_session
from datetime import datetime


router = APIRouter(prefix="/universities", tags=["Universities"])


# ── Request Schemas ──────────────────────────────────────────────────────────

class UniversityCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=1, max_length=100)


class UniversityUpdateRequest(BaseModel):
    name: str | None = None
    domain: str | None = None
    country: str | None = None
    is_active: bool | None = None


class UniversityResponse(BaseModel):
    id: str
    name: str
    domain: str
    country: str
    is_active: bool
    created_at: datetime
    modified_at: datetime

    model_config = {"from_attributes": True}


class UniversityListResponse(BaseModel):
    items: list[UniversityResponse]
    total: int
    skip: int
    limit: int


# ── Dependency ───────────────────────────────────────────────────────────────

DbSession = Annotated[AsyncSession, Depends(get_async_session)]


def get_repo(session: DbSession) -> SQLAlchemyUniversityRepository:
    return SQLAlchemyUniversityRepository(session)


# ── Mapper ───────────────────────────────────────────────────────────────────

def _to_http(dto: UniversityResponseDTO) -> UniversityResponse:
    return UniversityResponse(**dto.__dict__)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/", response_model=UniversityResponse, status_code=status.HTTP_201_CREATED)
async def create_university(
    body: UniversityCreateRequest,
    repo: SQLAlchemyUniversityRepository = Depends(get_repo),
):
    try:
        dto = CreateUniversityDTO(**body.dict())
        result = await CreateUniversityUseCase(repo).execute(dto)
        return _to_http(result)
    except UniversityAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=UniversityListResponse)
async def list_universities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    repo: SQLAlchemyUniversityRepository = Depends(get_repo),
):
    results = await ListUniversitiesUseCase(repo).execute(skip, limit)
    return UniversityListResponse(
        items=[_to_http(r) for r in results],
        total=len(results),
        skip=skip,
        limit=limit,
    )


@router.get("/{university_id}", response_model=UniversityResponse)
async def get_university(
    university_id: str,
    repo: SQLAlchemyUniversityRepository = Depends(get_repo),
):
    try:
        result = await GetUniversityUseCase(repo).execute(university_id)
        return _to_http(result)
    except UniversityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{university_id}", response_model=UniversityResponse)
async def update_university(
    university_id: str,
    body: UniversityUpdateRequest,
    repo: SQLAlchemyUniversityRepository = Depends(get_repo),
):
    try:
        dto = UpdateUniversityDTO(university_id=university_id, **body.dict())
        result = await UpdateUniversityUseCase(repo).execute(dto)
        return _to_http(result)
    except UniversityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{university_id}")
async def delete_university(
    university_id: str,
    repo: SQLAlchemyUniversityRepository = Depends(get_repo),
):
    try:
        await DeleteUniversityUseCase(repo).execute(university_id)
        return {"deleted": True}
    except UniversityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
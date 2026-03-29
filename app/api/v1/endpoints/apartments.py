from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.application.dto.apartment_dto import ApartmentResponseDTO, CreateApartmentDTO
from app.application.dto.apartment_sync_dto import ApartmentSyncResultDTO
from app.application.use_cases.create_apartment import CreateApartmentUseCase
from app.application.use_cases.list_apartments import (
    ListApartmentsByLocationUseCase,
    ListApartmentsUseCase,
)
from app.application.use_cases.sync_external_apartments import SyncExternalApartmentsUseCase
from app.infrastructure.database.repositories.apartment_repository_impl import (
    SQLAlchemyApartmentRepository,
)
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/apartments", tags=["Apartments"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


class ApartmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=1, max_length=20)
    monthly_rent: float = Field(..., gt=0)
    bedrooms: int = Field(default=1, ge=0)
    bathrooms: float = Field(default=1.0, ge=0)
    is_furnished: bool = False
    available_from: str | None = None
    images_urls: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    contact_email: str = Field(..., min_length=1)
    contact_phone: str | None = None


class ApartmentSyncRequest(BaseModel):
    locations: list[str] = Field(default_factory=list)
    max_rent: float | None = Field(default=None, gt=0)
    limit_per_location: int = Field(default=20, ge=1, le=100)


class ApartmentResponse(BaseModel):
    id: str
    title: str
    description: str
    address: str
    city: str
    state: str
    zip_code: str
    monthly_rent: float
    bedrooms: int
    bathrooms: float
    is_furnished: bool
    is_available: bool
    available_from: str | None
    images_urls: list[str]
    amenities: list[str]
    posted_by: str
    source_type: str
    external_id: str | None
    source_name: str | None
    source_url: str | None
    contact_email: str | None
    contact_phone: str | None
    first_seen_at: str | None
    last_seen_at: str | None
    created_at: str
    modified_at: str


class ApartmentListResponse(BaseModel):
    items: list[ApartmentResponse]
    total: int
    skip: int
    limit: int


class ApartmentSyncResponse(BaseModel):
    requested_locations: list[str]
    fetched: int
    created: int
    updated: int
    deactivated: int
    skipped: int


def get_repo(session: DbSession) -> SQLAlchemyApartmentRepository:
    return SQLAlchemyApartmentRepository(session)


def get_profile_repo(session: DbSession) -> SQLAlchemyStudentProfileRepository:
    return SQLAlchemyStudentProfileRepository(session)


def _to_http(dto: ApartmentResponseDTO) -> ApartmentResponse:
    return ApartmentResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        address=dto.address,
        city=dto.city,
        state=dto.state,
        zip_code=dto.zip_code,
        monthly_rent=dto.monthly_rent,
        bedrooms=dto.bedrooms,
        bathrooms=dto.bathrooms,
        is_furnished=dto.is_furnished,
        is_available=dto.is_available,
        available_from=dto.available_from,
        images_urls=dto.images_urls,
        amenities=dto.amenities,
        posted_by=dto.posted_by,
        source_type=dto.source_type,
        external_id=dto.external_id,
        source_name=dto.source_name,
        source_url=dto.source_url,
        contact_email=dto.contact_email,
        contact_phone=dto.contact_phone,
        first_seen_at=dto.first_seen_at.isoformat() if dto.first_seen_at else None,
        last_seen_at=dto.last_seen_at.isoformat() if dto.last_seen_at else None,
        created_at=dto.created_at.isoformat(),
        modified_at=dto.modified_at.isoformat(),
    )


def _to_sync_http(dto: ApartmentSyncResultDTO) -> ApartmentSyncResponse:
    return ApartmentSyncResponse(**dto.model_dump())


@router.post("/", response_model=ApartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_apartment(
    body: ApartmentCreateRequest,
    current_user_id: CurrentUserId,
    repo: SQLAlchemyApartmentRepository = Depends(get_repo),
):
    dto = CreateApartmentDTO(
        posted_by=current_user_id,
        **body.model_dump(),
    )
    result = await CreateApartmentUseCase(repo).execute(dto)
    return _to_http(result)


@router.get("/", response_model=ApartmentListResponse)
async def list_apartments(
    city: str | None = Query(None),
    state: str | None = Query(None),
    max_rent: float | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: SQLAlchemyApartmentRepository = Depends(get_repo),
):
    results = await ListApartmentsUseCase(repo).execute(
        city=city, state=state, max_rent=max_rent, skip=skip, limit=limit
    )
    return ApartmentListResponse(
        items=[_to_http(r) for r in results],
        total=len(results),
        skip=skip,
        limit=limit,
    )


@router.get("/by-location", response_model=ApartmentListResponse)
async def list_apartments_by_location(
    locations: list[str] = Query(...),
    max_rent: float | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: SQLAlchemyApartmentRepository = Depends(get_repo),
):
    results = await ListApartmentsByLocationUseCase(repo).execute(
        locations=locations,
        max_rent=max_rent,
        skip=skip,
        limit=limit,
    )
    return ApartmentListResponse(
        items=[_to_http(r) for r in results],
        total=len(results),
        skip=skip,
        limit=limit,
    )


@router.post("/sync", response_model=ApartmentSyncResponse)
async def sync_external_apartments(
    body: ApartmentSyncRequest,
    _current_user_id: CurrentUserId,
    apartments: SQLAlchemyApartmentRepository = Depends(get_repo),
    profiles: SQLAlchemyStudentProfileRepository = Depends(get_profile_repo),
):
    try:
        result = await SyncExternalApartmentsUseCase(
            apartments=apartments,
            profiles=profiles,
        ).execute(
            locations=body.locations or None,
            max_rent=body.max_rent,
            limit_per_location=body.limit_per_location,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _to_sync_http(result)

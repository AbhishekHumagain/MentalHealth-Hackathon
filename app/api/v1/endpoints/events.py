from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.application.dto.event_dto import CreateEventDTO, EventResponseDTO, UpdateEventDTO
from app.application.dto.event_rsvp_dto import EventAttendeeListDTO, EventRSVPResponseDTO, EventRSVPStatusDTO
from app.application.services.event_validation import validate_event_payload
from app.application.use_cases.create_event import CreateEventUseCase
from app.application.use_cases.event_rsvp import (
    CancelEventRSVPUseCase,
    GetMyEventRSVPUseCase,
    ListEventAttendeesUseCase,
    RSVPToEventUseCase,
)
from app.application.use_cases.get_event import GetEventUseCase
from app.application.use_cases.list_events import ListEventsUseCase
from app.application.use_cases.update_event import UpdateEventUseCase
from app.domain.exceptions.event import EventNotFoundError, UnauthorizedEventUpdateError
from app.domain.exceptions.event_rsvp import EventRSVPNotAllowedError
from app.infrastructure.database.models.university_model import UniversityModel
from app.infrastructure.database.repositories.event_repository_impl import SQLAlchemyEventRepository
from app.infrastructure.database.repositories.event_rsvp_repository_impl import SQLAlchemyEventRSVPRepository
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/events", tags=["Events"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]
Mode = Literal["virtual", "in_person", "hybrid"]
HostType = Literal["university", "admin"]

# ── Upload storage ────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("/app/uploads/events")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024   # 5 MB per image
MAX_BANNER_BYTES = 5 * 1024 * 1024  # 5 MB banner
MAX_IMAGES = 7


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    organizer_name: str = Field(..., min_length=1, max_length=255)
    mode: Mode
    location: str | None = Field(default=None, max_length=255)
    meeting_url: HttpUrl | None = None
    start_at: datetime
    end_at: datetime
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class EventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    organizer_name: str | None = Field(default=None, min_length=1, max_length=255)
    mode: Mode | None = None
    location: str | None = Field(default=None, max_length=255)
    meeting_url: HttpUrl | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class EventResponse(BaseModel):
    id: str
    title: str
    description: str
    hosted_by: str
    host_type: HostType
    organizer_name: str
    mode: Mode
    location: str | None
    meeting_url: str | None
    start_at: datetime
    end_at: datetime
    tags: list[str]
    is_active: bool
    risk_score: float
    risk_level: str
    risk_reasons: list[str]
    banner_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    rsvp_count: int
    my_rsvp_status: str | None = None
    created_at: datetime
    modified_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    skip: int
    limit: int


class EventRSVPResponse(BaseModel):
    event_id: str
    user_id: str
    status: str
    google_calendar_url: str
    created_at: datetime
    modified_at: datetime


class EventRSVPStatusResponse(BaseModel):
    event_id: str
    user_id: str
    status: str
    created_at: datetime
    modified_at: datetime


class EventAttendeeResponse(BaseModel):
    user_id: str
    status: str
    created_at: datetime
    modified_at: datetime


class EventAttendeeListResponse(BaseModel):
    event_id: str
    total: int
    attendees: list[EventAttendeeResponse]


def get_repo(session: DbSession) -> SQLAlchemyEventRepository:
    return SQLAlchemyEventRepository(session)


def get_rsvp_repo(session: DbSession) -> SQLAlchemyEventRSVPRepository:
    return SQLAlchemyEventRSVPRepository(session)


def _assert_can_host(claims) -> str:
    if "admin" in claims.roles:
        return "admin"
    if "university" in claims.roles:
        return "university"
    raise HTTPException(status_code=403, detail="Only university and admin users can host events.")


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        value = " ".join(tag.lower().split())
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


async def _to_http(
    dto: EventResponseDTO,
    *,
    claims,
    rsvp_repo: SQLAlchemyEventRSVPRepository,
) -> EventResponse:
    my_rsvp = await rsvp_repo.get_by_event_and_user(event_id=dto.id, user_id=claims.sub)
    return EventResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        hosted_by=dto.hosted_by,
        host_type=dto.host_type,  # type: ignore[arg-type]
        organizer_name=dto.organizer_name,
        mode=dto.mode,  # type: ignore[arg-type]
        location=dto.location,
        meeting_url=dto.meeting_url,
        start_at=dto.start_at,
        end_at=dto.end_at,
        tags=dto.tags,
        is_active=dto.is_active,
        risk_score=dto.risk_score,
        risk_level=dto.risk_level,
        risk_reasons=dto.risk_reasons,
        banner_url=dto.banner_url,
        image_urls=list(dto.image_urls),
        rsvp_count=await rsvp_repo.count_for_event(event_id=dto.id),
        my_rsvp_status=my_rsvp.status if my_rsvp else None,
        created_at=dto.created_at,
        modified_at=dto.modified_at,
    )


def _to_rsvp_http(dto: EventRSVPResponseDTO) -> EventRSVPResponse:
    return EventRSVPResponse(
        event_id=dto.event_id,
        user_id=dto.user_id,
        status=dto.status,
        google_calendar_url=dto.google_calendar_url,
        created_at=dto.created_at,
        modified_at=dto.modified_at,
    )


def _to_rsvp_status_http(dto: EventRSVPStatusDTO) -> EventRSVPStatusResponse:
    return EventRSVPStatusResponse(
        event_id=dto.event_id,
        user_id=dto.user_id,
        status=dto.status,
        created_at=dto.created_at,
        modified_at=dto.modified_at,
    )


def _to_attendee_list_http(dto: EventAttendeeListDTO) -> EventAttendeeListResponse:
    return EventAttendeeListResponse(
        event_id=dto.event_id,
        total=dto.total,
        attendees=[
            EventAttendeeResponse(
                user_id=item.user_id,
                status=item.status,
                created_at=item.created_at,
                modified_at=item.modified_at,
            )
            for item in dto.attendees
        ],
    )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreateRequest,
    claims: CurrentUser,
    session: DbSession,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    host_type = _assert_can_host(claims)
    try:
        validate_event_payload(
            mode=body.mode,
            location=body.location,
            meeting_url=str(body.meeting_url) if body.meeting_url else None,
            start_at=body.start_at,
            end_at=body.end_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if host_type == "university":
        result = await session.execute(
            select(func.count()).select_from(UniversityModel).where(
                UniversityModel.keycloak_user_id == claims.sub
            )
        )
        if (result.scalar_one() or 0) == 0:
            raise HTTPException(status_code=403, detail="University account is not linked to a university record.")

    dto = CreateEventDTO(
        title=body.title,
        description=body.description,
        hosted_by=claims.sub,
        host_type=host_type,
        organizer_name=body.organizer_name,
        mode=body.mode,
        location=body.location,
        meeting_url=str(body.meeting_url) if body.meeting_url else None,
        start_at=body.start_at,
        end_at=body.end_at,
        tags=_normalize_tags(body.tags),
        is_active=body.is_active,
    )
    return await _to_http(await CreateEventUseCase(repo).execute(dto), claims=claims, rsvp_repo=rsvp_repo)


@router.get("/", response_model=EventListResponse)
async def list_events(
    claims: CurrentUser,
    mode: Mode | None = Query(None),
    tag: str | None = Query(None),
    host_type: HostType | None = Query(None),
    start_from: datetime | None = Query(None),
    end_to: datetime | None = Query(None),
    upcoming_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    _ = claims
    results = await ListEventsUseCase(repo).execute(
        mode=mode,
        tag=tag.lower() if tag else None,
        host_type=host_type,
        start_from=start_from,
        end_to=end_to,
        upcoming_only=upcoming_only,
        skip=skip,
        limit=limit,
    )
    return EventListResponse(
        items=[await _to_http(item, claims=claims, rsvp_repo=rsvp_repo) for item in results],
        total=len(results),
        skip=skip,
        limit=limit,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    claims: CurrentUser,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    _ = claims
    try:
        return await _to_http(await GetEventUseCase(repo).execute(event_id), claims=claims, rsvp_repo=rsvp_repo)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    body: EventUpdateRequest,
    claims: CurrentUser,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    existing = await repo.get_by_id(event_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")

    mode = body.mode or existing.mode
    start_at = body.start_at or existing.start_at
    end_at = body.end_at or existing.end_at
    location = body.location if body.location is not None else existing.location
    meeting_url = (
        str(body.meeting_url)
        if body.meeting_url is not None
        else existing.meeting_url
    )
    try:
        validate_event_payload(
            mode=mode,
            location=location,
            meeting_url=meeting_url,
            start_at=start_at,
            end_at=end_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    dto = UpdateEventDTO(
        event_id=event_id,
        editor_user_id=claims.sub,
        editor_is_admin="admin" in claims.roles,
        title=body.title,
        description=body.description,
        organizer_name=body.organizer_name,
        mode=body.mode,
        start_at=body.start_at,
        end_at=body.end_at,
        location=body.location,
        meeting_url=str(body.meeting_url) if body.meeting_url else None,
        tags=_normalize_tags(body.tags) if body.tags is not None else None,
        is_active=body.is_active,
    )
    try:
        updated = await UpdateEventUseCase(repo).execute(dto)
        return await _to_http(updated, claims=claims, rsvp_repo=rsvp_repo)
    except UnauthorizedEventUpdateError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{event_id}/rsvp", response_model=EventRSVPResponse)
async def rsvp_to_event(
    event_id: str,
    claims: CurrentUser,
    event_repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    try:
        result = await RSVPToEventUseCase(event_repo, rsvp_repo).execute(
            event_id=event_id,
            user_id=claims.sub,
        )
        return _to_rsvp_http(result)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EventRSVPNotAllowedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{event_id}/rsvp", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_rsvp(
    event_id: str,
    claims: CurrentUser,
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    await CancelEventRSVPUseCase(rsvp_repo).execute(event_id=event_id, user_id=claims.sub)
    return None


@router.get("/{event_id}/rsvp/me", response_model=EventRSVPStatusResponse | None)
async def get_my_rsvp(
    event_id: str,
    claims: CurrentUser,
    event_repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    try:
        result = await GetMyEventRSVPUseCase(event_repo, rsvp_repo).execute(
            event_id=event_id,
            user_id=claims.sub,
        )
        return _to_rsvp_status_http(result) if result else None
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Image helpers ─────────────────────────────────────────────────────────────

def _assert_can_manage(claims, event) -> None:
    """Raise 403 if caller is neither the host nor an admin."""
    if "admin" not in claims.roles and event.hosted_by != claims.sub:
        raise HTTPException(status_code=403, detail="Only the event host or an admin can manage images.")


async def _save_upload(file: UploadFile, event_id: str, max_bytes: int) -> str:
    """Validate, save the file, and return its public URL path."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: jpeg, png, gif, webp.",
        )
    contents = await file.read()
    if len(contents) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File exceeds {mb} MB limit.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    event_dir = UPLOAD_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    (event_dir / filename).write_bytes(contents)
    return f"/uploads/events/{event_id}/{filename}"


def _delete_file_if_exists(url: str) -> None:
    """Remove a stored file given its URL path."""
    if url and url.startswith("/uploads/"):
        path = Path("/app") / url.lstrip("/")
        if path.exists():
            path.unlink(missing_ok=True)


# ── Banner endpoints ──────────────────────────────────────────────────────────

@router.post("/{event_id}/banner", response_model=EventResponse)
async def upload_banner(
    event_id: str,
    claims: CurrentUser,
    session: DbSession,
    file: UploadFile = File(...),
    repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    """Upload or replace the event banner image (host or admin only). Max 5 MB."""
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    _assert_can_manage(claims, event)

    # Remove old banner file from disk
    if event.banner_url:
        _delete_file_if_exists(event.banner_url)

    url = await _save_upload(file, event_id, MAX_BANNER_BYTES)
    event.banner_url = url
    event.mark_modified(claims.sub)
    updated = await repo.update(event)
    from app.application.use_cases.create_event import _to_dto
    return await _to_http(_to_dto(updated), claims=claims, rsvp_repo=rsvp_repo)


@router.delete("/{event_id}/banner", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    event_id: str,
    claims: CurrentUser,
    session: DbSession,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
):
    """Remove the event banner (host or admin only)."""
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    _assert_can_manage(claims, event)

    if event.banner_url:
        _delete_file_if_exists(event.banner_url)
        event.banner_url = None
        event.mark_modified(claims.sub)
        await repo.update(event)


# ── Image endpoints ───────────────────────────────────────────────────────────

class ImageListResponse(BaseModel):
    event_id: str
    banner_url: str | None
    image_urls: list[str]
    image_count: int
    slots_remaining: int


@router.get("/{event_id}/images", response_model=ImageListResponse)
async def list_images(
    event_id: str,
    claims: CurrentUser,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
):
    """List all images and banner for an event."""
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    return ImageListResponse(
        event_id=event_id,
        banner_url=event.banner_url,
        image_urls=event.image_urls,
        image_count=len(event.image_urls),
        slots_remaining=MAX_IMAGES - len(event.image_urls),
    )


@router.post("/{event_id}/images", response_model=ImageListResponse)
async def upload_images(
    event_id: str,
    claims: CurrentUser,
    session: DbSession,
    files: list[UploadFile] = File(...),
    repo: SQLAlchemyEventRepository = Depends(get_repo),
):
    """Upload up to 7 images total for an event (host or admin only). Max 5 MB each.

    You can upload multiple files in one request. The total across all uploads
    cannot exceed 7 images per event.
    """
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    _assert_can_manage(claims, event)

    slots = MAX_IMAGES - len(event.image_urls)
    if slots <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"This event already has {MAX_IMAGES} images. Delete some before uploading more.",
        )
    if len(files) > slots:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. You can upload at most {slots} more image(s) (max {MAX_IMAGES} total).",
        )

    for file in files:
        url = await _save_upload(file, event_id, MAX_IMAGE_BYTES)
        event.image_urls.append(url)

    event.mark_modified(claims.sub)
    updated = await repo.update(event)
    return ImageListResponse(
        event_id=event_id,
        banner_url=updated.banner_url,
        image_urls=updated.image_urls,
        image_count=len(updated.image_urls),
        slots_remaining=MAX_IMAGES - len(updated.image_urls),
    )


@router.delete("/{event_id}/images/{image_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    event_id: str,
    image_index: int,
    claims: CurrentUser,
    session: DbSession,
    repo: SQLAlchemyEventRepository = Depends(get_repo),
):
    """Delete an event image by its index (0-based) in the image_urls list (host or admin only)."""
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    _assert_can_manage(claims, event)

    if image_index < 0 or image_index >= len(event.image_urls):
        raise HTTPException(
            status_code=404,
            detail=f"Image index {image_index} is out of range. Event has {len(event.image_urls)} image(s).",
        )

    url = event.image_urls.pop(image_index)
    _delete_file_if_exists(url)
    event.mark_modified(claims.sub)
    await repo.update(event)


@router.get("/{event_id}/attendees", response_model=EventAttendeeListResponse)
async def list_event_attendees(
    event_id: str,
    claims: CurrentUser,
    event_repo: SQLAlchemyEventRepository = Depends(get_repo),
    rsvp_repo: SQLAlchemyEventRSVPRepository = Depends(get_rsvp_repo),
):
    try:
        result = await ListEventAttendeesUseCase(event_repo, rsvp_repo).execute(
            event_id=event_id,
            requester_user_id=claims.sub,
            requester_is_admin="admin" in claims.roles,
        )
        return _to_attendee_list_http(result)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnauthorizedEventUpdateError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

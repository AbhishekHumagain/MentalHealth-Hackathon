from __future__ import annotations

from app.application.dto.event_dto import CreateEventDTO, EventResponseDTO
from app.application.services.event_validation import validate_event_payload
from app.domain.entities.event import Event
from app.domain.repositories.event_repository import EventRepository


class CreateEventUseCase:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreateEventDTO) -> EventResponseDTO:
        validate_event_payload(
            mode=dto.mode,
            location=dto.location,
            meeting_url=dto.meeting_url,
            start_at=dto.start_at,
            end_at=dto.end_at,
        )
        event = Event(
            title=dto.title,
            description=dto.description,
            hosted_by=dto.hosted_by,
            host_type=dto.host_type,
            organizer_name=dto.organizer_name,
            mode=dto.mode,
            location=dto.location,
            meeting_url=dto.meeting_url,
            start_at=dto.start_at,
            end_at=dto.end_at,
            tags=dto.tags,
            is_active=dto.is_active,
        )
        saved = await self._repo.create(event)
        return _to_dto(saved)


def _to_dto(event: Event) -> EventResponseDTO:
    return EventResponseDTO(
        id=event.id,
        title=event.title,
        description=event.description,
        hosted_by=event.hosted_by,
        host_type=event.host_type,
        organizer_name=event.organizer_name,
        mode=event.mode,
        location=event.location,
        meeting_url=event.meeting_url,
        start_at=event.start_at,
        end_at=event.end_at,
        tags=event.tags,
        is_active=event.is_active,
        created_at=event.created_at,
        modified_at=event.modified_at,
    )

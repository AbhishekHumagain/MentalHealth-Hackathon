from __future__ import annotations

from app.application.dto.event_dto import EventResponseDTO, UpdateEventDTO
from app.application.services.event_validation import validate_event_payload
from app.application.use_cases.create_event import _to_dto
from app.domain.exceptions.event import EventNotFoundError, UnauthorizedEventUpdateError
from app.domain.repositories.event_repository import EventRepository


class UpdateEventUseCase:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, dto: UpdateEventDTO) -> EventResponseDTO:
        event = await self._repo.get_by_id(dto.event_id)
        if event is None:
            raise EventNotFoundError(f"Event {dto.event_id} not found.")

        if not dto.editor_is_admin and event.hosted_by != dto.editor_user_id:
            raise UnauthorizedEventUpdateError("You are not allowed to update this event.")

        if dto.title is not None:
            event.title = dto.title
        if dto.description is not None:
            event.description = dto.description
        if dto.organizer_name is not None:
            event.organizer_name = dto.organizer_name
        if dto.mode is not None:
            event.mode = dto.mode
        if dto.start_at is not None:
            event.start_at = dto.start_at
        if dto.end_at is not None:
            event.end_at = dto.end_at
        if dto.location is not None:
            event.location = dto.location
        if dto.meeting_url is not None:
            event.meeting_url = dto.meeting_url
        if dto.tags is not None:
            event.tags = dto.tags
        if dto.is_active is not None:
            event.is_active = dto.is_active

        validate_event_payload(
            mode=event.mode,
            location=event.location,
            meeting_url=event.meeting_url,
            start_at=event.start_at,
            end_at=event.end_at,
        )
        event.mark_modified(dto.editor_user_id)
        saved = await self._repo.update(event)
        return _to_dto(saved)

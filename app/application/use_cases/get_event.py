from __future__ import annotations

from app.application.dto.event_dto import EventResponseDTO
from app.application.use_cases.create_event import _to_dto
from app.domain.exceptions.event import EventNotFoundError
from app.domain.repositories.event_repository import EventRepository


class GetEventUseCase:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, event_id: str) -> EventResponseDTO:
        event = await self._repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found.")
        return _to_dto(event)

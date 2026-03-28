from __future__ import annotations

from datetime import datetime

from app.application.dto.event_dto import EventResponseDTO
from app.application.use_cases.create_event import _to_dto
from app.domain.repositories.event_repository import EventRepository


class ListEventsUseCase:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        *,
        mode: str | None = None,
        tag: str | None = None,
        host_type: str | None = None,
        start_from: datetime | None = None,
        end_to: datetime | None = None,
        upcoming_only: bool = True,
        skip: int = 0,
        limit: int = 20,
    ) -> list[EventResponseDTO]:
        events = await self._repo.list_all(
            mode=mode,
            tag=tag,
            host_type=host_type,
            start_from=start_from,
            end_to=end_to,
            upcoming_only=upcoming_only,
            skip=skip,
            limit=limit,
        )
        return [_to_dto(event) for event in events]

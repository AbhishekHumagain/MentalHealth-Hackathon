from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    async def create(self, event: Event) -> Event:
        ...

    @abstractmethod
    async def get_by_id(self, event_id: str) -> Event | None:
        ...

    @abstractmethod
    async def list_all(
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
    ) -> list[Event]:
        ...

    @abstractmethod
    async def update(self, event: Event) -> Event:
        ...

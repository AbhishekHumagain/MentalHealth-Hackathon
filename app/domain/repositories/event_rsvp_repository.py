from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.event_rsvp import EventRSVP


class EventRSVPRepository(ABC):
    @abstractmethod
    async def upsert_going(self, *, event_id: str, user_id: str) -> EventRSVP:
        ...

    @abstractmethod
    async def get_by_event_and_user(self, *, event_id: str, user_id: str) -> EventRSVP | None:
        ...

    @abstractmethod
    async def delete_by_event_and_user(self, *, event_id: str, user_id: str) -> bool:
        ...

    @abstractmethod
    async def count_for_event(self, *, event_id: str) -> int:
        ...

    @abstractmethod
    async def count_for_host(self, *, hosted_by: str) -> int:
        ...

    @abstractmethod
    async def count_all(self) -> int:
        ...

    @abstractmethod
    async def list_attendees_for_event(self, *, event_id: str) -> list[EventRSVP]:
        ...

    @abstractmethod
    async def list_upcoming_for_user(self, *, user_id: str) -> list[EventRSVP]:
        ...

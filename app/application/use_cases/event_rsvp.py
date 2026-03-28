from __future__ import annotations

from datetime import datetime, timezone

from app.application.dto.event_rsvp_dto import (
    EventAttendeeDTO,
    EventAttendeeListDTO,
    EventRSVPResponseDTO,
    EventRSVPStatusDTO,
)
from app.application.services.google_calendar import build_google_calendar_url
from app.domain.entities.event import Event
from app.domain.exceptions.event import EventNotFoundError, UnauthorizedEventUpdateError
from app.domain.exceptions.event_rsvp import EventRSVPNotAllowedError
from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.event_rsvp_repository import EventRSVPRepository


def _ensure_rsvp_allowed(event: Event) -> None:
    if not event.is_active:
        raise EventRSVPNotAllowedError("Cannot RSVP to an inactive event.")
    if event.end_at <= datetime.now(timezone.utc):
        raise EventRSVPNotAllowedError("Cannot RSVP to an event that has already ended.")


class RSVPToEventUseCase:
    def __init__(self, event_repo: EventRepository, rsvp_repo: EventRSVPRepository) -> None:
        self._event_repo = event_repo
        self._rsvp_repo = rsvp_repo

    async def execute(self, *, event_id: str, user_id: str) -> EventRSVPResponseDTO:
        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found.")
        _ensure_rsvp_allowed(event)

        rsvp = await self._rsvp_repo.upsert_going(event_id=event_id, user_id=user_id)
        return EventRSVPResponseDTO(
            event_id=event_id,
            user_id=user_id,
            status=rsvp.status,
            google_calendar_url=build_google_calendar_url(event),
            created_at=rsvp.created_at,
            modified_at=rsvp.modified_at,
        )


class CancelEventRSVPUseCase:
    def __init__(self, rsvp_repo: EventRSVPRepository) -> None:
        self._rsvp_repo = rsvp_repo

    async def execute(self, *, event_id: str, user_id: str) -> bool:
        return await self._rsvp_repo.delete_by_event_and_user(event_id=event_id, user_id=user_id)


class GetMyEventRSVPUseCase:
    def __init__(self, event_repo: EventRepository, rsvp_repo: EventRSVPRepository) -> None:
        self._event_repo = event_repo
        self._rsvp_repo = rsvp_repo

    async def execute(self, *, event_id: str, user_id: str) -> EventRSVPStatusDTO | None:
        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found.")
        rsvp = await self._rsvp_repo.get_by_event_and_user(event_id=event_id, user_id=user_id)
        if rsvp is None:
            return None
        return EventRSVPStatusDTO(
            event_id=event_id,
            user_id=user_id,
            status=rsvp.status,
            created_at=rsvp.created_at,
            modified_at=rsvp.modified_at,
        )


class ListEventAttendeesUseCase:
    def __init__(self, event_repo: EventRepository, rsvp_repo: EventRSVPRepository) -> None:
        self._event_repo = event_repo
        self._rsvp_repo = rsvp_repo

    async def execute(
        self,
        *,
        event_id: str,
        requester_user_id: str,
        requester_is_admin: bool,
    ) -> EventAttendeeListDTO:
        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found.")
        if not requester_is_admin and event.hosted_by != requester_user_id:
            raise UnauthorizedEventUpdateError("You are not allowed to view this attendee list.")

        attendees = await self._rsvp_repo.list_attendees_for_event(event_id=event_id)
        return EventAttendeeListDTO(
            event_id=event_id,
            total=len(attendees),
            attendees=[
                EventAttendeeDTO(
                    user_id=item.user_id,
                    status=item.status,
                    created_at=item.created_at,
                    modified_at=item.modified_at,
                )
                for item in attendees
            ],
        )

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.services.google_calendar import build_google_calendar_url
from app.application.use_cases.event_rsvp import (
    CancelEventRSVPUseCase,
    GetMyEventRSVPUseCase,
    ListEventAttendeesUseCase,
    RSVPToEventUseCase,
)
from app.domain.entities.event import Event
from app.domain.entities.event_rsvp import EventRSVP
from app.domain.exceptions.event import UnauthorizedEventUpdateError
from app.domain.exceptions.event_rsvp import EventRSVPNotAllowedError


class InMemoryEventRepository:
    def __init__(self, events: list[Event] | None = None) -> None:
        self.items = {event.id: event for event in (events or [])}

    async def get_by_id(self, event_id: str) -> Event | None:
        return self.items.get(event_id)


class InMemoryEventRSVPRepository:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], EventRSVP] = {}

    async def upsert_going(self, *, event_id: str, user_id: str) -> EventRSVP:
        key = (event_id, user_id)
        existing = self.items.get(key)
        if existing is None:
            existing = EventRSVP(event_id=event_id, user_id=user_id, status="going")
            self.items[key] = existing
        else:
            existing.status = "going"
            existing.mark_modified(user_id)
        return existing

    async def get_by_event_and_user(self, *, event_id: str, user_id: str) -> EventRSVP | None:
        return self.items.get((event_id, user_id))

    async def delete_by_event_and_user(self, *, event_id: str, user_id: str) -> bool:
        return self.items.pop((event_id, user_id), None) is not None

    async def count_for_event(self, *, event_id: str) -> int:
        return sum(1 for item in self.items.values() if item.event_id == event_id)

    async def count_for_host(self, *, hosted_by: str) -> int:
        return 0

    async def count_all(self) -> int:
        return len(self.items)

    async def list_attendees_for_event(self, *, event_id: str) -> list[EventRSVP]:
        return [item for item in self.items.values() if item.event_id == event_id]

    async def list_upcoming_for_user(self, *, user_id: str) -> list[EventRSVP]:
        return [item for item in self.items.values() if item.user_id == user_id]


def _future_event() -> Event:
    start_at = datetime.now(timezone.utc) + timedelta(days=2)
    return Event(
        title="OPT Workshop",
        description="Support session",
        hosted_by="host-1",
        host_type="university",
        organizer_name="Career Center",
        mode="virtual",
        meeting_url="https://example.com/opt",
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        tags=["opt", "career"],
        is_active=True,
    )


async def test_rsvp_creates_and_is_idempotent() -> None:
    event = _future_event()
    event_repo = InMemoryEventRepository([event])
    rsvp_repo = InMemoryEventRSVPRepository()
    use_case = RSVPToEventUseCase(event_repo, rsvp_repo)

    first = await use_case.execute(event_id=event.id, user_id="student-1")
    second = await use_case.execute(event_id=event.id, user_id="student-1")

    assert first.status == "going"
    assert second.status == "going"
    assert len(rsvp_repo.items) == 1
    assert "calendar.google.com" in first.google_calendar_url


async def test_rsvp_cancel_removes_status() -> None:
    event = _future_event()
    event_repo = InMemoryEventRepository([event])
    rsvp_repo = InMemoryEventRSVPRepository()
    await RSVPToEventUseCase(event_repo, rsvp_repo).execute(event_id=event.id, user_id="student-1")

    removed = await CancelEventRSVPUseCase(rsvp_repo).execute(event_id=event.id, user_id="student-1")
    status = await GetMyEventRSVPUseCase(event_repo, rsvp_repo).execute(event_id=event.id, user_id="student-1")

    assert removed is True
    assert status is None


async def test_rsvp_rejects_inactive_or_ended_events() -> None:
    past_start = datetime.now(timezone.utc) - timedelta(days=2)
    ended_event = Event(
        title="Past Event",
        description="Done",
        hosted_by="host-1",
        host_type="university",
        organizer_name="Career Center",
        mode="virtual",
        meeting_url="https://example.com/past",
        start_at=past_start,
        end_at=past_start + timedelta(hours=1),
        tags=["career"],
        is_active=True,
    )
    event_repo = InMemoryEventRepository([ended_event])
    rsvp_repo = InMemoryEventRSVPRepository()

    try:
        await RSVPToEventUseCase(event_repo, rsvp_repo).execute(event_id=ended_event.id, user_id="student-1")
        assert False, "Expected EventRSVPNotAllowedError"
    except EventRSVPNotAllowedError:
        assert True


async def test_attendee_list_requires_host_or_admin() -> None:
    event = _future_event()
    event_repo = InMemoryEventRepository([event])
    rsvp_repo = InMemoryEventRSVPRepository()
    await RSVPToEventUseCase(event_repo, rsvp_repo).execute(event_id=event.id, user_id="student-1")

    try:
        await ListEventAttendeesUseCase(event_repo, rsvp_repo).execute(
            event_id=event.id,
            requester_user_id="other-user",
            requester_is_admin=False,
        )
        assert False, "Expected UnauthorizedEventUpdateError"
    except UnauthorizedEventUpdateError:
        assert True


def test_google_calendar_link_contains_event_data() -> None:
    event = _future_event()
    url = build_google_calendar_url(event)

    assert "calendar.google.com/calendar/render" in url
    assert "OPT+Workshop" in url
    assert "Meeting+URL" in url

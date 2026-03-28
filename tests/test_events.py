from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.dto.event_dto import CreateEventDTO, UpdateEventDTO
from app.application.use_cases.create_event import CreateEventUseCase
from app.application.use_cases.list_events import ListEventsUseCase
from app.application.use_cases.update_event import UpdateEventUseCase
from app.domain.entities.event import Event
from app.domain.exceptions.event import UnauthorizedEventUpdateError


class InMemoryEventRepository:
    def __init__(self) -> None:
        self.items: dict[str, Event] = {}

    async def create(self, event: Event) -> Event:
        self.items[event.id] = event
        return event

    async def get_by_id(self, event_id: str) -> Event | None:
        return self.items.get(event_id)

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
        now = datetime.now(timezone.utc)
        items = list(self.items.values())
        filtered: list[Event] = []
        for event in items:
            if upcoming_only and not event.is_upcoming(now):
                continue
            if mode and event.mode != mode:
                continue
            if tag and tag not in event.tags:
                continue
            if host_type and event.host_type != host_type:
                continue
            if start_from and event.start_at < start_from:
                continue
            if end_to and event.start_at > end_to:
                continue
            filtered.append(event)
        filtered.sort(key=lambda item: item.start_at)
        return filtered[skip : skip + limit]

    async def update(self, event: Event) -> Event:
        self.items[event.id] = event
        return event


async def test_create_event() -> None:
    repo = InMemoryEventRepository()
    start_at = datetime.now(timezone.utc) + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)

    created = await CreateEventUseCase(repo).execute(
        CreateEventDTO(
            title="Resume Review",
            description="Bring your resume for feedback.",
            hosted_by="uni-1",
            host_type="university",
            organizer_name="Career Center",
            mode="virtual",
            meeting_url="https://example.com/meet",
            start_at=start_at,
            end_at=end_at,
            tags=["career", "resume"],
        )
    )

    assert created.title == "Resume Review"
    assert created.host_type == "university"
    assert created.tags == ["career", "resume"]


async def test_list_events_filters_upcoming_by_mode_and_tag() -> None:
    repo = InMemoryEventRepository()
    now = datetime.now(timezone.utc)
    await repo.create(
        Event(
            title="Career Fair",
            description="Meet employers",
            hosted_by="uni-1",
            host_type="university",
            organizer_name="Career Center",
            mode="in_person",
            location="Campus Hall",
            start_at=now + timedelta(days=2),
            end_at=now + timedelta(days=2, hours=3),
            tags=["career", "internships"],
        )
    )
    await repo.create(
        Event(
            title="Past Event",
            description="Already done",
            hosted_by="admin-1",
            host_type="admin",
            organizer_name="Admin",
            mode="virtual",
            meeting_url="https://example.com/past",
            start_at=now - timedelta(days=2),
            end_at=now - timedelta(days=2, hours=-1),
            tags=["wellbeing"],
        )
    )

    results = await ListEventsUseCase(repo).execute(mode="in_person", tag="career")

    assert len(results) == 1
    assert results[0].title == "Career Fair"


async def test_update_event_blocks_non_owner_non_admin() -> None:
    repo = InMemoryEventRepository()
    event = await repo.create(
        Event(
            title="Workshop",
            description="Interview prep",
            hosted_by="uni-1",
            host_type="university",
            organizer_name="Career Office",
            mode="virtual",
            meeting_url="https://example.com/workshop",
            start_at=datetime.now(timezone.utc) + timedelta(days=1),
            end_at=datetime.now(timezone.utc) + timedelta(days=1, hours=2),
            tags=["interview"],
        )
    )

    try:
        await UpdateEventUseCase(repo).execute(
            UpdateEventDTO(
                event_id=event.id,
                editor_user_id="other-user",
                editor_is_admin=False,
                title="New Title",
            )
        )
        assert False, "Expected UnauthorizedEventUpdateError"
    except UnauthorizedEventUpdateError:
        assert True


async def test_create_event_rejects_virtual_without_meeting_url() -> None:
    repo = InMemoryEventRepository()
    start_at = datetime.now(timezone.utc) + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)

    try:
        await CreateEventUseCase(repo).execute(
            CreateEventDTO(
                title="Visa Q&A",
                description="Support session",
                hosted_by="admin-1",
                host_type="admin",
                organizer_name="Support Team",
                mode="virtual",
                start_at=start_at,
                end_at=end_at,
                tags=["visa"],
            )
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "meeting_url" in str(exc)


async def test_update_event_rejects_invalid_time_range() -> None:
    repo = InMemoryEventRepository()
    start_at = datetime.now(timezone.utc) + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)
    event = await repo.create(
        Event(
            title="Housing Info",
            description="Housing support session",
            hosted_by="admin-1",
            host_type="admin",
            organizer_name="Housing Office",
            mode="hybrid",
            location="Student Center",
            meeting_url="https://example.com/housing",
            start_at=start_at,
            end_at=end_at,
            tags=["housing"],
        )
    )

    try:
        await UpdateEventUseCase(repo).execute(
            UpdateEventDTO(
                event_id=event.id,
                editor_user_id="admin-1",
                editor_is_admin=True,
                end_at=start_at - timedelta(minutes=5),
            )
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "end_at" in str(exc)

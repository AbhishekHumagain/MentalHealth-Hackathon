from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.event import Event
from app.domain.repositories.event_repository import EventRepository
from app.infrastructure.database.models.event_model import EventModel


class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, event: Event) -> Event:
        model = EventModel.from_entity(event)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, event_id: str) -> Event | None:
        try:
            parsed = uuid.UUID(event_id)
        except ValueError:
            return None

        result = await self._session.execute(select(EventModel).where(EventModel.id == parsed))
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

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
        query = select(EventModel)

        if upcoming_only:
            query = query.where(
                EventModel.is_active.is_(True),
                EventModel.start_at >= datetime.now(timezone.utc),
            )
        if mode:
            query = query.where(EventModel.mode == mode)
        if tag:
            query = query.where(EventModel.tags.any(tag))
        if host_type:
            query = query.where(EventModel.host_type == host_type)
        if start_from:
            query = query.where(EventModel.start_at >= start_from)
        if end_to:
            query = query.where(EventModel.start_at <= end_to)

        query = query.order_by(EventModel.start_at.asc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, event: Event) -> Event:
        model = await self._session.get(EventModel, uuid.UUID(event.id))
        if model is None:
            raise ValueError(f"Event {event.id} not found.")
        model.apply_entity(event)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

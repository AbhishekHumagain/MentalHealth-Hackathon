from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.event_rsvp import EventRSVP
from app.domain.repositories.event_rsvp_repository import EventRSVPRepository
from app.infrastructure.database.models.event_model import EventModel
from app.infrastructure.database.models.event_rsvp_model import EventRSVPModel


class SQLAlchemyEventRSVPRepository(EventRSVPRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_going(self, *, event_id: str, user_id: str) -> EventRSVP:
        event_uuid = uuid.UUID(event_id)
        result = await self._session.execute(
            select(EventRSVPModel).where(
                EventRSVPModel.event_id == event_uuid,
                EventRSVPModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = EventRSVPModel(
                event_id=event_uuid,
                user_id=user_id,
                status="going",
            )
            self._session.add(model)
        else:
            model.status = "going"

        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_event_and_user(self, *, event_id: str, user_id: str) -> EventRSVP | None:
        result = await self._session.execute(
            select(EventRSVPModel).where(
                EventRSVPModel.event_id == uuid.UUID(event_id),
                EventRSVPModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def delete_by_event_and_user(self, *, event_id: str, user_id: str) -> bool:
        result = await self._session.execute(
            delete(EventRSVPModel)
            .where(
                EventRSVPModel.event_id == uuid.UUID(event_id),
                EventRSVPModel.user_id == user_id,
            )
            .returning(EventRSVPModel.id)
        )
        await self._session.flush()
        return result.scalar_one_or_none() is not None

    async def count_for_event(self, *, event_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(EventRSVPModel).where(
                EventRSVPModel.event_id == uuid.UUID(event_id)
            )
        )
        return result.scalar_one() or 0

    async def count_for_host(self, *, hosted_by: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(EventRSVPModel)
            .join(EventModel, EventModel.id == EventRSVPModel.event_id)
            .where(EventModel.hosted_by == hosted_by)
        )
        return result.scalar_one() or 0

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(EventRSVPModel))
        return result.scalar_one() or 0

    async def list_attendees_for_event(self, *, event_id: str) -> list[EventRSVP]:
        result = await self._session.execute(
            select(EventRSVPModel)
            .where(EventRSVPModel.event_id == uuid.UUID(event_id))
            .order_by(EventRSVPModel.created_at.asc())
        )
        return [model.to_entity() for model in result.scalars().all()]

    async def list_upcoming_for_user(self, *, user_id: str) -> list[EventRSVP]:
        result = await self._session.execute(
            select(EventRSVPModel)
            .join(EventModel, EventModel.id == EventRSVPModel.event_id)
            .where(
                EventRSVPModel.user_id == user_id,
                EventModel.is_active.is_(True),
                EventModel.start_at >= func.now(),
            )
            .order_by(EventModel.start_at.asc())
        )
        return [model.to_entity() for model in result.scalars().all()]

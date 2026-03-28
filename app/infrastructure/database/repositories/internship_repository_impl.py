from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.internship import Internship
from app.domain.repositories.internship_repository import InternshipRepository
from app.infrastructure.database.models.internship_model import InternshipModel


class SQLAlchemyInternshipRepository(InternshipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, internship: Internship) -> Internship:
        model = InternshipModel.from_entity(internship)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def list_available(self, target_date: date) -> list[Internship]:
        threshold = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        result = await self._session.execute(
            select(InternshipModel).where(
                InternshipModel.is_active.is_(True),
                or_(
                    InternshipModel.expires_at.is_(None),
                    InternshipModel.expires_at >= threshold,
                ),
            )
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Internship]:
        result = await self._session.execute(
            select(InternshipModel)
            .order_by(InternshipModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def get_by_id(self, internship_id: str) -> Internship | None:
        try:
            parsed = uuid.UUID(internship_id)
        except ValueError:
            return None

        result = await self._session.execute(
            select(InternshipModel).where(InternshipModel.id == parsed)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

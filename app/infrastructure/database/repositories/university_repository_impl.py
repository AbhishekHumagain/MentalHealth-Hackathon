from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.University import University
from app.domain.repositories.university_repository import UniversityRepository
from app.infrastructure.database.models.university_model import UniversityModel


class SQLAlchemyUniversityRepository(UniversityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Interface implementation ──────────────────────────────────────────────

    async def create(self, university: University) -> University:
        model = UniversityModel.from_entity(university)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, university_id: str) -> University | None:
        model = await self._fetch_model(university_id)
        return model.to_entity() if model else None

    async def get_by_domain(self, domain: str) -> University | None:
        result = await self._session.execute(
            select(UniversityModel).where(UniversityModel.domain == domain)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[University]:
        result = await self._session.execute(
            select(UniversityModel)
            .order_by(UniversityModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, university: University) -> University:
        model = await self._fetch_model(university.id)
        if model is None:
            raise ValueError(f"University '{university.id}' not found.")
        model.apply_entity(university)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def delete(self, university_id: str) -> bool:
        model = await self._fetch_model(university_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    # ── Helper ────────────────────────────────────────────────────────────────

    async def _fetch_model(self, university_id: str) -> UniversityModel | None:
        try:
            uid = uuid.UUID(university_id)
        except ValueError:
            return None

        result = await self._session.execute(
            select(UniversityModel).where(UniversityModel.id == uid)
        )
        return result.scalar_one_or_none()
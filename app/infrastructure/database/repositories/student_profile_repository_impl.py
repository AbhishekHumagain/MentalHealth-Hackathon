from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.student_profile import StudentProfile
from app.domain.repositories.student_profile_repository import StudentProfileRepository
from app.infrastructure.database.models.student_profile_model import StudentProfileModel


class SQLAlchemyStudentProfileRepository(StudentProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, profile: StudentProfile) -> StudentProfile:
        model = StudentProfileModel.from_entity(profile)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_user_id(self, user_id: str) -> StudentProfile | None:
        result = await self._session.execute(
            select(StudentProfileModel).where(StudentProfileModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_id(self, profile_id: str) -> StudentProfile | None:
        model = await self._fetch_model(profile_id)
        return model.to_entity() if model else None

    async def list_active(self) -> list[StudentProfile]:
        result = await self._session.execute(
            select(StudentProfileModel).where(StudentProfileModel.is_active.is_(True))
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, profile: StudentProfile) -> StudentProfile:
        model = await self._fetch_model(profile.id)
        if model is None:
            raise ValueError(f"Student profile '{profile.id}' not found.")
        model.apply_entity(profile)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def _fetch_model(self, profile_id: str) -> StudentProfileModel | None:
        try:
            parsed = uuid.UUID(profile_id)
        except ValueError:
            return None

        result = await self._session.execute(
            select(StudentProfileModel).where(StudentProfileModel.id == parsed)
        )
        return result.scalar_one_or_none()

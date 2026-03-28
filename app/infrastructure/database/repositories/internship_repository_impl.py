from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import and_, func, not_, or_, select, update
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

    async def upsert_by_source(self, internship: Internship) -> tuple[Internship, bool]:
        if not internship.source_name or not internship.external_id:
            saved = await self.create(internship)
            return saved, True

        result = await self._session.execute(
            select(InternshipModel).where(
                InternshipModel.source_name == internship.source_name,
                InternshipModel.external_id == internship.external_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            saved = await self.create(internship)
            return saved, True

        model.apply_entity(internship)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity(), False

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

    async def mark_missing_external_inactive(
        self,
        source_name: str,
        external_ids: set[str],
    ) -> int:
        conditions = [
            InternshipModel.source_name == source_name,
            InternshipModel.source_type == "external_api",
            InternshipModel.is_active.is_(True),
        ]
        if external_ids:
            conditions.append(not_(InternshipModel.external_id.in_(external_ids)))

        result = await self._session.execute(
            update(InternshipModel)
            .where(and_(*conditions))
            .values(
                is_active=False,
                expires_at=datetime.now(timezone.utc),
                modified_at=func.now(),
            )
        )
        await self._session.flush()
        return int(result.rowcount or 0)

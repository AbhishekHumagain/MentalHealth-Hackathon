from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, not_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.apartment import Apartment
from app.domain.exceptions.apartment_exceptions import ApartmentNotFound
from app.domain.repositories.apartment_repository import AbstractApartmentRepository
from app.infrastructure.database.models.apartment_model import ApartmentModel


def _to_entity(m: ApartmentModel) -> Apartment:
    return Apartment(
        id=m.id,
        title=m.title,
        description=m.description,
        address=m.address,
        city=m.city,
        state=m.state,
        zip_code=m.zip_code,
        monthly_rent=m.monthly_rent,
        bedrooms=m.bedrooms,
        bathrooms=m.bathrooms,
        is_furnished=m.is_furnished,
        is_available=m.is_available,
        available_from=m.available_from,
        images_urls=m.images_urls or [],
        amenities=m.amenities or [],
        posted_by=m.posted_by,
        source_type=m.source_type,
        external_id=m.external_id,
        source_name=m.source_name,
        source_url=m.source_url,
        contact_email=m.contact_email,
        contact_phone=m.contact_phone,
        first_seen_at=m.first_seen_at,
        last_seen_at=m.last_seen_at,
        raw_payload=m.raw_payload,
        is_deleted=m.is_deleted,
        created_at=m.created_at,
        modified_at=m.modified_at,
    )


class SQLAlchemyApartmentRepository(AbstractApartmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, apartment: Apartment) -> Apartment:
        model = ApartmentModel(
            id=apartment.id,
            title=apartment.title,
            description=apartment.description,
            address=apartment.address,
            city=apartment.city,
            state=apartment.state,
            zip_code=apartment.zip_code,
            monthly_rent=apartment.monthly_rent,
            bedrooms=apartment.bedrooms,
            bathrooms=apartment.bathrooms,
            is_furnished=apartment.is_furnished,
            is_available=apartment.is_available,
            available_from=apartment.available_from,
            images_urls=apartment.images_urls,
            amenities=apartment.amenities,
            posted_by=apartment.posted_by,
            source_type=apartment.source_type,
            external_id=apartment.external_id,
            source_name=apartment.source_name,
            source_url=apartment.source_url,
            contact_email=apartment.contact_email,
            contact_phone=apartment.contact_phone,
            first_seen_at=apartment.first_seen_at,
            last_seen_at=apartment.last_seen_at,
            raw_payload=apartment.raw_payload,
            created_at=apartment.created_at,
            modified_at=apartment.modified_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def upsert_by_source(self, apartment: Apartment) -> tuple[Apartment, bool]:
        if not apartment.source_name or not apartment.external_id:
            saved = await self.create(apartment)
            return saved, True

        model = await self._get_model_by_source_identity(apartment.source_name, apartment.external_id)
        if model is None:
            saved = await self.create(apartment)
            return saved, True

        if apartment.first_seen_at is None:
            apartment.first_seen_at = model.first_seen_at

        model.title = apartment.title
        model.description = apartment.description
        model.address = apartment.address
        model.city = apartment.city
        model.state = apartment.state
        model.zip_code = apartment.zip_code
        model.monthly_rent = apartment.monthly_rent
        model.bedrooms = apartment.bedrooms
        model.bathrooms = apartment.bathrooms
        model.is_furnished = apartment.is_furnished
        model.is_available = apartment.is_available
        model.available_from = apartment.available_from
        model.images_urls = apartment.images_urls
        model.amenities = apartment.amenities
        model.posted_by = apartment.posted_by
        model.source_type = apartment.source_type
        model.source_name = apartment.source_name
        model.source_url = apartment.source_url
        model.contact_email = apartment.contact_email
        model.contact_phone = apartment.contact_phone
        model.first_seen_at = apartment.first_seen_at
        model.last_seen_at = apartment.last_seen_at
        model.raw_payload = apartment.raw_payload
        model.modified_at = apartment.modified_at

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model), False

    async def get_by_id(self, apartment_id: str) -> Apartment | None:
        result = await self._session.execute(
            select(ApartmentModel).where(
                ApartmentModel.id == apartment_id,
                ApartmentModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_all(
        self,
        city: str | None = None,
        state: str | None = None,
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        query = select(ApartmentModel).where(
            ApartmentModel.is_deleted.is_(False),
            ApartmentModel.is_available.is_(True),
        )
        if city:
            query = query.where(ApartmentModel.city.ilike(f"%{city}%"))
        if state:
            query = query.where(ApartmentModel.state.ilike(f"%{state}%"))
        if max_rent:
            query = query.where(ApartmentModel.monthly_rent <= max_rent)

        query = (
            query.order_by(
                ApartmentModel.monthly_rent.asc(),
                ApartmentModel.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [_to_entity(m) for m in result.scalars().all()]

    async def list_by_locations(
        self,
        locations: list[str],
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        conditions = [
            or_(
                ApartmentModel.city.ilike(f"%{loc}%"),
                ApartmentModel.state.ilike(f"%{loc}%"),
                ApartmentModel.zip_code.ilike(f"%{loc}%"),
            )
            for loc in locations
        ]
        query = select(ApartmentModel).where(
            ApartmentModel.is_deleted.is_(False),
            ApartmentModel.is_available.is_(True),
            or_(*conditions),
        )
        if max_rent:
            query = query.where(ApartmentModel.monthly_rent <= max_rent)

        query = (
            query.order_by(
                ApartmentModel.monthly_rent.asc(),
                ApartmentModel.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [_to_entity(m) for m in result.scalars().all()]

    async def delete(self, apartment_id: str, user_id: str) -> Apartment:
        result = await self._session.execute(
            select(ApartmentModel).where(ApartmentModel.id == apartment_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ApartmentNotFound(f"Apartment {apartment_id} not found.")
        model.is_deleted = True
        await self._session.flush()
        return _to_entity(model)

    async def get_by_source_identity(
        self,
        source_name: str,
        external_id: str,
    ) -> Apartment | None:
        model = await self._get_model_by_source_identity(source_name, external_id)
        return _to_entity(model) if model else None

    async def mark_missing_external_inactive(
        self,
        source_name: str,
        external_ids: set[str],
    ) -> int:
        conditions = [
            ApartmentModel.source_name == source_name,
            ApartmentModel.source_type != "manual",
            ApartmentModel.is_available.is_(True),
            ApartmentModel.is_deleted.is_(False),
        ]
        if external_ids:
            conditions.append(not_(ApartmentModel.external_id.in_(external_ids)))

        result = await self._session.execute(
            update(ApartmentModel)
            .where(and_(*conditions))
            .values(
                is_available=False,
                modified_at=func.now(),
            )
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def _get_model_by_source_identity(
        self,
        source_name: str,
        external_id: str,
    ) -> ApartmentModel | None:
        result = await self._session.execute(
            select(ApartmentModel).where(
                ApartmentModel.source_name == source_name,
                ApartmentModel.external_id == external_id,
                ApartmentModel.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

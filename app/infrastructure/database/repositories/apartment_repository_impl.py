from __future__ import annotations

from sqlalchemy import select
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
        contact_email=m.contact_email,
        contact_phone=m.contact_phone,
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
            contact_email=apartment.contact_email,
            contact_phone=apartment.contact_phone,
            created_at=apartment.created_at,
            modified_at=apartment.modified_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

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

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return [_to_entity(m) for m in result.scalars().all()]

    async def list_by_locations(
        self,
        locations: list[str],
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        from sqlalchemy import or_
        conditions = [
            or_(
                ApartmentModel.city.ilike(f"%{loc}%"),
                ApartmentModel.state.ilike(f"%{loc}%"),
            )
            for loc in locations
        ]
        from sqlalchemy import or_ as sql_or
        query = (
            select(ApartmentModel)
            .where(
                ApartmentModel.is_deleted.is_(False),
                ApartmentModel.is_available.is_(True),
                sql_or(*conditions),
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
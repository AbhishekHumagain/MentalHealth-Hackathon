from __future__ import annotations

from app.application.dto.apartment_dto import ApartmentResponseDTO
from app.application.use_cases.create_apartment import _to_dto
from app.domain.repositories.apartment_repository import AbstractApartmentRepository


class ListApartmentsUseCase:
    def __init__(self, repo: AbstractApartmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        city: str | None = None,
        state: str | None = None,
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ApartmentResponseDTO]:
        apartments = await self._repo.list_all(
            city=city,
            state=state,
            max_rent=max_rent,
            skip=skip,
            limit=limit,
        )
        return [_to_dto(a) for a in apartments]


class ListApartmentsByLocationUseCase:
    def __init__(self, repo: AbstractApartmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        locations: list[str],
        skip: int = 0,
        limit: int = 20,
    ) -> list[ApartmentResponseDTO]:
        apartments = await self._repo.list_by_locations(
            locations=locations,
            skip=skip,
            limit=limit,
        )
        return [_to_dto(a) for a in apartments]
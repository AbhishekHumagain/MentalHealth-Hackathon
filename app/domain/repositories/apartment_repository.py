from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.apartment import Apartment


class AbstractApartmentRepository(ABC):

    @abstractmethod
    async def create(self, apartment: Apartment) -> Apartment:
        ...

    @abstractmethod
    async def get_by_id(self, apartment_id: str) -> Apartment | None:
        ...

    @abstractmethod
    async def list_all(
        self,
        city: str | None = None,
        state: str | None = None,
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        ...

    @abstractmethod
    async def list_by_locations(
        self,
        locations: list[str],
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        ...

    @abstractmethod
    async def delete(self, apartment_id: str, user_id: str) -> Apartment:
        ...
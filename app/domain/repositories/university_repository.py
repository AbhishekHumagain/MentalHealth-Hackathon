from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.University import University


class UniversityRepository(ABC):
    """Port (interface) for university persistence."""

    @abstractmethod
    async def create(self, university: University) -> University:
        """Persist a new university and return the saved entity."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, university_id: str) -> University | None:
        """Return the entity with the given ID, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_domain(self, domain: str) -> University | None:
        """Return a university by domain (used for uniqueness checks)."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[University]:
        #Return a paginated list of universities
        raise NotImplementedError

    @abstractmethod
    async def update(self, university: University) -> University:
        #Persist changes and return updated entity
        raise NotImplementedError

    @abstractmethod
    async def delete(self, university_id: str) -> bool:
        #Delete university. Returns True if deleted, False if not found
        raise NotImplementedError
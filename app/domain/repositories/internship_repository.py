from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.internship import Internship


class InternshipRepository(ABC):
    @abstractmethod
    async def create(self, internship: Internship) -> Internship:
        raise NotImplementedError

    @abstractmethod
    async def upsert_by_source(self, internship: Internship) -> tuple[Internship, bool]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_source_identity(
        self,
        source_name: str,
        external_id: str,
    ) -> Internship | None:
        raise NotImplementedError

    @abstractmethod
    async def list_available(self, target_date: date) -> list[Internship]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Internship]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, internship_id: str) -> Internship | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_missing_external_inactive(
        self,
        source_name: str,
        external_ids: set[str],
    ) -> int:
        raise NotImplementedError

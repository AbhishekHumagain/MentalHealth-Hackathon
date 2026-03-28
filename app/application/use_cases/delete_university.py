from __future__ import annotations

from app.domain.exceptions.university import UniversityNotFoundError
from app.domain.repositories.university_repository import UniversityRepository


class DeleteUniversityUseCase:
    def __init__(self, repository: UniversityRepository) -> None:
        self._repo = repository

    async def execute(self, university_id: str) -> None:
        deleted = await self._repo.delete(university_id)
        if not deleted:
            raise UniversityNotFoundError(university_id)
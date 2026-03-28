from __future__ import annotations

from app.application.dto.internship_dto import InternshipResponseDTO
from app.domain.repositories.internship_repository import InternshipRepository

from app.application.use_cases.create_internship import _to_dto


class ListInternshipsUseCase:
    def __init__(self, repository: InternshipRepository) -> None:
        self._repository = repository

    async def execute(self, skip: int, limit: int) -> list[InternshipResponseDTO]:
        internships = await self._repository.list_all(skip=skip, limit=limit)
        return [_to_dto(item) for item in internships]

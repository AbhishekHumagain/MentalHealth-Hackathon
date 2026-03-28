from __future__ import annotations

from app.application.dto.university_dto import UniversityResponseDTO
from app.domain.repositories.university_repository import UniversityRepository


class ListUniversitiesUseCase:
    def __init__(self, repository: UniversityRepository) -> None:
        self._repo = repository

    async def execute(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[UniversityResponseDTO]:
        entities = await self._repo.list_all(skip=skip, limit=limit)
        return [_to_response_dto(e) for e in entities]


def _to_response_dto(entity) -> UniversityResponseDTO:
    return UniversityResponseDTO(
        id=entity.id,
        name=entity.name,
        domain=entity.domain,
        country=entity.country,
        is_active=entity.is_active,
        created_at=entity.created_at,
        modified_at=entity.modified_at,
    )
from __future__ import annotations

from app.application.dto.university_dto import UniversityResponseDTO
from app.domain.exceptions.university import UniversityNotFoundError
from app.domain.repositories.university_repository import UniversityRepository


class GetUniversityUseCase:
    def __init__(self, repository: UniversityRepository) -> None:
        self._repo = repository

    async def execute(self, university_id: str) -> UniversityResponseDTO:
        entity = await self._repo.get_by_id(university_id)
        if not entity:
            raise UniversityNotFoundError(university_id)

        return _to_response_dto(entity)


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
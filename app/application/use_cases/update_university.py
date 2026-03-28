from __future__ import annotations

from app.application.dto.university_dto import UpdateUniversityDTO, UniversityResponseDTO
from app.domain.exceptions.university import UniversityNotFoundError
from app.domain.repositories.university_repository import UniversityRepository


class UpdateUniversityUseCase:
    def __init__(self, repository: UniversityRepository) -> None:
        self._repo = repository

    async def execute(self, dto: UpdateUniversityDTO) -> UniversityResponseDTO:
        entity = await self._repo.get_by_id(dto.university_id)
        if not entity:
            raise UniversityNotFoundError(dto.university_id)

        if dto.name is not None:
            entity.name = dto.name
        if dto.domain is not None:
            entity.domain = dto.domain
        if dto.country is not None:
            entity.country = dto.country
        if dto.is_active is not None:
            entity.is_active = dto.is_active

        entity.mark_modified(dto.requesting_user_id)

        updated = await self._repo.update(entity)
        return _to_response_dto(updated)


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
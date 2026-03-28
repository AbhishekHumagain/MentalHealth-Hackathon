from __future__ import annotations

from app.application.dto.university_dto import CreateUniversityDTO, UniversityResponseDTO
from app.domain.entities.University import University
from app.domain.exceptions.university import UniversityAlreadyExistsError
from app.domain.repositories.university_repository import UniversityRepository


class CreateUniversityUseCase:
    def __init__(self, repository: UniversityRepository) -> None:
        self._repo = repository

    async def execute(self, dto: CreateUniversityDTO) -> UniversityResponseDTO:
        existing = await self._repo.get_by_domain(dto.domain)
        if existing:
            raise UniversityAlreadyExistsError(dto.domain)

        entity = University(
            name=dto.name,
            domain=dto.domain,
            country=dto.country,
            keycloak_user_id=dto.keycloak_user_id,
            created_by=dto.requesting_user_id,
        )

        saved = await self._repo.create(entity)
        return _to_response_dto(saved)


def _to_response_dto(entity: University) -> UniversityResponseDTO:
    return UniversityResponseDTO(
        id=entity.id,
        name=entity.name,
        domain=entity.domain,
        country=entity.country,
        is_active=entity.is_active,
        keycloak_user_id=entity.keycloak_user_id,
        created_at=entity.created_at,
        modified_at=entity.modified_at,
    )
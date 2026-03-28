from __future__ import annotations

from app.application.dto.internship_dto import CreateInternshipDTO, InternshipResponseDTO
from app.domain.entities.internship import Internship
from app.domain.repositories.internship_repository import InternshipRepository


class CreateInternshipUseCase:
    def __init__(self, repository: InternshipRepository) -> None:
        self._repository = repository

    async def execute(self, dto: CreateInternshipDTO) -> InternshipResponseDTO:
        saved = await self._repository.create(
            Internship(
                title=dto.title,
                company=dto.company,
                description=dto.description,
                location=dto.location,
            application_url=dto.application_url,
            posted_by=dto.posted_by,
            source_type=dto.source_type,
            external_id=dto.external_id,
            source_name=dto.source_name,
            source_url=dto.source_url,
            majors=dto.majors,
            keywords=dto.keywords,
            is_active=dto.is_active,
            expires_at=dto.expires_at,
            last_seen_at=dto.last_seen_at,
        )
        )
        return _to_dto(saved)


def _to_dto(internship: Internship) -> InternshipResponseDTO:
    return InternshipResponseDTO(
        id=internship.id,
        title=internship.title,
        company=internship.company,
        description=internship.description,
        location=internship.location,
        application_url=internship.application_url,
        posted_by=internship.posted_by,
        source_type=internship.source_type,
        external_id=internship.external_id,
        source_name=internship.source_name,
        source_url=internship.source_url,
        majors=internship.majors,
        keywords=internship.keywords,
        is_active=internship.is_active,
        expires_at=internship.expires_at,
        last_seen_at=internship.last_seen_at,
        created_at=internship.created_at,
        modified_at=internship.modified_at,
    )

from __future__ import annotations

from app.application.dto.student_profile_dto import (
    CreateStudentProfileDTO,
    StudentProfileResponseDTO,
)
from app.domain.entities.student_profile import StudentProfile
from app.domain.exceptions.student_profile import StudentProfileAlreadyExistsError
from app.domain.repositories.student_profile_repository import StudentProfileRepository


class CreateStudentProfileUseCase:
    def __init__(self, repository: StudentProfileRepository) -> None:
        self._repository = repository

    async def execute(self, dto: CreateStudentProfileDTO) -> StudentProfileResponseDTO:
        existing = await self._repository.get_by_user_id(dto.user_id)
        if existing:
            raise StudentProfileAlreadyExistsError(dto.user_id)

        saved = await self._repository.create(
            StudentProfile(
                user_id=dto.user_id,
                university_id=dto.university_id,
                major=dto.major,
                skills=dto.skills,
                interests=dto.interests,
                graduation_year=dto.graduation_year,
                preferred_locations=dto.preferred_locations,
            )
        )
        return _to_dto(saved)


def _to_dto(profile: StudentProfile) -> StudentProfileResponseDTO:
    return StudentProfileResponseDTO(
        id=profile.id,
        user_id=profile.user_id,
        university_id=profile.university_id,
        major=profile.major,
        skills=profile.skills,
        interests=profile.interests,
        graduation_year=profile.graduation_year,
        preferred_locations=profile.preferred_locations,
        is_active=profile.is_active,
        created_at=profile.created_at,
        modified_at=profile.modified_at,
    )

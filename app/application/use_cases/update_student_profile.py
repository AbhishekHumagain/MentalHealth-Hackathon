from __future__ import annotations

from app.application.dto.student_profile_dto import (
    StudentProfileResponseDTO,
    UpdateStudentProfileDTO,
)
from app.domain.exceptions.student_profile import StudentProfileNotFoundError
from app.domain.repositories.student_profile_repository import StudentProfileRepository

from app.application.use_cases.create_student_profile import _to_dto


class UpdateStudentProfileUseCase:
    def __init__(self, repository: StudentProfileRepository) -> None:
        self._repository = repository

    async def execute(self, dto: UpdateStudentProfileDTO) -> StudentProfileResponseDTO:
        profile = await self._repository.get_by_user_id(dto.user_id)
        if profile is None:
            raise StudentProfileNotFoundError(dto.user_id)

        if dto.university_id is not None:
            profile.university_id = dto.university_id
        if dto.major is not None:
            profile.major = dto.major
        if dto.skills is not None:
            profile.skills = dto.skills
        if dto.interests is not None:
            profile.interests = dto.interests
        if dto.graduation_year is not None:
            profile.graduation_year = dto.graduation_year
        if dto.preferred_locations is not None:
            profile.preferred_locations = dto.preferred_locations
        if dto.is_active is not None:
            profile.is_active = dto.is_active

        profile.mark_modified(dto.user_id)
        saved = await self._repository.update(profile)
        return _to_dto(saved)

from __future__ import annotations

from app.application.dto.student_profile_dto import StudentProfileResponseDTO
from app.domain.exceptions.student_profile import StudentProfileNotFoundError
from app.domain.repositories.student_profile_repository import StudentProfileRepository

from app.application.use_cases.create_student_profile import _to_dto


class GetStudentProfileUseCase:
    def __init__(self, repository: StudentProfileRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: str) -> StudentProfileResponseDTO:
        profile = await self._repository.get_by_user_id(user_id)
        if profile is None:
            raise StudentProfileNotFoundError(user_id)
        return _to_dto(profile)

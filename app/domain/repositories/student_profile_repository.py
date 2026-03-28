from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.student_profile import StudentProfile


class StudentProfileRepository(ABC):
    @abstractmethod
    async def create(self, profile: StudentProfile) -> StudentProfile:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> StudentProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, profile_id: str) -> StudentProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self) -> list[StudentProfile]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, profile: StudentProfile) -> StudentProfile:
        raise NotImplementedError

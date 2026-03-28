from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.student_profile import StudentProfile
from app.infrastructure.database.base import Base


class StudentProfileModel(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    university_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    major: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    interests: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_locations: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def to_entity(self) -> StudentProfile:
        return StudentProfile(
            id=str(self.id),
            user_id=self.user_id,
            university_id=str(self.university_id),
            major=self.major,
            skills=list(self.skills),
            interests=list(self.interests),
            graduation_year=self.graduation_year,
            preferred_locations=list(self.preferred_locations),
            is_active=self.is_active,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

    @classmethod
    def from_entity(cls, entity: StudentProfile) -> "StudentProfileModel":
        return cls(
            id=uuid.UUID(entity.id),
            user_id=entity.user_id,
            university_id=uuid.UUID(entity.university_id),
            major=entity.major,
            skills=entity.skills,
            interests=entity.interests,
            graduation_year=entity.graduation_year,
            preferred_locations=entity.preferred_locations,
            is_active=entity.is_active,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
        )

    def apply_entity(self, entity: StudentProfile) -> None:
        self.university_id = uuid.UUID(entity.university_id)
        self.major = entity.major
        self.skills = entity.skills
        self.interests = entity.interests
        self.graduation_year = entity.graduation_year
        self.preferred_locations = entity.preferred_locations
        self.is_active = entity.is_active
        self.modified_at = entity.modified_at

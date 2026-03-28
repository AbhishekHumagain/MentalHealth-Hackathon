from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.internship_recommendation import InternshipRecommendation
from app.infrastructure.database.base import Base


class InternshipRecommendationModel(Base):
    __tablename__ = "internship_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "internship_id",
            "recommended_for_date",
            name="uq_profile_internship_day",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    internship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("internships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_for_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def to_entity(self) -> InternshipRecommendation:
        return InternshipRecommendation(
            id=str(self.id),
            student_profile_id=str(self.student_profile_id),
            internship_id=str(self.internship_id),
            score=self.score,
            reason=self.reason,
            recommended_for_date=self.recommended_for_date,
            created_at=self.created_at,
            modified_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: InternshipRecommendation) -> "InternshipRecommendationModel":
        return cls(
            id=uuid.UUID(entity.id),
            student_profile_id=uuid.UUID(entity.student_profile_id),
            internship_id=uuid.UUID(entity.internship_id),
            score=entity.score,
            reason=entity.reason,
            recommended_for_date=entity.recommended_for_date,
            created_at=entity.created_at,
        )

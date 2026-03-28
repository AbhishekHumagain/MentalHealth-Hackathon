from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.application.dto.internship_dto import CreateInternshipDTO
from app.application.dto.student_profile_dto import CreateStudentProfileDTO, UpdateStudentProfileDTO
from app.application.services.internship_matching import InternshipMatchingService
from app.application.use_cases.create_internship import CreateInternshipUseCase
from app.application.use_cases.create_student_profile import CreateStudentProfileUseCase
from app.application.use_cases.generate_daily_recommendations import (
    GenerateDailyRecommendationsUseCase,
)
from app.application.use_cases.list_my_recommendations import ListMyRecommendationsUseCase
from app.application.use_cases.update_student_profile import UpdateStudentProfileUseCase
from app.domain.entities.internship import Internship
from app.domain.entities.internship_recommendation import InternshipRecommendation
from app.domain.entities.student_profile import StudentProfile


class InMemoryStudentProfileRepository:
    def __init__(self) -> None:
        self.items: dict[str, StudentProfile] = {}

    async def create(self, profile: StudentProfile) -> StudentProfile:
        self.items[profile.user_id] = profile
        return profile

    async def get_by_user_id(self, user_id: str) -> StudentProfile | None:
        return self.items.get(user_id)

    async def get_by_id(self, profile_id: str) -> StudentProfile | None:
        return next((item for item in self.items.values() if item.id == profile_id), None)

    async def list_active(self) -> list[StudentProfile]:
        return [item for item in self.items.values() if item.is_active]

    async def update(self, profile: StudentProfile) -> StudentProfile:
        self.items[profile.user_id] = profile
        return profile


class InMemoryInternshipRepository:
    def __init__(self) -> None:
        self.items: dict[str, Internship] = {}

    async def create(self, internship: Internship) -> Internship:
        self.items[internship.id] = internship
        return internship

    async def list_available(self, target_date: date) -> list[Internship]:
        return [item for item in self.items.values() if item.is_available_on(target_date)]

    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Internship]:
        items = list(self.items.values())
        return items[skip : skip + limit]

    async def get_by_id(self, internship_id: str) -> Internship | None:
        return self.items.get(internship_id)


class InMemoryRecommendationRepository:
    def __init__(self) -> None:
        self.items: list[InternshipRecommendation] = []

    async def replace_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
        recommendations: list[InternshipRecommendation],
    ) -> None:
        self.items = [
            item
            for item in self.items
            if not (item.student_profile_id == profile_id and item.recommended_for_date == target_date)
        ]
        self.items.extend(recommendations)

    async def list_for_profile_on_date(
        self,
        profile_id: str,
        target_date: date,
    ) -> list[InternshipRecommendation]:
        filtered = [
            item
            for item in self.items
            if item.student_profile_id == profile_id and item.recommended_for_date == target_date
        ]
        return sorted(filtered, key=lambda item: item.score, reverse=True)


@pytest.mark.asyncio
async def test_create_and_update_student_profile() -> None:
    profiles = InMemoryStudentProfileRepository()

    created = await CreateStudentProfileUseCase(profiles).execute(
        CreateStudentProfileDTO(
            user_id="student-1",
            university_id="11111111-1111-1111-1111-111111111111",
            major="Computer Science",
            skills=["python"],
            interests=["ai"],
            graduation_year=2027,
            preferred_locations=["Kathmandu"],
        )
    )
    assert created.major == "Computer Science"
    assert created.skills == ["python"]

    updated = await UpdateStudentProfileUseCase(profiles).execute(
        UpdateStudentProfileDTO(
            user_id="student-1",
            major="Software Engineering",
            preferred_locations=["Remote"],
            is_active=True,
        )
    )
    assert updated.major == "Software Engineering"
    assert updated.preferred_locations == ["Remote"]


@pytest.mark.asyncio
async def test_create_internship_and_list_recommendations_for_matching_major() -> None:
    profiles = InMemoryStudentProfileRepository()
    internships = InMemoryInternshipRepository()
    recommendations = InMemoryRecommendationRepository()

    await CreateStudentProfileUseCase(profiles).execute(
        CreateStudentProfileDTO(
            user_id="student-1",
            university_id="11111111-1111-1111-1111-111111111111",
            major="Computer Science",
            skills=["python", "backend"],
            interests=["ai"],
            preferred_locations=["Remote"],
        )
    )

    internship = await CreateInternshipUseCase(internships).execute(
        CreateInternshipDTO(
            title="Backend Intern",
            company="Acme",
            description="Python backend internship for computer science students interested in AI",
            location="Remote",
            application_url="https://example.com/jobs/1",
            posted_by="assoc-admin",
            majors=["Computer Science"],
            keywords=["python", "backend", "ai"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=10),
        )
    )
    assert internship.title == "Backend Intern"

    generated_count = await GenerateDailyRecommendationsUseCase(
        profiles=profiles,
        internships=internships,
        recommendations=recommendations,
        matching_service=InternshipMatchingService(),
    ).execute(date(2026, 3, 28))

    assert generated_count == 1

    results = await ListMyRecommendationsUseCase(
        profiles=profiles,
        recommendations=recommendations,
        internships=internships,
    ).execute("student-1", date(2026, 3, 28))

    assert len(results) == 1
    assert results[0].internship_title == "Backend Intern"
    assert results[0].reason == "Matched your major: Computer Science"
    assert results[0].score >= 10


@pytest.mark.asyncio
async def test_expired_internships_are_excluded_and_daily_runs_replace_results() -> None:
    profiles = InMemoryStudentProfileRepository()
    internships = InMemoryInternshipRepository()
    recommendations = InMemoryRecommendationRepository()
    target_date = date(2026, 3, 28)

    created_profile = await CreateStudentProfileUseCase(profiles).execute(
        CreateStudentProfileDTO(
            user_id="student-1",
            university_id="11111111-1111-1111-1111-111111111111",
            major="Business",
        )
    )

    active_internship = Internship(
        title="Operations Intern",
        company="Bright Co",
        description="Business operations internship",
        location="Kathmandu",
        application_url="https://example.com/jobs/2",
        posted_by="admin",
        majors=["Business Administration"],
        keywords=["operations"],
        expires_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
    )
    expired_internship = Internship(
        title="Old Intern",
        company="Old Co",
        description="Expired role",
        location="Remote",
        application_url="https://example.com/jobs/3",
        posted_by="admin",
        majors=["Business"],
        keywords=["finance"],
        expires_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
    )
    await internships.create(active_internship)
    await internships.create(expired_internship)

    use_case = GenerateDailyRecommendationsUseCase(profiles, internships, recommendations)
    first_count = await use_case.execute(target_date)
    second_count = await use_case.execute(target_date)

    stored = await recommendations.list_for_profile_on_date(created_profile.id, target_date)

    assert first_count == 1
    assert second_count == 1
    assert len(stored) == 1
    assert stored[0].internship_id == active_internship.id

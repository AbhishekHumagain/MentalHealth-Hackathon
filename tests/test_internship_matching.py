from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.application.dto.internship_dto import CreateInternshipDTO
from app.application.services.external_internship_provider import (
    ExternalInternshipRecord,
    _is_relevant_match,
)
from app.application.services.major_taxonomy import MajorTaxonomyService
from app.application.dto.student_profile_dto import CreateStudentProfileDTO, UpdateStudentProfileDTO
from app.application.services.internship_matching import InternshipMatchingService
from app.application.use_cases.create_internship import CreateInternshipUseCase
from app.application.use_cases.create_student_profile import CreateStudentProfileUseCase
from app.application.use_cases.generate_daily_recommendations import (
    GenerateDailyRecommendationsUseCase,
)
from app.application.use_cases.list_my_recommendations import ListMyRecommendationsUseCase
from app.application.use_cases.sync_external_internships import SyncExternalInternshipsUseCase
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

    async def upsert_by_source(self, internship: Internship) -> tuple[Internship, bool]:
        if internship.source_name and internship.external_id:
            for existing in self.items.values():
                if (
                    existing.source_name == internship.source_name
                    and existing.external_id == internship.external_id
                ):
                    if internship.first_seen_at is None:
                        internship.first_seen_at = existing.first_seen_at
                    internship.id = existing.id
                    self.items[existing.id] = internship
                    return internship, False
        self.items[internship.id] = internship
        return internship, True

    async def get_by_source_identity(
        self,
        source_name: str,
        external_id: str,
    ) -> Internship | None:
        for internship in self.items.values():
            if internship.source_name == source_name and internship.external_id == external_id:
                return internship
        return None

    async def list_available(self, target_date: date) -> list[Internship]:
        return [item for item in self.items.values() if item.is_available_on(target_date)]

    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Internship]:
        items = list(self.items.values())
        return items[skip : skip + limit]

    async def get_by_id(self, internship_id: str) -> Internship | None:
        return self.items.get(internship_id)

    async def mark_missing_external_inactive(
        self,
        source_name: str,
        external_ids: set[str],
    ) -> int:
        count = 0
        for internship in self.items.values():
            if (
                internship.source_type == "external_api"
                and internship.source_name == source_name
                and internship.is_active
                and internship.external_id not in external_ids
            ):
                internship.is_active = False
                internship.expires_at = datetime.now(timezone.utc)
                count += 1
        return count


class FakeExternalInternshipProvider:
    def __init__(self, records: list[ExternalInternshipRecord]) -> None:
        self._records = records

    async def fetch_internships(self, search_terms: list[str]) -> list[ExternalInternshipRecord]:
        return self._records


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


def test_major_taxonomy_returns_expected_search_terms() -> None:
    service = MajorTaxonomyService()

    terms = service.search_terms_for_major("Computer Science")

    assert "software engineer" in terms
    assert "backend developer" in terms


def test_major_taxonomy_supports_common_demo_majors() -> None:
    service = MajorTaxonomyService()

    design_terms = service.search_terms_for_major("Design")
    accounting_terms = service.search_terms_for_major("Accounting")
    health_terms = service.search_terms_for_major("Health")

    assert "ui ux" in design_terms
    assert "accounting" in accounting_terms
    assert "public health" in health_terms
    assert service.search_terms_for_major("Anthropology") == ["Anthropology intern"]


def test_remotive_filtering_accepts_practical_internship_signals() -> None:
    assert _is_relevant_match(
        title="Software Engineer",
        category="Software Development",
        job_type="Internship",
    )
    assert _is_relevant_match(
        title="Backend Intern",
        category="Software Development",
        job_type="Full-Time",
    )
    assert not _is_relevant_match(
        title="Senior Backend Engineer",
        category="Software Development",
        job_type="Full-Time",
    )


def test_remotive_filtering_allows_entry_level_roles_for_broad_searches() -> None:
    assert _is_relevant_match(
        title="Junior Data Analyst",
        category="Data",
        job_type="Full-Time",
        search_term="data analyst",
    )
    assert not _is_relevant_match(
        title="Senior Data Analyst",
        category="Data",
        job_type="Full-Time",
        search_term="data analyst",
    )


def test_remotive_filtering_allows_family_category_match_for_demo_mode() -> None:
    assert _is_relevant_match(
        title="Software Engineer",
        category="Software Development",
        job_type="Full-Time",
        search_term="software engineer",
        inferred_majors=["Computer Science"],
    )
    assert _is_relevant_match(
        title="Marketing Specialist",
        category="Marketing",
        job_type="Full-Time",
        search_term="marketing",
        inferred_majors=["Marketing"],
    )


@pytest.mark.asyncio
async def test_external_sync_upserts_and_generates_recommendations() -> None:
    profiles = InMemoryStudentProfileRepository()
    internships = InMemoryInternshipRepository()
    recommendations = InMemoryRecommendationRepository()
    target_date = date(2026, 3, 28)

    await CreateStudentProfileUseCase(profiles).execute(
        CreateStudentProfileDTO(
            user_id="student-1",
            university_id="11111111-1111-1111-1111-111111111111",
            major="Computer Science",
            skills=["python"],
        )
    )

    provider = FakeExternalInternshipProvider(
        [
            ExternalInternshipRecord(
                external_id="job-1",
                title="Software Engineer Intern",
                company="Remote Co",
                description="Python backend internship",
                location="Remote",
                application_url="https://example.com/jobs/100",
                source_url="https://example.com/jobs/100",
                source_name="remotive",
                majors=["Computer Science"],
                keywords=["python", "backend"],
                last_seen_at=datetime.now(timezone.utc),
                raw_payload={"id": "job-1", "title": "Software Engineer Intern"},
            ),
            ExternalInternshipRecord(
                external_id="job-1",
                title="Software Engineer Intern Updated",
                company="Remote Co",
                description="Python backend internship updated",
                location="Remote",
                application_url="https://example.com/jobs/100",
                source_url="https://example.com/jobs/100",
                source_name="remotive",
                majors=["Computer Science"],
                keywords=["python", "backend"],
                last_seen_at=datetime.now(timezone.utc),
                raw_payload={"id": "job-1", "title": "Software Engineer Intern Updated"},
            ),
        ]
    )

    result = await SyncExternalInternshipsUseCase(
        internships=internships,
        profiles=profiles,
        recommendations=recommendations,
        provider=provider,
    ).execute(target_date)

    assert result.fetched == 2
    assert result.created == 1
    assert result.updated == 1

    all_internships = await internships.list_all()
    assert len(all_internships) == 1
    assert all_internships[0].title == "Software Engineer Intern Updated"
    assert all_internships[0].first_seen_at is not None
    assert all_internships[0].raw_payload is not None

    matches = await ListMyRecommendationsUseCase(
        profiles=profiles,
        recommendations=recommendations,
        internships=internships,
    ).execute("student-1", target_date)
    assert len(matches) == 1
    assert matches[0].internship_title == "Software Engineer Intern Updated"


@pytest.mark.asyncio
async def test_sync_preserves_first_seen_at_and_uses_provider_source_name() -> None:
    profiles = InMemoryStudentProfileRepository()
    internships = InMemoryInternshipRepository()
    recommendations = InMemoryRecommendationRepository()
    target_date = date(2026, 3, 28)
    original_first_seen = datetime(2026, 3, 20, tzinfo=timezone.utc)

    await internships.create(
        Internship(
            title="Existing Intern",
            company="Remote Co",
            description="Existing description",
            location="Remote",
            application_url="https://example.com/jobs/999",
            posted_by="system",
            source_type="external_api",
            external_id="job-1",
            source_name="remotive",
            source_url="https://example.com/jobs/999",
            majors=["Computer Science"],
            keywords=["python"],
            first_seen_at=original_first_seen,
            last_seen_at=original_first_seen,
            raw_payload={"id": "job-1"},
        )
    )

    provider = FakeExternalInternshipProvider(
        [
            ExternalInternshipRecord(
                external_id="job-1",
                title="Existing Intern Updated",
                company="Remote Co",
                description="Updated description",
                location="Remote",
                application_url="https://example.com/jobs/999",
                source_url="https://example.com/jobs/999",
                source_name="remotive",
                majors=["Computer Science"],
                keywords=["python", "backend"],
                last_seen_at=datetime.now(timezone.utc),
                raw_payload={"id": "job-1", "updated": True},
            )
        ]
    )

    await SyncExternalInternshipsUseCase(
        internships=internships,
        profiles=profiles,
        recommendations=recommendations,
        provider=provider,
    ).execute(target_date)

    saved = await internships.get_by_source_identity("remotive", "job-1")
    assert saved is not None
    assert saved.first_seen_at == original_first_seen
    assert saved.raw_payload == {"id": "job-1", "updated": True}


def test_matching_adds_title_and_freshness_bonus() -> None:
    service = InternshipMatchingService()
    profile = StudentProfile(user_id="student-1", university_id="u1", major="Computer Science")
    internship = Internship(
        title="Software Engineer Intern",
        company="Acme",
        description="Backend engineering internship",
        location="Remote",
        application_url="https://example.com/jobs/1",
        majors=["Computer Science"],
        keywords=["backend"],
        last_seen_at=datetime.now(timezone.utc),
    )

    results = service.score_profile(profile, [internship], date.today())

    assert len(results) == 1
    assert results[0].score >= 11.5

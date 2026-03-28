from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminUser, StudentUser, UniversityUser
from app.infrastructure.database.models.event_model import EventModel
from app.infrastructure.database.models.internship_model import InternshipModel
from app.infrastructure.database.models.student_profile_model import StudentProfileModel
from app.infrastructure.database.models.university_model import UniversityModel
from app.infrastructure.database.repositories.event_rsvp_repository_impl import (
    SQLAlchemyEventRSVPRepository,
)
from app.infrastructure.database.repositories.internship_recommendation_repository_impl import (
    SQLAlchemyInternshipRecommendationRepository,
)
from app.infrastructure.database.repositories.internship_repository_impl import (
    SQLAlchemyInternshipRepository,
)
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)
from app.infrastructure.database.repositories.university_repository_impl import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.database.session import get_async_session

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DbSession = Annotated[AsyncSession, Depends(get_async_session)]


# ── Shared response schemas ───────────────────────────────────────────────────


class InternshipSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    is_active: bool


class RecommendationSummary(BaseModel):
    internship_id: str
    internship_title: str
    internship_company: str
    score: float
    reason: str


class EventSummary(BaseModel):
    id: str
    title: str
    organizer_name: str
    mode: str
    host_type: str
    start_at: str
    location: str | None


# ── Student Dashboard ─────────────────────────────────────────────────────────


class StudentDashboard(BaseModel):
    user_id: str
    email: str
    profile_complete: bool
    university_name: str | None
    major: str | None
    graduation_year: int | None
    skills: list[str]
    interests: list[str]
    preferred_locations: list[str]
    todays_recommendations: list[RecommendationSummary]
    recent_internships: list[InternshipSummary]
    upcoming_events: list[EventSummary]
    upcoming_rsvps: list[EventSummary]


@router.get(
    "/student",
    response_model=StudentDashboard,
    summary="Student dashboard",
)
async def student_dashboard(
    claims: StudentUser,
    session: DbSession,
) -> StudentDashboard:
    """Returns the authenticated student's profile and today's recommendations."""
    profile_repo = SQLAlchemyStudentProfileRepository(session)
    internship_repo = SQLAlchemyInternshipRepository(session)
    recommendation_repo = SQLAlchemyInternshipRecommendationRepository(session)
    uni_repo = SQLAlchemyUniversityRepository(session)
    event_rsvp_repo = SQLAlchemyEventRSVPRepository(session)

    profile = await profile_repo.get_by_user_id(claims.sub)

    todays_recs: list[RecommendationSummary] = []
    university_name: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    skills: list[str] = []
    interests: list[str] = []
    preferred_locations: list[str] = []
    upcoming_events: list[EventSummary] = []
    upcoming_rsvps: list[EventSummary] = []

    if profile:
        major = profile.major
        graduation_year = profile.graduation_year
        skills = list(profile.skills)
        interests = list(profile.interests)
        preferred_locations = list(profile.preferred_locations)

        uni = await uni_repo.get_by_id(profile.university_id)
        if uni:
            university_name = uni.name

        recs = await recommendation_repo.list_for_profile_on_date(
            profile_id=profile.id,
            target_date=date.today(),
        )
        for rec in recs[:10]:
            internship = await internship_repo.get_by_id(rec.internship_id)
            if internship:
                todays_recs.append(
                    RecommendationSummary(
                        internship_id=internship.id,
                        internship_title=internship.title,
                        internship_company=internship.company,
                        score=rec.score,
                        reason=rec.reason,
                    )
                )

    # Latest 5 active internships regardless of profile
    result = await session.execute(
        select(InternshipModel)
        .where(InternshipModel.is_active.is_(True))
        .order_by(InternshipModel.created_at.desc())
        .limit(5)
    )
    recent_internships = [
        InternshipSummary(
            id=str(m.id),
            title=m.title,
            company=m.company,
            location=m.location,
            is_active=m.is_active,
        )
        for m in result.scalars().all()
    ]

    event_result = await session.execute(
        select(EventModel)
        .where(
            EventModel.is_active.is_(True),
            EventModel.start_at >= func.now(),
        )
        .order_by(EventModel.start_at.asc())
        .limit(5)
    )
    upcoming_events = [
        EventSummary(
            id=str(m.id),
            title=m.title,
            organizer_name=m.organizer_name,
            mode=m.mode,
            host_type=m.host_type,
            start_at=m.start_at.isoformat(),
            location=m.location,
        )
        for m in event_result.scalars().all()
    ]

    user_rsvps = await event_rsvp_repo.list_upcoming_for_user(user_id=claims.sub)
    if user_rsvps:
        rsvp_event_ids = [item.event_id for item in user_rsvps]
        rsvp_event_result = await session.execute(
            select(EventModel)
            .where(EventModel.id.in_(rsvp_event_ids))
            .order_by(EventModel.start_at.asc())
        )
        upcoming_rsvps = [
            EventSummary(
                id=str(m.id),
                title=m.title,
                organizer_name=m.organizer_name,
                mode=m.mode,
                host_type=m.host_type,
                start_at=m.start_at.isoformat(),
                location=m.location,
            )
            for m in rsvp_event_result.scalars().all()
        ]

    return StudentDashboard(
        user_id=claims.sub,
        email=claims.email,
        profile_complete=profile is not None,
        university_name=university_name,
        major=major,
        graduation_year=graduation_year,
        skills=skills,
        interests=interests,
        preferred_locations=preferred_locations,
        todays_recommendations=todays_recs,
        recent_internships=recent_internships,
        upcoming_events=upcoming_events,
        upcoming_rsvps=upcoming_rsvps,
    )


# ── University Dashboard ──────────────────────────────────────────────────────


class UniversityDashboard(BaseModel):
    user_id: str
    email: str
    university_id: str | None
    university_name: str | None
    domain: str | None
    country: str | None
    is_active: bool | None
    total_internships_posted: int
    active_internships: int
    recent_internships: list[InternshipSummary]
    total_events_hosted: int
    active_events: int
    total_event_rsvps: int
    recent_events: list[EventSummary]


@router.get(
    "/university",
    response_model=UniversityDashboard,
    summary="University dashboard",
)
async def university_dashboard(
    claims: UniversityUser,
    session: DbSession,
) -> UniversityDashboard:
    """Returns the authenticated university's profile and internship stats."""
    uni_repo = SQLAlchemyUniversityRepository(session)
    uni = await uni_repo.get_by_keycloak_user_id(claims.sub)

    university_id: str | None = None
    university_name: str | None = None
    domain: str | None = None
    country: str | None = None
    is_active: bool | None = None
    total_posted = 0
    active_count = 0
    recent_internships: list[InternshipSummary] = []
    total_events_hosted = 0
    active_events = 0
    total_event_rsvps = 0
    recent_events: list[EventSummary] = []

    if uni:
        university_id = uni.id
        university_name = uni.name
        domain = uni.domain
        country = uni.country
        is_active = uni.is_active

        # Internships posted by this Keycloak user
        total_result = await session.execute(
            select(func.count()).select_from(InternshipModel).where(
                InternshipModel.posted_by == claims.sub
            )
        )
        total_posted = total_result.scalar_one() or 0

        active_result = await session.execute(
            select(func.count()).select_from(InternshipModel).where(
                InternshipModel.posted_by == claims.sub,
                InternshipModel.is_active.is_(True),
            )
        )
        active_count = active_result.scalar_one() or 0

        recent_result = await session.execute(
            select(InternshipModel)
            .where(InternshipModel.posted_by == claims.sub)
            .order_by(InternshipModel.created_at.desc())
            .limit(5)
        )
        recent_internships = [
            InternshipSummary(
                id=str(m.id),
                title=m.title,
                company=m.company,
                location=m.location,
                is_active=m.is_active,
            )
            for m in recent_result.scalars().all()
        ]

        total_events_result = await session.execute(
            select(func.count()).select_from(EventModel).where(
                EventModel.hosted_by == claims.sub,
                EventModel.host_type == "university",
            )
        )
        total_events_hosted = total_events_result.scalar_one() or 0

        active_events_result = await session.execute(
            select(func.count()).select_from(EventModel).where(
                EventModel.hosted_by == claims.sub,
                EventModel.host_type == "university",
                EventModel.is_active.is_(True),
            )
        )
        active_events = active_events_result.scalar_one() or 0
        event_rsvp_repo = SQLAlchemyEventRSVPRepository(session)
        total_event_rsvps = await event_rsvp_repo.count_for_host(hosted_by=claims.sub)

        recent_events_result = await session.execute(
            select(EventModel)
            .where(
                EventModel.hosted_by == claims.sub,
                EventModel.host_type == "university",
            )
            .order_by(EventModel.start_at.asc())
            .limit(5)
        )
        recent_events = [
            EventSummary(
                id=str(m.id),
                title=m.title,
                organizer_name=m.organizer_name,
                mode=m.mode,
                host_type=m.host_type,
                start_at=m.start_at.isoformat(),
                location=m.location,
            )
            for m in recent_events_result.scalars().all()
        ]

    return UniversityDashboard(
        user_id=claims.sub,
        email=claims.email,
        university_id=university_id,
        university_name=university_name,
        domain=domain,
        country=country,
        is_active=is_active,
        total_internships_posted=total_posted,
        active_internships=active_count,
        recent_internships=recent_internships,
        total_events_hosted=total_events_hosted,
        active_events=active_events,
        total_event_rsvps=total_event_rsvps,
        recent_events=recent_events,
    )


# ── Admin Dashboard ───────────────────────────────────────────────────────────


class AdminDashboard(BaseModel):
    user_id: str
    email: str
    total_universities: int
    active_universities: int
    total_students: int
    active_students: int
    total_internships: int
    active_internships: int
    total_events: int
    active_events: int
    total_event_rsvps: int
    recent_universities: list[dict]


@router.get(
    "/admin",
    response_model=AdminDashboard,
    summary="Admin dashboard",
)
async def admin_dashboard(
    claims: AdminUser,
    session: DbSession,
) -> AdminDashboard:
    """Returns system-wide statistics visible only to admins."""
    # University counts
    total_uni = (
        await session.execute(select(func.count()).select_from(UniversityModel))
    ).scalar_one() or 0

    active_uni = (
        await session.execute(
            select(func.count()).select_from(UniversityModel).where(
                UniversityModel.is_active.is_(True)
            )
        )
    ).scalar_one() or 0

    # Student counts
    total_students = (
        await session.execute(select(func.count()).select_from(StudentProfileModel))
    ).scalar_one() or 0

    active_students = (
        await session.execute(
            select(func.count()).select_from(StudentProfileModel).where(
                StudentProfileModel.is_active.is_(True)
            )
        )
    ).scalar_one() or 0

    # Internship counts
    total_intern = (
        await session.execute(select(func.count()).select_from(InternshipModel))
    ).scalar_one() or 0

    active_intern = (
        await session.execute(
            select(func.count()).select_from(InternshipModel).where(
                InternshipModel.is_active.is_(True)
            )
        )
    ).scalar_one() or 0

    total_events = (
        await session.execute(select(func.count()).select_from(EventModel))
    ).scalar_one() or 0

    active_events = (
        await session.execute(
            select(func.count()).select_from(EventModel).where(
                EventModel.is_active.is_(True)
            )
        )
    ).scalar_one() or 0
    total_event_rsvps = await SQLAlchemyEventRSVPRepository(session).count_all()

    # Recent universities
    recent_uni_result = await session.execute(
        select(UniversityModel).order_by(UniversityModel.created_at.desc()).limit(10)
    )
    recent_universities = [
        {
            "id": str(m.id),
            "name": m.name,
            "domain": m.domain,
            "country": m.country,
            "is_active": m.is_active,
        }
        for m in recent_uni_result.scalars().all()
    ]

    return AdminDashboard(
        user_id=claims.sub,
        email=claims.email,
        total_universities=total_uni,
        active_universities=active_uni,
        total_students=total_students,
        active_students=active_students,
        total_internships=total_intern,
        active_internships=active_intern,
        total_events=total_events,
        active_events=active_events,
        total_event_rsvps=total_event_rsvps,
        recent_universities=recent_universities,
    )

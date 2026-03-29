from __future__ import annotations

from datetime import date, datetime, timezone

from app.application.dto.internship_sync_dto import InternshipSyncResultDTO
from app.application.services.external_internship_provider import (
    AdzunaInternshipProvider,
    ExternalInternshipProvider,
)
from app.application.services.listing_risk import ListingRiskService
from app.application.services.major_taxonomy import MajorTaxonomyService
from app.domain.entities.internship import Internship
from app.domain.repositories.internship_repository import InternshipRepository
from app.domain.repositories.internship_recommendation_repository import (
    InternshipRecommendationRepository,
)
from app.domain.repositories.student_profile_repository import StudentProfileRepository

from app.application.use_cases.generate_daily_recommendations import (
    GenerateDailyRecommendationsUseCase,
)


class SyncExternalInternshipsUseCase:
    def __init__(
        self,
        internships: InternshipRepository,
        profiles: StudentProfileRepository,
        recommendations: InternshipRecommendationRepository,
        provider: ExternalInternshipProvider | None = None,
        taxonomy: MajorTaxonomyService | None = None,
        risk_service: ListingRiskService | None = None,
    ) -> None:
        self._internships = internships
        self._profiles = profiles
        self._recommendations = recommendations
        self._provider = provider or AdzunaInternshipProvider()
        self._taxonomy = taxonomy or MajorTaxonomyService()
        self._risk_service = risk_service or ListingRiskService()

    async def execute(self, target_date: date) -> InternshipSyncResultDTO:
        provider_source_name = getattr(self._provider, "SOURCE_NAME", "external_api")
        search_terms = sorted(
            {
                term
                for major in self._taxonomy.supported_majors()
                for term in self._taxonomy.search_terms_for_major(major)
            }
        )
        external_records = await self._provider.fetch_internships(search_terms)

        created = 0
        updated = 0
        skipped = 0
        seen_ids: set[str] = set()

        for record in external_records:
            if not record.application_url:
                skipped += 1
                continue

            seen_ids.add(record.external_id)
            existing = await self._internships.get_by_source_identity(
                record.source_name,
                record.external_id,
            )
            now = datetime.now(timezone.utc)
            risk = self._risk_service.analyze_internship(
                title=record.title,
                company=record.company,
                description=record.description,
                application_url=record.application_url,
                source_url=record.source_url,
                raw_payload=record.raw_payload,
            )
            saved, was_created = await self._internships.upsert_by_source(
                Internship(
                    title=record.title,
                    company=record.company,
                    description=record.description,
                    location=record.location,
                    application_url=record.application_url,
                    posted_by="system",
                    source_type="external_api",
                    external_id=record.external_id,
                    source_name=record.source_name,
                    source_url=record.source_url,
                    majors=record.majors,
                    keywords=record.keywords,
                    is_active=True,
                    risk_score=risk.score,
                    risk_level=risk.level,
                    risk_reasons=risk.reasons,
                    expires_at=record.expires_at,
                    first_seen_at=(
                        record.first_seen_at
                        or (existing.first_seen_at if existing else None)
                        or record.last_seen_at
                        or now
                    ),
                    last_seen_at=record.last_seen_at or now,
                    raw_payload=record.raw_payload,
                )
            )
            if was_created:
                created += 1
            else:
                updated += 1

        deactivated = await self._internships.mark_missing_external_inactive(
            provider_source_name,
            seen_ids,
        )
        recommendations_generated = await GenerateDailyRecommendationsUseCase(
            profiles=self._profiles,
            internships=self._internships,
            recommendations=self._recommendations,
        ).execute(target_date)

        return InternshipSyncResultDTO(
            target_date=target_date,
            fetched=len(external_records),
            created=created,
            updated=updated,
            deactivated=deactivated,
            skipped=skipped,
            recommendations_generated=recommendations_generated,
        )

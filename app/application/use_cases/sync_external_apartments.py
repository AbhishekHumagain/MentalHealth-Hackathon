from __future__ import annotations

from datetime import datetime, timezone

from app.application.dto.apartment_sync_dto import ApartmentSyncResultDTO
from app.application.services.external_housing_provider import (
    ExternalApartmentRecord,
    HousingProvider,
    build_housing_provider,
)
from app.domain.entities.apartment import Apartment
from app.domain.repositories.apartment_repository import AbstractApartmentRepository
from app.domain.repositories.student_profile_repository import StudentProfileRepository


class SyncExternalApartmentsUseCase:
    def __init__(
        self,
        apartments: AbstractApartmentRepository,
        profiles: StudentProfileRepository,
        provider: HousingProvider | None = None,
    ) -> None:
        self._apartments = apartments
        self._profiles = profiles
        self._provider = provider or build_housing_provider()

    async def execute(
        self,
        *,
        locations: list[str] | None = None,
        max_rent: float | None = None,
        limit_per_location: int = 20,
    ) -> ApartmentSyncResultDTO:
        requested_locations = locations or await self._collect_preferred_locations()
        requested_locations = _normalize_locations(requested_locations)
        if not requested_locations:
            raise ValueError(
                "No apartment sync locations available. Pass locations explicitly or create student profiles with preferred locations."
            )

        external_records = await self._provider.fetch_apartments(
            requested_locations,
            limit_per_location=limit_per_location,
        )

        created = 0
        updated = 0
        skipped = 0
        seen_ids: set[str] = set()

        for record in external_records:
            if max_rent is not None and record.monthly_rent > max_rent:
                skipped += 1
                continue
            if not record.address or not record.city or not record.state:
                skipped += 1
                continue

            seen_ids.add(record.external_id)
            existing = await self._apartments.get_by_source_identity(record.source_name, record.external_id)
            now = datetime.now(timezone.utc)
            _, was_created = await self._apartments.upsert_by_source(
                Apartment(
                    title=record.title,
                    description=record.description,
                    address=record.address,
                    city=record.city,
                    state=record.state,
                    zip_code=record.zip_code,
                    monthly_rent=record.monthly_rent,
                    bedrooms=record.bedrooms,
                    bathrooms=record.bathrooms,
                    is_furnished=record.is_furnished,
                    is_available=record.is_available,
                    available_from=record.available_from,
                    images_urls=record.images_urls,
                    amenities=record.amenities,
                    posted_by="system",
                    source_type=record.source_type,
                    external_id=record.external_id,
                    source_name=record.source_name,
                    source_url=record.source_url,
                    contact_email=record.contact_email,
                    contact_phone=record.contact_phone,
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

        deactivated = await self._apartments.mark_missing_external_inactive(
            getattr(self._provider, "SOURCE_NAME", "external_api"),
            seen_ids,
        )

        return ApartmentSyncResultDTO(
            requested_locations=requested_locations,
            fetched=len(external_records),
            created=created,
            updated=updated,
            deactivated=deactivated,
            skipped=skipped,
        )

    async def _collect_preferred_locations(self) -> list[str]:
        profiles = await self._profiles.list_active()
        return [
            location
            for profile in profiles
            for location in profile.preferred_locations
            if location
        ]


def _normalize_locations(locations: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for location in locations:
        value = " ".join(location.split())
        if value and value.lower() not in seen:
            normalized.append(value)
            seen.add(value.lower())
    return normalized

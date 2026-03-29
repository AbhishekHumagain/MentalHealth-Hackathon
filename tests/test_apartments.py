from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.dto.apartment_dto import CreateApartmentDTO
from app.application.services.external_housing_provider import (
    DemoSeedHousingProvider,
    ExternalApartmentRecord,
    _normalize_rentcast_listing,
)
from app.application.use_cases.create_apartment import CreateApartmentUseCase
from app.application.use_cases.list_apartments import ListApartmentsByLocationUseCase, ListApartmentsUseCase
from app.application.use_cases.sync_external_apartments import SyncExternalApartmentsUseCase
from app.domain.entities.apartment import Apartment
from app.domain.entities.student_profile import StudentProfile


class InMemoryApartmentRepository:
    def __init__(self) -> None:
        self.items: dict[str, Apartment] = {}

    async def create(self, apartment: Apartment) -> Apartment:
        self.items[apartment.id] = apartment
        return apartment

    async def upsert_by_source(self, apartment: Apartment) -> tuple[Apartment, bool]:
        if apartment.source_name and apartment.external_id:
            for existing in self.items.values():
                if existing.source_name == apartment.source_name and existing.external_id == apartment.external_id:
                    apartment.id = existing.id
                    if apartment.first_seen_at is None:
                        apartment.first_seen_at = existing.first_seen_at
                    self.items[existing.id] = apartment
                    return apartment, False
        self.items[apartment.id] = apartment
        return apartment, True

    async def get_by_id(self, apartment_id: str) -> Apartment | None:
        return self.items.get(apartment_id)

    async def list_all(
        self,
        city: str | None = None,
        state: str | None = None,
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        items = [
            apartment
            for apartment in self.items.values()
            if not apartment.is_deleted and apartment.is_available
        ]
        if city:
            items = [apartment for apartment in items if city.lower() in apartment.city.lower()]
        if state:
            items = [apartment for apartment in items if state.lower() in apartment.state.lower()]
        if max_rent is not None:
            items = [apartment for apartment in items if apartment.monthly_rent <= max_rent]
        items.sort(key=lambda apartment: apartment.monthly_rent)
        return items[skip : skip + limit]

    async def list_by_locations(
        self,
        locations: list[str],
        max_rent: float | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Apartment]:
        lowered = [location.lower() for location in locations]
        items = [
            apartment
            for apartment in self.items.values()
            if not apartment.is_deleted
            and apartment.is_available
            and any(
                location in apartment.city.lower()
                or location in apartment.state.lower()
                or location in apartment.zip_code.lower()
                for location in lowered
            )
        ]
        if max_rent is not None:
            items = [apartment for apartment in items if apartment.monthly_rent <= max_rent]
        items.sort(key=lambda apartment: apartment.monthly_rent)
        return items[skip : skip + limit]

    async def delete(self, apartment_id: str, user_id: str) -> Apartment:
        apartment = self.items[apartment_id]
        apartment.is_deleted = True
        return apartment

    async def get_by_source_identity(self, source_name: str, external_id: str) -> Apartment | None:
        return next(
            (
                apartment
                for apartment in self.items.values()
                if apartment.source_name == source_name and apartment.external_id == external_id
            ),
            None,
        )

    async def mark_missing_external_inactive(self, source_name: str, external_ids: set[str]) -> int:
        count = 0
        for apartment in self.items.values():
            if (
                apartment.source_type != "manual"
                and apartment.source_name == source_name
                and apartment.is_available
                and apartment.external_id not in external_ids
            ):
                apartment.is_available = False
                count += 1
        return count


class InMemoryStudentProfileRepository:
    def __init__(self, profiles: list[StudentProfile] | None = None) -> None:
        self.items = profiles or []

    async def list_active(self) -> list[StudentProfile]:
        return [profile for profile in self.items if profile.is_active]


class FakeHousingProvider:
    SOURCE_NAME = "rentcast"

    def __init__(self, records: list[ExternalApartmentRecord]) -> None:
        self._records = records

    async def fetch_apartments(
        self,
        locations: list[str],
        *,
        limit_per_location: int = 20,
    ) -> list[ExternalApartmentRecord]:
        return self._records


@pytest.mark.asyncio
async def test_create_apartment_and_list_filters() -> None:
    repo = InMemoryApartmentRepository()

    created = await CreateApartmentUseCase(repo).execute(
        CreateApartmentDTO(
            title="Cheap Room",
            description="Near campus",
            address="123 Main St",
            city="Boston",
            state="MA",
            zip_code="02118",
            monthly_rent=900,
            contact_email="owner@example.com",
            posted_by="user-1",
        )
    )

    assert created.source_type == "manual"
    listed = await ListApartmentsUseCase(repo).execute(city="Boston", max_rent=1000)
    assert len(listed) == 1
    assert listed[0].title == "Cheap Room"


@pytest.mark.asyncio
async def test_list_by_location_prefers_cheaper_matches() -> None:
    repo = InMemoryApartmentRepository()
    await repo.create(
        Apartment(
            title="Expensive Boston Unit",
            description="Downtown",
            address="1 A St",
            city="Boston",
            state="MA",
            zip_code="02118",
            monthly_rent=2200,
        )
    )
    await repo.create(
        Apartment(
            title="Affordable Boston Unit",
            description="Student friendly",
            address="2 B St",
            city="Boston",
            state="MA",
            zip_code="02118",
            monthly_rent=1200,
        )
    )

    results = await ListApartmentsByLocationUseCase(repo).execute(locations=["Boston"], limit=10)

    assert [item.title for item in results] == ["Affordable Boston Unit", "Expensive Boston Unit"]


def test_rentcast_normalization_maps_listing() -> None:
    record = _normalize_rentcast_listing(
        {
            "id": "listing-1",
            "formattedAddress": "123 Main St, Boston, MA 02118",
            "city": "Boston",
            "state": "MA",
            "zipCode": "02118",
            "price": 1800,
            "bedrooms": 2,
            "bathrooms": 1.5,
            "description": "Near campus",
            "listingUrl": "https://rentcast.example/listing-1",
            "photos": ["https://example.com/photo.jpg"],
            "features": ["Laundry"],
        }
    )

    assert record is not None
    assert record.external_id == "listing-1"
    assert record.city == "Boston"
    assert record.monthly_rent == 1800
    assert record.source_name == "rentcast"


@pytest.mark.asyncio
async def test_demo_seed_provider_generates_reasonable_records() -> None:
    provider = DemoSeedHousingProvider()

    records = await provider.fetch_apartments(["Boston, MA"], limit_per_location=3)

    assert len(records) == 3
    assert all(record.source_type == "demo_seed" for record in records)
    assert all(record.source_name == "internal_demo" for record in records)
    assert any("Boston" in record.city for record in records)


@pytest.mark.asyncio
async def test_sync_external_apartments_creates_updates_and_deactivates() -> None:
    repo = InMemoryApartmentRepository()
    profiles = InMemoryStudentProfileRepository(
        [
            StudentProfile(
                user_id="student-1",
                university_id="u1",
                preferred_locations=["Boston, MA"],
            )
        ]
    )
    old = Apartment(
        title="Old Listing",
        description="Old",
        address="1 Old St",
        city="Boston",
        state="MA",
        zip_code="02118",
        monthly_rent=2000,
        source_type="external_api",
        source_name="rentcast",
        external_id="old-1",
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    await repo.create(old)

    provider = FakeHousingProvider(
        [
            ExternalApartmentRecord(
                external_id="listing-1",
                title="Apartment in Boston - $1600/mo",
                description="Near campus",
                address="123 Main St",
                city="Boston",
                state="MA",
                zip_code="02118",
                monthly_rent=1600,
                bedrooms=2,
                bathrooms=1.0,
                source_url="https://rentcast.example/listing-1",
                last_seen_at=datetime.now(timezone.utc),
            ),
            ExternalApartmentRecord(
                external_id="listing-1",
                title="Apartment in Boston - $1500/mo",
                description="Updated rent",
                address="123 Main St",
                city="Boston",
                state="MA",
                zip_code="02118",
                monthly_rent=1500,
                bedrooms=2,
                bathrooms=1.0,
                source_url="https://rentcast.example/listing-1",
                last_seen_at=datetime.now(timezone.utc),
            ),
        ]
    )

    result = await SyncExternalApartmentsUseCase(
        apartments=repo,
        profiles=profiles,
        provider=provider,
    ).execute()

    assert result.created == 1
    assert result.updated == 1
    assert result.deactivated == 1
    saved = await repo.get_by_source_identity("rentcast", "listing-1")
    assert saved is not None
    assert saved.monthly_rent == 1500
    assert saved.source_type == "external_api"

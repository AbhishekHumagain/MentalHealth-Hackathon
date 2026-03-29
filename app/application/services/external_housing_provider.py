from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class ExternalApartmentRecord:
    external_id: str
    title: str
    description: str
    address: str
    city: str
    state: str
    zip_code: str
    monthly_rent: float
    bedrooms: int = 0
    bathrooms: float = 0.0
    is_furnished: bool = False
    is_available: bool = True
    available_from: str | None = None
    images_urls: list[str] = field(default_factory=list)
    amenities: list[str] = field(default_factory=list)
    source_type: str = "external_api"
    source_name: str = "rentcast"
    source_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, object] | None = None


class HousingProvider:
    async def fetch_apartments(
        self,
        locations: list[str],
        *,
        limit_per_location: int = 20,
        ) -> list[ExternalApartmentRecord]:
        raise NotImplementedError


class DemoSeedHousingProvider(HousingProvider):
    SOURCE_NAME = "internal_demo"

    _CITY_PROFILES: dict[str, dict[str, object]] = {
        "boston, ma": {
            "zip_code": "02115",
            "multiplier": 1.2,
            "neighborhoods": ["Fenway", "Allston", "Back Bay", "Mission Hill"],
        },
        "chicago, il": {
            "zip_code": "60605",
            "multiplier": 1.0,
            "neighborhoods": ["South Loop", "Lakeview", "Uptown", "Pilsen"],
        },
        "new york, ny": {
            "zip_code": "10012",
            "multiplier": 1.45,
            "neighborhoods": ["Astoria", "Harlem", "Lower East Side", "Bushwick"],
        },
        "dallas, tx": {
            "zip_code": "75201",
            "multiplier": 0.92,
            "neighborhoods": ["Deep Ellum", "Oak Lawn", "Bishop Arts", "Old East Dallas"],
        },
        "austin, tx": {
            "zip_code": "78701",
            "multiplier": 1.03,
            "neighborhoods": ["West Campus", "Riverside", "Mueller", "North Loop"],
        },
        "seattle, wa": {
            "zip_code": "98101",
            "multiplier": 1.18,
            "neighborhoods": ["Capitol Hill", "U-District", "Ballard", "Beacon Hill"],
        },
        "san francisco, ca": {
            "zip_code": "94103",
            "multiplier": 1.52,
            "neighborhoods": ["SoMa", "Sunset", "Mission", "Inner Richmond"],
        },
    }

    _TEMPLATES: tuple[dict[str, object], ...] = (
        {
            "headline": "Furnished studio near transit",
            "bedrooms": 0,
            "bathrooms": 1.0,
            "rent": 1180,
            "furnished": True,
            "amenities": ["WiFi", "Laundry", "Study lounge"],
            "street": "12 College Ave",
            "description": "Compact studio popular with interns who want walkable transit and furnished move-in.",
        },
        {
            "headline": "Shared 2BR with utilities included",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "rent": 1425,
            "furnished": False,
            "amenities": ["Utilities included", "Bike storage", "Heating"],
            "street": "48 Maple St",
            "description": "Budget-friendly shared apartment with simple lease terms and a quiet residential block.",
        },
        {
            "headline": "Student-friendly 1BR close to downtown",
            "bedrooms": 1,
            "bathrooms": 1.0,
            "rent": 1560,
            "furnished": False,
            "amenities": ["Gym", "Package room", "Pet friendly"],
            "street": "215 Harrison St",
            "description": "Bright one-bedroom with space for remote work and easy access to downtown employers.",
        },
        {
            "headline": "2BR near campus shuttle",
            "bedrooms": 2,
            "bathrooms": 1.5,
            "rent": 1750,
            "furnished": True,
            "amenities": ["Campus shuttle", "Dishwasher", "On-site laundry"],
            "street": "77 Garden St",
            "description": "Flexible mid-term lease option, popular with students relocating for internships.",
        },
        {
            "headline": "Quiet 1BR in residential block",
            "bedrooms": 1,
            "bathrooms": 1.0,
            "rent": 1495,
            "furnished": False,
            "amenities": ["Parking", "Storage", "Courtyard"],
            "street": "340 Cedar Ave",
            "description": "Calmer neighborhood option for students who want lower rent without losing city access.",
        },
        {
            "headline": "Modern 3BR for roommates",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "rent": 2100,
            "furnished": False,
            "amenities": ["In-unit laundry", "Balcony", "Central air"],
            "street": "901 Union Pl",
            "description": "Roommate-friendly layout with strong value when split between three tenants.",
        },
    )

    async def fetch_apartments(
        self,
        locations: list[str],
        *,
        limit_per_location: int = 20,
    ) -> list[ExternalApartmentRecord]:
        listings_by_id: dict[str, ExternalApartmentRecord] = {}
        for location in locations:
            for record in self._generate_records_for_location(location, limit_per_location):
                listings_by_id[record.external_id] = record
        return list(listings_by_id.values())

    def _generate_records_for_location(
        self,
        location: str,
        limit_per_location: int,
    ) -> list[ExternalApartmentRecord]:
        city, state = _split_location(location)
        location_key = f"{city.lower()}, {state.lower()}" if state else city.lower()
        profile = self._CITY_PROFILES.get(
            location_key,
            {
                "zip_code": "00000",
                "multiplier": 1.0,
                "neighborhoods": ["Downtown", "Midtown", "University District", "Central"],
            },
        )
        neighborhoods = list(profile["neighborhoods"])
        multiplier = float(profile["multiplier"])
        zip_code = str(profile["zip_code"])
        slug = _slugify(location_key.replace(", ", "-"))
        now = datetime.now(timezone.utc)
        records: list[ExternalApartmentRecord] = []

        for index, template in enumerate(self._TEMPLATES[:limit_per_location], start=1):
            neighborhood = neighborhoods[(index - 1) % len(neighborhoods)]
            bedrooms = int(template["bedrooms"])
            monthly_rent = round(float(template["rent"]) * multiplier + (index % 2) * 45, 2)
            title = f"{template['headline'].title()} in {neighborhood}"
            description = (
                f"{template['description']} Located in {neighborhood}, {city}. "
                f"Great for students looking for a practical commute and predictable monthly costs."
            )
            external_id = f"demo-{slug}-{index}"
            records.append(
                ExternalApartmentRecord(
                    external_id=external_id,
                    title=title,
                    description=description,
                    address=f"{template['street']}, {neighborhood}",
                    city=city or "Demo City",
                    state=state or "US",
                    zip_code=zip_code,
                    monthly_rent=monthly_rent,
                    bedrooms=bedrooms,
                    bathrooms=float(template["bathrooms"]),
                    is_furnished=bool(template["furnished"]),
                    is_available=True,
                    available_from="2026-04-01",
                    amenities=list(template["amenities"]),
                    source_type="demo_seed",
                    source_name=self.SOURCE_NAME,
                    source_url=f"https://housing-demo.example/listings/{external_id}",
                    contact_email=f"leasing-{slug}@housing-demo.example",
                    contact_phone="(555) 010-2026",
                    first_seen_at=now,
                    last_seen_at=now,
                    raw_payload={
                        "seed_location": location,
                        "seed_neighborhood": neighborhood,
                        "demo_provider": True,
                    },
                )
            )
        return records


class RentCastHousingProvider(HousingProvider):
    BASE_URL = "https://api.rentcast.io/v1/listings/rental/long-term"
    SOURCE_NAME = "rentcast"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.rentcast_api_key
        if not self._api_key:
            raise ValueError(
                "Missing RentCast configuration: RENTCAST_API_KEY. "
                "Set this environment variable before syncing apartments."
            )

    async def fetch_apartments(
        self,
        locations: list[str],
        *,
        limit_per_location: int = 20,
    ) -> list[ExternalApartmentRecord]:
        listings_by_id: dict[str, ExternalApartmentRecord] = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for location in locations:
                city, state = _split_location(location)
                params = {
                    "city": city,
                    "limit": limit_per_location,
                    "status": "Active",
                }
                if state:
                    params["state"] = state
                response = await client.get(
                    self.BASE_URL,
                    headers={"X-Api-Key": self._api_key},
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                results = data if isinstance(data, list) else data.get("results", [])

                for item in results:
                    record = _normalize_rentcast_listing(item, fallback_city=city, fallback_state=state)
                    if record is None:
                        continue
                    listings_by_id[record.external_id] = record
        return list(listings_by_id.values())


def build_housing_provider() -> HousingProvider:
    settings = get_settings()
    provider_name = settings.housing_provider.strip().lower()
    if provider_name == "rentcast":
        return RentCastHousingProvider()
    if provider_name in {"demo", "demo_seed", "seed"}:
        return DemoSeedHousingProvider()
    if provider_name == "auto":
        if settings.rentcast_api_key:
            return RentCastHousingProvider()
        return DemoSeedHousingProvider()
    raise ValueError(
        "Unsupported housing provider configuration. "
        "Use HOUSING_PROVIDER=demo_seed, auto, or rentcast."
    )


def _split_location(location: str) -> tuple[str, str | None]:
    parts = [part.strip() for part in location.split(",") if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return location.strip(), None


def _to_float(value: object | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: object | None) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1"}
    return False


def _to_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_title(bedrooms: int, city: str, monthly_rent: float) -> str:
    bedroom_label = f"{bedrooms} BR " if bedrooms > 0 else ""
    city_label = city or "Rental"
    return f"{bedroom_label}Apartment in {city_label} - ${int(monthly_rent)}/mo"


def _slugify(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value).strip("-")


def _normalize_rentcast_listing(
    item: dict[str, object],
    *,
    fallback_city: str = "",
    fallback_state: str | None = None,
) -> ExternalApartmentRecord | None:
    external_id = str(
        item.get("id")
        or item.get("listingId")
        or item.get("propertyId")
        or ""
    )
    if not external_id:
        return None

    monthly_rent = _to_float(item.get("price") or item.get("rent") or item.get("monthlyRent"))
    if monthly_rent is None:
        return None

    address = (
        str(item.get("formattedAddress") or "")
        or str(item.get("addressLine1") or "")
        or str(item.get("address") or "")
    )
    city_value = str(item.get("city") or fallback_city or "")
    state_value = str(item.get("state") or fallback_state or "")
    zip_code = str(item.get("zipCode") or item.get("zip") or "")
    bedrooms = int(item.get("bedrooms") or 0)
    bathrooms = float(item.get("bathrooms") or 0.0)
    title = _build_title(bedrooms, city_value, monthly_rent)
    source_url = str(
        item.get("listingUrl")
        or item.get("url")
        or item.get("propertyUrl")
        or ""
    ) or None
    images = [
        str(value)
        for value in (
            item.get("photos")
            or item.get("images")
            or item.get("imageUrls")
            or []
        )
        if value
    ]
    amenities = [
        str(value)
        for value in (
            item.get("features")
            or item.get("amenities")
            or []
        )
        if value
    ]
    description = str(item.get("description") or item.get("remarks") or title)
    return ExternalApartmentRecord(
        external_id=external_id,
        title=title,
        description=description,
        address=address,
        city=city_value,
        state=state_value,
        zip_code=zip_code,
        monthly_rent=monthly_rent,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        is_furnished=_to_bool(item.get("furnished") or item.get("isFurnished")),
        is_available=True,
        available_from=_to_str(item.get("availableDate") or item.get("availableFrom")),
        images_urls=images,
        amenities=amenities,
        source_name=RentCastHousingProvider.SOURCE_NAME,
        source_url=source_url,
        contact_email=_to_str(item.get("contactEmail")),
        contact_phone=_to_str(item.get("contactPhone")),
        last_seen_at=datetime.now(timezone.utc),
        raw_payload=item,
    )

from __future__ import annotations

from app.domain.entities.apartment import Apartment


class ApartmentRankingService:
    def rank_for_locations(
        self,
        apartments: list[Apartment],
        locations: list[str],
    ) -> list[Apartment]:
        normalized_locations = [location.lower().strip() for location in locations if location.strip()]
        return sorted(
            apartments,
            key=lambda apartment: (
                -self._location_score(apartment, normalized_locations),
                apartment.monthly_rent,
                apartment.created_at,
            ),
        )

    def _location_score(self, apartment: Apartment, locations: list[str]) -> int:
        city = apartment.city.lower()
        state = apartment.state.lower()
        zip_code = apartment.zip_code.lower()
        for location in locations:
            if location == city or location == state or location == zip_code:
                return 3
            if location in city or location in state or location in zip_code:
                return 2
            if city in location or state in location:
                return 1
        return 0

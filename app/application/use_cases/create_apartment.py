from __future__ import annotations

from app.application.dto.apartment_dto import ApartmentResponseDTO, CreateApartmentDTO
from app.domain.entities.apartment import Apartment
from app.domain.repositories.apartment_repository import AbstractApartmentRepository


class CreateApartmentUseCase:
    def __init__(self, repo: AbstractApartmentRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreateApartmentDTO) -> ApartmentResponseDTO:
        apartment = Apartment(
            title=dto.title,
            description=dto.description,
            address=dto.address,
            city=dto.city,
            state=dto.state,
            zip_code=dto.zip_code,
            monthly_rent=dto.monthly_rent,
            bedrooms=dto.bedrooms,
            bathrooms=dto.bathrooms,
            is_furnished=dto.is_furnished,
            available_from=dto.available_from,
            images_urls=dto.images_urls,
            amenities=dto.amenities,
            posted_by=dto.posted_by,
            source_type=dto.source_type,
            external_id=dto.external_id,
            source_name=dto.source_name,
            source_url=dto.source_url,
            contact_email=dto.contact_email,
            contact_phone=dto.contact_phone,
            first_seen_at=dto.first_seen_at,
            last_seen_at=dto.last_seen_at,
            raw_payload=dto.raw_payload,
        )
        saved = await self._repo.create(apartment)
        return _to_dto(saved)


def _to_dto(a: Apartment) -> ApartmentResponseDTO:
    return ApartmentResponseDTO(
        id=a.id,
        title=a.title,
        description=a.description,
        address=a.address,
        city=a.city,
        state=a.state,
        zip_code=a.zip_code,
        monthly_rent=a.monthly_rent,
        bedrooms=a.bedrooms,
        bathrooms=a.bathrooms,
        is_furnished=a.is_furnished,
        is_available=a.is_available,
        available_from=a.available_from,
        images_urls=a.images_urls,
        amenities=a.amenities,
        posted_by=a.posted_by,
        source_type=a.source_type,
        external_id=a.external_id,
        source_name=a.source_name,
        source_url=a.source_url,
        contact_email=a.contact_email,
        contact_phone=a.contact_phone,
        first_seen_at=a.first_seen_at,
        last_seen_at=a.last_seen_at,
        raw_payload=a.raw_payload,
        created_at=a.created_at,
        modified_at=a.modified_at,
    )

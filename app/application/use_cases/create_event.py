from __future__ import annotations

from app.application.dto.event_dto import CreateEventDTO, EventResponseDTO
from app.application.services.listing_risk import ListingRiskService
from app.application.services.event_validation import validate_event_payload
from app.domain.entities.event import Event
from app.domain.repositories.event_repository import EventRepository


class CreateEventUseCase:
    def __init__(
        self,
        repo: EventRepository,
        risk_service: ListingRiskService | None = None,
    ) -> None:
        self._repo = repo
        self._risk_service = risk_service or ListingRiskService()

    async def execute(self, dto: CreateEventDTO) -> EventResponseDTO:
        validate_event_payload(
            mode=dto.mode,
            location=dto.location,
            meeting_url=dto.meeting_url,
            start_at=dto.start_at,
            end_at=dto.end_at,
        )
        risk = self._risk_service.analyze_event(
            title=dto.title,
            description=dto.description,
            organizer_name=dto.organizer_name,
            location=dto.location,
            meeting_url=dto.meeting_url,
            mode=dto.mode,
        )
        event = Event(
            title=dto.title,
            description=dto.description,
            hosted_by=dto.hosted_by,
            host_type=dto.host_type,
            organizer_name=dto.organizer_name,
            mode=dto.mode,
            location=dto.location,
            meeting_url=dto.meeting_url,
            start_at=dto.start_at,
            end_at=dto.end_at,
            tags=dto.tags,
            is_active=dto.is_active,
            risk_score=risk.score,
            risk_level=risk.level,
            risk_reasons=risk.reasons,
            banner_url=dto.banner_url,
            image_urls=list(dto.image_urls),
        )
        saved = await self._repo.create(event)
        return _to_dto(saved)


def _to_dto(event: Event) -> EventResponseDTO:
    return EventResponseDTO(
        id=event.id,
        title=event.title,
        description=event.description,
        hosted_by=event.hosted_by,
        host_type=event.host_type,
        organizer_name=event.organizer_name,
        mode=event.mode,
        location=event.location,
        meeting_url=event.meeting_url,
        start_at=event.start_at,
        end_at=event.end_at,
        tags=event.tags,
        is_active=event.is_active,
        risk_score=event.risk_score,
        risk_level=event.risk_level,
        risk_reasons=event.risk_reasons,
        banner_url=event.banner_url,
        image_urls=list(event.image_urls),
        created_at=event.created_at,
        modified_at=event.modified_at,
    )

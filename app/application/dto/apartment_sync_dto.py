from __future__ import annotations

from pydantic import BaseModel


class ApartmentSyncResultDTO(BaseModel):
    requested_locations: list[str]
    fetched: int
    created: int
    updated: int
    deactivated: int
    skipped: int

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class InternshipSyncResultDTO(BaseModel):
    target_date: date
    fetched: int
    created: int
    updated: int
    deactivated: int
    skipped: int
    recommendations_generated: int

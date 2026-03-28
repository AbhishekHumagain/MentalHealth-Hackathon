from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.Base import BaseModel


@dataclass
class EventRSVP(BaseModel):
    event_id: str = ""
    user_id: str = ""
    status: str = "going"

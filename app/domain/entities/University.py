from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.Base import BaseModel


@dataclass
class University(BaseModel):
    name: str = ""
    domain: str = ""          # e.g., msstate.edu
    country: str = ""
    is_active: bool = True
    keycloak_user_id: str | None = None   # Keycloak sub of the managing account

    # ── Business rules ──────────────────────────────────────────────────────

    def deactivate(self, user_id: str | None = None) -> None:
        self.is_active = False
        self.mark_modified(user_id)

    def activate(self, user_id: str | None = None) -> None:
        self.is_active = True
        self.mark_modified(user_id)
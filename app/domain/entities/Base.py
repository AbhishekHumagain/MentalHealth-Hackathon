from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class BaseModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str | None = None

    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_by: str | None = None

    is_deleted: bool = False

    # ── Domain behavior ──────────────────────────────────────────────────────

    def mark_modified(self, user_id: str | None = None) -> None:
        self.modified_at = datetime.now(timezone.utc)
        self.modified_by = user_id

    def soft_delete(self, user_id: str | None = None) -> None:
        self.is_deleted = True
        self.mark_modified(user_id)
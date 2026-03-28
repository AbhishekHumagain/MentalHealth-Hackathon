from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseDTO:
    id: str
    created_at: datetime
    created_by: str | None
    modified_at: datetime
    modified_by: str | None
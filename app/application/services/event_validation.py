from __future__ import annotations

from datetime import datetime


ALLOWED_EVENT_MODES = {"virtual", "in_person", "hybrid"}


def validate_event_payload(
    *,
    mode: str,
    location: str | None,
    meeting_url: str | None,
    start_at: datetime,
    end_at: datetime,
) -> None:
    if mode not in ALLOWED_EVENT_MODES:
        raise ValueError(f"Invalid event mode: {mode}.")
    if end_at <= start_at:
        raise ValueError("end_at must be after start_at.")
    if mode == "virtual" and not meeting_url:
        raise ValueError("meeting_url is required for virtual events.")
    if mode == "in_person" and not location:
        raise ValueError("location is required for in-person events.")

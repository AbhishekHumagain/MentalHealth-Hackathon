from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode

from app.domain.entities.event import Event


def _format_calendar_timestamp(value: datetime) -> str:
    utc_value = value.astimezone(timezone.utc)
    return utc_value.strftime("%Y%m%dT%H%M%SZ")


def build_google_calendar_url(event: Event) -> str:
    details = event.description.strip()
    if event.mode in {"virtual", "hybrid"} and event.meeting_url:
        details = f"{details}\n\nMeeting URL: {event.meeting_url}".strip()

    location = event.location or ""
    if event.mode == "virtual" and event.meeting_url:
        location = event.meeting_url

    params = {
        "action": "TEMPLATE",
        "text": event.title,
        "details": details,
        "location": location,
        "dates": (
            f"{_format_calendar_timestamp(event.start_at)}/"
            f"{_format_calendar_timestamp(event.end_at)}"
        ),
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)

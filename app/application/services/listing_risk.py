from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

_URGENCY_PATTERNS = (
    "apply immediately",
    "limited spots",
    "instant hire",
    "urgent hiring",
    "hurry",
    "act now",
)
_PAYMENT_PATTERNS = (
    "application fee",
    "training fee",
    "security deposit",
    "gift card",
    "crypto",
    "bitcoin",
    "wire transfer",
    "cashapp",
    "venmo",
    "send payment",
)
_PERSONAL_CONTACT_PATTERNS = (
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "telegram",
    "whatsapp",
)
_SPAM_PATTERNS = (
    "easy money",
    "no experience needed",
    "guaranteed job",
    "guaranteed income",
    "earn fast",
    "limited time only",
)
_VAGUE_COMPANIES = {
    "",
    "company",
    "hiring company",
    "confidential",
    "undisclosed",
    "unknown",
    "n/a",
}
_VAGUE_ORGANIZERS = {
    "",
    "admin",
    "team",
    "staff",
    "organizer",
    "support",
}
_SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "tiny.cc",
}
_INTERN_TERMS = {"intern", "internship", "junior", "entry", "entry-level", "entrylevel"}


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    level: str
    reasons: list[str]


class ListingRiskService:
    def analyze_internship(
        self,
        *,
        title: str,
        company: str,
        description: str,
        application_url: str,
        source_url: str | None = None,
        raw_payload: dict[str, object] | None = None,
    ) -> RiskAssessment:
        score = 0.0
        reasons: list[str] = []
        title_text = title.strip()
        company_text = company.strip().lower()
        description_text = description.strip()
        combined = " ".join([title_text, description_text]).lower()

        if company_text in _VAGUE_COMPANIES:
            score += 3.0
            reasons.append("Company identity is missing or vague.")

        score += self._add_pattern_risk(
            combined,
            _URGENCY_PATTERNS,
            weight=2.0,
            reason="Listing uses pressure or urgency language.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _PAYMENT_PATTERNS,
            weight=5.0,
            reason="Listing mentions payment, fees, or money transfer requests.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _PERSONAL_CONTACT_PATTERNS,
            weight=3.0,
            reason="Listing relies on personal email or messaging apps instead of normal company channels.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _SPAM_PATTERNS,
            weight=2.0,
            reason="Listing contains spam-like language.",
            reasons=reasons,
        )

        if not application_url:
            score += 4.0
            reasons.append("Listing is missing an application URL.")
        elif self._is_suspicious_url(application_url):
            score += 2.0
            reasons.append("Application URL looks suspicious or heavily shortened.")

        if source_url and application_url and self._domains_mismatch(source_url, application_url):
            score += 1.5
            reasons.append("Source URL and application URL point to different domains.")

        if self._title_description_mismatch(title_text, description_text):
            score += 1.5
            reasons.append("Listing title and description do not line up clearly.")

        if self._looks_unrealistic_for_internship(title_text, description_text, raw_payload):
            score += 3.0
            reasons.append("Compensation claims look unusually high for an intern or junior role.")

        return self._finalize(score, reasons)

    def analyze_event(
        self,
        *,
        title: str,
        description: str,
        organizer_name: str,
        location: str | None,
        meeting_url: str | None,
        mode: str,
    ) -> RiskAssessment:
        score = 0.0
        reasons: list[str] = []
        title_text = title.strip()
        organizer_text = organizer_name.strip().lower()
        description_text = description.strip()
        combined = " ".join(
            part for part in [title_text, description_text, organizer_name, location or "", meeting_url or ""] if part
        ).lower()

        if organizer_text in _VAGUE_ORGANIZERS:
            score += 2.5
            reasons.append("Organizer identity is too vague.")

        score += self._add_pattern_risk(
            combined,
            _PAYMENT_PATTERNS,
            weight=4.0,
            reason="Event mentions payment or money transfer requests.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _PERSONAL_CONTACT_PATTERNS,
            weight=2.5,
            reason="Event relies on personal messaging or non-official contact methods.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _URGENCY_PATTERNS,
            weight=1.5,
            reason="Event uses pressure or manipulation language.",
            reasons=reasons,
        )
        score += self._add_pattern_risk(
            combined,
            _SPAM_PATTERNS,
            weight=2.0,
            reason="Event description contains spam-like language.",
            reasons=reasons,
        )

        if meeting_url and self._is_suspicious_url(meeting_url):
            score += 2.5
            reasons.append("Meeting or signup link looks suspicious or heavily shortened.")

        if mode in {"virtual", "hybrid"} and self._title_description_mismatch(title_text, description_text):
            score += 1.0
            reasons.append("Event title and description do not line up clearly.")

        if location and location.strip().lower() in {"tbd", "to be decided", "coming soon"}:
            score += 1.5
            reasons.append("Event location is vague.")

        return self._finalize(score, reasons)

    def _add_pattern_risk(
        self,
        text: str,
        patterns: Iterable[str],
        *,
        weight: float,
        reason: str,
        reasons: list[str],
    ) -> float:
        if any(pattern in text for pattern in patterns):
            reasons.append(reason)
            return weight
        return 0.0

    def _domains_mismatch(self, source_url: str, application_url: str) -> bool:
        source_domain = self._domain(source_url)
        application_domain = self._domain(application_url)
        if not source_domain or not application_domain:
            return False
        return source_domain != application_domain

    def _domain(self, value: str) -> str:
        parsed = urlparse(value)
        return (parsed.netloc or "").lower().removeprefix("www.")

    def _is_suspicious_url(self, value: str) -> bool:
        domain = self._domain(value)
        return domain in _SHORTENER_DOMAINS or not domain

    def _title_description_mismatch(self, title: str, description: str) -> bool:
        title_tokens = self._meaningful_tokens(title)
        description_tokens = self._meaningful_tokens(description)
        if not title_tokens or not description_tokens:
            return False
        overlap = title_tokens & description_tokens
        return len(overlap) == 0 and len(title_tokens) >= 2

    def _looks_unrealistic_for_internship(
        self,
        title: str,
        description: str,
        raw_payload: dict[str, object] | None,
    ) -> bool:
        normalized_title = title.lower()
        normalized_description = description.lower()
        if not any(term in normalized_title for term in _INTERN_TERMS):
            return False

        salary_max = raw_payload.get("salary_max") if raw_payload else None
        if isinstance(salary_max, (int, float)) and salary_max >= 120000:
            return True

        if re.search(r"\$\s?\d{4,}\s*/\s*week", normalized_description):
            return True
        if re.search(r"\$\s?(1[2-9]\d{4,}|[2-9]\d{5,})", normalized_description):
            return True
        return False

    def _meaningful_tokens(self, value: str) -> set[str]:
        tokens = {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) >= 4}
        return {token for token in tokens if token not in {"remote", "event", "apply", "career"}}

    def _finalize(self, score: float, reasons: list[str]) -> RiskAssessment:
        deduped_reasons = list(dict.fromkeys(reasons))
        rounded_score = round(score, 1)
        if rounded_score >= 7.0:
            level = RISK_HIGH
        elif rounded_score >= 3.0:
            level = RISK_MEDIUM
        else:
            level = RISK_LOW
        return RiskAssessment(score=rounded_score, level=level, reasons=deduped_reasons)

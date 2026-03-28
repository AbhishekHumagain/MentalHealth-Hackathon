from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class ExternalInternshipRecord:
    external_id: str
    title: str
    company: str
    description: str
    location: str
    application_url: str
    source_url: str
    source_name: str
    majors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, object] | None = None


class ExternalInternshipProvider:
    async def fetch_internships(self, search_terms: list[str]) -> list[ExternalInternshipRecord]:
        raise NotImplementedError


class AdzunaInternshipProvider(ExternalInternshipProvider):
    BASE_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    SOURCE_NAME = "adzuna"

    def __init__(self) -> None:
        settings = get_settings()
        self._app_id = settings.adzuna_app_id
        self._app_key = settings.adzuna_app_key
        self._country = settings.adzuna_country or "us"
        missing = [
            name
            for name, value in [
                ("ADZUNA_APP_ID", self._app_id),
                ("ADZUNA_APP_KEY", self._app_key),
            ]
            if not value
        ]
        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(
                f"Missing Adzuna configuration: {missing_list}. "
                "Set these environment variables before syncing internships."
            )

    async def fetch_internships(self, search_terms: list[str]) -> list[ExternalInternshipRecord]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            jobs_by_id: dict[str, ExternalInternshipRecord] = {}
            for term in search_terms:
                response = await client.get(
                    self.BASE_URL_TEMPLATE.format(country=self._country),
                    params={
                        "app_id": self._app_id,
                        "app_key": self._app_key,
                        "what": term,
                        "results_per_page": 20,
                        "content-type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                for job in data.get("results", []):
                    title = str(job.get("title") or "")
                    category = str((job.get("category") or {}).get("label") or "")
                    job_type = " ".join(
                        filter(
                            None,
                            [
                                str(job.get("contract_time") or ""),
                                str(job.get("contract_type") or ""),
                            ],
                        )
                    )
                    majors = _infer_majors_from_term(term)
                    if not _is_relevant_match(
                        title=title,
                        category=category,
                        job_type=job_type,
                        search_term=term,
                        inferred_majors=majors,
                    ):
                        continue

                    external_id = str(job.get("id") or "")
                    if not external_id:
                        continue

                    keywords = _extract_keywords(
                        [
                            title,
                            category,
                            job_type,
                            term,
                        ]
                    )
                    job_url = str(job.get("redirect_url") or job.get("adref") or "")
                    jobs_by_id[external_id] = ExternalInternshipRecord(
                        external_id=external_id,
                        title=title,
                        company=str((job.get("company") or {}).get("display_name") or ""),
                        description=str(job.get("description") or ""),
                        location=str((job.get("location") or {}).get("display_name") or "Remote"),
                        application_url=job_url,
                        source_url=job_url,
                        source_name=self.SOURCE_NAME,
                        majors=majors,
                        keywords=keywords,
                        last_seen_at=datetime.now(timezone.utc),
                        raw_payload=job,
                    )
            return list(jobs_by_id.values())


def _infer_majors_from_term(term: str) -> list[str]:
    lowered = term.lower()
    if any(token in lowered for token in ["software", "backend", "frontend", "full stack", "web developer"]):
        return ["Computer Science"]
    if any(
        token in lowered
        for token in [
            "data science",
            "data analyst",
            "machine learning",
            "analytics",
            "business intelligence",
        ]
    ):
        return ["Data Science"]
    if any(token in lowered for token in ["information technology", "it support", "systems"]):
        return ["Information Technology"]
    if any(token in lowered for token in ["marketing", "digital marketing", "social media", "content marketing"]):
        return ["Marketing"]
    if any(token in lowered for token in ["accounting", "bookkeeping"]):
        return ["Accounting"]
    if any(token in lowered for token in ["tax", "tax analyst", "taxation"]):
        return ["Tax"]
    if any(token in lowered for token in ["finance", "audit", "investment"]):
        return ["Accounting"]
    if any(token in lowered for token in ["business", "operations", "management"]):
        return ["Business"]
    if any(token in lowered for token in ["civil", "construction"]):
        return ["Civil Engineering"]
    if any(token in lowered for token in ["electrical", "embedded", "hardware"]):
        return ["Electrical Engineering"]
    if any(token in lowered for token in ["mechanical", "manufacturing", "cad"]):
        return ["Mechanical Engineering"]
    if any(token in lowered for token in ["psychology", "research assistant", "mental health"]):
        return ["Psychology"]
    if any(token in lowered for token in ["public health", "healthcare", "health analyst", "clinical"]):
        return ["Health"]
    if any(token in lowered for token in ["design", "ui", "ux", "product design", "graphic"]):
        return ["Design"]
    return []


def _is_relevant_match(
    title: str,
    category: str,
    job_type: str,
    search_term: str = "",
    inferred_majors: list[str] | None = None,
) -> bool:
    normalized_title = title.lower()
    normalized_category = category.lower()
    normalized_job_type = job_type.lower()
    normalized_search_term = search_term.lower()
    inferred_majors = inferred_majors or []

    strong_signal = (
        "intern" in normalized_job_type
        or "intern" in normalized_title
        or "internship" in normalized_title
        or "intern" in normalized_category
    )
    if strong_signal:
        return True

    # For broader role-based searches, allow clearly entry-level titles.
    broad_search = "intern" not in normalized_search_term
    entry_level_signal = any(
        token in normalized_title
        for token in [
            "junior",
            "entry level",
            "entry-level",
            "graduate",
            "apprentice",
            "trainee",
        ]
    )
    if broad_search and entry_level_signal:
        return True

    # Final demo fallback: if the query was broad and the result clearly matches the
    # target role/category family, import it so we can verify the ingestion pipeline.
    family_tokens: list[str] = []
    for major in inferred_majors:
        normalized_major = major.lower()
        if normalized_major == "computer science":
            family_tokens.extend(["software", "developer", "engineering", "web"])
        elif normalized_major == "data science":
            family_tokens.extend(["data", "analytics", "machine learning", "business intelligence"])
        elif normalized_major == "information technology":
            family_tokens.extend(["it", "systems", "cloud", "support"])
        elif normalized_major == "business":
            family_tokens.extend(["business", "operations", "management"])
        elif normalized_major == "marketing":
            family_tokens.extend(["marketing", "brand", "content", "social media"])
        elif normalized_major == "accounting":
            family_tokens.extend(["accounting", "finance", "audit", "bookkeeping"])
        elif normalized_major == "tax":
            family_tokens.extend(["tax", "audit", "accounting"])
        elif normalized_major == "electrical engineering":
            family_tokens.extend(["electrical", "embedded", "hardware"])
        elif normalized_major == "civil engineering":
            family_tokens.extend(["civil", "construction", "site engineer"])
        elif normalized_major == "mechanical engineering":
            family_tokens.extend(["mechanical", "manufacturing", "cad"])
        elif normalized_major == "psychology":
            family_tokens.extend(["psychology", "research", "mental health", "human resources"])
        elif normalized_major == "health":
            family_tokens.extend(["health", "healthcare", "clinical", "public health"])
        elif normalized_major == "design":
            family_tokens.extend(["design", "ui", "ux", "graphic", "visual"])

    haystack = f"{normalized_title} {normalized_category}"
    return broad_search and any(token in haystack for token in family_tokens)


def _extract_keywords(values: list[object]) -> list[str]:
    keywords: set[str] = set()
    for value in values:
        if not value:
            continue
        for token in str(value).lower().replace("/", " ").replace("-", " ").split():
            token = token.strip(",.()")
            if len(token) >= 3:
                keywords.add(token)
    return sorted(keywords)

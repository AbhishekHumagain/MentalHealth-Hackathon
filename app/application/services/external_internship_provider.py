from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import httpx


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
    last_seen_at: datetime | None = None


class ExternalInternshipProvider:
    async def fetch_internships(self, search_terms: list[str]) -> list[ExternalInternshipRecord]:
        raise NotImplementedError


class RemotiveInternshipProvider(ExternalInternshipProvider):
    BASE_URL = "https://remotive.com/api/remote-jobs"
    SOURCE_NAME = "remotive"

    async def fetch_internships(self, search_terms: list[str]) -> list[ExternalInternshipRecord]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            jobs_by_id: dict[str, ExternalInternshipRecord] = {}
            for term in search_terms:
                response = await client.get(self.BASE_URL, params={"search": term})
                response.raise_for_status()
                data = response.json()

                for job in data.get("jobs", []):
                    category = str(job.get("category") or "")
                    candidate_text = " ".join(
                        [
                            str(job.get("title") or ""),
                            category,
                            str(job.get("candidate_required_location") or ""),
                        ]
                    ).lower()
                    if "intern" not in candidate_text:
                        continue

                    external_id = str(job.get("id"))
                    if not external_id:
                        continue

                    majors = _infer_majors_from_term(term)
                    keywords = _extract_keywords(
                        [
                            job.get("title"),
                            category,
                            job.get("job_type"),
                            term,
                        ]
                    )
                    jobs_by_id[external_id] = ExternalInternshipRecord(
                        external_id=external_id,
                        title=str(job.get("title") or ""),
                        company=str(job.get("company_name") or ""),
                        description=str(job.get("description") or ""),
                        location=str(job.get("candidate_required_location") or "Remote"),
                        application_url=str(job.get("url") or ""),
                        source_url=str(job.get("url") or ""),
                        source_name=self.SOURCE_NAME,
                        majors=majors,
                        keywords=keywords,
                        last_seen_at=datetime.utcnow(),
                    )
            return list(jobs_by_id.values())


def _infer_majors_from_term(term: str) -> list[str]:
    lowered = term.lower()
    if any(token in lowered for token in ["software", "backend", "data", "machine learning"]):
        return ["Computer Science"]
    if any(token in lowered for token in ["business", "operations", "marketing", "finance"]):
        return ["Business"]
    if any(token in lowered for token in ["electrical", "embedded", "hardware"]):
        return ["Electrical Engineering"]
    return []


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

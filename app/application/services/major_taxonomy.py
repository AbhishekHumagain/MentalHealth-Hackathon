from __future__ import annotations

from app.application.services.internship_matching import MAJOR_SYNONYMS


MAJOR_SEARCH_TERMS: dict[str, list[str]] = {
    "computer science": [
        "software engineer",
        "backend developer",
        "frontend developer",
        "full stack developer",
        "web developer",
    ],
    "data science": [
        "data science",
        "data analyst",
        "machine learning",
        "analytics",
        "business intelligence",
    ],
    "information technology": [
        "information technology",
        "it support",
        "systems administrator",
        "cloud support",
    ],
    "business": [
        "business analyst",
        "operations",
        "management trainee",
        "operations analyst",
    ],
    "marketing": [
        "marketing",
        "digital marketing",
        "content marketing",
        "social media",
    ],
    "accounting": [
        "accounting",
        "audit",
        "bookkeeping",
        "finance",
    ],
    "tax": [
        "tax",
        "tax analyst",
        "audit",
        "accounting",
    ],
    "electrical engineering": [
        "electrical engineering",
        "embedded systems",
        "hardware engineer",
    ],
    "civil engineering": [
        "civil engineering",
        "construction",
        "site engineer",
    ],
    "mechanical engineering": [
        "mechanical engineering",
        "manufacturing",
        "cad designer",
    ],
    "psychology": [
        "psychology",
        "research assistant",
        "mental health",
        "human resources",
    ],
    "health": [
        "public health",
        "healthcare",
        "health analyst",
        "clinical",
        "mental health",
    ],
    "design": [
        "ui ux",
        "product design",
        "graphic design",
        "visual design",
    ],
}


class MajorTaxonomyService:
    def supported_majors(self) -> list[str]:
        return sorted(MAJOR_SEARCH_TERMS.keys())

    def search_terms_for_major(self, major: str) -> list[str]:
        normalized = self._normalize(major)
        if normalized in MAJOR_SEARCH_TERMS:
            return MAJOR_SEARCH_TERMS[normalized]

        for canonical, aliases in MAJOR_SYNONYMS.items():
            if normalized == canonical or normalized in aliases:
                return MAJOR_SEARCH_TERMS.get(canonical, [f"{major} intern"])

        return [f"{major} intern"]

    def all_search_terms(self) -> dict[str, list[str]]:
        return {major: list(terms) for major, terms in MAJOR_SEARCH_TERMS.items()}

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().split())

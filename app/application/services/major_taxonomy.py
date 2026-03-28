from __future__ import annotations

from app.application.services.internship_matching import MAJOR_SYNONYMS


MAJOR_SEARCH_TERMS: dict[str, list[str]] = {
    "computer science": [
        "software engineer intern",
        "backend intern",
        "data intern",
        "machine learning intern",
    ],
    "business": [
        "business analyst intern",
        "operations intern",
        "marketing intern",
        "finance intern",
    ],
    "electrical engineering": [
        "electrical engineering intern",
        "embedded systems intern",
        "hardware intern",
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

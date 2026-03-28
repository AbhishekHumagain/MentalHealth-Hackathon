from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.domain.entities.internship import Internship
from app.domain.entities.student_profile import StudentProfile


MAJOR_SYNONYMS: dict[str, set[str]] = {
    "computer science": {"computer science", "software engineering", "informatics", "it"},
    "business": {"business", "business administration", "management", "commerce"},
    "electrical engineering": {"electrical engineering", "electronics engineering"},
}


@dataclass(frozen=True)
class MatchResult:
    internship: Internship
    score: float
    reason: str


class InternshipMatchingService:
    def score_profile(
        self,
        profile: StudentProfile,
        internships: list[Internship],
        target_date: date,
    ) -> list[MatchResult]:
        results: list[MatchResult] = []
        profile_major = self._normalize(profile.major)
        profile_tokens = self._profile_tokens(profile)

        for internship in internships:
            if not internship.is_available_on(target_date):
                continue

            score = 0.0
            reason = "Matched your interests and skills"

            if self._major_matches(profile_major, internship.majors):
                score += 10.0
                reason = f"Matched your major: {profile.major}"

            overlap = len(profile_tokens & self._internship_tokens(internship))
            if overlap:
                score += min(5.0, overlap * 1.5)
                if score < 10:
                    reason = "Matched your skills/interests keywords"

            if score <= 0:
                continue

            results.append(MatchResult(internship=internship, score=score, reason=reason))

        return sorted(results, key=lambda item: item.score, reverse=True)

    def _major_matches(self, normalized_major: str, internship_majors: list[str]) -> bool:
        if not normalized_major:
            return False
        internship_major_set = {self._normalize(item) for item in internship_majors}
        if normalized_major in internship_major_set:
            return True
        for canonical, aliases in MAJOR_SYNONYMS.items():
            if normalized_major == canonical or normalized_major in aliases:
                return bool(internship_major_set & ({canonical} | aliases))
        return False

    def _profile_tokens(self, profile: StudentProfile) -> set[str]:
        values = [profile.major, *profile.skills, *profile.interests, *profile.preferred_locations]
        return self._tokenize(values)

    def _internship_tokens(self, internship: Internship) -> set[str]:
        values = [
            internship.title,
            internship.company,
            internship.description,
            internship.location,
            *internship.majors,
            *internship.keywords,
        ]
        return self._tokenize(values)

    def _tokenize(self, values: list[str]) -> set[str]:
        tokens: set[str] = set()
        for value in values:
            for token in re.findall(r"[a-z0-9]+", value.lower()):
                if len(token) >= 3:
                    tokens.add(token)
        return tokens

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().split())

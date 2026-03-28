from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.domain.entities.Base import BaseModel

# ── Anonymous character pool ──────────────────────────────────────────────────

_CHARACTERS: list[str] = [
    "Pikachu", "Naruto", "Goku", "Luffy", "Spongebob", "Patrick",
    "Gandalf", "Frodo", "Hermione", "HarryPotter", "Batman", "Superman",
    "Spiderman", "IronMan", "Thor", "Hulk", "Deadpool", "Wolverine",
    "Yoda", "Dumbledore", "Sherlock", "Doraemon", "Totoro", "Simba",
    "Nemo", "Stitch", "Elsa", "Moana", "Shrek", "Woody", "BuzzLightyear",
    "Olaf", "Groot", "Rocket", "Thanos", "Loki", "WonderWoman", "Flash",
    "Aquaman", "BlackPanther", "Dory", "Timon", "Pumbaa", "Goofy",
    "Mickey", "Donald", "Baloo", "Mowgli", "Aladdin", "Mulan",
    "Rapunzel", "Ariel", "Belle", "Tarzan", "Hercules", "Merida",
    "WallE", "Remy", "LightningMcQueen", "FinnMertens", "JakeTheDog",
    "Marceline", "Dipper", "Mabel", "Hiro", "Baymax", "Wasabi",
    "StevenUniverse", "Garnet", "Amethyst", "CaptainAmerica", "Hawkeye",
    "BlackWidow", "Scarlet", "Vision", "Arlo", "Coco", "Miguel",
    "Zootopia", "Nick", "Judy", "Bluey", "Bingo", "Peppa", "Sonic",
    "Tails", "Knuckles", "MegaMan", "Kirby", "Link", "Zelda", "Mario",
    "Luigi", "Bowser", "Peach", "Yoshi", "Wario", "Donkey", "Diddy",
]


def generate_anonymous_name() -> str:
    """Return a random cartoon/fictional name with a 4-digit suffix, e.g. 'Pikachu#4821'."""
    character = random.choice(_CHARACTERS)
    number = random.randint(1000, 9999)
    return f"{character}#{number}"


# ── Report status ─────────────────────────────────────────────────────────────

ReportStatus = Literal["pending", "resolved", "dismissed"]
PostCategory = Literal["general", "internship", "housing", "academics", "career", "events", "other"]


# ── Domain Entities ───────────────────────────────────────────────────────────

@dataclass
class ForumPost(BaseModel):
    author_id: str = ""                      # Keycloak sub
    author_display_name: str = ""            # Real name shown when not anonymous
    is_anonymous: bool = False
    anonymous_name: str = ""                 # e.g. "Pikachu#4821"
    title: str = ""
    content: str = ""
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    likes_count: int = 0
    comments_count: int = 0

    # ── Business rules ──────────────────────────────────────────────────────

    @property
    def display_name(self) -> str:
        """Name visible to readers — anonymous_name when posted anonymously."""
        return self.anonymous_name if self.is_anonymous else self.author_display_name

    def update_content(
        self,
        title: str | None,
        content: str | None,
        category: str | None,
        tags: list[str] | None,
        user_id: str | None = None,
    ) -> None:
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if category is not None:
            self.category = category
        if tags is not None:
            self.tags = tags
        self.mark_modified(user_id)

    def increment_likes(self) -> None:
        self.likes_count += 1

    def decrement_likes(self) -> None:
        self.likes_count = max(0, self.likes_count - 1)

    def increment_comments(self) -> None:
        self.comments_count += 1

    def decrement_comments(self) -> None:
        self.comments_count = max(0, self.comments_count - 1)


@dataclass
class ForumComment(BaseModel):
    post_id: str = ""
    author_id: str = ""
    author_display_name: str = ""
    is_anonymous: bool = False
    anonymous_name: str = ""
    content: str = ""

    @property
    def display_name(self) -> str:
        return self.anonymous_name if self.is_anonymous else self.author_display_name

    def update_content(self, content: str, user_id: str | None = None) -> None:
        self.content = content
        self.mark_modified(user_id)


@dataclass
class ForumLike:
    """Tracks which user liked which post (no BaseModel — no audit fields needed)."""
    id: str = field(default_factory=lambda: __import__("uuid").uuid4().__str__())
    post_id: str = ""
    user_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ForumReport(BaseModel):
    post_id: str = ""
    reporter_id: str = ""
    reason: str = ""
    status: str = "pending"          # pending | resolved | dismissed
    admin_note: str = ""
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    def resolve(self, admin_id: str, note: str = "") -> None:
        self.status = "resolved"
        self.admin_note = note
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = admin_id
        self.mark_modified(admin_id)

    def dismiss(self, admin_id: str, note: str = "") -> None:
        self.status = "dismissed"
        self.admin_note = note
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = admin_id
        self.mark_modified(admin_id)

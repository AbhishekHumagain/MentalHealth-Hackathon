from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# ── Post DTOs ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CreateForumPostDTO:
    author_id: str
    author_display_name: str
    title: str
    content: str
    is_anonymous: bool = False
    category: str = "general"
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateForumPostDTO:
    post_id: str
    requesting_user_id: str
    requesting_user_roles: list[str]
    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: list[str] | None = None


@dataclass(frozen=True)
class DeleteForumPostDTO:
    post_id: str
    requesting_user_id: str
    requesting_user_roles: list[str]


@dataclass
class ForumPostResponseDTO:
    id: str
    display_name: str               # real name or anonymous_name
    is_anonymous: bool
    title: str
    content: str
    category: str
    tags: list[str]
    likes_count: int
    comments_count: int
    created_at: datetime
    modified_at: datetime
    # enriched fields (set after creation)
    is_liked_by_me: bool = False
    report_count: int = 0
    # only visible to the requesting user themselves or admin
    author_id: str | None = None


# ── Comment DTOs ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CreateForumCommentDTO:
    post_id: str
    author_id: str
    author_display_name: str
    content: str
    is_anonymous: bool = False


@dataclass(frozen=True)
class DeleteForumCommentDTO:
    comment_id: str
    requesting_user_id: str
    requesting_user_roles: list[str]


@dataclass
class ForumCommentResponseDTO:
    id: str
    post_id: str
    display_name: str
    is_anonymous: bool
    content: str
    created_at: datetime
    modified_at: datetime
    author_id: str | None = None


# ── Like DTOs ─────────────────────────────────────────────────────────────────

@dataclass
class LikeToggleResponseDTO:
    post_id: str
    liked: bool
    likes_count: int


# ── Report DTOs ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CreateForumReportDTO:
    post_id: str
    reporter_id: str
    reason: str


@dataclass(frozen=True)
class ResolveForumReportDTO:
    report_id: str
    admin_id: str
    action: str        # "resolve" or "dismiss"
    note: str = ""


@dataclass
class ForumReportResponseDTO:
    id: str
    post_id: str
    post_title: str
    reporter_id: str
    reason: str
    status: str
    admin_note: str
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminUser, CurrentUser
from app.application.dto.forum_dto import (
    CreateForumCommentDTO,
    CreateForumPostDTO,
    CreateForumReportDTO,
    DeleteForumCommentDTO,
    DeleteForumPostDTO,
    ResolveForumReportDTO,
    UpdateForumPostDTO,
)
from app.application.use_cases.forum_use_cases import (
    CreateForumCommentUseCase,
    CreateForumPostUseCase,
    DeleteForumCommentUseCase,
    DeleteForumPostUseCase,
    GetForumPostUseCase,
    ListForumCommentsUseCase,
    ListForumPostsUseCase,
    ListForumReportsUseCase,
    ReportForumPostUseCase,
    ResolveForumReportUseCase,
    ToggleLikeUseCase,
)
from app.domain.exceptions.forum_exceptions import (
    ForumAlreadyReportedError,
    ForumCommentNotFoundError,
    ForumPermissionError,
    ForumPostNotFoundError,
    ForumReportNotFoundError,
)
from app.infrastructure.database.repositories.forum_repository_impl import (
    SQLAlchemyForumCommentRepository,
    SQLAlchemyForumLikeRepository,
    SQLAlchemyForumPostRepository,
    SQLAlchemyForumReportRepository,
)
from app.infrastructure.database.session import get_async_session
from app.infrastructure.keycloak.jwt_validator import TokenClaims

router = APIRouter(prefix="/forum", tags=["Forum"])

# ── Request / Response Schemas ────────────────────────────────────────────────

VALID_CATEGORIES = {"general", "internship", "housing", "academics", "career", "events", "other"}


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    is_anonymous: bool = False
    category: str = Field("general")
    tags: list[str] = Field(default_factory=list, max_length=10)

    def model_post_init(self, __context) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")


class UpdatePostRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1, max_length=10000)
    category: str | None = None
    tags: list[str] | None = None


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_anonymous: bool = False


class ReportPostRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000)


class ResolveReportRequest(BaseModel):
    action: str = Field(..., pattern="^(resolve|dismiss)$")
    note: str = Field("", max_length=1000)


class PostResponse(BaseModel):
    id: str
    display_name: str
    is_anonymous: bool
    title: str
    content: str
    category: str
    tags: list[str]
    likes_count: int
    comments_count: int
    created_at: datetime
    modified_at: datetime
    is_liked_by_me: bool
    report_count: int
    author_id: str | None

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    skip: int
    limit: int


class CommentResponse(BaseModel):
    id: str
    post_id: str
    display_name: str
    is_anonymous: bool
    content: str
    created_at: datetime
    modified_at: datetime
    author_id: str | None

    model_config = {"from_attributes": True}


class LikeResponse(BaseModel):
    post_id: str
    liked: bool
    likes_count: int


class ReportResponse(BaseModel):
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

    model_config = {"from_attributes": True}


# ── Dependencies ──────────────────────────────────────────────────────────────

DbSession = Annotated[AsyncSession, Depends(get_async_session)]


def _repos(session: DbSession):
    return (
        SQLAlchemyForumPostRepository(session),
        SQLAlchemyForumCommentRepository(session),
        SQLAlchemyForumLikeRepository(session),
        SQLAlchemyForumReportRepository(session),
    )


def _display_name(claims: TokenClaims) -> str:
    parts = [claims.first_name or "", claims.last_name or ""]
    full = " ".join(p for p in parts if p).strip()
    return full or claims.email or claims.sub


# ── Post Endpoints ────────────────────────────────────────────────────────────

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: CreatePostRequest,
    claims: CurrentUser,
    session: DbSession,
):
    """Any authenticated user can create a forum post."""
    post_repo, _, _, _ = _repos(session)
    dto = CreateForumPostDTO(
        author_id=claims.sub,
        author_display_name=_display_name(claims),
        title=body.title,
        content=body.content,
        is_anonymous=body.is_anonymous,
        category=body.category,
        tags=body.tags,
    )
    result = await CreateForumPostUseCase(post_repo).execute(dto)
    return PostResponse(**result.__dict__)


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    claims: CurrentUser,
    session: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
):
    """List all forum posts — visible to everyone."""
    post_repo, _, like_repo, _ = _repos(session)
    posts, total = await ListForumPostsUseCase(post_repo, like_repo).execute(
        requesting_user_id=claims.sub,
        skip=skip,
        limit=limit,
        category=category,
    )
    return PostListResponse(
        items=[PostResponse(**p.__dict__) for p in posts],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    claims: CurrentUser,
    session: DbSession,
):
    """Get a single forum post with like/report metadata."""
    post_repo, _, like_repo, report_repo = _repos(session)
    is_admin = "admin" in claims.roles
    try:
        result = await GetForumPostUseCase(post_repo, like_repo, report_repo).execute(
            post_id=post_id,
            requesting_user_id=claims.sub,
            is_admin=is_admin,
        )
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PostResponse(**result.__dict__)


@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    body: UpdatePostRequest,
    claims: CurrentUser,
    session: DbSession,
):
    """Author (or admin) can edit a post."""
    post_repo, _, _, _ = _repos(session)
    dto = UpdateForumPostDTO(
        post_id=post_id,
        requesting_user_id=claims.sub,
        requesting_user_roles=list(claims.roles),
        title=body.title,
        content=body.content,
        category=body.category,
        tags=body.tags,
    )
    try:
        result = await UpdateForumPostUseCase(post_repo).execute(dto)
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ForumPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return PostResponse(**result.__dict__)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    claims: CurrentUser,
    session: DbSession,
):
    """Author or admin can delete a post (also deletes all its comments, likes, reports)."""
    post_repo, _, _, report_repo = _repos(session)
    dto = DeleteForumPostDTO(
        post_id=post_id,
        requesting_user_id=claims.sub,
        requesting_user_roles=list(claims.roles),
    )
    try:
        await DeleteForumPostUseCase(post_repo, report_repo).execute(dto)
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ForumPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


# ── Comment Endpoints ─────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    body: CreateCommentRequest,
    claims: CurrentUser,
    session: DbSession,
):
    """Any authenticated user can comment on a post."""
    post_repo, comment_repo, _, _ = _repos(session)
    dto = CreateForumCommentDTO(
        post_id=post_id,
        author_id=claims.sub,
        author_display_name=_display_name(claims),
        content=body.content,
        is_anonymous=body.is_anonymous,
    )
    try:
        result = await CreateForumCommentUseCase(post_repo, comment_repo).execute(dto)
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return CommentResponse(**result.__dict__)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    post_id: str,
    claims: CurrentUser,
    session: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List all comments for a post."""
    post_repo, comment_repo, _, _ = _repos(session)
    try:
        results = await ListForumCommentsUseCase(post_repo, comment_repo).execute(
            post_id=post_id,
            requesting_user_id=claims.sub,
            skip=skip,
            limit=limit,
        )
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [CommentResponse(**c.__dict__) for c in results]


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    post_id: str,
    comment_id: str,
    claims: CurrentUser,
    session: DbSession,
):
    """Author or admin can delete a comment."""
    post_repo, comment_repo, _, _ = _repos(session)
    dto = DeleteForumCommentDTO(
        comment_id=comment_id,
        requesting_user_id=claims.sub,
        requesting_user_roles=list(claims.roles),
    )
    try:
        await DeleteForumCommentUseCase(post_repo, comment_repo).execute(dto)
    except ForumCommentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ForumPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


# ── Like Endpoints ────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def toggle_like(
    post_id: str,
    claims: CurrentUser,
    session: DbSession,
):
    """Toggle like on a post. Calling again removes the like."""
    post_repo, _, like_repo, _ = _repos(session)
    try:
        result = await ToggleLikeUseCase(post_repo, like_repo).execute(
            post_id=post_id,
            user_id=claims.sub,
        )
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return LikeResponse(**result.__dict__)


# ── Report Endpoints ──────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report_post(
    post_id: str,
    body: ReportPostRequest,
    claims: CurrentUser,
    session: DbSession,
):
    """Report a post for inappropriate content."""
    post_repo, _, _, report_repo = _repos(session)
    dto = CreateForumReportDTO(
        post_id=post_id,
        reporter_id=claims.sub,
        reason=body.reason,
    )
    try:
        result = await ReportForumPostUseCase(post_repo, report_repo).execute(dto)
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ForumAlreadyReportedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ReportResponse(**result.__dict__)


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(
    claims: AdminUser,
    session: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(pending|resolved|dismissed)$"),
):
    """Admin only — list all reports, optionally filtered by status."""
    post_repo, _, _, report_repo = _repos(session)
    results = await ListForumReportsUseCase(post_repo, report_repo).execute(
        skip=skip,
        limit=limit,
        status=status,
    )
    return [ReportResponse(**r.__dict__) for r in results]


@router.post("/reports/{report_id}/resolve", response_model=ReportResponse)
async def resolve_report(
    report_id: str,
    body: ResolveReportRequest,
    claims: AdminUser,
    session: DbSession,
):
    """Admin only — resolve or dismiss a report."""
    post_repo, _, _, report_repo = _repos(session)
    dto = ResolveForumReportDTO(
        report_id=report_id,
        admin_id=claims.sub,
        action=body.action,
        note=body.note,
    )
    try:
        result = await ResolveForumReportUseCase(post_repo, report_repo).execute(dto)
    except ForumReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ReportResponse(**result.__dict__)

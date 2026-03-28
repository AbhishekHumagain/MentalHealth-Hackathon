from __future__ import annotations

from app.application.dto.forum_dto import (
    CreateForumCommentDTO,
    CreateForumPostDTO,
    CreateForumReportDTO,
    DeleteForumCommentDTO,
    DeleteForumPostDTO,
    ForumCommentResponseDTO,
    ForumPostResponseDTO,
    ForumReportResponseDTO,
    LikeToggleResponseDTO,
    ResolveForumReportDTO,
    UpdateForumPostDTO,
)
from app.domain.entities.forum import ForumComment, ForumLike, ForumPost, ForumReport, generate_anonymous_name
from app.domain.exceptions.forum_exceptions import (
    ForumAlreadyReportedError,
    ForumCommentNotFoundError,
    ForumPermissionError,
    ForumPostNotFoundError,
    ForumReportNotFoundError,
)
from app.domain.repositories.forum_repository import (
    ForumCommentRepository,
    ForumLikeRepository,
    ForumPostRepository,
    ForumReportRepository,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post_to_dto(post: ForumPost, *, author_id_visible: bool = False) -> ForumPostResponseDTO:
    return ForumPostResponseDTO(
        id=post.id,
        display_name=post.display_name,
        is_anonymous=post.is_anonymous,
        title=post.title,
        content=post.content,
        category=post.category,
        tags=post.tags,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        created_at=post.created_at,
        modified_at=post.modified_at,
        author_id=post.author_id if author_id_visible else None,
    )


def _comment_to_dto(comment: ForumComment, *, author_id_visible: bool = False) -> ForumCommentResponseDTO:
    return ForumCommentResponseDTO(
        id=comment.id,
        post_id=comment.post_id,
        display_name=comment.display_name,
        is_anonymous=comment.is_anonymous,
        content=comment.content,
        created_at=comment.created_at,
        modified_at=comment.modified_at,
        author_id=comment.author_id if author_id_visible else None,
    )


def _report_to_dto(report: ForumReport, post_title: str = "") -> ForumReportResponseDTO:
    return ForumReportResponseDTO(
        id=report.id,
        post_id=report.post_id,
        post_title=post_title,
        reporter_id=report.reporter_id,
        reason=report.reason,
        status=report.status,
        admin_note=report.admin_note,
        created_at=report.created_at,
        resolved_at=report.resolved_at,
        resolved_by=report.resolved_by,
    )


# ── Post Use Cases ────────────────────────────────────────────────────────────

class CreateForumPostUseCase:
    def __init__(self, post_repo: ForumPostRepository) -> None:
        self._repo = post_repo

    async def execute(self, dto: CreateForumPostDTO) -> ForumPostResponseDTO:
        anon_name = generate_anonymous_name() if dto.is_anonymous else ""
        post = ForumPost(
            author_id=dto.author_id,
            author_display_name=dto.author_display_name,
            is_anonymous=dto.is_anonymous,
            anonymous_name=anon_name,
            title=dto.title,
            content=dto.content,
            category=dto.category,
            tags=list(dto.tags),
            created_by=dto.author_id,
        )
        saved = await self._repo.create(post)
        return _post_to_dto(saved, author_id_visible=True)


class ListForumPostsUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        like_repo: ForumLikeRepository,
    ) -> None:
        self._posts = post_repo
        self._likes = like_repo

    async def execute(
        self,
        requesting_user_id: str,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
    ) -> tuple[list[ForumPostResponseDTO], int]:
        posts = await self._posts.list_all(skip=skip, limit=limit, category=category)
        total = await self._posts.count_all(category=category)

        post_ids = [p.id for p in posts]
        liked_ids = set(await self._likes.get_liked_post_ids(requesting_user_id, post_ids))

        dtos: list[ForumPostResponseDTO] = []
        for post in posts:
            dto = _post_to_dto(post, author_id_visible=(post.author_id == requesting_user_id))
            dto.is_liked_by_me = post.id in liked_ids
            dtos.append(dto)

        return dtos, total


class GetForumPostUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        like_repo: ForumLikeRepository,
        report_repo: ForumReportRepository,
    ) -> None:
        self._posts = post_repo
        self._likes = like_repo
        self._reports = report_repo

    async def execute(
        self,
        post_id: str,
        requesting_user_id: str,
        is_admin: bool = False,
    ) -> ForumPostResponseDTO:
        post = await self._posts.get_by_id(post_id)
        if post is None:
            raise ForumPostNotFoundError(post_id)

        like = await self._likes.get(post_id, requesting_user_id)
        report_count = await self._reports.count_pending_by_post(post_id)

        author_id_visible = is_admin or (post.author_id == requesting_user_id)
        dto = _post_to_dto(post, author_id_visible=author_id_visible)
        dto.is_liked_by_me = like is not None
        dto.report_count = report_count if is_admin else 0
        return dto


class UpdateForumPostUseCase:
    def __init__(self, post_repo: ForumPostRepository) -> None:
        self._repo = post_repo

    async def execute(self, dto: UpdateForumPostDTO) -> ForumPostResponseDTO:
        post = await self._repo.get_by_id(dto.post_id)
        if post is None:
            raise ForumPostNotFoundError(dto.post_id)

        is_admin = "admin" in dto.requesting_user_roles
        is_author = post.author_id == dto.requesting_user_id
        if not (is_author or is_admin):
            raise ForumPermissionError("Only the author can edit their post.")

        post.update_content(
            title=dto.title,
            content=dto.content,
            category=dto.category,
            tags=dto.tags,
            user_id=dto.requesting_user_id,
        )
        updated = await self._repo.update(post)
        return _post_to_dto(updated, author_id_visible=True)


class DeleteForumPostUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        report_repo: ForumReportRepository,
    ) -> None:
        self._posts = post_repo
        self._reports = report_repo

    async def execute(self, dto: DeleteForumPostDTO) -> None:
        post = await self._posts.get_by_id(dto.post_id)
        if post is None:
            raise ForumPostNotFoundError(dto.post_id)

        is_admin = "admin" in dto.requesting_user_roles
        is_author = post.author_id == dto.requesting_user_id
        if not (is_author or is_admin):
            raise ForumPermissionError("Only the author or an admin can delete this post.")

        await self._posts.delete(dto.post_id)


# ── Comment Use Cases ─────────────────────────────────────────────────────────

class CreateForumCommentUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        comment_repo: ForumCommentRepository,
    ) -> None:
        self._posts = post_repo
        self._comments = comment_repo

    async def execute(self, dto: CreateForumCommentDTO) -> ForumCommentResponseDTO:
        post = await self._posts.get_by_id(dto.post_id)
        if post is None:
            raise ForumPostNotFoundError(dto.post_id)

        anon_name = generate_anonymous_name() if dto.is_anonymous else ""
        comment = ForumComment(
            post_id=dto.post_id,
            author_id=dto.author_id,
            author_display_name=dto.author_display_name,
            is_anonymous=dto.is_anonymous,
            anonymous_name=anon_name,
            content=dto.content,
            created_by=dto.author_id,
        )
        saved = await self._comments.create(comment)

        # Update denormalized counter on the post
        post.increment_comments()
        await self._posts.update(post)

        return _comment_to_dto(saved, author_id_visible=True)


class ListForumCommentsUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        comment_repo: ForumCommentRepository,
    ) -> None:
        self._posts = post_repo
        self._comments = comment_repo

    async def execute(
        self,
        post_id: str,
        requesting_user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ForumCommentResponseDTO]:
        post = await self._posts.get_by_id(post_id)
        if post is None:
            raise ForumPostNotFoundError(post_id)

        comments = await self._comments.list_by_post(post_id, skip=skip, limit=limit)
        return [
            _comment_to_dto(c, author_id_visible=(c.author_id == requesting_user_id))
            for c in comments
        ]


class DeleteForumCommentUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        comment_repo: ForumCommentRepository,
    ) -> None:
        self._posts = post_repo
        self._comments = comment_repo

    async def execute(self, dto: DeleteForumCommentDTO) -> None:
        comment = await self._comments.get_by_id(dto.comment_id)
        if comment is None:
            raise ForumCommentNotFoundError(dto.comment_id)

        is_admin = "admin" in dto.requesting_user_roles
        is_author = comment.author_id == dto.requesting_user_id
        if not (is_author or is_admin):
            raise ForumPermissionError("Only the author or an admin can delete this comment.")

        await self._comments.delete(dto.comment_id)

        # Update denormalized counter on the post
        post = await self._posts.get_by_id(comment.post_id)
        if post:
            post.decrement_comments()
            await self._posts.update(post)


# ── Like Use Cases ────────────────────────────────────────────────────────────

class ToggleLikeUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        like_repo: ForumLikeRepository,
    ) -> None:
        self._posts = post_repo
        self._likes = like_repo

    async def execute(self, post_id: str, user_id: str) -> LikeToggleResponseDTO:
        post = await self._posts.get_by_id(post_id)
        if post is None:
            raise ForumPostNotFoundError(post_id)

        existing = await self._likes.get(post_id, user_id)
        if existing:
            # Unlike
            await self._likes.delete(post_id, user_id)
            post.decrement_likes()
            liked = False
        else:
            # Like
            like = ForumLike(post_id=post_id, user_id=user_id)
            await self._likes.create(like)
            post.increment_likes()
            liked = True

        updated = await self._posts.update(post)
        return LikeToggleResponseDTO(
            post_id=post_id,
            liked=liked,
            likes_count=updated.likes_count,
        )


# ── Report Use Cases ──────────────────────────────────────────────────────────

class ReportForumPostUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        report_repo: ForumReportRepository,
    ) -> None:
        self._posts = post_repo
        self._reports = report_repo

    async def execute(self, dto: CreateForumReportDTO) -> ForumReportResponseDTO:
        post = await self._posts.get_by_id(dto.post_id)
        if post is None:
            raise ForumPostNotFoundError(dto.post_id)

        # Prevent duplicate reports from same user
        existing = await self._reports.get_by_post_and_reporter(dto.post_id, dto.reporter_id)
        if existing and existing.status == "pending":
            raise ForumAlreadyReportedError(dto.post_id)

        report = ForumReport(
            post_id=dto.post_id,
            reporter_id=dto.reporter_id,
            reason=dto.reason,
            created_by=dto.reporter_id,
        )
        saved = await self._reports.create(report)
        return _report_to_dto(saved, post_title=post.title)


class ListForumReportsUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        report_repo: ForumReportRepository,
    ) -> None:
        self._posts = post_repo
        self._reports = report_repo

    async def execute(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[ForumReportResponseDTO]:
        reports = await self._reports.list_all(skip=skip, limit=limit, status=status)
        result = []
        for report in reports:
            post = await self._posts.get_by_id(report.post_id)
            post_title = post.title if post else "[deleted]"
            result.append(_report_to_dto(report, post_title=post_title))
        return result


class ResolveForumReportUseCase:
    def __init__(
        self,
        post_repo: ForumPostRepository,
        report_repo: ForumReportRepository,
    ) -> None:
        self._posts = post_repo
        self._reports = report_repo

    async def execute(self, dto: ResolveForumReportDTO) -> ForumReportResponseDTO:
        report = await self._reports.get_by_id(dto.report_id)
        if report is None:
            raise ForumReportNotFoundError(dto.report_id)

        if dto.action == "resolve":
            report.resolve(dto.admin_id, dto.note)
        else:
            report.dismiss(dto.admin_id, dto.note)

        updated = await self._reports.update(report)
        post = await self._posts.get_by_id(updated.post_id)
        post_title = post.title if post else "[deleted]"
        return _report_to_dto(updated, post_title=post_title)

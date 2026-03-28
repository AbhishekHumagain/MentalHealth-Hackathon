from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.forum import ForumComment, ForumLike, ForumPost, ForumReport
from app.domain.repositories.forum_repository import (
    ForumCommentRepository,
    ForumLikeRepository,
    ForumPostRepository,
    ForumReportRepository,
)
from app.infrastructure.database.models.forum_model import (
    ForumCommentModel,
    ForumLikeModel,
    ForumPostModel,
    ForumReportModel,
)


# ── Post Repository ───────────────────────────────────────────────────────────

class SQLAlchemyForumPostRepository(ForumPostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, post: ForumPost) -> ForumPost:
        model = ForumPostModel.from_entity(post)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, post_id: str) -> ForumPost | None:
        model = await self._fetch_post(post_id)
        return model.to_entity() if model else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
    ) -> list[ForumPost]:
        stmt = (
            select(ForumPostModel)
            .where(ForumPostModel.is_deleted == False)  # noqa: E712
            .order_by(ForumPostModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if category:
            stmt = stmt.where(ForumPostModel.category == category)
        result = await self._session.execute(stmt)
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, post: ForumPost) -> ForumPost:
        model = await self._fetch_post(post.id)
        if model is None:
            raise ValueError(f"Forum post '{post.id}' not found.")
        model.apply_entity(post)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def delete(self, post_id: str) -> bool:
        model = await self._fetch_post(post_id)
        if model is None:
            return False
        # Hard delete — cascade removes comments, likes, reports
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count_all(self, category: str | None = None) -> int:
        stmt = select(func.count()).select_from(ForumPostModel).where(
            ForumPostModel.is_deleted == False  # noqa: E712
        )
        if category:
            stmt = stmt.where(ForumPostModel.category == category)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _fetch_post(self, post_id: str) -> ForumPostModel | None:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ForumPostModel).where(ForumPostModel.id == uid)
        )
        return result.scalar_one_or_none()


# ── Comment Repository ────────────────────────────────────────────────────────

class SQLAlchemyForumCommentRepository(ForumCommentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, comment: ForumComment) -> ForumComment:
        model = ForumCommentModel.from_entity(comment)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, comment_id: str) -> ForumComment | None:
        model = await self._fetch_comment(comment_id)
        return model.to_entity() if model else None

    async def list_by_post(
        self,
        post_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ForumComment]:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return []
        result = await self._session.execute(
            select(ForumCommentModel)
            .where(ForumCommentModel.post_id == uid)
            .where(ForumCommentModel.is_deleted == False)  # noqa: E712
            .order_by(ForumCommentModel.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, comment: ForumComment) -> ForumComment:
        model = await self._fetch_comment(comment.id)
        if model is None:
            raise ValueError(f"Forum comment '{comment.id}' not found.")
        model.apply_entity(comment)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def delete(self, comment_id: str) -> bool:
        model = await self._fetch_comment(comment_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count_by_post(self, post_id: str) -> int:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return 0
        result = await self._session.execute(
            select(func.count()).select_from(ForumCommentModel).where(
                ForumCommentModel.post_id == uid,
                ForumCommentModel.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def _fetch_comment(self, comment_id: str) -> ForumCommentModel | None:
        try:
            uid = uuid.UUID(comment_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ForumCommentModel).where(ForumCommentModel.id == uid)
        )
        return result.scalar_one_or_none()


# ── Like Repository ───────────────────────────────────────────────────────────

class SQLAlchemyForumLikeRepository(ForumLikeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, like: ForumLike) -> ForumLike:
        model = ForumLikeModel.from_entity(like)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get(self, post_id: str, user_id: str) -> ForumLike | None:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ForumLikeModel).where(
                ForumLikeModel.post_id == uid,
                ForumLikeModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def delete(self, post_id: str, user_id: str) -> bool:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return False
        result = await self._session.execute(
            select(ForumLikeModel).where(
                ForumLikeModel.post_id == uid,
                ForumLikeModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def get_liked_post_ids(self, user_id: str, post_ids: list[str]) -> list[str]:
        if not post_ids:
            return []
        uids = []
        for pid in post_ids:
            try:
                uids.append(uuid.UUID(pid))
            except ValueError:
                pass
        if not uids:
            return []
        result = await self._session.execute(
            select(ForumLikeModel.post_id).where(
                ForumLikeModel.user_id == user_id,
                ForumLikeModel.post_id.in_(uids),
            )
        )
        return [str(row) for row in result.scalars().all()]


# ── Report Repository ─────────────────────────────────────────────────────────

class SQLAlchemyForumReportRepository(ForumReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, report: ForumReport) -> ForumReport:
        model = ForumReportModel.from_entity(report)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, report_id: str) -> ForumReport | None:
        model = await self._fetch_report(report_id)
        return model.to_entity() if model else None

    async def get_by_post_and_reporter(
        self, post_id: str, reporter_id: str
    ) -> ForumReport | None:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ForumReportModel).where(
                ForumReportModel.post_id == uid,
                ForumReportModel.reporter_id == reporter_id,
            ).order_by(ForumReportModel.created_at.desc())
        )
        model = result.scalars().first()
        return model.to_entity() if model else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[ForumReport]:
        stmt = (
            select(ForumReportModel)
            .order_by(ForumReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(ForumReportModel.status == status)
        result = await self._session.execute(stmt)
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, report: ForumReport) -> ForumReport:
        model = await self._fetch_report(report.id)
        if model is None:
            raise ValueError(f"Forum report '{report.id}' not found.")
        model.apply_entity(report)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_entity()

    async def count_pending_by_post(self, post_id: str) -> int:
        try:
            uid = uuid.UUID(post_id)
        except ValueError:
            return 0
        result = await self._session.execute(
            select(func.count()).select_from(ForumReportModel).where(
                ForumReportModel.post_id == uid,
                ForumReportModel.status == "pending",
            )
        )
        return result.scalar_one()

    async def _fetch_report(self, report_id: str) -> ForumReportModel | None:
        try:
            uid = uuid.UUID(report_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ForumReportModel).where(ForumReportModel.id == uid)
        )
        return result.scalar_one_or_none()

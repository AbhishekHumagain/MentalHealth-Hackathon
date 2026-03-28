from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.forum import ForumComment, ForumLike, ForumPost, ForumReport
from app.infrastructure.database.base import Base


class ForumPostModel(Base):
    __tablename__ = "forum_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    author_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    anonymous_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general", index=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    comments: Mapped[list[ForumCommentModel]] = relationship(
        "ForumCommentModel", back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list[ForumLikeModel]] = relationship(
        "ForumLikeModel", back_populates="post", cascade="all, delete-orphan"
    )
    reports: Mapped[list[ForumReportModel]] = relationship(
        "ForumReportModel", back_populates="post", cascade="all, delete-orphan"
    )

    # ── Mappers ────────────────────────────────────────────────────────────────

    @classmethod
    def from_entity(cls, entity: ForumPost) -> "ForumPostModel":
        return cls(
            id=uuid.UUID(entity.id),
            author_id=entity.author_id,
            author_display_name=entity.author_display_name,
            is_anonymous=entity.is_anonymous,
            anonymous_name=entity.anonymous_name,
            title=entity.title,
            content=entity.content,
            category=entity.category,
            tags=list(entity.tags),
            likes_count=entity.likes_count,
            comments_count=entity.comments_count,
            is_deleted=entity.is_deleted,
            created_at=entity.created_at,
            created_by=entity.created_by,
            modified_at=entity.modified_at,
            modified_by=entity.modified_by,
        )

    def to_entity(self) -> ForumPost:
        return ForumPost(
            id=str(self.id),
            author_id=self.author_id,
            author_display_name=self.author_display_name,
            is_anonymous=self.is_anonymous,
            anonymous_name=self.anonymous_name,
            title=self.title,
            content=self.content,
            category=self.category,
            tags=list(self.tags or []),
            likes_count=self.likes_count,
            comments_count=self.comments_count,
            is_deleted=self.is_deleted,
            created_at=self.created_at,
            created_by=self.created_by,
            modified_at=self.modified_at,
            modified_by=self.modified_by,
        )

    def apply_entity(self, entity: ForumPost) -> None:
        self.title = entity.title
        self.content = entity.content
        self.category = entity.category
        self.tags = list(entity.tags)
        self.likes_count = entity.likes_count
        self.comments_count = entity.comments_count
        self.is_deleted = entity.is_deleted
        self.modified_at = entity.modified_at
        self.modified_by = entity.modified_by


class ForumCommentModel(Base):
    __tablename__ = "forum_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    anonymous_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    post: Mapped[ForumPostModel] = relationship("ForumPostModel", back_populates="comments")

    @classmethod
    def from_entity(cls, entity: ForumComment) -> "ForumCommentModel":
        return cls(
            id=uuid.UUID(entity.id),
            post_id=uuid.UUID(entity.post_id),
            author_id=entity.author_id,
            author_display_name=entity.author_display_name,
            is_anonymous=entity.is_anonymous,
            anonymous_name=entity.anonymous_name,
            content=entity.content,
            is_deleted=entity.is_deleted,
            created_at=entity.created_at,
            created_by=entity.created_by,
            modified_at=entity.modified_at,
            modified_by=entity.modified_by,
        )

    def to_entity(self) -> ForumComment:
        return ForumComment(
            id=str(self.id),
            post_id=str(self.post_id),
            author_id=self.author_id,
            author_display_name=self.author_display_name,
            is_anonymous=self.is_anonymous,
            anonymous_name=self.anonymous_name,
            content=self.content,
            is_deleted=self.is_deleted,
            created_at=self.created_at,
            created_by=self.created_by,
            modified_at=self.modified_at,
            modified_by=self.modified_by,
        )

    def apply_entity(self, entity: ForumComment) -> None:
        self.content = entity.content
        self.is_deleted = entity.is_deleted
        self.modified_at = entity.modified_at
        self.modified_by = entity.modified_by


class ForumLikeModel(Base):
    __tablename__ = "forum_likes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    post: Mapped[ForumPostModel] = relationship("ForumPostModel", back_populates="likes")

    @classmethod
    def from_entity(cls, entity: ForumLike) -> "ForumLikeModel":
        return cls(
            id=uuid.UUID(entity.id),
            post_id=uuid.UUID(entity.post_id),
            user_id=entity.user_id,
            created_at=entity.created_at,
        )

    def to_entity(self) -> ForumLike:
        return ForumLike(
            id=str(self.id),
            post_id=str(self.post_id),
            user_id=self.user_id,
            created_at=self.created_at,
        )


class ForumReportModel(Base):
    __tablename__ = "forum_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    admin_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    post: Mapped[ForumPostModel] = relationship("ForumPostModel", back_populates="reports")

    @classmethod
    def from_entity(cls, entity: ForumReport) -> "ForumReportModel":
        return cls(
            id=uuid.UUID(entity.id),
            post_id=uuid.UUID(entity.post_id),
            reporter_id=entity.reporter_id,
            reason=entity.reason,
            status=entity.status,
            admin_note=entity.admin_note,
            resolved_at=entity.resolved_at,
            resolved_by=entity.resolved_by,
            created_at=entity.created_at,
            created_by=entity.created_by,
            modified_at=entity.modified_at,
            modified_by=entity.modified_by,
        )

    def to_entity(self) -> ForumReport:
        return ForumReport(
            id=str(self.id),
            post_id=str(self.post_id),
            reporter_id=self.reporter_id,
            reason=self.reason,
            status=self.status,
            admin_note=self.admin_note,
            resolved_at=self.resolved_at,
            resolved_by=self.resolved_by,
            created_at=self.created_at,
            created_by=self.created_by,
            modified_at=self.modified_at,
            modified_by=self.modified_by,
        )

    def apply_entity(self, entity: ForumReport) -> None:
        self.status = entity.status
        self.admin_note = entity.admin_note
        self.resolved_at = entity.resolved_at
        self.resolved_by = entity.resolved_by
        self.modified_at = entity.modified_at
        self.modified_by = entity.modified_by

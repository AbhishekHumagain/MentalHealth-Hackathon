from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.forum import ForumComment, ForumLike, ForumPost, ForumReport


class ForumPostRepository(ABC):

    @abstractmethod
    async def create(self, post: ForumPost) -> ForumPost:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, post_id: str) -> ForumPost | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
    ) -> list[ForumPost]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, post: ForumPost) -> ForumPost:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def count_all(self, category: str | None = None) -> int:
        raise NotImplementedError


class ForumCommentRepository(ABC):

    @abstractmethod
    async def create(self, comment: ForumComment) -> ForumComment:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, comment_id: str) -> ForumComment | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_post(
        self,
        post_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ForumComment]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, comment: ForumComment) -> ForumComment:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, comment_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def count_by_post(self, post_id: str) -> int:
        raise NotImplementedError


class ForumLikeRepository(ABC):

    @abstractmethod
    async def create(self, like: ForumLike) -> ForumLike:
        raise NotImplementedError

    @abstractmethod
    async def get(self, post_id: str, user_id: str) -> ForumLike | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, post_id: str, user_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_liked_post_ids(self, user_id: str, post_ids: list[str]) -> list[str]:
        raise NotImplementedError


class ForumReportRepository(ABC):

    @abstractmethod
    async def create(self, report: ForumReport) -> ForumReport:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, report_id: str) -> ForumReport | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_post_and_reporter(
        self, post_id: str, reporter_id: str
    ) -> ForumReport | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[ForumReport]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, report: ForumReport) -> ForumReport:
        raise NotImplementedError

    @abstractmethod
    async def count_pending_by_post(self, post_id: str) -> int:
        raise NotImplementedError

from __future__ import annotations


class ForumPostNotFoundError(Exception):
    def __init__(self, post_id: str) -> None:
        super().__init__(f"Forum post '{post_id}' not found.")


class ForumCommentNotFoundError(Exception):
    def __init__(self, comment_id: str) -> None:
        super().__init__(f"Forum comment '{comment_id}' not found.")


class ForumReportNotFoundError(Exception):
    def __init__(self, report_id: str) -> None:
        super().__init__(f"Forum report '{report_id}' not found.")


class ForumPermissionError(Exception):
    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message)


class ForumAlreadyReportedError(Exception):
    def __init__(self, post_id: str) -> None:
        super().__init__(f"You have already reported post '{post_id}'.")


class ForumAlreadyLikedError(Exception):
    def __init__(self, post_id: str) -> None:
        super().__init__(f"You have already liked post '{post_id}'.")

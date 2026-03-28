class StudentProfileAlreadyExistsError(Exception):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"Student profile already exists for user '{user_id}'.")


class StudentProfileNotFoundError(Exception):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"Student profile not found for user '{user_id}'.")

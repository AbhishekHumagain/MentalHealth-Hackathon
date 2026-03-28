class UniversityNotFoundError(Exception):
    #Raised when a University record cannot be located.

    def __init__(self, university_id: str) -> None:
        super().__init__(f"University '{university_id}' not found.")
        self.university_id = university_id


class UniversityAlreadyExistsError(Exception):
    #Raised on an attempt to create a duplicate university

    def __init__(self, name: str) -> None:
        super().__init__(f"University '{name}' already exists.")
        self.name = name


class UniversityValidationError(Exception):
    #Raised when business-rule validation fails on a university

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UniversityInactiveError(Exception):
    #Raised when an operation is attempted on an inactive university

    def __init__(self, university_id: str) -> None:
        super().__init__(f"University '{university_id}' is inactive.")
        self.university_id = university_id
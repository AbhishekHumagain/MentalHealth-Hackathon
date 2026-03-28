class InternshipNotFoundError(Exception):
    def __init__(self, internship_id: str) -> None:
        super().__init__(f"Internship '{internship_id}' not found.")

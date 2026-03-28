from app.infrastructure.database.models.university_model import UniversityModel  # noqa: F401
from app.infrastructure.database.models.student_profile_model import StudentProfileModel  # noqa: F401
from app.infrastructure.database.models.internship_model import InternshipModel  # noqa: F401
from app.infrastructure.database.models.internship_recommendation_model import (  # noqa: F401
    InternshipRecommendationModel,
)

__all__ = [
    "UniversityModel",
    "StudentProfileModel",
    "InternshipModel",
    "InternshipRecommendationModel",
]

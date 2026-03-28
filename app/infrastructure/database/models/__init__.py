from app.infrastructure.database.models.university_model import UniversityModel  # noqa: F401
from app.infrastructure.database.models.chat_models import (  # noqa: F401
    ChatRoomModel,
    ChatRoomMemberModel,
    ChatMessageModel,
    ChatRequestModel,
)
from app.infrastructure.database.models.apartment_model import ApartmentModel  # noqa: F401

__all__ = [
    "UniversityModel",
    "ChatRoomModel",
    "ChatRoomMemberModel",
    "ChatMessageModel",
    "ChatRequestModel",
    "ApartmentModel",
]

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRoomTypeDTO(str, Enum):
    DIRECT = "direct"
    ASSOCIATION = "association"


class ChatRequestStatusDTO(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SendChatRequestDTO(BaseModel):
    to_user_id: UUID


class RespondChatRequestDTO(BaseModel):
    accept: bool


class SendMessageDTO(BaseModel):
    content: str
    is_anonymous: bool = False


class ChatRequestResponseDTO(BaseModel):
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    status: ChatRequestStatusDTO
    created_at: datetime
    room_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class ChatRoomResponseDTO(BaseModel):
    id: UUID
    room_type: ChatRoomTypeDTO
    association_id: Optional[UUID] = None
    name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponseDTO(BaseModel):
    id: UUID
    room_id: UUID
    sender_id: Optional[UUID] = None
    content: str
    is_anonymous: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRoomListResponseDTO(BaseModel):
    rooms: List[ChatRoomResponseDTO]


class ChatUserSearchResultDTO(BaseModel):
    id: UUID
    email: str
    first_name: str = ""
    last_name: str = ""
    display_name: str


class ChatUserSearchListResponseDTO(BaseModel):
    users: List[ChatUserSearchResultDTO]

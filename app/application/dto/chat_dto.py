from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRoomTypeDTO(str, Enum):
    DIRECT = "direct"
    ASSOCIATION = "association"


class ChatRequestStatusDTO(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ChatRelationshipStatusDTO(str, Enum):
    NONE = "none"
    OUTGOING_PENDING = "outgoing_pending"
    INCOMING_PENDING = "incoming_pending"
    CONNECTED = "connected"


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
    from_user_display_name: Optional[str] = None
    from_user_email: Optional[str] = None
    to_user_display_name: Optional[str] = None
    to_user_email: Optional[str] = None

    model_config = {"from_attributes": True}


class ChatRoomResponseDTO(BaseModel):
    id: UUID
    room_type: ChatRoomTypeDTO
    association_id: Optional[UUID] = None
    name: Optional[str] = None
    created_at: datetime
    member_ids: List[UUID] = Field(default_factory=list)
    direct_user_id: Optional[UUID] = None
    direct_display_name: Optional[str] = None
    direct_email: Optional[str] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None

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
    relationship_status: ChatRelationshipStatusDTO = ChatRelationshipStatusDTO.NONE
    request_id: Optional[UUID] = None
    room_id: Optional[UUID] = None


class ChatUserSearchListResponseDTO(BaseModel):
    users: List[ChatUserSearchResultDTO]

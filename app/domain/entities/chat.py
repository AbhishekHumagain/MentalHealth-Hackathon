from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ChatRoomType(str, Enum):
    DIRECT = "direct"            # 1-on-1 chat
    ASSOCIATION = "association"  # Group chat for a student association


class ChatRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class ChatRoom:
    id: UUID
    room_type: ChatRoomType
    association_id: Optional[UUID]
    name: Optional[str]
    created_at: datetime
    is_active: bool = True

    @staticmethod
    def create_direct() -> "ChatRoom":
        return ChatRoom(
            id=uuid4(),
            room_type=ChatRoomType.DIRECT,
            association_id=None,
            name=None,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_association(association_id: UUID, name: str) -> "ChatRoom":
        return ChatRoom(
            id=uuid4(),
            room_type=ChatRoomType.ASSOCIATION,
            association_id=association_id,
            name=name,
            created_at=datetime.utcnow(),
        )


@dataclass
class ChatRoomMember:
    id: UUID
    room_id: UUID
    user_id: UUID
    joined_at: datetime
    is_admin: bool = False

    @staticmethod
    def create(room_id: UUID, user_id: UUID, is_admin: bool = False) -> "ChatRoomMember":
        return ChatRoomMember(
            id=uuid4(),
            room_id=room_id,
            user_id=user_id,
            joined_at=datetime.utcnow(),
            is_admin=is_admin,
        )


@dataclass
class ChatMessage:
    id: UUID
    room_id: UUID
    sender_id: UUID
    content: str
    is_anonymous: bool
    created_at: datetime
    is_deleted: bool = False

    @staticmethod
    def create(
        room_id: UUID, sender_id: UUID, content: str, anonymous: bool = False
    ) -> "ChatMessage":
        return ChatMessage(
            id=uuid4(),
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            is_anonymous=anonymous,
            created_at=datetime.utcnow(),
        )


@dataclass
class ChatRequest:
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    status: ChatRequestStatus
    created_at: datetime
    room_id: Optional[UUID] = None

    @staticmethod
    def create(from_user_id: UUID, to_user_id: UUID) -> "ChatRequest":
        return ChatRequest(
            id=uuid4(),
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status=ChatRequestStatus.PENDING,
            created_at=datetime.utcnow(),
        )
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat import (
    ChatMessage,
    ChatRequest,
    ChatRequestStatus,
    ChatRoom,
    ChatRoomMember,
)


class AbstractChatRepository(ABC):

    @abstractmethod
    async def create_chat_request(self, request: ChatRequest) -> ChatRequest: ...

    @abstractmethod
    async def get_chat_request(self, request_id: UUID) -> Optional[ChatRequest]: ...

    @abstractmethod
    async def get_existing_request(self, from_user: UUID, to_user: UUID) -> Optional[ChatRequest]: ...

    @abstractmethod
    async def update_request_status(
        self, request_id: UUID, status: ChatRequestStatus, room_id: Optional[UUID] = None
    ) -> ChatRequest: ...

    @abstractmethod
    async def get_pending_requests_for_user(self, user_id: UUID) -> List[ChatRequest]: ...

    @abstractmethod
    async def create_room(self, room: ChatRoom) -> ChatRoom: ...

    @abstractmethod
    async def get_room(self, room_id: UUID) -> Optional[ChatRoom]: ...

    @abstractmethod
    async def get_association_room(self, association_id: UUID) -> Optional[ChatRoom]: ...

    @abstractmethod
    async def get_rooms_for_user(self, user_id: UUID) -> List[ChatRoom]: ...

    @abstractmethod
    async def add_member(self, member: ChatRoomMember) -> ChatRoomMember: ...

    @abstractmethod
    async def is_member(self, room_id: UUID, user_id: UUID) -> bool: ...

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> ChatMessage: ...

    @abstractmethod
    async def get_messages(
        self, room_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[ChatMessage]: ...
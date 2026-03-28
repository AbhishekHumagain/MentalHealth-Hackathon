from uuid import UUID

from app.domain.entities.chat import (
    ChatMessage, ChatRequest, ChatRequestStatus,
    ChatRoom, ChatRoomMember,
)
from app.domain.exceptions.chat_exceptions import (
    ChatRequestAlreadyExists, ChatRequestAlreadyHandled,
    ChatRequestNotFound, ChatRoomNotFound, NotARoomMember,
)
from app.domain.repositories.chat_repository import AbstractChatRepository


class SendChatRequestUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, from_user_id: UUID, to_user_id: UUID) -> ChatRequest:
        existing = await self.repo.get_existing_request(from_user_id, to_user_id)
        if existing:
            raise ChatRequestAlreadyExists("Request already exists.")
        request = ChatRequest.create(from_user_id, to_user_id)
        return await self.repo.create_chat_request(request)


class RespondToChatRequestUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, request_id: UUID, current_user_id: UUID, accept: bool) -> ChatRequest:
        request = await self.repo.get_chat_request(request_id)
        if not request:
            raise ChatRequestNotFound("Chat request not found.")
        if request.status != ChatRequestStatus.PENDING:
            raise ChatRequestAlreadyHandled("Already handled.")
        if accept:
            room = ChatRoom.create_direct()
            room = await self.repo.create_room(room)
            await self.repo.add_member(ChatRoomMember.create(room.id, request.from_user_id))
            await self.repo.add_member(ChatRoomMember.create(room.id, request.to_user_id))
            return await self.repo.update_request_status(
                request_id, ChatRequestStatus.ACCEPTED, room_id=room.id
            )
        else:
            return await self.repo.update_request_status(
                request_id, ChatRequestStatus.REJECTED
            )


class GetMyRoomsUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, user_id: UUID):
        return await self.repo.get_rooms_for_user(user_id)


class GetOrCreateAssociationRoomUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, association_id: UUID, name: str) -> ChatRoom:
        existing = await self.repo.get_association_room(association_id)
        if existing:
            return existing
        room = ChatRoom.create_association(association_id, name)
        return await self.repo.create_room(room)


class JoinAssociationRoomUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, association_id: UUID, user_id: UUID) -> ChatRoom:
        room = await self.repo.get_association_room(association_id)
        if not room:
            raise ChatRoomNotFound("Association room not found.")
        already = await self.repo.is_member(room.id, user_id)
        if not already:
            await self.repo.add_member(ChatRoomMember.create(room.id, user_id))
        return room


class SendMessageUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(
        self, room_id: UUID, sender_id: UUID, content: str, is_anonymous: bool = False
    ) -> ChatMessage:
        if not await self.repo.is_member(room_id, sender_id):
            raise NotARoomMember("You are not in this room.")
        message = ChatMessage.create(room_id, sender_id, content, is_anonymous)
        return await self.repo.save_message(message)


class GetMessagesUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, room_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0):
        if not await self.repo.is_member(room_id, user_id):
            raise NotARoomMember("You are not in this room.")
        messages = await self.repo.get_messages(room_id, limit, offset)
        for msg in messages:
            if msg.is_anonymous:
                msg.sender_id = None
        return messages



from uuid import UUID

from app.application.dto.chat_dto import ChatUserSearchResultDTO
from app.domain.entities.chat import (
    ChatMessage, ChatRequest, ChatRequestStatus,
    ChatRoom, ChatRoomMember,
)
from app.domain.exceptions.chat_exceptions import (
    ChatRequestAlreadyExists, ChatRequestAlreadyHandled,
    ChatRequestForbidden, ChatRequestNotFound, ChatRoomNotFound, DirectChatAlreadyExists,
    NotARoomMember,
)
from app.domain.repositories.chat_repository import AbstractChatRepository


class SendChatRequestUseCase:
    def __init__(self, repo: AbstractChatRepository, ensure_user_exists=None):
        self.repo = repo
        self.ensure_user_exists = ensure_user_exists

    async def execute(self, from_user_id: UUID, to_user_id: UUID) -> ChatRequest:
        if from_user_id == to_user_id:
            raise ValueError("You cannot send a chat request to yourself.")
        if self.ensure_user_exists is not None:
            user_exists = await self.ensure_user_exists(str(to_user_id))
            if not user_exists:
                raise ValueError("Target user was not found.")
        existing_room = await self.repo.get_direct_room_for_users(from_user_id, to_user_id)
        if existing_room:
            raise DirectChatAlreadyExists(existing_room.id)
        existing = await self.repo.get_existing_request(from_user_id, to_user_id)
        if existing:
            if existing.status == ChatRequestStatus.PENDING:
                if existing.to_user_id == from_user_id:
                    return await _accept_request(self.repo, existing)
                raise ChatRequestAlreadyExists("Request already exists.")
            if existing.status == ChatRequestStatus.ACCEPTED and existing.room_id is not None:
                raise DirectChatAlreadyExists(existing.room_id)
        request = ChatRequest.create(from_user_id, to_user_id)
        return await self.repo.create_chat_request(request)


class RespondToChatRequestUseCase:
    def __init__(self, repo: AbstractChatRepository):
        self.repo = repo

    async def execute(self, request_id: UUID, current_user_id: UUID, accept: bool) -> ChatRequest:
        request = await self.repo.get_chat_request(request_id)
        if not request:
            raise ChatRequestNotFound("Chat request not found.")
        if request.to_user_id != current_user_id:
            raise ChatRequestForbidden("Only the recipient can respond to this chat request.")
        if request.status != ChatRequestStatus.PENDING:
            raise ChatRequestAlreadyHandled("Already handled.")
        if accept:
            return await _accept_request(self.repo, request)
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
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Message content cannot be empty.")
        if not await self.repo.is_member(room_id, sender_id):
            raise NotARoomMember("You are not in this room.")
        message = ChatMessage.create(room_id, sender_id, normalized_content, is_anonymous)
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


class SearchChatUsersUseCase:
    def __init__(self, user_search):
        self._user_search = user_search

    async def execute(
        self,
        *,
        query: str,
        current_user_id: UUID,
        limit: int = 20,
    ) -> list[ChatUserSearchResultDTO]:
        users = await self._user_search(query, max_results=limit)
        results: list[ChatUserSearchResultDTO] = []
        for user in users:
            try:
                user_id = UUID(user.id)
            except ValueError:
                continue
            if user_id == current_user_id:
                continue
            results.append(
                ChatUserSearchResultDTO(
                    id=user_id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    display_name=user.display_name,
                )
            )
        return results


async def _accept_request(repo: AbstractChatRepository, request: ChatRequest) -> ChatRequest:
    room = await repo.get_direct_room_for_users(request.from_user_id, request.to_user_id)
    if room is None:
        room = ChatRoom.create_direct()
        room = await repo.create_room(room)
        await repo.add_member(ChatRoomMember.create(room.id, request.from_user_id))
        await repo.add_member(ChatRoomMember.create(room.id, request.to_user_id))
    return await repo.update_request_status(
        request.id,
        ChatRequestStatus.ACCEPTED,
        room_id=room.id,
    )



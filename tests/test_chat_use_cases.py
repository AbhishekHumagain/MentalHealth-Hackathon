from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.application.use_cases.chat_use_cases import (
    RespondToChatRequestUseCase,
    SendChatRequestUseCase,
)
from app.domain.entities.chat import (
    ChatMessage,
    ChatRequest,
    ChatRequestStatus,
    ChatRoom,
    ChatRoomMember,
)
from app.domain.exceptions.chat_exceptions import (
    ChatRequestForbidden,
    DirectChatAlreadyExists,
)
from app.domain.repositories.chat_repository import AbstractChatRepository


class InMemoryChatRepository(AbstractChatRepository):
    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []
        self.rooms: list[ChatRoom] = []
        self.members: list[ChatRoomMember] = []
        self.messages: list[ChatMessage] = []

    async def create_chat_request(self, request: ChatRequest) -> ChatRequest:
        self.requests.append(request)
        return request

    async def get_chat_request(self, request_id: UUID) -> ChatRequest | None:
        return next((request for request in self.requests if request.id == request_id), None)

    async def get_existing_request(self, from_user: UUID, to_user: UUID) -> ChatRequest | None:
        candidates = [
            request
            for request in self.requests
            if {request.from_user_id, request.to_user_id} == {from_user, to_user}
        ]
        return sorted(candidates, key=lambda request: request.created_at, reverse=True)[0] if candidates else None

    async def update_request_status(
        self,
        request_id: UUID,
        status: ChatRequestStatus,
        room_id: UUID | None = None,
    ) -> ChatRequest:
        request = await self.get_chat_request(request_id)
        assert request is not None
        request.status = status
        request.room_id = room_id
        return request

    async def get_pending_requests_for_user(self, user_id: UUID) -> list[ChatRequest]:
        return [
            request
            for request in self.requests
            if request.to_user_id == user_id and request.status == ChatRequestStatus.PENDING
        ]

    async def get_outgoing_requests_for_user(self, user_id: UUID) -> list[ChatRequest]:
        return [
            request
            for request in self.requests
            if request.from_user_id == user_id and request.status == ChatRequestStatus.PENDING
        ]

    async def create_room(self, room: ChatRoom) -> ChatRoom:
        self.rooms.append(room)
        return room

    async def get_room(self, room_id: UUID) -> ChatRoom | None:
        return next((room for room in self.rooms if room.id == room_id), None)

    async def get_direct_room_for_users(self, first_user_id: UUID, second_user_id: UUID) -> ChatRoom | None:
        target_users = {first_user_id, second_user_id}
        for room in self.rooms:
            if room.room_type.value != "direct":
                continue
            member_ids = {member.user_id for member in self.members if member.room_id == room.id}
            if member_ids == target_users:
                return room
        return None

    async def get_association_room(self, association_id: UUID) -> ChatRoom | None:
        return next((room for room in self.rooms if room.association_id == association_id), None)

    async def get_rooms_for_user(self, user_id: UUID) -> list[ChatRoom]:
        room_ids = {member.room_id for member in self.members if member.user_id == user_id}
        return [room for room in self.rooms if room.id in room_ids]

    async def get_room_member_ids(self, room_id: UUID) -> list[UUID]:
        return [member.user_id for member in self.members if member.room_id == room_id]

    async def add_member(self, member: ChatRoomMember) -> ChatRoomMember:
        self.members.append(member)
        return member

    async def is_member(self, room_id: UUID, user_id: UUID) -> bool:
        return any(member.room_id == room_id and member.user_id == user_id for member in self.members)

    async def save_message(self, message: ChatMessage) -> ChatMessage:
        self.messages.append(message)
        return message

    async def get_messages(self, room_id: UUID, limit: int = 50, offset: int = 0) -> list[ChatMessage]:
        room_messages = [message for message in self.messages if message.room_id == room_id]
        return room_messages[offset : offset + limit]

    async def get_latest_message(self, room_id: UUID) -> ChatMessage | None:
        room_messages = [message for message in self.messages if message.room_id == room_id]
        return room_messages[-1] if room_messages else None


@pytest.mark.asyncio
async def test_send_chat_request_rejects_unknown_user() -> None:
    repo = InMemoryChatRepository()

    async def fake_user_exists(_user_id: str) -> bool:
        return False

    with pytest.raises(ValueError, match="Target user was not found"):
        await SendChatRequestUseCase(repo, fake_user_exists).execute(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_respond_to_chat_request_requires_recipient() -> None:
    repo = InMemoryChatRepository()
    sender = uuid4()
    recipient = uuid4()
    request = await repo.create_chat_request(ChatRequest.create(sender, recipient))

    with pytest.raises(ChatRequestForbidden):
        await RespondToChatRequestUseCase(repo).execute(request.id, uuid4(), True)


@pytest.mark.asyncio
async def test_send_chat_request_auto_accepts_incoming_pending_request() -> None:
    repo = InMemoryChatRepository()
    alice = uuid4()
    bob = uuid4()

    await repo.create_chat_request(ChatRequest.create(alice, bob))

    async def fake_user_exists(_user_id: str) -> bool:
        return True

    request = await SendChatRequestUseCase(repo, fake_user_exists).execute(bob, alice)

    assert request.status == ChatRequestStatus.ACCEPTED
    assert request.room_id is not None
    assert len(repo.rooms) == 1
    room_member_ids = {member.user_id for member in repo.members}
    assert room_member_ids == {alice, bob}


@pytest.mark.asyncio
async def test_send_chat_request_raises_when_direct_room_already_exists() -> None:
    repo = InMemoryChatRepository()
    alice = uuid4()
    bob = uuid4()
    room = await repo.create_room(ChatRoom.create_direct())
    await repo.add_member(ChatRoomMember.create(room.id, alice))
    await repo.add_member(ChatRoomMember.create(room.id, bob))

    async def fake_user_exists(_user_id: str) -> bool:
        return True

    with pytest.raises(DirectChatAlreadyExists):
        await SendChatRequestUseCase(repo, fake_user_exists).execute(alice, bob)

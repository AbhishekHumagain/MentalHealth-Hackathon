from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chat import (
    ChatMessage, ChatRequest, ChatRequestStatus,
    ChatRoom, ChatRoomMember, ChatRoomType,
)
from app.domain.repositories.chat_repository import AbstractChatRepository
from app.infrastructure.database.models.chat_models import (
    ChatMessageModel, ChatRequestModel,
    ChatRoomMemberModel, ChatRoomModel,
)


def _to_room(m: ChatRoomModel) -> ChatRoom:
    return ChatRoom(
        id=m.id, room_type=ChatRoomType(m.room_type),
        association_id=m.association_id, name=m.name,
        is_active=m.is_active, created_at=m.created_at,
    )


def _to_message(m: ChatMessageModel) -> ChatMessage:
    return ChatMessage(
        id=m.id, room_id=m.room_id, sender_id=m.sender_id,
        content=m.content, is_anonymous=m.is_anonymous,
        is_deleted=m.is_deleted, created_at=m.created_at,
    )


def _to_request(m: ChatRequestModel) -> ChatRequest:
    return ChatRequest(
        id=m.id, from_user_id=m.from_user_id, to_user_id=m.to_user_id,
        status=ChatRequestStatus(m.status), room_id=m.room_id,
        created_at=m.created_at,
    )


class SQLChatRepository(AbstractChatRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat_request(self, request: ChatRequest) -> ChatRequest:
        model = ChatRequestModel(
            id=request.id, from_user_id=request.from_user_id,
            to_user_id=request.to_user_id, status=request.status.value,
            created_at=request.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return _to_request(model)

    async def get_chat_request(self, request_id: UUID) -> Optional[ChatRequest]:
        result = await self.session.execute(
            select(ChatRequestModel).where(ChatRequestModel.id == request_id)
        )
        model = result.scalar_one_or_none()
        return _to_request(model) if model else None

    async def get_existing_request(self, from_user: UUID, to_user: UUID) -> Optional[ChatRequest]:
        result = await self.session.execute(
            select(ChatRequestModel).where(
                or_(
                    and_(ChatRequestModel.from_user_id == from_user, ChatRequestModel.to_user_id == to_user),
                    and_(ChatRequestModel.from_user_id == to_user, ChatRequestModel.to_user_id == from_user),
                )
            )
        )
        model = result.scalar_one_or_none()
        return _to_request(model) if model else None

    async def update_request_status(
        self, request_id: UUID, status: ChatRequestStatus, room_id: Optional[UUID] = None
    ) -> ChatRequest:
        result = await self.session.execute(
            select(ChatRequestModel).where(ChatRequestModel.id == request_id)
        )
        model = result.scalar_one()
        model.status = status.value
        if room_id:
            model.room_id = room_id
        await self.session.commit()
        await self.session.refresh(model)
        return _to_request(model)

    async def get_pending_requests_for_user(self, user_id: UUID) -> List[ChatRequest]:
        result = await self.session.execute(
            select(ChatRequestModel).where(
                ChatRequestModel.to_user_id == user_id,
                ChatRequestModel.status == "pending",
            )
        )
        return [_to_request(m) for m in result.scalars().all()]

    async def create_room(self, room: ChatRoom) -> ChatRoom:
        model = ChatRoomModel(
            id=room.id, room_type=room.room_type.value,
            association_id=room.association_id, name=room.name,
            is_active=room.is_active, created_at=room.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return _to_room(model)

    async def get_room(self, room_id: UUID) -> Optional[ChatRoom]:
        result = await self.session.execute(
            select(ChatRoomModel).where(ChatRoomModel.id == room_id)
        )
        model = result.scalar_one_or_none()
        return _to_room(model) if model else None

    async def get_association_room(self, association_id: UUID) -> Optional[ChatRoom]:
        result = await self.session.execute(
            select(ChatRoomModel).where(
                ChatRoomModel.association_id == association_id,
                ChatRoomModel.room_type == "association",
            )
        )
        model = result.scalar_one_or_none()
        return _to_room(model) if model else None

    async def get_rooms_for_user(self, user_id: UUID) -> List[ChatRoom]:
        result = await self.session.execute(
            select(ChatRoomModel)
            .join(ChatRoomMemberModel, ChatRoomMemberModel.room_id == ChatRoomModel.id)
            .where(ChatRoomMemberModel.user_id == user_id)
        )
        return [_to_room(m) for m in result.scalars().all()]

    async def add_member(self, member: ChatRoomMember) -> ChatRoomMember:
        model = ChatRoomMemberModel(
            id=member.id, room_id=member.room_id,
            user_id=member.user_id, joined_at=member.joined_at,
            is_admin=member.is_admin,
        )
        self.session.add(model)
        await self.session.commit()
        return member

    async def is_member(self, room_id: UUID, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(ChatRoomMemberModel).where(
                ChatRoomMemberModel.room_id == room_id,
                ChatRoomMemberModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_message(self, message: ChatMessage) -> ChatMessage:
        model = ChatMessageModel(
            id=message.id, room_id=message.room_id, sender_id=message.sender_id,
            content=message.content, is_anonymous=message.is_anonymous,
            created_at=message.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return _to_message(model)

    async def get_messages(self, room_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.room_id == room_id, ChatMessageModel.is_deleted == False)
            .order_by(ChatMessageModel.created_at.asc())
            .offset(offset).limit(limit)
        )
        return [_to_message(m) for m in result.scalars().all()]
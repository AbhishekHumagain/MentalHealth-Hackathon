import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class ChatRoomModel(Base):
    __tablename__ = "chat_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_type = Column(String(20), nullable=False)
    association_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("ChatRoomMemberModel", back_populates="room")
    messages = relationship("ChatMessageModel", back_populates="room")


class ChatRoomMemberModel(Base):
    __tablename__ = "chat_room_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

    room = relationship("ChatRoomModel", back_populates="members")


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("ChatRoomModel", back_populates="messages")


class ChatRequestModel(Base):
    __tablename__ = "chat_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(UUID(as_uuid=True), nullable=False)
    to_user_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), default="pending")
    room_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
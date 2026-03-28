import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.chat_dto import (
    ChatRequestResponseDTO, ChatRoomListResponseDTO,
    ChatRoomResponseDTO, RespondChatRequestDTO, SendChatRequestDTO,
)
from app.application.use_cases.chat_use_cases import (
    GetMessagesUseCase, GetMyRoomsUseCase, GetOrCreateAssociationRoomUseCase,
    JoinAssociationRoomUseCase, RespondToChatRequestUseCase,
    SendChatRequestUseCase, SendMessageUseCase,
)
from app.domain.exceptions.chat_exceptions import (
    ChatRequestAlreadyExists, ChatRequestAlreadyHandled,
    ChatRequestNotFound, ChatRoomNotFound, NotARoomMember,
)
from app.infrastructure.database.repositories.chat_repo_impl import SQLChatRepository
from app.infrastructure.database.session import get_async_session
from app.api.v1.websocket_manager import manager

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_current_user_id(x_user_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")


def get_chat_repo(session: AsyncSession = Depends(get_async_session)) -> SQLChatRepository:
    return SQLChatRepository(session)


@router.post("/requests", response_model=ChatRequestResponseDTO, status_code=201)
async def send_chat_request(
    body: SendChatRequestDTO,
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        request = await SendChatRequestUseCase(repo).execute(current_user, body.to_user_id)
    except ChatRequestAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ChatRequestResponseDTO(
        id=request.id, from_user_id=request.from_user_id,
        to_user_id=request.to_user_id, status=request.status,
        created_at=request.created_at, room_id=request.room_id,
    )


@router.post("/requests/{request_id}/respond", response_model=ChatRequestResponseDTO)
async def respond_to_chat_request(
    request_id: UUID,
    body: RespondChatRequestDTO,
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        request = await RespondToChatRequestUseCase(repo).execute(request_id, current_user, body.accept)
    except ChatRequestNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChatRequestAlreadyHandled as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ChatRequestResponseDTO(
        id=request.id, from_user_id=request.from_user_id,
        to_user_id=request.to_user_id, status=request.status,
        created_at=request.created_at, room_id=request.room_id,
    )


@router.get("/requests/pending")
async def get_pending_requests(
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    requests = await repo.get_pending_requests_for_user(current_user)
    return [
        ChatRequestResponseDTO(
            id=r.id, from_user_id=r.from_user_id, to_user_id=r.to_user_id,
            status=r.status, created_at=r.created_at, room_id=r.room_id,
        )
        for r in requests
    ]


@router.get("/rooms", response_model=ChatRoomListResponseDTO)
async def get_my_rooms(
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    rooms = await GetMyRoomsUseCase(repo).execute(current_user)
    return ChatRoomListResponseDTO(rooms=[
        ChatRoomResponseDTO(
            id=r.id, room_type=r.room_type, association_id=r.association_id,
            name=r.name, created_at=r.created_at,
        ) for r in rooms
    ])


@router.post("/associations/{association_id}/room")
async def get_or_create_association_room(
    association_id: UUID, name: str,
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    room = await GetOrCreateAssociationRoomUseCase(repo).execute(association_id, name)
    return ChatRoomResponseDTO(
        id=room.id, room_type=room.room_type, association_id=room.association_id,
        name=room.name, created_at=room.created_at,
    )


@router.post("/associations/{association_id}/join")
async def join_association_room(
    association_id: UUID,
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        room = await JoinAssociationRoomUseCase(repo).execute(association_id, current_user)
    except ChatRoomNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Joined successfully", "room_id": str(room.id)}


@router.get("/rooms/{room_id}/messages")
async def get_room_messages(
    room_id: UUID, limit: int = 50, offset: int = 0,
    current_user: UUID = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        messages = await GetMessagesUseCase(repo).execute(room_id, current_user, limit, offset)
    except NotARoomMember as e:
        raise HTTPException(status_code=403, detail=str(e))
    return [
        {
            "id": str(m.id), "room_id": str(m.room_id),
            "sender_id": str(m.sender_id) if m.sender_id else None,
            "content": m.content, "is_anonymous": m.is_anonymous,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket, room_id: str, user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLChatRepository(session)
    try:
        user_uuid = UUID(user_id)
        room_uuid = UUID(room_id)
    except ValueError:
        await websocket.close(code=1008)
        return

    if not await repo.is_member(room_uuid, user_uuid):
        await websocket.close(code=1008, reason="Not a member")
        return

    await manager.connect(websocket, room_id)
    await manager.broadcast(room_id, {
        "type": "join", "sender_id": user_id, "room_id": room_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                content = payload.get("content", "")
                is_anonymous = payload.get("is_anonymous", False)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            if not content.strip():
                continue

            try:
                msg = await SendMessageUseCase(repo).execute(room_uuid, user_uuid, content, is_anonymous)
            except NotARoomMember:
                await websocket.send_json({"type": "error", "detail": "Not a member"})
                continue

            await manager.broadcast(room_id, {
                "type": "message", "id": str(msg.id), "room_id": room_id,
                "sender_id": user_id if not is_anonymous else None,
                "content": content, "is_anonymous": is_anonymous,
                "timestamp": msg.created_at.isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {
            "type": "leave", "sender_id": user_id, "room_id": room_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
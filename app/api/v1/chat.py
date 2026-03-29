import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.application.dto.chat_dto import (
    ChatMessageResponseDTO, ChatRelationshipStatusDTO, ChatRequestResponseDTO,
    ChatRoomListResponseDTO, ChatRoomResponseDTO, ChatUserSearchListResponseDTO,
    RespondChatRequestDTO, SendChatRequestDTO, SendMessageDTO,
)
from app.application.use_cases.chat_use_cases import (
    GetMessagesUseCase, GetMyRoomsUseCase, GetOrCreateAssociationRoomUseCase,
    JoinAssociationRoomUseCase, RespondToChatRequestUseCase, SearchChatUsersUseCase,
    SendChatRequestUseCase, SendMessageUseCase,
)
from app.domain.exceptions.chat_exceptions import (
    ChatRequestAlreadyExists, ChatRequestAlreadyHandled,
    ChatRequestForbidden, ChatRequestNotFound, ChatRoomNotFound,
    DirectChatAlreadyExists, NotARoomMember,
)
from app.infrastructure.database.repositories.chat_repo_impl import SQLChatRepository
from app.infrastructure.database.session import get_async_session
from app.infrastructure.keycloak import admin_client as kc
from app.infrastructure.keycloak.jwt_validator import TokenValidationError, validate_token
from app.api.v1.websocket_manager import manager

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_repo(session: AsyncSession = Depends(get_async_session)) -> SQLChatRepository:
    return SQLChatRepository(session)


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Authenticated user id is not a valid UUID.") from exc


async def _target_user_exists(user_id: str) -> bool:
    return await kc.get_user_by_id(user_id) is not None


async def _load_user_lookup(user_ids: set[UUID]) -> dict[UUID, kc.KeycloakUserSummary]:
    raw_lookup = await kc.get_users_by_ids([str(user_id) for user_id in user_ids])
    return {UUID(user_id): summary for user_id, summary in raw_lookup.items()}


def _build_request_response(
    request,
    user_lookup: dict[UUID, kc.KeycloakUserSummary],
) -> ChatRequestResponseDTO:
    from_summary = user_lookup.get(request.from_user_id)
    to_summary = user_lookup.get(request.to_user_id)
    return ChatRequestResponseDTO(
        id=request.id,
        from_user_id=request.from_user_id,
        to_user_id=request.to_user_id,
        status=request.status,
        created_at=request.created_at,
        room_id=request.room_id,
        from_user_display_name=from_summary.display_name if from_summary else None,
        from_user_email=from_summary.email if from_summary else None,
        to_user_display_name=to_summary.display_name if to_summary else None,
        to_user_email=to_summary.email if to_summary else None,
    )


async def _build_room_response(
    room,
    *,
    current_user_id: UUID,
    repo: SQLChatRepository,
    user_lookup: dict[UUID, kc.KeycloakUserSummary],
) -> ChatRoomResponseDTO:
    member_ids = await repo.get_room_member_ids(room.id)
    latest_message = await repo.get_latest_message(room.id)

    direct_user_id = None
    direct_display_name = None
    direct_email = None
    if room.room_type.value == "direct":
        direct_user_id = next((member_id for member_id in member_ids if member_id != current_user_id), None)
        if direct_user_id is not None:
            direct_user = user_lookup.get(direct_user_id)
            if direct_user is not None:
                direct_display_name = direct_user.display_name
                direct_email = direct_user.email

    return ChatRoomResponseDTO(
        id=room.id,
        room_type=room.room_type,
        association_id=room.association_id,
        name=room.name,
        created_at=room.created_at,
        member_ids=member_ids,
        direct_user_id=direct_user_id,
        direct_display_name=direct_display_name,
        direct_email=direct_email,
        last_message_preview=latest_message.content if latest_message else None,
        last_message_at=latest_message.created_at if latest_message else None,
    )


@router.get("/users/search", response_model=ChatUserSearchListResponseDTO)
async def search_chat_users(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    current_user_uuid = _parse_user_id(current_user_id)
    try:
        results = await SearchChatUsersUseCase(kc.search_users).execute(
            query=q,
            current_user_id=current_user_uuid,
            limit=limit,
        )
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    enriched_results = []
    for result in results:
        room = await repo.get_direct_room_for_users(current_user_uuid, result.id)
        existing_request = await repo.get_existing_request(current_user_uuid, result.id)
        relationship_status = ChatRelationshipStatusDTO.NONE
        room_id = room.id if room else None
        request_id = None

        if room is not None:
            relationship_status = ChatRelationshipStatusDTO.CONNECTED
        elif existing_request is not None:
            if existing_request.status.value == "pending":
                request_id = existing_request.id
                if existing_request.from_user_id == current_user_uuid:
                    relationship_status = ChatRelationshipStatusDTO.OUTGOING_PENDING
                else:
                    relationship_status = ChatRelationshipStatusDTO.INCOMING_PENDING
            elif existing_request.status.value == "accepted" and existing_request.room_id is not None:
                relationship_status = ChatRelationshipStatusDTO.CONNECTED
                room_id = existing_request.room_id

        enriched_results.append(
            result.model_copy(
                update={
                    "relationship_status": relationship_status,
                    "request_id": request_id,
                    "room_id": room_id,
                }
            )
        )
    return ChatUserSearchListResponseDTO(users=enriched_results)


@router.post("/requests", response_model=ChatRequestResponseDTO, status_code=201)
async def send_chat_request(
    body: SendChatRequestDTO,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        request = await SendChatRequestUseCase(repo, _target_user_exists).execute(
            _parse_user_id(current_user_id),
            body.to_user_id,
        )
    except ChatRequestAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DirectChatAlreadyExists as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(e),
                "room_id": str(e.room_id),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    user_lookup = await _load_user_lookup({request.from_user_id, request.to_user_id})
    return _build_request_response(request, user_lookup)


@router.post("/requests/{request_id}/respond", response_model=ChatRequestResponseDTO)
async def respond_to_chat_request(
    request_id: UUID,
    body: RespondChatRequestDTO,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        request = await RespondToChatRequestUseCase(repo).execute(
            request_id,
            _parse_user_id(current_user_id),
            body.accept,
        )
    except ChatRequestNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChatRequestForbidden as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ChatRequestAlreadyHandled as e:
        raise HTTPException(status_code=409, detail=str(e))
    try:
        user_lookup = await _load_user_lookup({request.from_user_id, request.to_user_id})
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _build_request_response(request, user_lookup)


@router.get("/requests/pending", response_model=list[ChatRequestResponseDTO])
async def get_pending_requests(
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    requests = await repo.get_pending_requests_for_user(_parse_user_id(current_user_id))
    try:
        user_lookup = await _load_user_lookup(
            {user_id for request in requests for user_id in (request.from_user_id, request.to_user_id)}
        )
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [_build_request_response(request, user_lookup) for request in requests]


@router.get("/requests/outgoing", response_model=list[ChatRequestResponseDTO])
async def get_outgoing_requests(
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    requests = await repo.get_outgoing_requests_for_user(_parse_user_id(current_user_id))
    try:
        user_lookup = await _load_user_lookup(
            {user_id for request in requests for user_id in (request.from_user_id, request.to_user_id)}
        )
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [_build_request_response(request, user_lookup) for request in requests]


@router.get("/rooms", response_model=ChatRoomListResponseDTO)
async def get_my_rooms(
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    current_user_uuid = _parse_user_id(current_user_id)
    rooms = await GetMyRoomsUseCase(repo).execute(current_user_uuid)
    all_member_ids: set[UUID] = set()

    for room in rooms:
        member_ids = await repo.get_room_member_ids(room.id)
        all_member_ids.update(member_ids)

    try:
        user_lookup = await _load_user_lookup(all_member_ids)
    except kc.KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    room_responses = []
    for room in rooms:
        room_responses.append(
            await _build_room_response(
                room,
                current_user_id=current_user_uuid,
                repo=repo,
                user_lookup=user_lookup,
            )
        )
    return ChatRoomListResponseDTO(rooms=room_responses)


@router.post("/associations/{association_id}/room")
async def get_or_create_association_room(
    association_id: UUID, name: str,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    _ = _parse_user_id(current_user_id)
    room = await GetOrCreateAssociationRoomUseCase(repo).execute(association_id, name)
    return ChatRoomResponseDTO(
        id=room.id, room_type=room.room_type, association_id=room.association_id,
        name=room.name, created_at=room.created_at,
    )


@router.post("/associations/{association_id}/join")
async def join_association_room(
    association_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        room = await JoinAssociationRoomUseCase(repo).execute(association_id, _parse_user_id(current_user_id))
    except ChatRoomNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Joined successfully", "room_id": str(room.id)}


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponseDTO])
async def get_room_messages(
    room_id: UUID, limit: int = 50, offset: int = 0,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        messages = await GetMessagesUseCase(repo).execute(
            room_id,
            _parse_user_id(current_user_id),
            limit,
            offset,
        )
    except NotARoomMember as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [
        ChatMessageResponseDTO(
            id=m.id,
            room_id=m.room_id,
            sender_id=m.sender_id,
            content=m.content,
            is_anonymous=m.is_anonymous,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponseDTO, status_code=201)
async def send_room_message(
    room_id: UUID,
    body: SendMessageDTO,
    current_user_id: str = Depends(get_current_user_id),
    repo: SQLChatRepository = Depends(get_chat_repo),
):
    try:
        message = await SendMessageUseCase(repo).execute(
            room_id,
            _parse_user_id(current_user_id),
            body.content,
            body.is_anonymous,
        )
    except NotARoomMember as e:
        raise HTTPException(status_code=403, detail=str(e))

    await manager.broadcast(
        str(room_id),
        {
            "type": "message",
            "id": str(message.id),
            "room_id": str(room_id),
            "sender_id": current_user_id if not body.is_anonymous else None,
            "content": message.content,
            "is_anonymous": message.is_anonymous,
            "timestamp": message.created_at.isoformat(),
        },
    )
    return ChatMessageResponseDTO(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id if not message.is_anonymous else None,
        content=message.content,
        is_anonymous=message.is_anonymous,
        created_at=message.created_at,
    )


@router.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket, room_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLChatRepository(session)
    token = websocket.query_params.get("token")
    legacy_user_id = websocket.query_params.get("user_id")
    try:
        room_uuid = UUID(room_id)
    except ValueError:
        await websocket.close(code=1008)
        return

    if token:
        try:
            claims = await validate_token(token)
            user_uuid = UUID(claims.sub)
        except (TokenValidationError, ValueError):
            await websocket.close(code=1008, reason="Invalid token")
            return
    elif legacy_user_id:
        try:
            user_uuid = UUID(legacy_user_id)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid user id")
            return
    else:
        await websocket.close(code=1008, reason="Missing token")
        return

    user_id = str(user_uuid)

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

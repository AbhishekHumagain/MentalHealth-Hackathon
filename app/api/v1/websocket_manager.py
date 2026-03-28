from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        connections = self.active_connections.get(room_id, [])
        if websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, room_id: str, message: dict):
        dead = []
        for ws in self.active_connections.get(room_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_connections[room_id].remove(ws)


manager = ConnectionManager()
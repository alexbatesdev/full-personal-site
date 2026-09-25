import asyncio
import json
from enum import Enum
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["live-cursors"])

class Action(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    POSITIONS = "positions"
    MOVE = "move"

class Coords(BaseModel):
    x: float
    y: float

class WebSocketMessage(BaseModel):
    action: Action
    coords: Coords | None = None
    message: str | None = None
    user_id: str

connected_clients: dict[str, dict[str, Any]] = {}

@router.get("/cursors")
async def get_cursors() -> dict[str, dict[str, float]]:
    return {
        user_id: client["coords"].model_dump()
        for user_id, client in connected_clients.items()
    }

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_clients[user_id] = {
        "websocket": websocket,
        "coords": Coords(x=0, y=0),
    }

    try:
        while True:
            payload = await websocket.receive_text()
            message = WebSocketMessage.model_validate_json(payload)

            if message.action == Action.MOVE and message.coords is not None:
                connected_clients[user_id]["coords"] = Coords(
                    x=message.coords.x,
                    y=message.coords.y,
                )

            elif message.action == Action.MESSAGE:
                await broadcast_message(message)

    except WebSocketDisconnect:
        connected_clients.pop(user_id, None)
        await websocket.close()

async def broadcast_message(message: WebSocketMessage):
    disconnected_clients: list[str] = []

    for user_id, client in connected_clients.items():
        try:
            await client["websocket"].send_text(message.model_dump_json())
        except Exception:
            disconnected_clients.append(user_id)

    for user_id in disconnected_clients:
        connected_clients.pop(user_id, None)

async def broadcast_positions():
    while True:
        if connected_clients:
            positions = {
                user_id: client["coords"].model_dump()
                for user_id, client in connected_clients.items()
            }

            message = WebSocketMessage(
                action=Action.POSITIONS,
                coords=None,
                message=json.dumps(positions),
                user_id="server",
            )

            disconnected_clients: list[str] = []

            for user_id, client in connected_clients.items():
                try:
                    await client["websocket"].send_text(message.model_dump_json())
                except Exception:
                    disconnected_clients.append(user_id)

            for user_id in disconnected_clients:
                connected_clients.pop(user_id, None)

        await asyncio.sleep(0.03)
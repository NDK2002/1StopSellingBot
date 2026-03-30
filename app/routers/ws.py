
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import manager
import asyncio

router = APIRouter(prefix="/api/ws", tags=["websocket"])

@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive, listen for ping from client
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_text('pong')
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

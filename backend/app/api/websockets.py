from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import manager

ws_router = APIRouter()

@ws_router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket, user_id: int = Query(default=1)):
    """
    WebSocket endpoint for real-time market pulse updates and user notifications.
    Associates the connection with the given user_id for targeted alerts.
    """
    await manager.connect(websocket, user_id=user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

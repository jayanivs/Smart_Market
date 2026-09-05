import json
import os
import asyncio
from typing import List, Dict, Optional
from fastapi import WebSocket

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class ConnectionManager:
    """
    Manages active WebSocket connections with multi-instance support
    via Redis Pub/Sub channels (market_pulse:global and market_pulse:user:{user_id}).
    Falls back gracefully to local memory routing if Redis is unavailable.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, List[WebSocket]] = {}
        self.socket_user_map: Dict[WebSocket, int] = {}
        self.redis_pub = None
        self.redis_sub_task = None
        self._redis_available = False
        self._stopping = False

    async def init_redis(self):
        """Attempts to initialize Redis Pub/Sub client and starts the background listener."""
        try:
            import redis.asyncio as aioredis
            self.redis_pub = aioredis.from_url(REDIS_URL, decode_responses=True)
            await self.redis_pub.ping()
            self._redis_available = True
            self.redis_sub_task = asyncio.create_task(self._redis_listener())
            print(f"[WebSocketManager] Connected to Redis Pub/Sub at {REDIS_URL}")
        except Exception as e:
            self._redis_available = False
            print(f"[WebSocketManager] Redis Pub/Sub disabled (using local memory fallback): {e}")

    async def _redis_listener(self):
        """Background worker that listens for Redis Pub/Sub messages and distributes them locally."""
        import redis.asyncio as aioredis
        while not self._stopping:
            try:
                r = aioredis.from_url(REDIS_URL, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.psubscribe("market_pulse:*")
                print("[WebSocketManager] Subscribed to Redis channels: market_pulse:*")
                async for message in pubsub.listen():
                    if message and message.get("type") in ("pmessage", "message"):
                        channel = message.get("channel", "")
                        data_str = message.get("data")
                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str) if isinstance(data_str, str) else data_str
                        except Exception:
                            continue

                        if channel == "market_pulse:global":
                            await self._local_broadcast(data)
                        elif channel.startswith("market_pulse:user:"):
                            try:
                                uid = int(channel.split(":")[-1])
                                await self._local_send_user(uid, data)
                            except Exception:
                                pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[WebSocketManager] Redis listener disconnected ({e}), retrying in 3s...")
                await asyncio.sleep(3)

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Accepts a WebSocket connection and associates it with a user."""
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id is not None:
            self.socket_user_map[websocket] = user_id
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket from active connections."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        user_id = self.socket_user_map.pop(websocket, None)
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def _local_broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _local_send_user(self, user_id: int, message: dict):
        conns = list(self.user_connections.get(user_id, []))
        for conn in conns:
            try:
                await conn.send_json(message)
            except Exception:
                pass

    async def broadcast(self, message: dict):
        """
        Broadcasts a message globally to all connected users.
        Publishes to Redis if available, or broadcasts locally.
        """
        if self._redis_available and self.redis_pub:
            try:
                await self.redis_pub.publish("market_pulse:global", json.dumps(message))
                return
            except Exception:
                pass
        await self._local_broadcast(message)

    async def send_user_notification(self, user_id: int, message: dict):
        """
        Sends a notification specifically to a given user across server instances.
        Publishes to Redis channel market_pulse:user:{user_id}.
        """
        if self._redis_available and self.redis_pub:
            try:
                await self.redis_pub.publish(f"market_pulse:user:{user_id}", json.dumps(message))
                return
            except Exception:
                pass
        await self._local_send_user(user_id, message)

    async def close(self):
        self._stopping = True
        if self.redis_sub_task:
            self.redis_sub_task.cancel()
        if self.redis_pub:
            await self.redis_pub.close()

manager = ConnectionManager()

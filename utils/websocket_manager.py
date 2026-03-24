"""
🔌 WEBSOCKET MANAGER
Real-time bidirectional communication with clients
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional, Callable
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum
from utils.logger import logger


class MessageType(Enum):
    """WebSocket message types"""
    # System
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Query lifecycle
    QUERY_RECEIVED = "query_received"
    PLANNING_STARTED = "planning_started"
    PLANNING_COMPLETED = "planning_completed"
    EXECUTION_STARTED = "execution_started"
    STEP_PROGRESS = "step_progress"
    EXECUTION_COMPLETED = "execution_completed"
    CRITIQUE_STARTED = "critique_started"
    CRITIQUE_COMPLETED = "critique_completed"
    VERIFICATION_STARTED = "verification_started"
    RESULT_READY = "result_ready"
    
    # Voice
    VOICE_LISTENING = "voice_listening"
    VOICE_TRANSCRIBED = "voice_transcribed"
    VOICE_PROCESSING = "voice_processing"
    VOICE_SPEAKING = "voice_speaking"
    
    # Analytics
    ANALYTICS_UPDATE = "analytics_update"
    AGENT_STATUS = "agent_status"


class Connection:
    """WebSocket connection wrapper"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict = {}
    
    async def send_json(self, data: Dict):
        """Send JSON message"""
        try:
            await self.websocket.send_json(data)
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"Send error to {self.client_id}: {e}")
            raise
    
    async def send_message(
        self,
        message_type: MessageType,
        data: Any = None,
        **kwargs
    ):
        """Send structured message"""
        message = {
            "type": message_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "client_id": self.client_id,
            **kwargs
        }
        await self.send_json(message)


class WebSocketManager:
    """
    🔌 WEBSOCKET MANAGER
    
    Features:
    - Connection management
    - Broadcasting
    - Room/channel support
    - Subscription system
    - Heartbeat monitoring
    - Message queuing
    """
    
    def __init__(self):
        self.connections: Dict[str, Connection] = {}
        self.rooms: Dict[str, Set[str]] = {}  # room_id -> {client_ids}
        self._heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Message handlers
        self._handlers: Dict[str, Callable] = {}
        
        # Stats
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
        
        logger.info("🔌 WebSocketManager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str) -> Connection:
        """Register new WebSocket connection"""
        await websocket.accept()
        
        connection = Connection(websocket, client_id)
        self.connections[client_id] = connection
        
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.connections)
        
        # Send welcome message
        await connection.send_message(
            MessageType.CONNECTED,
            {
                "client_id": client_id,
                "server_time": datetime.now().isoformat()
            }
        )
        
        logger.info(f"🔌 Client connected: {client_id} (total: {len(self.connections)})")
        
        # Start heartbeat if not running
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection
    
    async def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.connections:
            connection = self.connections[client_id]
            
            # Leave all rooms
            for room_id in list(self.rooms.keys()):
                if client_id in self.rooms[room_id]:
                    self.rooms[room_id].remove(client_id)
            
            # Remove connection
            del self.connections[client_id]
            
            self.stats["active_connections"] = len(self.connections)
            
            logger.info(f"🔌 Client disconnected: {client_id} (total: {len(self.connections)})")
    
    async def send_to_client(
        self,
        client_id: str,
        message_type: MessageType,
        data: Any = None
    ):
        """Send message to specific client"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_message(message_type, data)
                self.stats["messages_sent"] += 1
            except Exception as e:
                logger.error(f"Failed to send to {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(
        self,
        message_type: MessageType,
        data: Any = None,
        exclude: Set[str] = None
    ):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        
        disconnected = []
        
        for client_id, connection in self.connections.items():
            if client_id in exclude:
                continue
            
            try:
                await connection.send_message(message_type, data)
                self.stats["messages_sent"] += 1
            except Exception as e:
                logger.error(f"Broadcast error to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up failed connections
        for client_id in disconnected:
            await self.disconnect(client_id)
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message_type: MessageType,
        data: Any = None
    ):
        """Broadcast to all clients in a room"""
        if room_id not in self.rooms:
            return
        
        for client_id in list(self.rooms[room_id]):
            await self.send_to_client(client_id, message_type, data)
    
    def join_room(self, client_id: str, room_id: str):
        """Add client to a room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(client_id)
        logger.debug(f"🔌 {client_id} joined room '{room_id}'")
    
    def leave_room(self, client_id: str, room_id: str):
        """Remove client from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(client_id)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
    
    def subscribe(self, client_id: str, topic: str):
        """Subscribe client to a topic"""
        if client_id in self.connections:
            self.connections[client_id].subscriptions.add(topic)
    
    def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe client from a topic"""
        if client_id in self.connections:
            self.connections[client_id].subscriptions.discard(topic)
    
    async def publish(self, topic: str, message_type: MessageType, data: Any = None):
        """Publish message to all subscribers of a topic"""
        for client_id, connection in self.connections.items():
            if topic in connection.subscriptions:
                await self.send_to_client(client_id, message_type, data)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register message handler"""
        self._handlers[message_type] = handler
    
    async def handle_message(self, client_id: str, message: Dict):
        """Handle incoming message"""
        self.stats["messages_received"] += 1
        
        message_type = message.get("type")
        
        if message_type in self._handlers:
            try:
                await self._handlers[message_type](client_id, message)
            except Exception as e:
                logger.error(f"Handler error for {message_type}: {e}")
                await self.send_to_client(
                    client_id,
                    MessageType.ERROR,
                    {"error": str(e)}
                )
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all clients"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                if not self.connections:
                    continue
                
                await self.broadcast(
                    MessageType.PING,
                    {"server_time": datetime.now().isoformat()}
                )
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    def get_stats(self) -> Dict:
        """Get WebSocket statistics"""
        return {
            **self.stats,
            "rooms": {
                room_id: len(clients)
                for room_id, clients in self.rooms.items()
            }
        }
    
    async def shutdown(self):
        """Shutdown all connections"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        for client_id in list(self.connections.keys()):
            await self.disconnect(client_id)
        
        logger.info("🔌 WebSocketManager shutdown complete")


# ============ SINGLETON ============
_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create WebSocket manager instance"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
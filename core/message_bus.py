"""
📬 MESSAGE BUS
Inter-agent communication system with pub/sub pattern.
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from utils.logger import logger
import uuid


class EventType(Enum):
    """Event types for the message bus"""
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # Pipeline events
    PLANNING_STARTED = "planning.started"
    PLANNING_COMPLETED = "planning.completed"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    STEP_COMPLETED = "step.completed"
    CRITIQUE_STARTED = "critique.started"
    CRITIQUE_COMPLETED = "critique.completed"
    VERIFICATION_COMPLETED = "verification.completed"
    
    # Voice events
    VOICE_INPUT_STARTED = "voice.input.started"
    VOICE_INPUT_COMPLETED = "voice.input.completed"
    VOICE_OUTPUT_STARTED = "voice.output.started"
    VOICE_OUTPUT_COMPLETED = "voice.output.completed"
    
    # System events
    QUERY_RECEIVED = "query.received"
    RESPONSE_READY = "response.ready"
    ERROR_OCCURRED = "error.occurred"
    
    # Custom
    CUSTOM = "custom"


@dataclass
class Event:
    """Event object for message bus"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM
    source: str = "system"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id
        }


class MessageBus:
    """
    📬 MESSAGE BUS
    
    Pub/Sub system for inter-agent communication.
    
    Features:
    - Subscribe to specific event types
    - Wildcard subscriptions
    - Async event handling
    - Event history
    - WebSocket broadcast support
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history = 500
        self._websocket_clients: List[Any] = []
        
        logger.info("📬 MessageBus initialized")
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to a specific event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"📬 Subscribed to {event_type.value}")
    
    def subscribe_all(self, handler: Callable):
        """Subscribe to all events"""
        self._wildcard_subscribers.append(handler)
        logger.debug("📬 Subscribed to ALL events")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
    
    async def publish(self, event: Event):
        """Publish an event"""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        logger.debug(f"📬 Event: {event.type.value} from {event.source}")
        
        # Get handlers
        handlers = self._subscribers.get(event.type, []) + self._wildcard_subscribers
        
        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
        
        # Broadcast to WebSocket clients
        await self._broadcast_websocket(event)
    
    async def emit(
        self,
        event_type: EventType,
        source: str = "system",
        data: Dict = None,
        correlation_id: str = None
    ):
        """Convenience method to create and publish event"""
        event = Event(
            type=event_type,
            source=source,
            data=data or {},
            correlation_id=correlation_id
        )
        await self.publish(event)
    
    # ============ WEBSOCKET SUPPORT ============
    
    def register_websocket(self, websocket):
        """Register a WebSocket client for live updates"""
        self._websocket_clients.append(websocket)
        logger.info(f"📬 WebSocket client registered (total: {len(self._websocket_clients)})")
    
    def unregister_websocket(self, websocket):
        """Unregister a WebSocket client"""
        self._websocket_clients = [w for w in self._websocket_clients if w != websocket]
        logger.info(f"📬 WebSocket client unregistered (total: {len(self._websocket_clients)})")
    
    async def _broadcast_websocket(self, event: Event):
        """Broadcast event to all WebSocket clients"""
        if not self._websocket_clients:
            return
        
        message = event.to_dict()
        
        # Remove closed connections
        active_clients = []
        for client in self._websocket_clients:
            try:
                await client.send_json(message)
                active_clients.append(client)
            except Exception as e:
                logger.debug(f"WebSocket send failed: {e}")
        
        self._websocket_clients = active_clients
    
    # ============ HISTORY ============
    
    def get_history(self, limit: int = 50, event_type: EventType = None) -> List[Dict]:
        """Get event history"""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return [e.to_dict() for e in events[-limit:]]
    
    def clear_history(self):
        """Clear event history"""
        self._event_history = []


# ============ SINGLETON ============
_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get or create message bus instance"""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus
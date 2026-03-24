"""
🎯 BASE AGENT CLASS
Every agent inherits from this - ensures independence and standardization
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from utils.logger import logger


class AgentStatus(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class MessageType(Enum):
    """Inter-agent message types"""
    REQUEST = "request"
    RESPONSE = "response"
    FEEDBACK = "feedback"
    ERROR = "error"
    BROADCAST = "broadcast"


@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    message_type: MessageType = MessageType.REQUEST
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # Links related messages
    priority: int = 5  # 1=highest, 10=lowest
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority
        }


@dataclass
class AgentMemory:
    """Agent's personal memory - short term and long term"""
    short_term: List[Dict] = field(default_factory=list)  # Current session
    long_term: List[Dict] = field(default_factory=list)   # Persistent
    max_short_term: int = 50
    max_long_term: int = 500
    
    def remember(self, item: Dict, long_term: bool = False):
        """Store memory item"""
        item["remembered_at"] = datetime.now().isoformat()
        
        if long_term:
            self.long_term.append(item)
            if len(self.long_term) > self.max_long_term:
                self.long_term.pop(0)
        else:
            self.short_term.append(item)
            if len(self.short_term) > self.max_short_term:
                self.short_term.pop(0)
    
    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        """Recall relevant memories"""
        query_lower = query.lower()
        all_memories = self.short_term + self.long_term
        
        # Simple relevance scoring
        scored = []
        for mem in all_memories:
            score = 0
            mem_str = str(mem).lower()
            for word in query_lower.split():
                if word in mem_str:
                    score += 1
            if score > 0:
                scored.append((score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in scored[:limit]]
    
    def clear_short_term(self):
        """Clear session memory"""
        self.short_term = []


class BaseAgent(ABC):
    """
    🎯 ABSTRACT BASE AGENT
    
    Every agent MUST inherit from this class.
    Ensures:
    - Independent operation
    - Standard communication
    - Self-monitoring
    - Memory management
    - Error handling
    """
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.outbox: asyncio.Queue = asyncio.Queue()
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.task_count = 0
        self.success_count = 0
        self.error_count = 0
        self.confidence_threshold = 0.7
        self._running = False
        
        # Performance metrics
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_execution_time_ms": 0,
            "total_execution_time_ms": 0
        }
        
        logger.info(f"🤖 Agent initialized: {self.name} ({self.agent_id})")
    
    # ============ ABSTRACT METHODS (Must implement) ============
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing logic - MUST be implemented by each agent
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input before processing
        """
        pass
    
    @abstractmethod
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate output after processing
        """
        pass
    
    # ============ CORE METHODS ============
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution wrapper with monitoring and error handling
        """
        start_time = datetime.now()
        self.status = AgentStatus.EXECUTING
        self.last_active = start_time
        self.task_count += 1
        
        result = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "status": "pending",
            "input": input_data,
            "output": None,
            "error": None,
            "execution_time_ms": 0,
            "confidence": 0.0,
            "timestamp": start_time.isoformat()
        }
        
        try:
            # Step 1: Validate input
            if not await self.validate_input(input_data):
                raise ValueError(f"Input validation failed for {self.name}")
            
            # Step 2: Process
            self.status = AgentStatus.THINKING
            output = await self.process(input_data)
            
            # Step 3: Validate output
            if not await self.validate_output(output):
                raise ValueError(f"Output validation failed for {self.name}")
            
            # Step 4: Calculate confidence
            confidence = await self.calculate_confidence(input_data, output)
            
            # Step 5: Self-reflect (optional improvement)
            if confidence < self.confidence_threshold:
                logger.warning(f"⚠️ {self.name}: Low confidence ({confidence:.2f}), attempting improvement...")
                output = await self.self_improve(input_data, output, confidence)
                confidence = await self.calculate_confidence(input_data, output)
            
            # Success
            result["status"] = "success"
            result["output"] = output
            result["confidence"] = confidence
            self.success_count += 1
            self.metrics["successful_tasks"] += 1
            
            # Remember this success
            self.memory.remember({
                "type": "success",
                "input_summary": str(input_data)[:200],
                "output_summary": str(output)[:200],
                "confidence": confidence
            })
            
        except Exception as e:
            # Failure
            result["status"] = "failed"
            result["error"] = str(e)
            self.error_count += 1
            self.metrics["failed_tasks"] += 1
            self.status = AgentStatus.FAILED
            
            # Remember this failure for learning
            self.memory.remember({
                "type": "failure",
                "input_summary": str(input_data)[:200],
                "error": str(e)
            })
            
            logger.error(f"❌ {self.name} failed: {e}")
        
        finally:
            # Calculate timing
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds() * 1000
            result["execution_time_ms"] = round(execution_time, 2)
            
            # Update metrics
            self.metrics["total_tasks"] += 1
            self.metrics["total_execution_time_ms"] += execution_time
            self.metrics["avg_execution_time_ms"] = (
                self.metrics["total_execution_time_ms"] / self.metrics["total_tasks"]
            )
            
            # Reset status
            self.status = AgentStatus.IDLE if result["status"] == "success" else AgentStatus.FAILED
        
        return result
    
    async def calculate_confidence(self, input_data: Dict, output: Dict) -> float:
        """
        Calculate confidence score (0.0 to 1.0)
        Override in child classes for specific logic
        """
        # Base confidence calculation
        confidence = 0.5
        
        # Has output?
        if output and len(str(output)) > 10:
            confidence += 0.2
        
        # No errors in output?
        if "error" not in str(output).lower():
            confidence += 0.2
        
        # Based on historical success rate
        if self.task_count > 0:
            success_rate = self.success_count / self.task_count
            confidence += success_rate * 0.1
        
        return min(confidence, 1.0)
    
    async def self_improve(self, input_data: Dict, current_output: Dict, confidence: float) -> Dict:
        """
        Self-improvement mechanism - agent tries to improve low-confidence output
        Override in child classes for specific improvement logic
        """
        logger.info(f"🔄 {self.name}: Self-improvement attempt...")
        # Default: return current output (override for specific improvements)
        return current_output
    
    # ============ COMMUNICATION ============
    
    async def send_message(self, receiver: str, payload: Dict, msg_type: MessageType = MessageType.REQUEST):
        """Send message to another agent"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=msg_type,
            payload=payload
        )
        await self.outbox.put(message)
        logger.debug(f"📤 {self.name} -> {receiver}: {msg_type.value}")
        return message.id
    
    async def receive_message(self, timeout: float = 5.0) -> Optional[AgentMessage]:
        """Receive message from inbox"""
        try:
            message = await asyncio.wait_for(self.inbox.get(), timeout=timeout)
            logger.debug(f"📥 {self.name} received from {message.sender}")
            return message
        except asyncio.TimeoutError:
            return None
    
    async def broadcast(self, payload: Dict):
        """Broadcast message to all agents"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver="*",  # Broadcast
            message_type=MessageType.BROADCAST,
            payload=payload
        )
        await self.outbox.put(message)
    
    # ============ STATUS & MONITORING ============
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metrics": self.metrics,
            "memory_size": {
                "short_term": len(self.memory.short_term),
                "long_term": len(self.memory.long_term)
            }
        }
    
    def is_healthy(self) -> bool:
        """Health check"""
        if self.status == AgentStatus.FAILED:
            return False
        if self.task_count > 10 and (self.error_count / self.task_count) > 0.5:
            return False  # Too many failures
        return True
    
    def __repr__(self):
        return f"<{self.name} ({self.status.value}) - Tasks: {self.task_count}, Success: {self.success_count}>"
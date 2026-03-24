"""
🔧 STATE MACHINE
Advanced state management for the multi-agent system.
Tracks execution flow, handles transitions, manages history.
"""

import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from utils.logger import logger


class SystemState(Enum):
    """System-wide states"""
    IDLE = "idle"
    RECEIVING_INPUT = "receiving_input"
    PLANNING = "planning"
    EXECUTING = "executing"
    CRITIQUING = "critiquing"
    VERIFYING = "verifying"
    RESPONDING = "responding"
    SPEAKING = "speaking"  # Voice output
    LISTENING = "listening"  # Voice input
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class StateTransition:
    """Record of a state transition"""
    from_state: SystemState
    to_state: SystemState
    timestamp: datetime
    trigger: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Current execution context"""
    query: str = ""
    plan: List[Dict] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    critique: Dict = field(default_factory=dict)
    final_output: Dict = field(default_factory=dict)
    iteration: int = 0
    start_time: Optional[datetime] = None
    voice_enabled: bool = False
    voice_input_text: str = ""


class StateMachine:
    """
    🔧 ADVANCED STATE MACHINE
    
    Features:
    - State transitions with validation
    - Event hooks for state changes
    - Execution context management
    - History tracking
    - Concurrent state handling
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        SystemState.IDLE: [
            SystemState.RECEIVING_INPUT,
            SystemState.LISTENING,
            SystemState.PLANNING
        ],
        SystemState.LISTENING: [
            SystemState.RECEIVING_INPUT,
            SystemState.PLANNING,
            SystemState.IDLE,
            SystemState.ERROR
        ],
        SystemState.RECEIVING_INPUT: [
            SystemState.PLANNING,
            SystemState.LISTENING,
            SystemState.ERROR
        ],
        SystemState.PLANNING: [
            SystemState.EXECUTING,
            SystemState.ERROR,
            SystemState.IDLE
        ],
        SystemState.EXECUTING: [
            SystemState.CRITIQUING,
            SystemState.VERIFYING,
            SystemState.ERROR
        ],
        SystemState.CRITIQUING: [
            SystemState.EXECUTING,  # Retry
            SystemState.VERIFYING,
            SystemState.ERROR
        ],
        SystemState.VERIFYING: [
            SystemState.RESPONDING,
            SystemState.COMPLETED,
            SystemState.ERROR
        ],
        SystemState.RESPONDING: [
            SystemState.SPEAKING,
            SystemState.COMPLETED,
            SystemState.IDLE
        ],
        SystemState.SPEAKING: [
            SystemState.COMPLETED,
            SystemState.LISTENING,
            SystemState.IDLE
        ],
        SystemState.ERROR: [
            SystemState.IDLE,
            SystemState.PLANNING
        ],
        SystemState.COMPLETED: [
            SystemState.IDLE,
            SystemState.LISTENING
        ]
    }
    
    def __init__(self):
        self.current_state = SystemState.IDLE
        self.context = ExecutionContext()
        self.history: List[StateTransition] = []
        self.max_history = 100
        
        # Event hooks
        self._on_enter_hooks: Dict[SystemState, List[Callable]] = {}
        self._on_exit_hooks: Dict[SystemState, List[Callable]] = {}
        self._global_hooks: List[Callable] = []
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("🔧 StateMachine initialized")
    
    async def transition(
        self, 
        to_state: SystemState, 
        trigger: str = "manual",
        metadata: Dict = None
    ) -> bool:
        """
        Transition to a new state
        
        Returns True if transition successful, False otherwise
        """
        async with self._lock:
            from_state = self.current_state
            
            # Validate transition
            if not self._is_valid_transition(from_state, to_state):
                logger.warning(
                    f"⚠️ Invalid transition: {from_state.value} -> {to_state.value}"
                )
                return False
            
            # Record transition
            transition = StateTransition(
                from_state=from_state,
                to_state=to_state,
                timestamp=datetime.now(),
                trigger=trigger,
                metadata=metadata or {}
            )
            
            self.history.append(transition)
            
            # Trim history if needed
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            
            # Execute exit hooks
            await self._execute_hooks(self._on_exit_hooks.get(from_state, []), transition)
            
            # Change state
            self.current_state = to_state
            
            # Execute enter hooks
            await self._execute_hooks(self._on_enter_hooks.get(to_state, []), transition)
            
            # Execute global hooks
            await self._execute_hooks(self._global_hooks, transition)
            
            logger.info(f"🔄 State: {from_state.value} → {to_state.value} ({trigger})")
            
            return True
    
    def _is_valid_transition(self, from_state: SystemState, to_state: SystemState) -> bool:
        """Check if transition is valid"""
        valid_targets = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    async def _execute_hooks(self, hooks: List[Callable], transition: StateTransition):
        """Execute state hooks"""
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(transition)
                else:
                    hook(transition)
            except Exception as e:
                logger.error(f"Hook execution error: {e}")
    
    # ============ HOOK REGISTRATION ============
    
    def on_enter(self, state: SystemState):
        """Decorator for enter hooks"""
        def decorator(func: Callable):
            if state not in self._on_enter_hooks:
                self._on_enter_hooks[state] = []
            self._on_enter_hooks[state].append(func)
            return func
        return decorator
    
    def on_exit(self, state: SystemState):
        """Decorator for exit hooks"""
        def decorator(func: Callable):
            if state not in self._on_exit_hooks:
                self._on_exit_hooks[state] = []
            self._on_exit_hooks[state].append(func)
            return func
        return decorator
    
    def on_transition(self, func: Callable):
        """Register global transition hook"""
        self._global_hooks.append(func)
        return func
    
    # ============ CONTEXT MANAGEMENT ============
    
    def set_context(self, **kwargs):
        """Update execution context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
    
    def get_context(self) -> ExecutionContext:
        """Get current context"""
        return self.context
    
    def reset_context(self):
        """Reset context for new execution"""
        self.context = ExecutionContext()
    
    # ============ STATUS ============
    
    def get_status(self) -> Dict:
        """Get current state machine status"""
        return {
            "current_state": self.current_state.value,
            "context": {
                "query": self.context.query[:100] if self.context.query else "",
                "plan_steps": len(self.context.plan),
                "results_count": len(self.context.results),
                "iteration": self.context.iteration,
                "voice_enabled": self.context.voice_enabled
            },
            "history_length": len(self.history),
            "last_transition": self.history[-1].to_state.value if self.history else None
        }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent transition history"""
        recent = self.history[-limit:]
        return [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "trigger": t.trigger,
                "timestamp": t.timestamp.isoformat()
            }
            for t in recent
        ]


# ============ SINGLETON ============
_state_machine: Optional[StateMachine] = None


def get_state_machine() -> StateMachine:
    """Get or create state machine instance"""
    global _state_machine
    if _state_machine is None:
        _state_machine = StateMachine()
    return _state_machine
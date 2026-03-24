"""
🤖 AI Operations Assistant - Agents Package

Multi-agent system with independent, specialized agents.
"""

from agents.base_agent import (
    BaseAgent,
    AgentStatus,
    AgentMessage,
    MessageType,
    AgentMemory
)
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.verifier import VerifierAgent
from agents.orchestrator import Orchestrator, get_orchestrator, process_query

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentStatus",
    "AgentMessage",
    "MessageType",
    "AgentMemory",
    
    # Agents
    "PlannerAgent",
    "ExecutorAgent",
    "CriticAgent",
    "VerifierAgent",
    
    # Orchestrator
    "Orchestrator",
    "get_orchestrator",
    "process_query"
]

__version__ = "2.0.0"
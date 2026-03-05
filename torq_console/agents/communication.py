"""
TORQ Multi-Agent Orchestration System - Communication Layer

Handles inter-agent messaging, collaboration chains, and result aggregation.
This module provides the communication infrastructure for multi-agent workflows.

This module is designed to work standalone without heavy torq_console imports.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# Communication Models
# ============================================================================

class MessageType(str, Enum):
    """Types of inter-agent messages."""
    QUERY = "query"                    # Initial query to agent
    RESPONSE = "response"              # Response from agent
    HANDOFF = "handoff"                # Transfer to another agent
    COLLABORATE = "collaborate"        # Request collaboration
    AGGREGATE = "aggregate"            # Aggregate results
    ERROR = "error"                    # Error notification
    STATUS = "status"                  # Status update


class CollaborationMode(str, Enum):
    """Modes of agent collaboration."""
    SEQUENTIAL = "sequential"          # Agents work one after another
    PARALLEL = "parallel"              # Agents work simultaneously
    HIERARCHICAL = "hierarchical"      # Lead agent delegates to sub-agents
    CONSENSUS = "consensus"            # Agents vote on best approach


@dataclass
class AgentMessage:
    """Message between agents."""
    message_id: str
    task_id: str
    message_type: MessageType
    source_agent: str
    target_agent: Optional[str]        # None for broadcast
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_message_id: Optional[str] = None  # For message chains

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "task_id": self.task_id,
            "message_type": self.message_type.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "content": self.content,
            "context": self.context,
            "result": self.result,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "parent_message_id": self.parent_message_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        message_type = data.get("message_type", "query")
        if isinstance(message_type, str):
            try:
                message_type = MessageType(message_type)
            except ValueError:
                message_type = MessageType.QUERY

        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            task_id=data.get("task_id", ""),
            message_type=message_type,
            source_agent=data.get("source_agent", ""),
            target_agent=data.get("target_agent"),
            content=data.get("content", ""),
            context=data.get("context", {}),
            result=data.get("result"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            parent_message_id=data.get("parent_message_id")
        )


@dataclass
class CollaborationChain:
    """A chain of agent collaborations."""
    chain_id: str
    task_id: str
    agents: List[str]                  # Order of agents in chain
    messages: List[AgentMessage] = field(default_factory=list)
    final_result: Optional[Any] = None
    status: str = "pending"            # pending, running, completed, failed
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the chain."""
        self.messages.append(message)

    def get_current_agent(self) -> Optional[str]:
        """Get the current agent (next to process)."""
        processed_agents = {m.source_agent for m in self.messages}
        for agent in self.agents:
            if agent not in processed_agents:
                return agent
        return None

    def is_complete(self) -> bool:
        """Check if chain is complete (all agents processed)."""
        processed_agents = {m.source_agent for m in self.messages}
        return all(agent in processed_agents for agent in self.agents)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_id": self.chain_id,
            "task_id": self.task_id,
            "agents": self.agents,
            "messages": [m.to_dict() for m in self.messages],
            "final_result": self.final_result,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }


@dataclass
class AggregatedResult:
    """Result from aggregating multiple agent responses."""
    task_id: str
    responses: Dict[str, Any]          # agent_id -> response
    primary_agent: Optional[str] = None
    synthesized_response: Optional[str] = None
    confidence_score: float = 0.0
    consensus_level: float = 0.0       # 0-1, how much agents agree
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "responses": self.responses,
            "primary_agent": self.primary_agent,
            "synthesized_response": self.synthesized_response,
            "confidence_score": self.confidence_score,
            "consensus_level": self.consensus_level,
            "metadata": self.metadata
        }


# ============================================================================
# Agent Communication Interface
# ============================================================================

class AgentCommunicator:
    """
    Handles communication between agents in multi-agent workflows.

    Features:
    - Send messages between agents
    - Create collaboration chains
    - Aggregate results from multiple agents
    - Track message history
    """

    def __init__(self):
        """Initialize agent communicator."""
        self._active_chains: Dict[str, CollaborationChain] = {}
        self._message_history: List[AgentMessage] = []

    def create_message(
        self,
        task_id: str,
        message_type: MessageType,
        source_agent: str,
        content: str,
        target_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        result: Any = None,
        parent_message_id: Optional[str] = None
    ) -> AgentMessage:
        """Create a new agent message."""
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            task_id=task_id,
            message_type=message_type,
            source_agent=source_agent,
            target_agent=target_agent,
            content=content,
            context=context or {},
            result=result,
            parent_message_id=parent_message_id
        )

    def create_collaboration_chain(
        self,
        task_id: str,
        agents: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> CollaborationChain:
        """Create a new collaboration chain."""
        chain = CollaborationChain(
            chain_id=str(uuid.uuid4()),
            task_id=task_id,
            agents=agents,
            metadata=metadata or {}
        )
        self._active_chains[chain.chain_id] = chain
        logger.info(f"Created collaboration chain {chain.chain_id} with agents: {agents}")
        return chain

    def get_chain(self, chain_id: str) -> Optional[CollaborationChain]:
        """Get a collaboration chain by ID."""
        return self._active_chains.get(chain_id)

    def add_message_to_chain(self, chain_id: str, message: AgentMessage) -> bool:
        """Add a message to a collaboration chain."""
        chain = self.get_chain(chain_id)
        if not chain:
            logger.warning(f"Chain not found: {chain_id}")
            return False

        chain.add_message(message)
        self._message_history.append(message)

        # Check if chain is complete
        if chain.is_complete():
            chain.status = "completed"
            chain.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Collaboration chain {chain_id} completed")

        return True

    def get_next_agent_in_chain(self, chain_id: str) -> Optional[str]:
        """Get the next agent to process in a chain."""
        chain = self.get_chain(chain_id)
        if not chain:
            return None
        return chain.get_current_agent()

    def create_handoff_message(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        context: Dict[str, Any],
        reason: str
    ) -> AgentMessage:
        """Create a handoff message between agents."""
        return self.create_message(
            task_id=task_id,
            message_type=MessageType.HANDOFF,
            source_agent=from_agent,
            target_agent=to_agent,
            content=reason,
            context=context
        )

    async def send_message(
        self,
        message: AgentMessage,
        handler: Optional[Callable[[AgentMessage], Awaitable[Any]]] = None
    ) -> Optional[Any]:
        """
        Send a message to an agent.

        Args:
            message: The message to send
            handler: Optional async handler function to process the message

        Returns:
            Result from handler if provided, None otherwise
        """
        self._message_history.append(message)
        logger.debug(
            f"Sent message {message.message_id}: {message.source_agent} -> "
            f"{message.target_agent or 'broadcast'} ({message.message_type.value})"
        )

        if handler:
            try:
                result = await handler(message)
                message.result = result
                return result
            except Exception as e:
                logger.error(f"Handler error for message {message.message_id}: {e}")
                return None

        return None

    def aggregate_results(
        self,
        task_id: str,
        responses: Dict[str, Any],
        mode: str = "first"  # first, best, synthesize, vote
    ) -> AggregatedResult:
        """
        Aggregate results from multiple agents.

        Args:
            task_id: Task identifier
            responses: Dictionary of agent_id -> response
            mode: Aggregation mode (first, best, synthesize, vote)

        Returns:
            AggregatedResult with combined responses
        """
        result = AggregatedResult(
            task_id=task_id,
            responses=responses
        )

        if not responses:
            result.confidence_score = 0.0
            return result

        if mode == "first":
            # Use first response
            first_agent = next(iter(responses))
            result.primary_agent = first_agent
            result.synthesized_response = str(responses[first_agent])
            result.confidence_score = 0.8

        elif mode == "best":
            # Find longest/most detailed response
            best_agent = max(responses.keys(), key=lambda k: len(str(responses[k])))
            result.primary_agent = best_agent
            result.synthesized_response = str(responses[best_agent])
            result.confidence_score = 0.85

        elif mode == "synthesize":
            # Combine all responses
            parts = []
            for agent_id, response in responses.items():
                parts.append(f"[{agent_id}]: {response}")

            result.synthesized_response = "\n\n".join(parts)
            result.confidence_score = 0.9

        elif mode == "vote":
            # For future: implement voting mechanism
            # Currently defaults to synthesis
            result.synthesized_response = "\n\n".join(
                f"[{agent_id}]: {response}" for agent_id, response in responses.items()
            )
            result.consensus_level = 0.5
            result.confidence_score = 0.7

        # Calculate consensus level (simplified)
        if len(responses) > 1:
            # Higher confidence when more agents respond
            result.consensus_level = min(1.0, 0.5 + (len(responses) * 0.1))

        return result

    def get_message_history(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentMessage]:
        """Get message history, optionally filtered by task_id."""
        if task_id:
            history = [m for m in self._message_history if m.task_id == task_id]
        else:
            history = self._message_history

        # Return most recent first
        return list(reversed(history[-limit:]))

    def cleanup_chain(self, chain_id: str) -> bool:
        """Remove a completed chain from active chains."""
        if chain_id in self._active_chains:
            chain = self._active_chains[chain_id]
            if chain.status in ("completed", "failed"):
                del self._active_chains[chain_id]
                logger.debug(f"Cleaned up chain {chain_id}")
                return True
        return False

    def get_active_chain_count(self) -> int:
        """Get number of active collaboration chains."""
        return len(self._active_chains)

    def get_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        return {
            "total_messages": len(self._message_history),
            "active_chains": len(self._active_chains),
            "chains_by_status": self._get_chain_status_counts()
        }

    def _get_chain_status_counts(self) -> Dict[str, int]:
        """Get count of chains by status."""
        counts: Dict[str, int] = {}
        for chain in self._active_chains.values():
            counts[chain.status] = counts.get(chain.status, 0) + 1
        return counts


# ============================================================================
# Global Communicator Instance
# ============================================================================

_communicator: Optional[AgentCommunicator] = None


def get_agent_communicator() -> AgentCommunicator:
    """Get global agent communicator instance."""
    global _communicator
    if _communicator is None:
        _communicator = AgentCommunicator()
    return _communicator

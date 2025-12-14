"""
Conversational Agent - Unified conversation handling.

Consolidates all conversation-focused agents (Prince Flowers variants,
Marvin conversation agents, etc.) into a single, modular agent.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from .base_agent import BaseAgent, AgentCapability, AgentContext, AgentResult
from .interfaces import IConversationAgent, ConversationMode, ConversationTurn
from .capabilities import ConversationCapability
from ..registry import register_agent


class ConversationalAgent(BaseAgent, IConversationAgent):
    """
    Unified conversational agent that consolidates all conversation-focused functionality.

    Replaces multiple scattered conversation agents:
    - Prince Flowers variants (10+ files)
    - Marvin conversation agents
    - Enhanced conversation systems
    - Memory-enabled conversation agents

    Features:
    - Multi-turn conversations with context preservation
    - Session management with persistence
    - Capability-based response generation
    - Memory integration for learning
    - Multiple conversation modes
    """

    def __init__(
        self,
        llm_provider=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize conversational agent."""
        super().__init__(
            agent_id="conversational_agent",
            agent_name="Conversational Agent",
            capabilities=[
                AgentCapability.CONVERSATION,
                AgentCapability.MEMORY_MANAGEMENT,
                AgentCapability.LEARNING
            ],
            llm_provider=llm_provider,
           =config
        )

        # Initialize conversation capability
        self.conversation_cap = ConversationCapability(config)

        # Session management
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._max_sessions = self.config.get("max_sessions", 100)
        self._session_timeout = self.config.get("session_timeout", 3600)  # 1 hour

        # Agent personality and behavior
        self._personality = self.config.get("personality", "helpful_assistant")
        self._response_style = self.config.get("response_style", "detailed")

        self.logger.info(f"ConversationalAgent initialized with personality: {self._personality}")

    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute conversation request."""
        # Use conversation capability for processing
        return await self.conversation_cap.execute(
            message=request,
            session_id=context.session_id if context else None,
            context=context
        )

    async def start_conversation(
        self,
        initial_message: str,
        mode: ConversationMode = ConversationMode.MULTI_TURN,
        context: Optional[AgentContext] = None
    ) -> str:
        """Start a new conversation session."""
        session_id = str(uuid.uuid4())

        # Initialize session
        self._sessions[session_id] = {
            "mode": mode,
            "created_at": asyncio.get_event_loop().time(),
            "last_activity": asyncio.get_event_loop().time(),
            "message_count": 0,
            "context": context.metadata if context else {}
        }

        # Process initial message
        result = await self.conversation_cap.execute(
            message=initial_message,
            session_id=session_id,
            context=context
        )

        self._sessions[session_id]["message_count"] += 1

        self.logger.info(f"Started conversation session {session_id} with mode {mode}")
        return session_id

    async def continue_conversation(
        self,
        session_id: str,
        message: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Continue an existing conversation."""
        if session_id not in self._sessions:
            return AgentResult(
                success=False,
                content="Session not found. Please start a new conversation.",
                error="Invalid session ID"
            )

        # Update session activity
        session = self._sessions[session_id]
        session["last_activity"] = asyncio.get_event_loop().time()
        session["message_count"] += 1

        # Process message
        result = await self.conversation_cap.execute(
            message=message,
            session_id=session_id,
            context=context
        )

        # Add session info to result
        result.metadata["session_id"] = session_id
        result.metadata["message_count"] = session["message_count"]
        result.metadata["session_duration"] = (
            session["last_activity"] - session["created_at"]
        )

        return result

    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history for a session."""
        return await self.conversation_cap.get_conversation_history(session_id, limit)

    async def end_conversation(self, session_id: str) -> bool:
        """End a conversation session."""
        if session_id not in self._sessions:
            return False

        # Clean up conversation capability
        await self.conversation_cap.clear_conversation(session_id)

        # Remove session
        del self._sessions[session_id]
        self.logger.info(f"Ended conversation session {session_id}")
        return True

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active conversation sessions."""
        current_time = asyncio.get_event_loop().time()
        active_sessions = []

        for session_id, session in self._sessions.items():
            # Check if session is still active (not timed out)
            if current_time - session["last_activity"] < self._session_timeout:
                session_info = {
                    "session_id": session_id,
                    "mode": session["mode"],
                    "created_at": session["created_at"],
                    "last_activity": session["last_activity"],
                    "message_count": session["message_count"],
                    "duration": current_time - session["created_at"]
                }
                active_sessions.append(session_info)

        return active_sessions

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired conversation sessions."""
        current_time = asyncio.get_event_loop().time()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if current_time - session["last_activity"] >= self._session_timeout:
                expired_sessions.append(session_id)

        # Clean up expired sessions
        for session_id in expired_sessions:
            await self.end_conversation(session_id)

        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    async def _health_check_impl(self) -> bool:
        """Agent-specific health check."""
        try:
            # Check conversation capability
            test_result = await self.conversation_cap.execute(
                message="Health check test",
                session_id="health_check"
            )

            # Clean up health check session
            await self.conversation_cap.clear_conversation("health_check")

            return test_result.success

        except Exception as e:
            self.logger.error(f"Conversational agent health check failed: {e}")
            return False

    async def _reset_impl(self) -> None:
        """Reset agent-specific state."""
        # Clear all sessions
        for session_id in list(self._sessions.keys()):
            await self.end_conversation(session_id)

        # Reset conversation capability
        self._sessions.clear()

    def get_agent_info(self) -> Dict[str, Any]:
        """Get detailed agent information."""
        base_info = super().get_agent_info() if hasattr(super(), 'get_agent_info') else {}

        current_time = asyncio.get_event_loop().time()
        active_count = 0

        for session in self._sessions.values():
            if current_time - session["last_activity"] < self._session_timeout:
                active_count += 1

        conversation_info = {
            "active_sessions": active_count,
            "total_sessions": len(self._sessions),
            "personality": self._personality,
            "response_style": self._response_style,
            "session_timeout": self._session_timeout
        }

        if base_info:
            base_info.update(conversation_info)
            return base_info

        return conversation_info


# Register the agent
register_agent(
    ConversationalAgent,
    "conversational_agent",
    "Conversational Agent",
    [
        AgentCapability.CONVERSATION,
        AgentCapability.MEMORY_MANAGEMENT,
        AgentCapability.LEARNING
    ],
    config={
        "max_sessions": 100,
        "session_timeout": 3600,
        "personality": "helpful_assistant",
        "response_style": "detailed"
    },
    metadata={
        "description": "Unified conversational agent that consolidates all conversation-focused functionality",
        "replaces": [
            "prince_flowers_agent",
            "enhanced_prince_flowers",
            "marvin_prince_flowers",
            "memory_enhanced_prince_flowers",
            "conversation_session"
        ],
        "features": [
            "Multi-turn conversations",
            "Session management",
            "Context preservation",
            "Memory integration",
            "Multiple conversation modes"
        ]
    }
)
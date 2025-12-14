"""
Enhanced Prince Flowers with Letta Memory Integration.

Provides persistent memory, learning, and context-aware responses
for the Prince Flowers conversational agent.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Memory integration
try:
    from torq_console.memory import LettaMemoryManager, LETTA_AVAILABLE
except ImportError:
    LETTA_AVAILABLE = False
    LettaMemoryManager = None

# Agent modules
from .conversation_session import ConversationSession, SessionManager
from .preference_learning import PreferenceLearning
from .feedback_learning import FeedbackLearning

logger = logging.getLogger(__name__)


class EnhancedPrinceFlowers:
    """
    Enhanced Prince Flowers agent with Letta memory integration.

    Features:
    - Persistent conversation memory
    - Learning from user feedback
    - Preference adaptation
    - Context-aware responses
    """

    def __init__(
        self,
        memory_enabled: bool = True,
        memory_backend: str = "sqlite",
        memory_db_path: Optional[str] = None
    ):
        """
        Initialize Enhanced Prince Flowers.

        Args:
            memory_enabled: Enable Letta memory features
            memory_backend: Memory backend (sqlite, postgresql, redis)
            memory_db_path: Path to memory database
        """
        self.memory_enabled = memory_enabled and LETTA_AVAILABLE
        self.logger = logging.getLogger(__name__)

        # Initialize memory manager
        if self.memory_enabled:
            try:
                self.memory = LettaMemoryManager(
                    agent_name="prince_flowers",
                    backend=memory_backend,
                    db_path=memory_db_path,
                    enabled=True
                )
                self.logger.info("Prince Flowers memory initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize memory: {e}")
                self.memory_enabled = False
                self.memory = None
        else:
            self.memory = None
            if not LETTA_AVAILABLE:
                self.logger.warning("Letta not available, memory features disabled")

        # Conversation state
        self.current_session_id: Optional[str] = None
        self.session_message_count = 0

    async def chat_with_memory(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with memory context.

        Args:
            user_message: User's message
            session_id: Session identifier (creates new if None)
            include_context: Whether to include memory context

        Returns:
            Response dictionary with message and metadata
        """
        # Create or continue session
        if session_id is None:
            session_id = self._create_session_id()
        self.current_session_id = session_id

        # Interaction ID for feedback tracking
        interaction_id = f"{session_id}_{self.session_message_count}"
        self.session_message_count += 1

        # Step 1: Store user message in memory
        if self.memory_enabled:
            await self._store_user_message(user_message, session_id, interaction_id)

        # Step 2: Retrieve relevant context from memory
        context = []
        if self.memory_enabled and include_context:
            context = await self._get_relevant_context(user_message, session_id)

        # Step 3: Generate response (placeholder for actual agent)
        response = await self._generate_response(user_message, context)

        # Step 4: Store response in memory
        if self.memory_enabled:
            await self._store_assistant_response(response, session_id, interaction_id)

        # Return response with metadata
        return {
            "response": response,
            "session_id": session_id,
            "interaction_id": interaction_id,
            "context_used": len(context),
            "memory_enabled": self.memory_enabled,
            "timestamp": datetime.now().isoformat()
        }

    async def _store_user_message(
        self,
        message: str,
        session_id: str,
        interaction_id: str
    ):
        """Store user message in memory."""
        try:
            await self.memory.add_memory(
                content=f"User: {message}",
                metadata={
                    "role": "user",
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                    "timestamp": datetime.now().isoformat()
                },
                importance=0.7
            )
        except Exception as e:
            self.logger.error(f"Error storing user message: {e}")

    async def _store_assistant_response(
        self,
        response: str,
        session_id: str,
        interaction_id: str
    ):
        """Store assistant response in memory."""
        try:
            await self.memory.add_memory(
                content=f"Assistant: {response}",
                metadata={
                    "role": "assistant",
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                    "timestamp": datetime.now().isoformat()
                },
                importance=0.6
            )
        except Exception as e:
            self.logger.error(f"Error storing response: {e}")

    async def _get_relevant_context(
        self,
        query: str,
        session_id: str,
        max_memories: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from memory."""
        try:
            context = await self.memory.get_relevant_context(
                query=query,
                max_memories=max_memories
            )

            # Filter to current session if needed
            # (For now, get all relevant memories)
            return context

        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return []

    async def _generate_response(
        self,
        user_message: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """
        Generate response (placeholder for actual agent).

        In production, this would call the actual Prince Flowers agent
        with the retrieved context.
        """
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nContext from previous conversations:\n"
            for mem in context[:3]:  # Use top 3 most relevant
                context_str += f"- {mem.get('content', '')}\n"

        # Placeholder response (in production, use actual agent)
        response = f"[Enhanced Prince Flowers Response]\n\n"
        response += f"Understanding your request: {user_message}\n"

        if context:
            response += f"\nBased on our conversation history, I remember:\n"
            response += context_str

        response += "\n[This is a placeholder. In production, the actual Prince Flowers agent would generate a contextual response.]"

        return response

    async def record_feedback(
        self,
        interaction_id: str,
        score: float,
        feedback_type: str = "general"
    ) -> bool:
        """
        Record user feedback for learning.

        Args:
            interaction_id: ID of the interaction
            score: Feedback score (0.0-1.0)
            feedback_type: Type of feedback

        Returns:
            True if feedback was recorded
        """
        if not self.memory_enabled:
            return False

        try:
            await self.memory.record_feedback(
                interaction_id=interaction_id,
                score=score,
                feedback_type=feedback_type
            )
            return True

        except Exception as e:
            self.logger.error(f"Error recording feedback: {e}")
            return False

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get summary of a conversation session.

        Args:
            session_id: Session to summarize

        Returns:
            Session summary with stats and context
        """
        if not self.memory_enabled:
            return {
                "session_id": session_id,
                "memory_enabled": False,
                "message": "Memory not available"
            }

        try:
            # Get session memories
            context = await self.memory.get_relevant_context(
                query=f"session {session_id}",
                max_memories=50
            )

            # Count messages
            user_messages = sum(1 for m in context if m.get('role') == 'user')
            assistant_messages = sum(1 for m in context if m.get('role') == 'assistant')

            return {
                "session_id": session_id,
                "total_messages": len(context),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "memory_enabled": True,
                "context": context[:10]  # Last 10 messages
            }

        except Exception as e:
            self.logger.error(f"Error getting session summary: {e}")
            return {
                "session_id": session_id,
                "error": str(e)
            }

    async def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get learned user preferences.

        Returns:
            Dictionary of preferences
        """
        if not self.memory_enabled:
            return {}

        try:
            preferences = await self.memory.get_user_preferences()
            return preferences

        except Exception as e:
            self.logger.error(f"Error getting preferences: {e}")
            return {}

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear a specific session's memories.

        Args:
            session_id: Session to clear

        Returns:
            True if successful
        """
        if not self.memory_enabled:
            return False

        try:
            # Note: Current implementation clears all memories
            # In production, would filter by session_id
            # For now, just reset session counter
            self.session_message_count = 0
            self.current_session_id = None
            return True

        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
            return False

    def _create_session_id(self) -> str:
        """Create a unique session ID."""
        return f"pf_{uuid.uuid4().hex[:12]}"

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        stats = {
            "memory_enabled": self.memory_enabled,
            "current_session": self.current_session_id,
            "session_message_count": self.session_message_count
        }

        if self.memory_enabled and self.memory:
            memory_stats = self.memory.get_stats()
            stats.update({"memory": memory_stats})

        return stats


# Global instance (optional)
_enhanced_prince_flowers: Optional[EnhancedPrinceFlowers] = None


def get_enhanced_prince_flowers(**kwargs) -> EnhancedPrinceFlowers:
    """Get or create global Enhanced Prince Flowers instance."""
    global _enhanced_prince_flowers

    if _enhanced_prince_flowers is None:
        _enhanced_prince_flowers = EnhancedPrinceFlowers(**kwargs)

    return _enhanced_prince_flowers

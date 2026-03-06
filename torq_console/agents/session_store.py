"""
Session Store for TORQ Console chat persistence.

Stores conversation history in Supabase for session continuity.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class SessionMessage:
    """A single message in a conversation."""

    def __init__(
        self,
        role: str,  # "user" or "assistant"
        content: str,
        timestamp: datetime,
        agent_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.agent_id = agent_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_id=data.get("agent_id"),
            metadata=data.get("metadata", {}),
        )


class SessionStore:
    """
    Session store for conversation persistence.

    Uses Supabase for storage.
    """

    def __init__(self, supabase_client=None):
        """
        Initialize the session store.

        Args:
            supabase_client: Supabase client for persistence
        """
        self.supabase = supabase_client

    async def get_session_history(
        self,
        session_id: str,
        max_messages: int = 20,
    ) -> List[SessionMessage]:
        """
        Retrieve conversation history for a session.

        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to return

        Returns:
            List of SessionMessage objects (oldest first)
        """
        if not self.supabase:
            logger.warning("No Supabase client - session history unavailable")
            return []

        try:
            result = self.supabase.table("chat_sessions").select("*").eq(
                "session_id", session_id
            ).execute()

            messages = []
            for row in result.data:
                # Parse messages array
                messages_data = row.get("messages", [])
                for msg in messages_data:
                    if msg.get("deleted", False):
                        continue
                    messages.append(SessionMessage.from_dict(msg))

            return messages

        except Exception as e:
            logger.error(f"Failed to load session history: {e}")
            return []

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Add a message to the session.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            agent_id: Agent that handled this (for assistant messages)
            metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.supabase:
            return False

        try:
            message_data = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": agent_id,
                "metadata": metadata or {},
                "deleted": False,
            }

            # Check if session exists
            existing = self.supabase.table("chat_sessions").select("*").eq(
                "session_id", session_id
            ).execute()

            if existing.data:
                # Append to existing session
                session = existing.data[0]
                messages = session.get("messages", [])
                messages.append(message_data)

                self.supabase.table("chat_sessions").update({
                    "messages": messages,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("session_id", session_id).execute()
            else:
                # Create new session
                self.supabase.table("chat_sessions").insert({
                    "session_id": session_id,
                    "messages": [message_data],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to add message to session: {e}")
            return False

    async def get_conversation_context(
        self,
        session_id: str,
        max_messages: int = 10,
    ) -> str:
        """
        Get formatted conversation history for LLM context.

        Args:
            session_id: Session identifier
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation history string
        """
        messages = await self.get_session_history(session_id, max_messages)

        if not messages:
            return ""

        # Format as conversation transcript
        lines = []
        for msg in messages:
            role = msg.role.upper()
            content = msg.content[:500]  # Truncate very long messages
            lines.append(f"{role}: {content}")

        return "\n\n".join(lines)


# Global session store instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> Optional[SessionStore]:
    """Get the global session store instance."""
    return _session_store


def set_session_store(store: SessionStore) -> None:
    """Set the global session store instance."""
    global _session_store
    _session_store = store

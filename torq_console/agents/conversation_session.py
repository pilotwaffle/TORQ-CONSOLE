"""
Conversation Session Tracking for TORQ Console Agents.

Manages conversation sessions with full history, context, and continuity.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    interaction_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationSession:
    """
    Manages a single conversation session with full history.

    Features:
    - Message tracking and linking
    - Session summaries
    - Context window management
    - Session persistence
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        max_messages: int = 100,
        context_window: int = 10
    ):
        """
        Initialize conversation session.

        Args:
            session_id: Unique session identifier
            max_messages: Maximum messages to keep in memory
            context_window: Number of recent messages for context
        """
        self.session_id = session_id or self._generate_session_id()
        self.max_messages = max_messages
        self.context_window = context_window

        # Message history
        self.messages: List[Message] = []

        # Session metadata
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        self.user_id: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to the session.

        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Additional metadata

        Returns:
            The created Message object
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.messages.append(message)
        self.last_activity = datetime.now()

        # Trim old messages if exceeding max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        self.logger.debug(f"Added {role} message to session {self.session_id}")
        return message

    def get_context(self, n_messages: Optional[int] = None) -> List[Message]:
        """
        Get recent messages for context.

        Args:
            n_messages: Number of messages (defaults to context_window)

        Returns:
            List of recent messages
        """
        if n_messages is None:
            n_messages = self.context_window

        return self.messages[-n_messages:]

    def get_recent_context(self, max_messages: Optional[int] = None) -> List[Message]:
        """
        Get recent messages for context (alias for get_context).

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self.get_context(n_messages=max_messages)

    def get_full_history(self) -> List[Message]:
        """Get complete message history."""
        return self.messages.copy()

    def get_message_by_id(self, interaction_id: str) -> Optional[Message]:
        """
        Find a specific message by interaction ID.

        Args:
            interaction_id: Message interaction ID

        Returns:
            Message if found, None otherwise
        """
        for message in self.messages:
            if message.interaction_id == interaction_id:
                return message
        return None

    def get_message_count(self) -> int:
        """
        Get total number of messages in session.

        Returns:
            Number of messages
        """
        return len(self.messages)

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate session summary.

        Returns:
            Dictionary with session statistics and summary
        """
        user_messages = [m for m in self.messages if m.role == "user"]
        assistant_messages = [m for m in self.messages if m.role == "assistant"]

        duration = datetime.now() - self.start_time
        messages_per_minute = len(self.messages) / max(duration.total_seconds() / 60, 1)

        summary = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "total_messages": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "messages_per_minute": round(messages_per_minute, 2),
            "last_activity": self.last_activity.isoformat(),
            "active": self.is_active()
        }

        # Add recent context
        recent_context = self.get_context(5)
        summary["recent_messages"] = [
            {
                "role": m.role,
                "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in recent_context
        ]

        return summary

    def get_summary(self) -> Dict[str, Any]:
        """
        Get session summary (alias for generate_summary).

        Returns:
            Dictionary with session statistics and summary
        """
        return self.generate_summary()

    def is_active(self, timeout_minutes: int = 30) -> bool:
        """
        Check if session is still active.

        Args:
            timeout_minutes: Inactivity timeout in minutes

        Returns:
            True if session is active
        """
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity < timeout

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "interaction_id": m.interaction_id,
                    "metadata": m.metadata
                }
                for m in self.messages
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Deserialize session from dictionary."""
        session = cls(session_id=data["session_id"])
        session.start_time = datetime.fromisoformat(data["start_time"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.user_id = data.get("user_id")
        session.metadata = data.get("metadata", {})

        # Restore messages
        for msg_data in data.get("messages", []):
            message = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                interaction_id=msg_data["interaction_id"],
                metadata=msg_data.get("metadata", {})
            )
            session.messages.append(message)

        return session

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"session_{uuid.uuid4().hex[:12]}"


class SessionManager:
    """
    Manages multiple conversation sessions.

    Features:
    - Session creation and retrieval
    - Active session tracking
    - Session cleanup
    - Session persistence
    """

    def __init__(
        self,
        max_sessions: int = 100,
        session_timeout_minutes: int = 30
    ):
        """
        Initialize session manager.

        Args:
            max_sessions: Maximum concurrent sessions
            session_timeout_minutes: Inactivity timeout
        """
        self.max_sessions = max_sessions
        self.session_timeout_minutes = session_timeout_minutes

        # Active sessions
        self.sessions: Dict[str, ConversationSession] = {}

        self.logger = logging.getLogger(__name__)

    def create_session(
        self,
        user_id: Optional[str] = None
    ) -> str:
        """
        Create a new conversation session.

        Args:
            user_id: Optional user identifier

        Returns:
            Session ID of the new ConversationSession
        """
        session = ConversationSession()
        session.user_id = user_id

        self.sessions[session.session_id] = session

        # Cleanup old sessions if needed
        if len(self.sessions) > self.max_sessions:
            self._cleanup_inactive_sessions()

        self.logger.info(f"Created session {session.session_id}")
        return session.session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession if found, None otherwise
        """
        return self.sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ConversationSession:
        """
        Get existing session or create new one.

        Args:
            session_id: Session identifier (creates new if None)
            user_id: Optional user identifier

        Returns:
            ConversationSession
        """
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        else:
            return self.create_session(user_id=user_id)

    def get_active_sessions(self) -> List[ConversationSession]:
        """Get all currently active sessions."""
        return [
            session for session in self.sessions.values()
            if session.is_active(self.session_timeout_minutes)
        ]

    def list_active_sessions(self) -> List[ConversationSession]:
        """List all currently active sessions (alias for get_active_sessions)."""
        return self.get_active_sessions()

    def end_session(self, session_id: str) -> bool:
        """
        End a session (alias for delete_session).

        Args:
            session_id: Session to end

        Returns:
            True if session was ended
        """
        return self.delete_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if session was deleted
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Deleted session {session_id}")
            return True
        return False

    def _cleanup_inactive_sessions(self):
        """Remove inactive sessions."""
        inactive_ids = [
            session_id for session_id, session in self.sessions.items()
            if not session.is_active(self.session_timeout_minutes)
        ]

        for session_id in inactive_ids:
            del self.sessions[session_id]
            self.logger.debug(f"Cleaned up inactive session {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        active_sessions = self.get_active_sessions()

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "max_sessions": self.max_sessions,
            "session_timeout_minutes": self.session_timeout_minutes
        }


# Global session manager
_session_manager: Optional[SessionManager] = None


def get_session_manager(**kwargs) -> SessionManager:
    """Get or create global session manager."""
    global _session_manager

    if _session_manager is None:
        _session_manager = SessionManager(**kwargs)

    return _session_manager

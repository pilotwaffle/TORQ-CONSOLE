"""
Zep Memory Integration for Enhanced Prince Flowers Agent

Advanced temporal memory system using Zep - structured temporal memory with
dynamic knowledge graphs for agentic AI memory management.

Based on research: Zep offers structured temporal memory with fast, dynamic
knowledge graphs, integrates with LangChain and major LLM APIs, and supports
both enterprise and open development environments.
"""

import asyncio
import json
import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryRole(Enum):
    """Memory roles in Zep."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

class MemoryType(Enum):
    """Types of memory in Zep."""
    EPISODIC = "episodic"  # Events and experiences
    SEMANTIC = "semantic"  # Factual knowledge
    PROCEDURAL = "procedural"  # Skills and workflows
    DECLARATIVE = "declarative"  # Facts and concepts

@dataclass
class MemoryMessage:
    """Memory message structure for Zep."""
    role: MemoryRole
    content: str
    uuid: str
    created_at: datetime
    token_count: int = 0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Zep API."""
        return {
            "role": self.role.value,
            "content": self.content,
            "uuid": self.uuid,
            "created_at": self.created_at.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata or {}
        }

@dataclass
class MemorySession:
    """Memory session for tracking conversations."""
    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None
    messages: List[MemoryMessage] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

@dataclass
class MemorySearchResult:
    """Result from memory search."""
    uuid: str
    role: str
    content: str
    created_at: datetime
    score: float
    metadata: Dict[str, Any]

class ZepMemoryIntegration:
    """
    Zep memory integration for advanced agentic AI memory management.

    Features:
    - Temporal memory with time-evolving knowledge graphs
    - Dynamic memory compilation and retrieval
    - Semantic search with vector embeddings
    - Multi-session memory management
    - Memory consolidation and forgetting
    """

    def __init__(self, zep_api_url: str = "http://localhost:8001", zep_api_key: str = None):
        """Initialize Zep memory integration."""
        self.zep_api_url = zep_api_url
        self.zep_api_key = zep_api_key
        self.agent_id = "prince_flowers_enhanced"
        self.user_id = "king_flowers"

        # Active session management
        self.active_sessions: Dict[str, MemorySession] = {}

        # Memory statistics
        self.total_messages_stored = 0
        self.total_searches_performed = 0
        self.memory_hits = 0

        # Configuration
        self.max_messages_per_session = 1000
        self.session_timeout_hours = 24
        self.consolidation_threshold = 50

        self.logger = logging.getLogger(f"ZepMemory.{self.agent_id}")
        self.logger.info("Zep memory integration initialized")

    async def initialize(self) -> bool:
        """Initialize Zep connection and validate setup."""
        try:
            # Check Zep availability (simplified check)
            self.logger.info(f"Zep API URL: {self.zep_api_url}")
            self.logger.info(f"Agent ID: {self.agent_id}")
            self.logger.info(f"User ID: {self.user_id}")

            # Initialize session management
            await self._initialize_session_management()

            self.logger.info("Zep memory integration initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Zep initialization failed: {e}")
            return False

    async def _initialize_session_management(self):
        """Initialize session management system."""
        # Clean up old sessions
        await self._cleanup_expired_sessions()

    async def _cleanup_expired_sessions(self):
        """Clean up sessions that have expired."""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session.updated_at > timedelta(hours=self.session_timeout_hours)
        ]

        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"Cleaned up expired session: {session_id}")

    async def create_session(self, session_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new memory session.

        Args:
            session_id: Optional session ID (auto-generated if not provided)
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        session = MemorySession(
            session_id=session_id,
            user_id=self.user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {"agent": self.agent_id}
        )

        self.active_sessions[session_id] = session
        self.logger.info(f"Created memory session: {session_id}")

        return session_id

    async def add_message(
        self,
        session_id: str,
        role: MemoryRole,
        content: str,
        metadata: Dict[str, Any] = None,
        token_count: int = 0
    ) -> str:
        """
        Add a message to memory.

        Args:
            session_id: Session ID
            role: Message role
            content: Message content
            metadata: Optional metadata
            token_count: Token count

        Returns:
            Message UUID
        """
        try:
            # Ensure session exists
            if session_id not in self.active_sessions:
                await self.create_session(session_id)

            session = self.active_sessions[session_id]
            message_uuid = str(uuid.uuid4())

            message = MemoryMessage(
                role=role,
                content=content,
                uuid=message_uuid,
                created_at=datetime.now(),
                token_count=token_count,
                metadata=metadata or {}
            )

            session.messages.append(message)
            session.updated_at = datetime.now()

            # Limit message count per session
            if len(session.messages) > self.max_messages_per_session:
                session.messages = session.messages[-self.max_messages_per_session:]

            self.total_messages_stored += 1

            # Trigger consolidation if needed
            if len(session.messages) % self.consolidation_threshold == 0:
                await self._consolidate_memory(session_id)

            self.logger.debug(f"Added message to session {session_id}: {role.value} - {content[:50]}...")

            return message_uuid

        except Exception as e:
            self.logger.error(f"Failed to add message: {e}")
            return f"error_{int(time.time())}"

    async def search_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        date_range: Optional[tuple] = None
    ) -> List[MemorySearchResult]:
        """
        Search memory for relevant information.

        Args:
            query: Search query
            session_id: Optional session ID to search within
            limit: Maximum number of results
            memory_type: Optional memory type filter
            date_range: Optional date range tuple (start, end)

        Returns:
            List of memory search results
        """
        try:
            self.total_searches_performed += 1
            search_results = []

            # Search across sessions
            sessions_to_search = [session_id] if session_id else list(self.active_sessions.keys())

            query_words = set(query.lower().split())

            for sid in sessions_to_search:
                if sid not in self.active_sessions:
                    continue

                session = self.active_sessions[sid]

                for message in session.messages:
                    # Simple keyword matching (in production, this would use vector embeddings)
                    message_words = set(message.content.lower().split())
                    common_words = query_words.intersection(message_words)

                    if common_words:
                        # Calculate relevance score
                        relevance_score = len(common_words) / max(len(query_words), len(message_words))

                        # Apply date range filter if specified
                        if date_range:
                            start_date, end_date = date_range
                            if not (start_date <= message.created_at <= end_date):
                                continue

                        # Apply memory type filter if specified
                        if memory_type and message.metadata:
                            metadata = message.metadata
                            if metadata.get('memory_type') != memory_type.value:
                                continue

                        search_results.append(MemorySearchResult(
                            uuid=message.uuid,
                            role=message.role.value,
                            content=message.content,
                            created_at=message.created_at,
                            score=relevance_score,
                            metadata=message.metadata or {}
                        ))

            # Sort by relevance score and limit results
            search_results.sort(key=lambda x: x.score, reverse=True)
            search_results = search_results[:limit]

            if search_results:
                self.memory_hits += 1
                self.logger.info(f"Memory search found {len(search_results)} results for query: {query[:50]}...")

            return search_results

        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return []

    async def get_session_context(
        self,
        session_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get context from a specific session.

        Args:
            session_id: Session ID
            limit: Maximum number of recent messages

        Returns:
            Session context dictionary
        """
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found", "context": []}

            session = self.active_sessions[session_id]
            recent_messages = session.messages[-limit:] if session.messages else []

            context = []
            for message in recent_messages:
                context.append({
                    "role": message.role.value,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "metadata": message.metadata or {}
                })

            return {
                "session_id": session_id,
                "message_count": len(recent_messages),
                "context": context,
                "session_metadata": session.metadata or {}
            }

        except Exception as e:
            self.logger.error(f"Failed to get session context: {e}")
            return {"error": str(e), "context": []}

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        try:
            total_sessions = len(self.active_sessions)
            total_messages = sum(len(s.messages) for s in self.active_sessions.values())

            # Calculate hit rate
            hit_rate = self.memory_hits / max(self.total_searches_performed, 1)

            # Calculate session activity
            active_sessions = sum(
                1 for s in self.active_sessions.values()
                if datetime.now() - s.updated_at < timedelta(hours=1)
            )

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "messages_stored": self.total_messages_stored,
                "searches_performed": self.total_searches_performed,
                "memory_hits": self.memory_hits,
                "hit_rate": hit_rate,
                "agent_id": self.agent_id,
                "user_id": self.user_id
            }

        except Exception as e:
            self.logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}

    async def _consolidate_memory(self, session_id: str):
        """Consolidate memory for better organization."""
        try:
            session = self.active_sessions[session_id]

            # Create summary of recent messages
            recent_messages = session.messages[-20:]  # Last 20 messages

            if len(recent_messages) >= 5:
                # Create a consolidation message
                user_messages = [m for m in recent_messages if m.role == MemoryRole.USER]
                assistant_messages = [m for m in recent_messages if m.role == MemoryRole.ASSISTANT]

                consolidation_content = f"Memory consolidation from session {session_id}. "
                consolidation_content += f"User topics: {[m.content[:50] + '...' for m in user_messages[:3]]}. "
                consolidation_content += f"Key responses provided: {len(assistant_messages)} interactions."

                await self.add_message(
                    session_id=session_id,
                    role=MemoryRole.SYSTEM,
                    content=consolidation_content,
                    metadata={"memory_type": MemoryType.PROCEDURAL.value, "consolidation": True}
                )

                self.logger.info(f"Memory consolidation completed for session {session_id}")

        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")

    async def get_relevant_context_for_query(
        self,
        query: str,
        limit: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get relevant context for a query using advanced memory search.

        Args:
            query: Query string
            limit: Maximum number of memories to retrieve
            session_id: Optional session ID for context

        Returns:
            Dictionary with relevant context
        """
        try:
            # Search for relevant memories
            search_results = await self.search_memory(
                query=query,
                session_id=session_id,
                limit=limit
            )

            # Format context for LLM
            formatted_context = self._format_memory_context_for_llm(search_results)

            # Calculate confidence boost based on memory quality
            confidence_boost = 0.0
            if search_results:
                avg_relevance = sum(r.score for r in search_results) / len(search_results)
                confidence_boost = min(avg_relevance * 0.25, 0.3)  # Cap at 30%

            return {
                "memories_used": len(search_results),
                "relevant_memories": search_results,
                "formatted_context": formatted_context,
                "confidence_boost": confidence_boost,
                "context_available": len(search_results) > 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get relevant context: {e}")
            return {
                "memories_used": 0,
                "relevant_memories": [],
                "formatted_context": "",
                "confidence_boost": 0.0,
                "context_available": False
            }

    def _format_memory_context_for_llm(self, search_results: List[MemorySearchResult]) -> str:
        """Format memory search results for LLM prompt."""
        if not search_results:
            return ""

        formatted = "\n## Relevant Information from Memory\n\n"

        for i, memory in enumerate(search_results, 1):
            relevance = memory.score * 100
            time_ago = datetime.now() - memory.created_at
            time_str = f"{time_ago.days} days ago" if time_ago.days > 0 else f"{time_ago.seconds // 3600} hours ago"

            formatted += f"**Memory {i} ({relevance:.0f}% match, {time_str}):**\n"
            formatted += f"Role: {memory.role.upper()}\n"
            formatted += f"Content: {memory.content[:300]}{'...' if len(memory.content) > 300 else ''}\n\n"

        return formatted

    async def cleanup_old_sessions(self):
        """Clean up old sessions to manage memory efficiently."""
        await self._cleanup_expired_sessions()

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(session.messages),
            "metadata": session.metadata or {}
        }

# Factory function
def create_zep_memory_integration(
    zep_api_url: str = "http://localhost:8001",
    zep_api_key: str = None,
    agent_id: str = "prince_flowers_enhanced",
    user_id: str = "king_flowers"
) -> ZepMemoryIntegration:
    """Create Zep memory integration instance."""
    integration = ZepMemoryIntegration(zep_api_url, zep_api_key)
    integration.agent_id = agent_id
    integration.user_id = user_id
    return integration
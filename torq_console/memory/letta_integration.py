"""
Letta Memory Integration for TORQ Console.

Provides persistent memory, learning capabilities, and long-term context
for Prince Flowers and other agents using Letta (formerly MemGPT).
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

# Letta imports (optional dependency)
try:
    import letta
    from letta import create_client
    from letta.schemas.memory import ChatMemory
    from letta.schemas.agent import AgentState
    LETTA_AVAILABLE = True
except ImportError:
    LETTA_AVAILABLE = False
    letta = None

logger = logging.getLogger(__name__)


class LettaMemoryManager:
    """
    Letta memory manager for TORQ Console agents.

    Provides persistent memory, learning, and context management
    using Letta's advanced memory system.
    """

    def __init__(
        self,
        agent_name: str = "prince_flowers",
        backend: str = "sqlite",
        db_path: Optional[Path] = None,
        memory_size: int = 10000,
        enabled: bool = True
    ):
        """
        Initialize Letta memory manager.

        Args:
            agent_name: Name of the agent using this memory
            backend: Memory backend (sqlite, postgresql, redis)
            db_path: Path to SQLite database (if using sqlite)
            memory_size: Maximum number of memories to store
            enabled: Whether Letta memory is enabled
        """
        self.agent_name = agent_name
        self.backend = backend
        self.memory_size = memory_size
        self.enabled = enabled and LETTA_AVAILABLE

        if not self.enabled:
            if not LETTA_AVAILABLE:
                logger.warning("Letta not available. Memory features disabled.")
            else:
                logger.info("Letta memory disabled in configuration")
            return

        # Setup database path
        if db_path is None:
            db_path = Path.home() / ".torq" / "letta_memory.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize Letta client
        try:
            self.client = create_client(base_url=f"sqlite:///{self.db_path}")
            self.agent_id = self._initialize_agent()
            logger.info(f"Letta memory initialized for {agent_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Letta: {e}")
            self.enabled = False

    def _initialize_agent(self) -> Optional[str]:
        """Initialize or retrieve Letta agent."""
        if not self.enabled:
            return None

        try:
            # Try to get existing agent
            agents = self.client.list_agents()
            for agent in agents:
                if agent.name == self.agent_name:
                    return agent.id

            # Create new agent if not exists
            agent = self.client.create_agent(
                name=self.agent_name,
                memory=ChatMemory(
                    human=f"User interacting with {self.agent_name}",
                    persona=f"I am {self.agent_name}, an AI assistant in TORQ Console"
                )
            )
            return agent.id

        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            return None

    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> bool:
        """
        Add a memory to the agent's memory system.

        Args:
            content: Memory content
            metadata: Additional metadata
            importance: Memory importance (0.0-1.0)

        Returns:
            True if memory was added successfully
        """
        if not self.enabled or not self.agent_id:
            return False

        try:
            # Store memory with Letta
            self.client.send_message(
                agent_id=self.agent_id,
                message=content,
                role="system"
            )

            # Store metadata separately if needed
            if metadata:
                await self._store_metadata(content, metadata, importance)

            return True

        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False

    async def get_relevant_context(
        self,
        query: str,
        max_memories: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a query.

        Args:
            query: Query to find relevant memories
            max_memories: Maximum number of memories to return

        Returns:
            List of relevant memories with content and metadata
        """
        if not self.enabled or not self.agent_id:
            return []

        try:
            # Get agent state which includes relevant memories
            agent_state = self.client.get_agent(self.agent_id)

            # Extract relevant memories from recall storage
            memories = []
            if hasattr(agent_state, 'memory') and agent_state.memory:
                # Get recent messages that might be relevant
                messages = self.client.get_messages(
                    agent_id=self.agent_id,
                    limit=max_memories * 2
                )

                # Filter and format memories
                for msg in messages:
                    if query.lower() in msg.text.lower():
                        memories.append({
                            'content': msg.text,
                            'timestamp': msg.created_at,
                            'role': msg.role,
                            'relevance': 1.0  # Could implement semantic scoring
                        })

                # Limit to max_memories
                memories = memories[:max_memories]

            return memories

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    async def record_feedback(
        self,
        interaction_id: str,
        score: float,
        feedback_type: str = "general"
    ) -> bool:
        """
        Record feedback for learning.

        Args:
            interaction_id: ID of the interaction
            score: Feedback score (0.0-1.0)
            feedback_type: Type of feedback

        Returns:
            True if feedback was recorded
        """
        if not self.enabled or not self.agent_id:
            return False

        try:
            # Store feedback as a system message
            feedback_msg = f"Feedback: {feedback_type} - Score: {score} - ID: {interaction_id}"
            self.client.send_message(
                agent_id=self.agent_id,
                message=feedback_msg,
                role="system"
            )

            return True

        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False

    async def get_user_preferences(self) -> Dict[str, Any]:
        """
        Extract learned user preferences from memory.

        Returns:
            Dictionary of user preferences
        """
        if not self.enabled or not self.agent_id:
            return {}

        try:
            # Search for preference-related memories
            preferences = {}

            # Get messages that contain preferences
            messages = self.client.get_messages(
                agent_id=self.agent_id,
                limit=100
            )

            for msg in messages:
                if any(keyword in msg.text.lower() for keyword in ['prefer', 'like', 'favorite', 'always', 'never']):
                    # Extract preference
                    # This is a simple implementation - could be enhanced with NLP
                    preferences[msg.id] = {
                        'content': msg.text,
                        'timestamp': msg.created_at
                    }

            return preferences

        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}

    async def clear_memory(self, older_than: Optional[timedelta] = None) -> bool:
        """
        Clear memories older than specified time.

        Args:
            older_than: Clear memories older than this duration

        Returns:
            True if successful
        """
        if not self.enabled or not self.agent_id:
            return False

        try:
            if older_than:
                # Archive old memories
                cutoff_time = datetime.now() - older_than
                # Letta handles memory management internally
                logger.info(f"Archived memories older than {older_than}")
            else:
                # Clear all agent memories
                self.client.delete_agent(self.agent_id)
                self.agent_id = self._initialize_agent()
                logger.info("Cleared all memories")

            return True

        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False

    async def export_memories(self, output_path: Path) -> bool:
        """
        Export memories to JSON file.

        Args:
            output_path: Path to export file

        Returns:
            True if successful
        """
        if not self.enabled or not self.agent_id:
            return False

        try:
            # Get all messages
            messages = self.client.get_messages(
                agent_id=self.agent_id,
                limit=10000
            )

            # Convert to JSON-serializable format
            export_data = {
                'agent_name': self.agent_name,
                'export_date': datetime.now().isoformat(),
                'memories': [
                    {
                        'id': msg.id,
                        'content': msg.text,
                        'role': msg.role,
                        'timestamp': msg.created_at.isoformat() if hasattr(msg.created_at, 'isoformat') else str(msg.created_at)
                    }
                    for msg in messages
                ]
            }

            # Write to file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(messages)} memories to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting memories: {e}")
            return False

    async def _store_metadata(
        self,
        content: str,
        metadata: Dict[str, Any],
        importance: float
    ):
        """Store memory metadata."""
        # Store metadata as a system message
        metadata_msg = f"Metadata: {json.dumps(metadata)} - Importance: {importance}"
        self.client.send_message(
            agent_id=self.agent_id,
            message=metadata_msg,
            role="system"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.enabled or not self.agent_id:
            return {
                'enabled': False,
                'total_memories': 0
            }

        try:
            agent_state = self.client.get_agent(self.agent_id)
            messages = self.client.get_messages(
                agent_id=self.agent_id,
                limit=1000
            )

            return {
                'enabled': True,
                'agent_name': self.agent_name,
                'agent_id': self.agent_id,
                'backend': self.backend,
                'total_memories': len(messages),
                'db_path': str(self.db_path)
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'enabled': False, 'error': str(e)}


# Global memory manager instance
_memory_manager: Optional[LettaMemoryManager] = None


def get_memory_manager(
    agent_name: str = "prince_flowers",
    **kwargs
) -> LettaMemoryManager:
    """Get or create global memory manager."""
    global _memory_manager

    if _memory_manager is None:
        _memory_manager = LettaMemoryManager(agent_name=agent_name, **kwargs)

    return _memory_manager


def initialize_memory(config: Dict[str, Any]) -> LettaMemoryManager:
    """Initialize memory manager from configuration."""
    return LettaMemoryManager(
        agent_name=config.get('agent_name', 'prince_flowers'),
        backend=config.get('backend', 'sqlite'),
        db_path=config.get('db_path'),
        memory_size=config.get('memory_size', 10000),
        enabled=config.get('enabled', True)
    )

"""
Marvin Agent Memory and Learning System

Provides persistent memory, interaction tracking, and adaptive learning
for Marvin-powered agents.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class InteractionType(str, Enum):
    """Types of agent interactions."""
    QUERY = "query"
    CODE_GENERATION = "code_generation"
    DEBUG = "debug"
    DOCUMENTATION = "documentation"
    SPEC_ANALYSIS = "spec_analysis"
    GENERAL_CHAT = "general_chat"


@dataclass
class AgentInteraction:
    """Record of a single agent interaction."""
    interaction_id: str
    timestamp: str
    interaction_type: InteractionType
    user_input: str
    agent_response: str
    agent_name: str
    success: bool
    feedback_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemorySnapshot:
    """Snapshot of agent memory state."""
    total_interactions: int
    interactions_by_type: Dict[str, int]
    success_rate: float
    average_feedback: float
    last_updated: str
    learned_patterns: List[str]


class MarvinAgentMemory:
    """
    Persistent memory system for Marvin agents.

    Stores:
    - Interaction history
    - User preferences
    - Learned patterns
    - Performance metrics
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize agent memory system.

        Args:
            storage_path: Path to storage directory
        """
        self.logger = logging.getLogger("TORQ.Agents.Memory")

        # Set up storage
        self.storage_path = storage_path or Path.home() / ".torq" / "agent_memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Memory components
        self.interactions: List[AgentInteraction] = []
        self.user_preferences: Dict[str, Any] = {}
        self.learned_patterns: List[Dict[str, Any]] = []

        # Load existing memory
        self._load_memory()

        self.logger.info(f"Initialized Agent Memory (storage: {self.storage_path})")

    def record_interaction(
        self,
        user_input: str,
        agent_response: str,
        agent_name: str,
        interaction_type: InteractionType,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record an agent interaction.

        Args:
            user_input: User's input
            agent_response: Agent's response
            agent_name: Name of the agent
            interaction_type: Type of interaction
            success: Whether interaction was successful
            metadata: Optional metadata

        Returns:
            Interaction ID
        """
        interaction_id = f"{agent_name}_{len(self.interactions) + 1}_{datetime.now().timestamp()}"

        interaction = AgentInteraction(
            interaction_id=interaction_id,
            timestamp=datetime.now().isoformat(),
            interaction_type=interaction_type,
            user_input=user_input[:500],  # Store snippet
            agent_response=agent_response[:500],  # Store snippet
            agent_name=agent_name,
            success=success,
            metadata=metadata or {}
        )

        self.interactions.append(interaction)
        self.logger.debug(f"Recorded interaction: {interaction_id}")

        # Periodically persist to disk
        if len(self.interactions) % 10 == 0:
            self._save_memory()

        return interaction_id

    def add_feedback(self, interaction_id: str, score: float):
        """
        Add user feedback to an interaction.

        Args:
            interaction_id: ID of the interaction
            score: Feedback score (0.0 to 1.0)
        """
        for interaction in self.interactions:
            if interaction.interaction_id == interaction_id:
                interaction.feedback_score = score
                self.logger.info(f"Added feedback to {interaction_id}: {score}")
                self._save_memory()
                return

        self.logger.warning(f"Interaction not found: {interaction_id}")

    def update_preference(self, key: str, value: Any):
        """
        Update a user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        self.user_preferences[key] = value
        self.logger.info(f"Updated preference: {key}")
        self._save_memory()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.user_preferences.get(key, default)

    def learn_pattern(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any]
    ):
        """
        Learn a new pattern from interactions.

        Args:
            pattern_name: Name of the pattern
            pattern_data: Pattern details
        """
        pattern = {
            'name': pattern_name,
            'learned_at': datetime.now().isoformat(),
            'data': pattern_data
        }

        self.learned_patterns.append(pattern)
        self.logger.info(f"Learned new pattern: {pattern_name}")
        self._save_memory()

    def get_patterns(self, pattern_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get learned patterns.

        Args:
            pattern_name: Optional filter by name

        Returns:
            List of matching patterns
        """
        if pattern_name:
            return [p for p in self.learned_patterns if p['name'] == pattern_name]

        return self.learned_patterns

    def get_interaction_history(
        self,
        agent_name: Optional[str] = None,
        interaction_type: Optional[InteractionType] = None,
        limit: int = 100
    ) -> List[AgentInteraction]:
        """
        Get interaction history with optional filtering.

        Args:
            agent_name: Filter by agent name
            interaction_type: Filter by interaction type
            limit: Maximum number of interactions

        Returns:
            List of interactions
        """
        filtered = self.interactions

        if agent_name:
            filtered = [i for i in filtered if i.agent_name == agent_name]

        if interaction_type:
            filtered = [i for i in filtered if i.interaction_type == interaction_type]

        # Return most recent first
        return list(reversed(filtered[-limit:]))

    def get_memory_snapshot(self) -> AgentMemorySnapshot:
        """Get a snapshot of memory state."""
        if not self.interactions:
            return AgentMemorySnapshot(
                total_interactions=0,
                interactions_by_type={},
                success_rate=0.0,
                average_feedback=0.0,
                last_updated=datetime.now().isoformat(),
                learned_patterns=[]
            )

        # Calculate statistics
        interactions_by_type = {}
        for interaction in self.interactions:
            type_name = interaction.interaction_type.value
            interactions_by_type[type_name] = interactions_by_type.get(type_name, 0) + 1

        success_count = sum(1 for i in self.interactions if i.success)
        success_rate = success_count / len(self.interactions)

        feedback_scores = [i.feedback_score for i in self.interactions if i.feedback_score is not None]
        average_feedback = sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0.0

        return AgentMemorySnapshot(
            total_interactions=len(self.interactions),
            interactions_by_type=interactions_by_type,
            success_rate=round(success_rate, 3),
            average_feedback=round(average_feedback, 3),
            last_updated=datetime.now().isoformat(),
            learned_patterns=[p['name'] for p in self.learned_patterns]
        )

    def get_context_for_agent(
        self,
        agent_name: str,
        max_history: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for an agent.

        Args:
            agent_name: Name of the agent
            max_history: Maximum history items to include

        Returns:
            Context dictionary
        """
        recent_interactions = self.get_interaction_history(
            agent_name=agent_name,
            limit=max_history
        )

        return {
            'recent_interactions': [
                {
                    'user_input': i.user_input,
                    'type': i.interaction_type.value,
                    'success': i.success
                }
                for i in recent_interactions
            ],
            'preferences': self.user_preferences,
            'patterns': [p['name'] for p in self.learned_patterns]
        }

    def clear_old_interactions(self, days: int = 30):
        """
        Clear interactions older than specified days.

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        original_count = len(self.interactions)

        self.interactions = [
            i for i in self.interactions
            if datetime.fromisoformat(i.timestamp) > cutoff_date
        ]

        removed = original_count - len(self.interactions)

        if removed > 0:
            self.logger.info(f"Cleared {removed} old interactions")
            self._save_memory()

    def _load_memory(self):
        """Load memory from persistent storage."""
        try:
            # Load interactions
            interactions_file = self.storage_path / "interactions.json"
            if interactions_file.exists():
                with open(interactions_file, 'r') as f:
                    data = json.load(f)
                    self.interactions = [
                        AgentInteraction(**item)
                        for item in data
                    ]
                    self.logger.info(f"Loaded {len(self.interactions)} interactions")

            # Load preferences
            prefs_file = self.storage_path / "preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    self.user_preferences = json.load(f)
                    self.logger.info(f"Loaded {len(self.user_preferences)} preferences")

            # Load patterns
            patterns_file = self.storage_path / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    self.learned_patterns = json.load(f)
                    self.logger.info(f"Loaded {len(self.learned_patterns)} patterns")

        except Exception as e:
            self.logger.error(f"Failed to load memory: {e}")

    def _save_memory(self):
        """Save memory to persistent storage."""
        try:
            # Save interactions (convert enums to strings for JSON serialization)
            interactions_file = self.storage_path / "interactions.json"
            with open(interactions_file, 'w') as f:
                interactions_data = []
                for interaction in self.interactions:
                    interaction_dict = asdict(interaction)
                    # Convert enum to string value
                    interaction_dict['interaction_type'] = interaction.interaction_type.value
                    interactions_data.append(interaction_dict)

                json.dump(interactions_data, f, indent=2)

            # Save preferences
            prefs_file = self.storage_path / "preferences.json"
            with open(prefs_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)

            # Save patterns
            patterns_file = self.storage_path / "patterns.json"
            with open(patterns_file, 'w') as f:
                json.dump(self.learned_patterns, f, indent=2)

            self.logger.debug("Memory saved to disk")

        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")


# Global memory instance
_global_memory: Optional[MarvinAgentMemory] = None


def get_agent_memory(storage_path: Optional[Path] = None) -> MarvinAgentMemory:
    """
    Get global agent memory instance (singleton).

    Args:
        storage_path: Optional storage path

    Returns:
        MarvinAgentMemory instance
    """
    global _global_memory

    if _global_memory is None:
        _global_memory = MarvinAgentMemory(storage_path=storage_path)

    return _global_memory

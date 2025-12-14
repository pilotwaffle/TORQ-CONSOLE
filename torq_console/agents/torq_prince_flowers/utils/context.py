"""
Context management utilities for TORQ Prince Flowers agent.

This module provides context tracking and management capabilities
including conversation history and state management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ContextManager:
    """Context management for maintaining conversation state and history."""

    def __init__(self):
        """Initialize the context manager."""
        self.logger = logging.getLogger("ContextManager")
        self.conversation_history = []
        self.current_context = {}
        self.max_history_size = 100

    def add_context_entry(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add an entry to the conversation history."""
        try:
            entry = {
                "timestamp": datetime.now(),
                "role": role,  # "user", "assistant", "system"
                "content": content,
                "metadata": metadata or {}
            }

            self.conversation_history.append(entry)

            # Maintain history size
            if len(self.conversation_history) > self.max_history_size:
                self.conversation_history.pop(0)

            self.logger.debug(f"Added context entry: {role}")

        except Exception as e:
            self.logger.error(f"Error adding context entry: {e}")

    def get_recent_context(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent context entries."""
        return self.conversation_history[-count:] if self.conversation_history else []

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context."""
        return {
            "total_entries": len(self.conversation_history),
            "current_context": self.current_context,
            "last_updated": datetime.now(),
            "recent_entries": self.get_recent_context(3)
        }

    def clear_context(self):
        """Clear all context history."""
        self.conversation_history.clear()
        self.current_context.clear()
        self.logger.info("Context cleared")

    def set_context_variable(self, key: str, value: Any):
        """Set a context variable."""
        self.current_context[key] = value

    def get_context_variable(self, key: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self.current_context.get(key, default)
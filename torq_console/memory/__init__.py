"""
Memory management for TORQ Console agents.

Provides persistent memory, learning, and context management using Letta.
"""

from .letta_integration import (
    LettaMemoryManager,
    get_memory_manager,
    initialize_memory,
    LETTA_AVAILABLE
)

__all__ = [
    'LettaMemoryManager',
    'get_memory_manager',
    'initialize_memory',
    'LETTA_AVAILABLE'
]

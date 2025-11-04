"""
Specialized ControlFlow Agents for TORQ Console

This module defines specialized agents for different task types.
"""

from .base_agents import (
    create_web_search_agent,
    create_analyst_agent,
    create_writer_agent,
    create_code_agent,
    create_general_agent
)

__all__ = [
    'create_web_search_agent',
    'create_analyst_agent',
    'create_writer_agent',
    'create_code_agent',
    'create_general_agent'
]

"""
Enhanced Prince Flowers Agent with ARTIST-style Agentic RL for TORQ Console.

This package provides a comprehensive agentic AI system with:
- Advanced reasoning capabilities
- Dynamic tool selection and composition
- Multi-turn reasoning chains
- Self-correction and adaptive planning
- Full MCP integration capabilities

The main entry point is the TORQPrinceFlowers class, which provides
a unified interface to all agent capabilities.
"""

# Core imports
from .core.agent import TORQPrinceFlowers
from .core.state import ReasoningMode, AgenticAction, ReasoningTrajectory, TORQAgentResult
from .interface import TORQPrinceFlowersInterface

# Re-export main classes for backward compatibility
__all__ = [
    'TORQPrinceFlowers',
    'TORQPrinceFlowersInterface',
    'ReasoningMode',
    'AgenticAction',
    'ReasoningTrajectory',
    'TORQAgentResult',
]

# Version information
__version__ = '0.80.0'
__author__ = 'TORQ Console Team'

# Convenience function for creating agent instances
def create_prince_flowers_agent(llm_provider=None, config=None):
    """Create a new TORQ Prince Flowers agent instance.

    Args:
        llm_provider: LLM provider instance (optional)
        config: Configuration dictionary (optional)

    Returns:
        TORQPrinceFlowers agent instance
    """
    return TORQPrinceFlowers(llm_provider=llm_provider, config=config)

def create_prince_flowers_interface(console_instance):
    """Create a new TORQ Prince Flowers interface.

    Args:
        console_instance: TORQ Console instance

    Returns:
        TORQPrinceFlowersInterface instance
    """
    return TORQPrinceFlowersInterface(console_instance)
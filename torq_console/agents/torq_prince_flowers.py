"""
TORQ Prince Flowers Agent - Backward Compatibility Shim

This file provides backward compatibility for the original torq_prince_flowers.py
by importing from the new modular structure.

This shim ensures that existing imports continue to work while the code
has been restructured into smaller, more manageable modules.

DEPRECATION WARNING: Direct imports from this file are deprecated.
Please import from the modular structure instead:
- from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
- from torq_console.agents.torq_prince_flowers import TORQPrinceFlowersInterface
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "Direct import from torq_console.agents.torq_prince_flowers.py is deprecated. "
    "Import from torq_console.agents.torq_prince_flowers package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all symbols from the new modular structure
from .torq_prince_flowers.core.agent import TORQPrinceFlowers
from .torq_prince_flowers.core.state import ReasoningMode, AgenticAction, ReasoningTrajectory, TORQAgentResult
from .torq_prince_flowers.interface import TORQPrinceFlowersInterface
from .torq_prince_flowers import create_prince_flowers_agent, create_prince_flowers_interface

# Re-export all symbols for backward compatibility
__all__ = [
    'TORQPrinceFlowers',
    'TORQPrinceFlowersInterface',
    'ReasoningMode',
    'AgenticAction',
    'ReasoningTrajectory',
    'TORQAgentResult',
    'create_prince_flowers_agent',
    'create_prince_flowers_interface',
]
"""
Swarm Intelligence Module for TORQ CONSOLE.

This module implements a multi-agent swarm system inspired by OpenAI Swarm
and natural swarm intelligence principles. It provides:

- SearchAgent: Handles web searches using multiple search APIs
- AnalysisAgent: Processes and filters search results
- SynthesisAgent: Combines information from multiple sources
- ResponseAgent: Formats and delivers final response
- SwarmOrchestrator: Coordinates agent handoffs and task delegation
"""

from .orchestrator import SwarmOrchestrator
from .agents.search_agent import SearchAgent
from .agents.analysis_agent import AnalysisAgent
from .agents.synthesis_agent import SynthesisAgent
from .agents.response_agent import ResponseAgent

__all__ = [
    'SwarmOrchestrator',
    'SearchAgent',
    'AnalysisAgent',
    'SynthesisAgent',
    'ResponseAgent'
]
__version__ = '1.0.0'
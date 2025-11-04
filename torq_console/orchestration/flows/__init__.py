"""
Flow Definitions for TORQ Console ControlFlow Integration

Defines reusable workflow patterns.
"""

from .research_flow import research_workflow, parallel_research_workflow
from .analysis_flow import analysis_workflow, code_analysis_workflow

__all__ = [
    'research_workflow',
    'parallel_research_workflow',
    'analysis_workflow',
    'code_analysis_workflow'
]

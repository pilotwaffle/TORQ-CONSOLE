"""
Task Definitions for TORQ Console ControlFlow Integration

Defines common task types and result models.
"""

from .base_tasks import (
    SearchResult,
    AnalysisResult,
    ReportResult,
    CodeAnalysisResult,
    TaskStatus
)

__all__ = [
    'SearchResult',
    'AnalysisResult',
    'ReportResult',
    'CodeAnalysisResult',
    'TaskStatus'
]

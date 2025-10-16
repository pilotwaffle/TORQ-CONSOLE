"""
Content Synthesis Module for TORQ Console

Phase 4: Enhanced Content Extraction and Synthesis

This module provides advanced content processing capabilities:
- Enhanced content extraction (tables, lists, images)
- Multi-document synthesis with citations
- Confidence scoring for results
"""

from .extractor import (
    ContentExtractor, ExtractedContent,
    ExtractedTable, ExtractedList, ExtractedImage
)
from .synthesizer import (
    MultiDocumentSynthesizer, SynthesisResult, CitedStatement
)
from .confidence import ConfidenceScorer, ConfidenceScore

__all__ = [
    'ContentExtractor',
    'ExtractedContent',
    'ExtractedTable',
    'ExtractedList',
    'ExtractedImage',
    'MultiDocumentSynthesizer',
    'SynthesisResult',
    'CitedStatement',
    'ConfidenceScorer',
    'ConfidenceScore'
]

__version__ = '1.0.0'

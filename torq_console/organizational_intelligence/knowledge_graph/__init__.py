"""
TORQ Layer 9 - Enterprise Knowledge Graph

L9-M1: Models and manages the organizational knowledge graph.
"""

from .graph_service import (
    KnowledgeGraphService,
    get_knowledge_graph_service,
)

__all__ = [
    "KnowledgeGraphService",
    "get_knowledge_graph_service",
]

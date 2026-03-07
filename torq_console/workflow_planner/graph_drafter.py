"""
Graph drafter - Normalizes and cleans LLM output.

Converts raw LLM output into a validated WorkflowDraft.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .models import WorkflowDraft, DraftNode, DraftEdge

logger = logging.getLogger(__name__)


def build_edges_from_dependencies(nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Build edges from node dependencies.

    If nodes have depends_on fields, convert them to explicit edges.

    Args:
        nodes: List of node dicts with depends_on fields

    Returns:
        List of edge dicts
    """
    edges: List[Dict[str, str]] = []

    for node in nodes:
        node_key = node.get("node_key")
        if not node_key:
            continue

        for dep in node.get("depends_on", []) or []:
            edges.append({
                "source_node_key": dep,
                "target_node_key": node_key,
            })

    return edges


def normalize_raw_draft(raw: Dict[str, Any]) -> WorkflowDraft:
    """
    Normalize raw LLM output into a valid WorkflowDraft.

    Args:
        raw: Raw dict from LLM

    Returns:
        Validated WorkflowDraft

    Raises:
        ValueError: If normalization fails
    """
    try:
        raw_nodes = raw.get("nodes", [])

        # Build edges from dependencies if not provided
        raw_edges = raw.get("edges")
        if not raw_edges:
            raw_edges = build_edges_from_dependencies(raw_nodes)

        # Normalize with defaults
        normalized = {
            "name": raw.get("name", "Generated Workflow"),
            "description": raw.get("description", "AI-generated workflow draft"),
            "rationale": raw.get("rationale", ""),
            "nodes": raw_nodes,
            "edges": raw_edges,
            "limits": raw.get(
                "limits",
                {
                    "max_nodes": 10,
                    "max_runtime_seconds": 900,
                    "max_parallel_nodes": 3,
                },
            ),
        }

        # Validate with Pydantic
        draft = WorkflowDraft.model_validate(normalized)

        logger.info(f"Normalized draft '{draft.name}' with {len(draft.nodes)} nodes")
        return draft

    except Exception as e:
        logger.error(f"Failed to normalize draft: {e}")
        raise ValueError(f"Normalization failed: {e}") from e

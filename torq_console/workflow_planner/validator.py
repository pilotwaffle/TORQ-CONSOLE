"""
Workflow draft validator.

Strict validation to ensure all generated workflows are safe and valid.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Set

from .models import WorkflowDraft

logger = logging.getLogger(__name__)


class WorkflowDraftValidationError(Exception):
    """Raised when a workflow draft fails validation."""

    pass


# Allowed agent IDs in TORQ Console
ALLOWED_AGENTS = {
    "conversational_agent",
    "workflow_agent",
    "research_agent",
    "orchestration_agent",
    "torq_prince_flowers",
}


def validate_workflow_draft(draft: WorkflowDraft) -> None:
    """
    Validate a workflow draft.

    Checks:
    - At least one node
    - No more than 10 nodes
    - Unique node keys
    - Valid agent IDs
    - No self-dependencies
    - All dependencies reference existing nodes
    - No cycles in the graph

    Args:
        draft: Workflow draft to validate

    Raises:
        WorkflowDraftValidationError: If validation fails
    """
    errors = []

    # Check node count
    if not draft.nodes:
        errors.append("Draft contains no nodes.")
    elif len(draft.nodes) > 10:
        errors.append("Draft exceeds max node count (10).")

    # Check for duplicate node keys
    node_keys = [node.node_key for node in draft.nodes]
    if len(node_keys) != len(set(node_keys)):
        duplicates = [k for k in node_keys if node_keys.count(k) > 1]
        errors.append(f"Duplicate node_key values found: {set(duplicates)}")

    # Build node key set for dependency validation
    node_key_set: Set[str] = set(node_keys)

    # Validate each node
    for node in draft.nodes:
        # Check agent_id
        if node.agent_id not in ALLOWED_AGENTS:
            errors.append(f"Invalid agent_id: {node.agent_id}")

        # Check dependencies
        for dep in node.depends_on:
            if dep not in node_key_set:
                errors.append(
                    f"Node '{node.node_key}' depends on unknown node '{dep}'."
                )
            if dep == node.node_key:
                errors.append(
                    f"Node '{node.node_key}' cannot depend on itself."
                )

    # Validate edges
    edge_keys = set()
    for edge in draft.edges:
        # Check source exists
        if edge.source_node_key not in node_key_set:
            errors.append(
                f"Edge source '{edge.source_node_key}' does not exist."
            )

        # Check target exists
        if edge.target_node_key not in node_key_set:
            errors.append(
                f"Edge target '{edge.target_node_key}' does not exist."
            )

        # Check for self-loop
        if edge.source_node_key == edge.target_node_key:
            errors.append("Self-loop edge detected.")

        # Check for duplicate edges
        edge_key = (edge.source_node_key, edge.target_node_key)
        if edge_key in edge_keys:
            errors.append(f"Duplicate edge: {edge.source_node_key} -> {edge.target_node_key}")
        edge_keys.add(edge_key)

    # Check for cycles
    try:
        _validate_acyclic(draft)
    except WorkflowDraftValidationError as e:
        errors.append(str(e))

    # Report all errors
    if errors:
        error_msg = "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise WorkflowDraftValidationError(error_msg)

    logger.info(f"Workflow draft '{draft.name}' validated successfully")


def _validate_acyclic(draft: WorkflowDraft) -> None:
    """
    Check that the workflow graph has no cycles using Kahn's algorithm.

    Args:
        draft: Workflow draft to validate

    Raises:
        WorkflowDraftValidationError: If a cycle is detected
    """
    # Build adjacency list and indegree map
    graph = defaultdict(list)
    indegree = {node.node_key: 0 for node in draft.nodes}

    for edge in draft.edges:
        graph[edge.source_node_key].append(edge.target_node_key)
        indegree[edge.target_node_key] = indegree.get(edge.target_node_key, 0) + 1

    # Kahn's algorithm
    queue = deque([k for k, v in indegree.items() if v == 0])
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # If we didn't visit all nodes, there's a cycle
    if visited != len(draft.nodes):
        raise WorkflowDraftValidationError("Cycle detected in generated workflow.")

"""
Mission Node Executor with Idempotency Guards

Provides safe, idempotent node execution that prevents:
- Duplicate execution of already-running or completed nodes
- Duplicate event emission
- Race conditions in parallel execution
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class NodeExecutionError(Exception):
    """Raised when node execution fails."""
    pass


class IdempotencyViolationError(Exception):
    """Raised when idempotency guard is violated."""
    pass


class MissionNodeExecutor:
    """
    Executes mission nodes with proper idempotency guards.

    Key guarantees:
    1. A node can only transition from PENDING → READY → RUNNING → COMPLETED
    2. State transitions are atomic (checked-and-set in database)
    3. Events are emitted exactly once per transition
    4. Handoffs are created exactly once per completion
    """

    # Terminal states that cannot transition
    TERMINAL_STATES = {"completed", "failed", "skipped"}

    # Valid transitions: from_state -> {to_states}
    VALID_TRANSITIONS = {
        "pending": {"ready", "blocked", "skipped"},
        "ready": {"running", "blocked", "skipped"},
        "running": {"completed", "failed", "blocked"},
        "blocked": {"ready", "skipped"},
        "failed": set(),  # Terminal
        "completed": set(),  # Terminal
        "skipped": set(),  # Terminal
    }

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def execute_node(
        self,
        mission_id: str,
        node_id: str,
        node_title: str,
        node_type: str,
        executor_fn: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a single node with full idempotency guards.

        Args:
            mission_id: Mission UUID
            node_id: Node UUID
            node_title: Node title for logging
            node_type: Node type (task, evidence, deliverable, etc.)
            executor_fn: Optional function to execute (defaults to simulation)

        Returns:
            Execution result with status, output, and metadata

        Raises:
            IdempotencyViolationError: If node already in terminal state
            NodeExecutionError: If execution fails
        """
        # Step 1: Get current state (database source of truth)
        current_state = self._get_node_state(node_id)

        # Step 2: Check idempotency - already completed or failed?
        if current_state["status"] in self.TERMINAL_STATES:
            logger.info(f"Node {node_title} already {current_state['status']}, skipping")
            return {
                "node_id": node_id,
                "status": current_state["status"],
                "skipped": True,
                "reason": f"Already in terminal state: {current_state['status']}"
            }

        # Step 3: Check idempotency - already running?
        if current_state["status"] == "running":
            logger.info(f"Node {node_title} already running, skipping")
            return {
                "node_id": node_id,
                "status": "running",
                "skipped": True,
                "reason": "Already running"
            }

        # Step 4: Attempt atomic transition to RUNNING
        if not self._try_transition_to_running(node_id, current_state["status"]):
            # Someone else claimed this node
            logger.info(f"Node {node_title} claimed by another process, skipping")
            return {
                "node_id": node_id,
                "status": current_state["status"],
                "skipped": True,
                "reason": "Lost race to claim node"
            }

        # Step 5: Emit node.started event (exactly once)
        self._emit_event_if_not_exists(
            mission_id, node_id, "node.started",
            {"node_type": node_type}
        )

        # Step 6: Execute the node
        try:
            output_data, confidence = self._execute_node_work(
                node_title, node_type, executor_fn
            )
        except Exception as e:
            # Mark as failed
            self._transition_to_failed(node_id, str(e))
            raise NodeExecutionError(f"Execution failed: {e}")

        # Step 7: Transition to COMPLETED (atomic)
        if not self._try_transition_to_completed(node_id, output_data, confidence):
            # Someone else marked this completed?
            logger.warning(f"Node {node_title} already completed by another process")
            return {
                "node_id": node_id,
                "status": "completed",
                "skipped": True,
                "reason": "Already completed by another process"
            }

        # Step 8: Emit node.completed event (exactly once)
        self._emit_event_if_not_exists(
            mission_id, node_id, "node.completed",
            {"node_type": node_type, "confidence": confidence}
        )

        # Step 9: Create handoff (exactly once)
        handoff_id = self._create_handoff_if_not_exists(
            mission_id, node_id, node_type, node_title, output_data, confidence
        )

        # Step 10: Activate dependent nodes
        activated_count = self._activate_dependent_nodes(mission_id, node_id)

        return {
            "node_id": node_id,
            "status": "completed",
            "skipped": False,
            "output_data": output_data,
            "confidence": confidence,
            "handoff_id": handoff_id,
            "dependents_activated": activated_count
        }

    def _get_node_state(self, node_id: str) -> Dict[str, Any]:
        """Get current node state from database."""
        result = self.supabase.table("mission_nodes").select("*").eq("id", node_id).execute()

        if not result.data:
            raise ValueError(f"Node {node_id} not found")

        return result.data[0]

    def _try_transition_to_running(self, node_id: str, current_status: str) -> bool:
        """
        Attempt atomic transition from READY/PENDING to RUNNING.

        Uses conditional update to ensure only one process succeeds.

        Returns:
            True if transition succeeded, False if lost race
        """
        if current_status not in ["pending", "ready"]:
            return False

        try:
            # Update only if status is still pending/ready
            result = self.supabase.table("mission_nodes").update({
                "status": "running",
                "started_at": "now()",
                "updated_at": "now()"
            }).eq("id", node_id).in_("status", ["pending", "ready"]).execute()

            # Check if any rows were updated
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error transitioning to running: {e}")
            return False

    def _try_transition_to_completed(
        self,
        node_id: str,
        output_data: Dict[str, Any],
        confidence: float
    ) -> bool:
        """
        Attempt atomic transition from RUNNING to COMPLETED.

        Returns:
            True if transition succeeded, False if lost race
        """
        try:
            result = self.supabase.table("mission_nodes").update({
                "status": "completed",
                "completed_at": "now()",
                "output_data": output_data,
                "confidence_score": confidence,
                "updated_at": "now()"
            }).eq("id", node_id).eq("status", "running").execute()

            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error transitioning to completed: {e}")
            return False

    def _transition_to_failed(self, node_id: str, error_message: str):
        """Transition node to FAILED state."""
        try:
            self.supabase.table("mission_nodes").update({
                "status": "failed",
                "completed_at": "now()",
                "error_message": error_message,
                "updated_at": "now()"
            }).eq("id", node_id).execute()
        except Exception as e:
            logger.error(f"Error transitioning to failed: {e}")

    def _execute_node_work(
        self,
        node_title: str,
        node_type: str,
        executor_fn: Optional[callable]
    ) -> tuple[Dict[str, Any], float]:
        """
        Execute the actual node work.

        Returns:
            (output_data, confidence_score)
        """
        if executor_fn:
            # Use provided executor
            result = executor_fn(node_title, node_type)
            return result.get("output", {}), result.get("confidence", 0.85)

        # Default simulation based on node type
        output_data = {"node_type": node_type, "title": node_title}

        if node_type == "task":
            if "Market Size" in node_title:
                output_data["findings"] = ["TAM: $2.5B", "CAGR: 12%"]
            elif "Competitor" in node_title:
                output_data["findings"] = ["3 major competitors", "Market fragmentation: High"]
            elif "Financial" in node_title:
                output_data["findings"] = ["5-year projection: $15M revenue", "ROI: 22%"]
        elif node_type == "evidence":
            output_data["synthesis"] = "Market entry recommended based on strong fundamentals"
            output_data["sources"] = ["Market Size Research", "Competitor Analysis", "Financial Projections"]
        elif node_type == "deliverable":
            output_data["deliverable"] = "Market Entry Recommendation Report"
            output_data["recommendation"] = "Proceed with market entry"

        # Confidence based on node type
        confidence = 0.85
        if node_type == "evidence":
            confidence = 0.90
        elif node_type == "deliverable":
            confidence = 0.95

        return output_data, confidence

    def _emit_event_if_not_exists(
        self,
        mission_id: str,
        node_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Emit event only if one of this type doesn't already exist for this node.

        Prevents duplicate events.
        """
        try:
            # Check if event already exists
            existing = self.supabase.table("mission_events").select("*").eq(
                "mission_id", mission_id
            ).eq("node_id", node_id).eq("event_type", event_type).limit(1).execute()

            if existing.data:
                # Event already exists, skip
                return existing.data[0]["id"]

            # Create new event
            event = {
                "id": str(uuid4()),
                "mission_id": mission_id,
                "event_type": event_type,
                "node_id": node_id,
                "event_data": event_data,
                "metadata": {},
                "timestamp": "now()"
            }

            result = self.supabase.table("mission_events").insert(event).execute()
            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error emitting event: {e}")
            return None

    def _create_handoff_if_not_exists(
        self,
        mission_id: str,
        node_id: str,
        node_type: str,
        node_title: str,
        output_data: Dict[str, Any],
        confidence: float
    ) -> Optional[str]:
        """
        Create handoff only if one doesn't already exist for this node.

        Uses canonical RICH handoff format.
        """
        try:
            # Check if handoff already exists
            existing = self.supabase.table("mission_handoffs").select("*").eq(
                "mission_id", mission_id
            ).eq("from_node_id", node_id).limit(1).execute()

            if existing.data:
                # Handoff already exists, skip
                return existing.data[0]["id"]

            # Build agent type from node type
            agent_type = f"{node_type}_agent"

            # Canonical RICH handoff format
            handoff = {
                "id": str(uuid4()),
                "mission_id": mission_id,
                "from_node_id": node_id,
                "from_agent_type": agent_type,
                "handoff_summary": {
                    "objective_completed": f"{node_title} completed",
                    "output_summary": str(output_data.get('findings', output_data.get('synthesis', output_data.get('deliverable', 'Done')))),
                    "key_findings": list(output_data.keys()) if isinstance(output_data, dict) else [],
                    "recommendations": ["Proceed to next node"]
                },
                "confidence": confidence,
                "confidence_basis": "Analysis completed successfully",
                "unresolved_questions": [],
                "assumptions_made": [],
                "limitations": [],
                "risks": [],
                "severity_indicators": [],
                "artifacts": output_data,
                "workspace_entries": [],
                "recommended_consumers": [],
                "required_next_actions": [],
                "status": "delivered",
                "delivery_attempts": 1
            }

            result = self.supabase.table("mission_handoffs").insert(handoff).execute()
            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error creating handoff: {e}")
            return None

    def _activate_dependent_nodes(
        self,
        mission_id: str,
        node_id: str
    ) -> int:
        """
        Find and activate nodes that depend on this node.

        Only activates nodes where ALL dependencies are now satisfied.

        Returns:
            Number of nodes activated
        """
        try:
            # Find outgoing edges (dependencies)
            edges_result = self.supabase.table("mission_edges").select("*").eq(
                "from_node_id", node_id
            ).execute()

            if not edges_result.data:
                return 0

            activated_count = 0

            for edge in edges_result.data:
                target_node_id = edge["to_node_id"]

                # Check if all dependencies are satisfied
                if self._are_all_dependencies_satisfied(target_node_id):
                    # Mark as ready (if not already)
                    self._emit_event_if_not_exists(
                        mission_id, target_node_id, "node.ready",
                        {"dependency_unblocked": node_id}
                    )

                    self.supabase.table("mission_nodes").update({
                        "status": "ready",
                        "updated_at": "now()"
                    }).eq("id", target_node_id).eq("status", "pending").execute()

                    activated_count += 1

            return activated_count

        except Exception as e:
            logger.error(f"Error activating dependent nodes: {e}")
            return 0

    def _are_all_dependencies_satisfied(self, node_id: str) -> bool:
        """Check if all dependencies for a node are satisfied."""
        try:
            # Get incoming edges
            edges_result = self.supabase.table("mission_edges").select("*").eq(
                "to_node_id", node_id
            ).execute()

            if not edges_result.data:
                # No dependencies
                return True

            for edge in edges_result.data:
                source_node_id = edge["from_node_id"]

                # Check if source is completed
                node_result = self.supabase.table("mission_nodes").select("status").eq(
                    "id", source_node_id
                ).execute()

                if not node_result.data or node_result.data[0]["status"] != "completed":
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False


class MissionCompleter:
    """
    Handles mission completion with idempotency guards.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def complete_mission(
        self,
        mission_id: str,
        overall_score: float = 0.88
    ) -> Dict[str, Any]:
        """
        Mark mission as completed (idempotent).

        Only updates if mission is not already completed.

        Returns:
            Result with status and whether update was applied
        """
        # Get current mission state
        mission_result = self.supabase.table("missions").select("*").eq(
            "id", mission_id
        ).execute()

        if not mission_result.data:
            raise ValueError(f"Mission {mission_id} not found")

        current_status = mission_result.data[0]["status"]

        # Idempotency check
        if current_status == "completed":
            logger.info(f"Mission {mission_id} already completed")
            return {
                "mission_id": mission_id,
                "status": "completed",
                "updated": False,
                "reason": "Already completed"
            }

        # Attempt atomic transition to completed
        try:
            result = self.supabase.table("missions").update({
                "status": "completed",
                "completed_at": "now()",
                "updated_at": "now()",
                "overall_score": overall_score
            }).eq("id", mission_id).in_("status", ["running", "in_progress", "planned"]).execute()

            updated = len(result.data) > 0

            if updated:
                # Emit mission.completed event (only once)
                self._emit_mission_completed_event_if_not_exists(
                    mission_id, overall_score
                )

            return {
                "mission_id": mission_id,
                "status": "completed",
                "updated": updated,
                "reason": "Marked completed" if updated else "Status transition not allowed"
            }

        except Exception as e:
            logger.error(f"Error completing mission: {e}")
            return {
                "mission_id": mission_id,
                "status": current_status,
                "updated": False,
                "error": str(e)
            }

    def _emit_mission_completed_event_if_not_exists(
        self,
        mission_id: str,
        final_score: float
    ) -> Optional[str]:
        """Emit mission.completed event only if it doesn't exist."""
        try:
            existing = self.supabase.table("mission_events").select("*").eq(
                "mission_id", mission_id
            ).eq("event_type", "mission.completed").limit(1).execute()

            if existing.data:
                return existing.data[0]["id"]

            event = {
                "id": str(uuid4()),
                "mission_id": mission_id,
                "event_type": "mission.completed",
                "node_id": None,
                "event_data": {
                    "final_score": final_score,
                    "all_nodes_completed": True
                },
                "metadata": {},
                "timestamp": "now()"
            }

            result = self.supabase.table("mission_events").insert(event).execute()
            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error emitting mission.completed event: {e}")
            return None

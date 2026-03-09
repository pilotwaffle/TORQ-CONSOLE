"""
Agent Teams - Context Manager

Phase 5.2: Agent Teams as a governed execution primitive.

This module manages shared workspace context for team executions.
"""

from __future__ import annotations

import logging
import json
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4


logger = logging.getLogger(__name__)


# ============================================================================
# Team Context Manager
# ============================================================================

class TeamContextManager:
    """
    Manages shared workspace context for team executions.

    Responsibilities:
    - Create workspace for team execution
    - Store intermediate outputs
    - Provide shared state access
    - Maintain round-by-round context
    """

    def __init__(self, supabase):
        """
        Initialize context manager.

        Args:
            supabase: Supabase client
        """
        self.supabase = supabase

    async def create_workspace(
        self,
        mission_id: UUID,
        node_id: UUID,
        team_execution_id: UUID,
    ) -> str:
        """
        Create a workspace for team execution.

        Args:
            mission_id: Mission identifier
            node_id: Node identifier
            team_execution_id: Team execution identifier

        Returns:
            Workspace ID
        """
        workspace_id = f"team_execution:{team_execution_id}"

        # Initialize workspace entry
        entry_data = {
            "workspace_id": workspace_id,
            "entry_type": "team_context",
            "content": {
                "mission_id": str(mission_id),
                "node_id": str(node_id),
                "team_execution_id": str(team_execution_id),
                "created_at": str(datetime_now()),
            },
            "metadata": {
                "scope": "team_execution",
                "team_execution_id": str(team_execution_id),
            },
        }

        try:
            # Try to use workspace_entries table if available
            self.supabase.table("workspace_entries").insert(entry_data).execute()
            logger.debug(f"Created workspace: {workspace_id}")
        except Exception as e:
            logger.warning(f"Could not create workspace entry: {e}")

        return workspace_id

    async def add_role_output(
        self,
        workspace_id: str,
        team_execution_id: UUID,
        round_number: int,
        role: str,
        output: Dict[str, Any],
    ) -> None:
        """
        Add role output to workspace.

        Args:
            workspace_id: Workspace identifier
            team_execution_id: Team execution identifier
            round_number: Round number
            role: Role name
            output: Role output
        """
        entry_id = f"round_{round_number}_{role}"

        entry_data = {
            "workspace_id": workspace_id,
            "entry_id": entry_id,
            "entry_type": "role_output",
            "content": {
                "round": round_number,
                "role": role,
                "output": output,
                "timestamp": str(datetime_now()),
            },
            "metadata": {
                "scope": "team_round",
                "team_execution_id": str(team_execution_id),
                "round": round_number,
                "role": role,
            },
        }

        try:
            self.supabase.table("workspace_entries").insert(entry_data).execute()
            logger.debug(f"Added role output: {role} (round {round_number})")
        except Exception as e:
            logger.warning(f"Could not add role output: {e}")

    async def get_round_outputs(
        self,
        workspace_id: str,
        round_number: int,
    ) -> Dict[str, Any]:
        """
        Get all outputs for a specific round.

        Args:
            workspace_id: Workspace identifier
            round_number: Round number

        Returns:
            Dictionary of role outputs
        """
        try:
            result = self.supabase.table("workspace_entries").select("*").eq(
                "workspace_id", workspace_id
            ).eq("metadata->>round", str(round_number)).execute()

            outputs = {}
            for entry in result.data:
                role = entry["metadata"].get("role")
                if role:
                    outputs[role] = entry["content"].get("output", {})

            return outputs
        except Exception as e:
            logger.warning(f"Could not get round outputs: {e}")
            return {}

    async def get_shared_state(
        self,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Get shared state for the team execution.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Shared state dictionary
        """
        try:
            result = self.supabase.table("workspace_entries").select("*").eq(
                "workspace_id", workspace_id
            ).eq("entry_type", "team_context").execute()

            if result.data:
                return result.data[0].get("content", {})
        except Exception as e:
            logger.warning(f"Could not get shared state: {e}")

        return {}

    async def update_shared_state(
        self,
        workspace_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """
        Update shared state.

        Args:
            workspace_id: Workspace identifier
            updates: State updates to apply
        """
        try:
            result = self.supabase.table("workspace_entries").select("*").eq(
                "workspace_id", workspace_id
            ).eq("entry_type", "team_context").execute()

            if result.data:
                existing_content = result.data[0].get("content", {})
                existing_content.update(updates)

                self.supabase.table("workspace_entries").update({
                    "content": existing_content
                }).eq("id", result.data[0]["id"]).execute()

                logger.debug(f"Updated shared state for {workspace_id}")
        except Exception as e:
            logger.warning(f"Could not update shared state: {e}")

    async def get_full_context(
        self,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Get full workspace context including all rounds.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Full context dictionary
        """
        try:
            result = self.supabase.table("workspace_entries").select("*").eq(
                "workspace_id", workspace_id
            ).order("created_at", asc=True).execute()

            context = {
                "shared_state": {},
                "rounds": {},
            }

            for entry in result.data:
                entry_type = entry.get("entry_type")
                content = entry.get("content", {})
                metadata = entry.get("metadata", {})

                if entry_type == "team_context":
                    context["shared_state"] = content
                elif entry_type == "role_output":
                    round_num = metadata.get("round")
                    role = metadata.get("role")
                    if round_num and role:
                        if round_num not in context["rounds"]:
                            context["rounds"][round_num] = {}
                        context["rounds"][round_num][role] = content.get("output", {})

            return context
        except Exception as e:
            logger.warning(f"Could not get full context: {e}")
            return {}


def datetime_now() -> str:
    """Get current datetime as ISO string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

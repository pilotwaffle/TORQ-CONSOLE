"""
PAE (Plan-Approve-Execute) Storage

Storage backend for PAE workflow data including plans, checkpoints,
and approval requests. Supports multiple storage backends.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from .models import ActionPlan, ApprovalRequest, WorkflowCheckpoint

logger = logging.getLogger(__name__)


class PlanStorage(ABC):
    """Abstract base class for plan storage backends."""

    @abstractmethod
    async def save_plan(self, plan: ActionPlan) -> None:
        """Save an action plan."""
        pass

    @abstractmethod
    async def get_plan(self, plan_id: UUID) -> Optional[ActionPlan]:
        """Get an action plan by ID."""
        pass

    @abstractmethod
    async def list_plans(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ActionPlan]:
        """List action plans with optional filters."""
        pass

    @abstractmethod
    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete an action plan."""
        pass

    @abstractmethod
    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Save a workflow checkpoint."""
        pass

    @abstractmethod
    async def get_checkpoint(self, checkpoint_id: UUID) -> Optional[WorkflowCheckpoint]:
        """Get a workflow checkpoint by ID."""
        pass

    @abstractmethod
    async def list_checkpoints(self, plan_id: UUID) -> List[WorkflowCheckpoint]:
        """List all checkpoints for a plan."""
        pass

    @abstractmethod
    async def save_approval(self, approval: ApprovalRequest) -> None:
        """Save an approval request."""
        pass

    @abstractmethod
    async def get_approval(self, approval_id: UUID) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        pass


class FilePlanStorage(PlanStorage):
    """File-based storage backend using JSON files."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize file-based storage.

        Args:
            storage_dir: Directory to store files (defaults to ~/.torq/pae)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".torq" / "pae"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.storage_dir / "plans").mkdir(exist_ok=True)
        (self.storage_dir / "checkpoints").mkdir(exist_ok=True)
        (self.storage_dir / "approvals").mkdir(exist_ok=True)

        logger.info(f"Initialized file storage at {self.storage_dir}")

    async def save_plan(self, plan: ActionPlan) -> None:
        """Save an action plan to a JSON file."""
        file_path = self.storage_dir / "plans" / f"{plan.id}.json"

        # Convert to dict and handle datetime serialization
        plan_dict = plan.dict()
        plan_dict = self._serialize_datetimes(plan_dict)

        with open(file_path, "w") as f:
            json.dump(plan_dict, f, indent=2, default=str)

        logger.debug(f"Saved plan {plan.id} to {file_path}")

    async def get_plan(self, plan_id: UUID) -> Optional[ActionPlan]:
        """Get an action plan from its JSON file."""
        file_path = self.storage_dir / "plans" / f"{plan_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                plan_dict = json.load(f)

            # Handle datetime deserialization
            plan_dict = self._deserialize_datetimes(plan_dict)

            return ActionPlan(**plan_dict)

        except Exception as e:
            logger.error(f"Failed to load plan {plan_id}: {e}")
            return None

    async def list_plans(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ActionPlan]:
        """List action plans from JSON files."""
        plans_dir = self.storage_dir / "plans"
        plans = []

        for file_path in plans_dir.glob("*.json"):
            try:
                plan = await self.get_plan(UUID(file_path.stem))
                if plan:
                    # Apply filters
                    if user_id and plan.created_by != user_id:
                        continue
                    if status and plan.status != status:
                        continue

                    plans.append(plan)

                    if len(plans) >= limit:
                        break

            except Exception as e:
                logger.error(f"Failed to load plan from {file_path}: {e}")

        # Sort by creation date (newest first)
        plans.sort(key=lambda p: p.created_at, reverse=True)

        return plans

    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete an action plan file."""
        file_path = self.storage_dir / "plans" / f"{plan_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted plan {plan_id}")

        # Also delete associated checkpoints
        await self._delete_plan_checkpoints(plan_id)

    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Save a workflow checkpoint to a JSON file."""
        file_path = self.storage_dir / "checkpoints" / f"{checkpoint.id}.json"

        checkpoint_dict = checkpoint.dict()
        checkpoint_dict = self._serialize_datetimes(checkpoint_dict)

        with open(file_path, "w") as f:
            json.dump(checkpoint_dict, f, indent=2, default=str)

        logger.debug(f"Saved checkpoint {checkpoint.id} to {file_path}")

    async def get_checkpoint(self, checkpoint_id: UUID) -> Optional[WorkflowCheckpoint]:
        """Get a workflow checkpoint from its JSON file."""
        file_path = self.storage_dir / "checkpoints" / f"{checkpoint_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                checkpoint_dict = json.load(f)

            checkpoint_dict = self._deserialize_datetimes(checkpoint_dict)

            return WorkflowCheckpoint(**checkpoint_dict)

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    async def list_checkpoints(self, plan_id: UUID) -> List[WorkflowCheckpoint]:
        """List all checkpoints for a plan."""
        checkpoints_dir = self.storage_dir / "checkpoints"
        checkpoints = []

        for file_path in checkpoints_dir.glob("*.json"):
            try:
                checkpoint = await self.get_checkpoint(UUID(file_path.stem))
                if checkpoint and checkpoint.plan_id == plan_id:
                    checkpoints.append(checkpoint)

            except Exception as e:
                logger.error(f"Failed to load checkpoint from {file_path}: {e}")

        # Sort by creation date (oldest first)
        checkpoints.sort(key=lambda c: c.created_at)

        return checkpoints

    async def save_approval(self, approval: ApprovalRequest) -> None:
        """Save an approval request to a JSON file."""
        file_path = self.storage_dir / "approvals" / f"{approval.id}.json"

        approval_dict = approval.dict()
        approval_dict = self._serialize_datetimes(approval_dict)

        with open(file_path, "w") as f:
            json.dump(approval_dict, f, indent=2, default=str)

        logger.debug(f"Saved approval {approval.id} to {file_path}")

    async def get_approval(self, approval_id: UUID) -> Optional[ApprovalRequest]:
        """Get an approval request from its JSON file."""
        file_path = self.storage_dir / "approvals" / f"{approval_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                approval_dict = json.load(f)

            approval_dict = self._deserialize_datetimes(approval_dict)

            return ApprovalRequest(**approval_dict)

        except Exception as e:
            logger.error(f"Failed to load approval {approval_id}: {e}")
            return None

    async def _delete_plan_checkpoints(self, plan_id: UUID) -> None:
        """Delete all checkpoints associated with a plan."""
        checkpoints = await self.list_checkpoints(plan_id)

        for checkpoint in checkpoints:
            file_path = self.storage_dir / "checkpoints" / f"{checkpoint.id}.json"
            if file_path.exists():
                file_path.unlink()

    def _serialize_datetimes(self, obj: Any) -> Any:
        """Convert datetime objects to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj

    def _deserialize_datetimes(self, obj: Any) -> Any:
        """Convert ISO strings back to datetime objects."""
        if isinstance(obj, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                return obj
        elif isinstance(obj, dict):
            return {k: self._deserialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetimes(item) for item in obj]
        else:
            return obj


class MemoryPlanStorage(PlanStorage):
    """In-memory storage backend for testing and temporary use."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.plans: Dict[UUID, ActionPlan] = {}
        self.checkpoints: Dict[UUID, WorkflowCheckpoint] = {}
        self.approvals: Dict[UUID, ApprovalRequest] = {}

    async def save_plan(self, plan: ActionPlan) -> None:
        """Save an action plan in memory."""
        self.plans[plan.id] = plan

    async def get_plan(self, plan_id: UUID) -> Optional[ActionPlan]:
        """Get an action plan from memory."""
        return self.plans.get(plan_id)

    async def list_plans(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ActionPlan]:
        """List action plans from memory."""
        plans = list(self.plans.values())

        # Apply filters
        if user_id:
            plans = [p for p in plans if p.created_by == user_id]
        if status:
            plans = [p for p in plans if p.status == status]

        # Sort and limit
        plans.sort(key=lambda p: p.created_at, reverse=True)
        return plans[:limit]

    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete an action plan from memory."""
        self.plans.pop(plan_id, None)
        await self._delete_plan_checkpoints(plan_id)

    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Save a workflow checkpoint in memory."""
        self.checkpoints[checkpoint.id] = checkpoint

    async def get_checkpoint(self, checkpoint_id: UUID) -> Optional[WorkflowCheckpoint]:
        """Get a workflow checkpoint from memory."""
        return self.checkpoints.get(checkpoint_id)

    async def list_checkpoints(self, plan_id: UUID) -> List[WorkflowCheckpoint]:
        """List all checkpoints for a plan from memory."""
        checkpoints = [
            c for c in self.checkpoints.values()
            if c.plan_id == plan_id
        ]
        checkpoints.sort(key=lambda c: c.created_at)
        return checkpoints

    async def save_approval(self, approval: ApprovalRequest) -> None:
        """Save an approval request in memory."""
        self.approvals[approval.id] = approval

    async def get_approval(self, approval_id: UUID) -> Optional[ApprovalRequest]:
        """Get an approval request from memory."""
        return self.approvals.get(approval_id)

    async def _delete_plan_checkpoints(self, plan_id: UUID) -> None:
        """Delete all checkpoints associated with a plan from memory."""
        to_delete = [
            cid for cid, checkpoint in self.checkpoints.items()
            if checkpoint.plan_id == plan_id
        ]
        for cid in to_delete:
            self.checkpoints.pop(cid, None)
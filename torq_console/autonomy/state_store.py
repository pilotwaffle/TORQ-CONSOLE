"""
State Store - Persistent storage for autonomous operations.

The State Store is responsible for:
- Persisting monitor definitions and state
- Storing task records and history
- Maintaining approval requests
- Providing query capabilities for audit trails
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .models import (
    Monitor, MonitorState, TaskStateRecord,
    AutonomousTask, TaskState, ApprovalRequest
)


logger = logging.getLogger(__name__)


class StateStore:
    """
    Persistent storage for autonomous operations state.

    In production, this would use Supabase/Postgres.
    For Phase 5A, uses file-based storage for simplicity.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the state store.

        Args:
            storage_path: Path to storage directory. Defaults to .torq-autonomy/
        """
        if storage_path is None:
            storage_path = ".torq-autonomy"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Subdirectories
        self.monitors_path = self.storage_path / "monitors"
        self.monitors_path.mkdir(exist_ok=True)

        self.tasks_path = self.storage_path / "tasks"
        self.tasks_path.mkdir(exist_ok=True)

        self.approvals_path = self.storage_path / "approvals"
        self.approvals_path.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # Monitor State
    # ========================================================================

    async def save_monitor(self, monitor: Monitor) -> bool:
        """Save a monitor definition."""
        try:
            file_path = self.monitors_path / f"{monitor.monitor_id}.json"
            data = monitor.model_dump()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            return True
        except Exception as e:
            self.logger.error(f"Error saving monitor {monitor.monitor_id}: {e}")
            return False

    async def load_monitor(self, monitor_id: str) -> Optional[Monitor]:
        """Load a monitor by ID."""
        try:
            file_path = self.monitors_path / f"{monitor_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = json.load(f)

            return Monitor(**data)
        except Exception as e:
            self.logger.error(f"Error loading monitor {monitor_id}: {e}")
            return None

    async def list_monitors(
        self,
        workspace_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Monitor]:
        """List all monitors."""
        monitors = []

        for file_path in self.monitors_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                monitor = Monitor(**data)

                # Apply filters
                if workspace_id and monitor.workspace_id != workspace_id:
                    continue
                if enabled_only and not monitor.enabled:
                    continue

                monitors.append(monitor)
            except Exception as e:
                self.logger.error(f"Error loading monitor from {file_path}: {e}")

        return monitors

    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        try:
            file_path = self.monitors_path / f"{monitor_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            self.logger.error(f"Error deleting monitor {monitor_id}: {e}")
        return False

    async def save_monitor_state(self, monitor_id: str, state: MonitorState) -> bool:
        """Save monitor state."""
        try:
            file_path = self.monitors_path / f"{monitor_id}_state.json"
            data = state.to_dict()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving monitor state {monitor_id}: {e}")
            return False

    async def load_monitor_state(self, monitor_id: str) -> Optional[MonitorState]:
        """Load monitor state."""
        try:
            file_path = self.monitors_path / f"{monitor_id}_state.json"
            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = json.load(f)

            return MonitorState.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading monitor state {monitor_id}: {e}")
            return None

    # ========================================================================
    # Task State
    # ========================================================================

    async def save_task_state(self, record: TaskStateRecord) -> bool:
        """Save a task state record."""
        try:
            # Create task directory
            task_dir = self.tasks_path / record.task_id
            task_dir.mkdir(exist_ok=True)

            # Append to history
            history_path = task_dir / "history.jsonl"
            with open(history_path, 'a') as f:
                f.write(json.dumps(record.to_dict()) + '\n')

            # Update current state
            state_path = task_dir / "current.json"
            with open(state_path, 'w') as f:
                json.dump(record.to_dict(), f, indent=2)

            return True
        except Exception as e:
            self.logger.error(f"Error saving task state {record.task_id}: {e}")
            return False

    async def load_task(self, task_id: str) -> Optional[AutonomousTask]:
        """Load a task by ID."""
        try:
            task_dir = self.tasks_path / task_id
            state_path = task_dir / "current.json"

            if not state_path.exists():
                return None

            with open(state_path, 'r') as f:
                data = json.load(f)

            task_data = data.get("data", {}).get("task")
            if task_data:
                return AutonomousTask(**task_data)

            return None
        except Exception as e:
            self.logger.error(f"Error loading task {task_id}: {e}")
            return None

    async def list_tasks(
        self,
        state: Optional[TaskState] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AutonomousTask]:
        """List tasks."""
        tasks = []

        for task_dir in self.tasks_path.iterdir():
            if not task_dir.is_dir():
                continue

            try:
                state_path = task_dir / "current.json"
                if not state_path.exists():
                    continue

                with open(state_path, 'r') as f:
                    data = json.load(f)

                task_data = data.get("data", {}).get("task")
                if task_data:
                    task = AutonomousTask(**task_data)

                    # Apply filters
                    if state and task.state != state:
                        continue
                    if workspace_id and task.workspace_id != workspace_id:
                        continue

                    tasks.append(task)

            except Exception as e:
                self.logger.error(f"Error loading task from {task_dir}: {e}")

        # Sort by created_at and limit
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def get_task_history(self, task_id: str) -> List[TaskStateRecord]:
        """Get state history for a task."""
        records = []

        try:
            task_dir = self.tasks_path / task_id
            history_path = task_dir / "history.jsonl"

            if not history_path.exists():
                return records

            with open(history_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        records.append(TaskStateRecord.from_dict(data))

        except Exception as e:
            self.logger.error(f"Error loading task history {task_id}: {e}")

        return records

    # ========================================================================
    # Approval Requests
    # ========================================================================

    async def save_approval(self, approval: ApprovalRequest) -> bool:
        """Save an approval request."""
        try:
            file_path = self.approvals_path / f"{approval.approval_id}.json"
            data = approval.model_dump()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            return True
        except Exception as e:
            self.logger.error(f"Error saving approval {approval.approval_id}: {e}")
            return False

    async def load_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Load an approval request."""
        try:
            file_path = self.approvals_path / f"{approval_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = json.load(f)

            return ApprovalRequest(**data)
        except Exception as e:
            self.logger.error(f"Error loading approval {approval_id}: {e}")
            return None

    async def list_approvals(
        self,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """List approval requests."""
        approvals = []

        for file_path in self.approvals_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                approval = ApprovalRequest(**data)

                # Apply filters
                if status and approval.status != status:
                    continue
                if workspace_id and approval.workspace_id != workspace_id:
                    continue

                approvals.append(approval)
            except Exception as e:
                self.logger.error(f"Error loading approval from {file_path}: {e}")

        # Sort by created_at
        approvals.sort(key=lambda a: a.created_at, reverse=True)
        return approvals

    async def update_approval(self, approval_id: str, updates: Dict[str, Any]) -> bool:
        """Update an approval request."""
        try:
            approval = await self.load_approval(approval_id)
            if not approval:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(approval, key):
                    setattr(approval, key, value)

            # Save updated approval
            return await self.save_approval(approval)

        except Exception as e:
            self.logger.error(f"Error updating approval {approval_id}: {e}")
            return False

    # ========================================================================
    # Cleanup
    # ========================================================================

    async def cleanup_old_data(self, max_age_seconds: int = 30 * 24 * 3600) -> int:
        """
        Clean up old data.

        Args:
            max_age_seconds: Maximum age of data to keep (default 30 days)

        Returns:
            Number of items cleaned up
        """
        cleaned = 0
        cutoff_time = time.time() - max_age_seconds

        # Clean up old completed tasks
        for task_dir in self.tasks_path.iterdir():
            if not task_dir.is_dir():
                continue

            try:
                state_path = task_dir / "current.json"
                if not state_path.exists():
                    continue

                with open(state_path, 'r') as f:
                    data = json.load(f)

                created_at = data.get("timestamp", 0)
                state = data.get("state", "")

                # Clean up old finished tasks
                if state in ["succeeded", "failed", "cancelled"] and created_at < cutoff_time:
                    import shutil
                    shutil.rmtree(task_dir)
                    cleaned += 1

            except Exception as e:
                self.logger.error(f"Error cleaning up {task_dir}: {e}")

        self.logger.info(f"Cleaned up {cleaned} old task records")
        return cleaned

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex types."""
        if isinstance(obj, float):
            return round(obj, 3)
        raise TypeError(f"Type {type(obj)} not serializable")


# Singleton instance
_state_store: Optional[StateStore] = None


def get_state_store(storage_path: Optional[str] = None) -> StateStore:
    """Get the singleton state store instance."""
    global _state_store
    if _state_store is None:
        _state_store = StateStore(storage_path=storage_path)
    return _state_store

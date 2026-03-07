"""
Task Engine - Core autonomous task execution engine.

The Task Engine is responsible for:
- Creating autonomous tasks from trigger events
- Scheduling and queuing tasks
- Managing retries and state transitions
- Dispatching work to the orchestrator
- Persisting task state
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timezone

from .models import (
    AutonomousTask, TaskState, ExecutionMode,
    TriggerEvent, Monitor, TaskStateRecord
)
from .state_store import StateStore


logger = logging.getLogger(__name__)


class TaskQueue:
    """Queue for managing pending autonomous tasks."""

    def __init__(self, max_size: int = 1000):
        self._queue: deque[AutonomousTask] = deque()
        self._max_size = max_size
        self._task_ids: Set[str] = set()

    def enqueue(self, task: AutonomousTask) -> bool:
        """Add a task to the queue."""
        if len(self._queue) >= self._max_size:
            logger.warning("Task queue is full, cannot enqueue task")
            return False

        if task.task_id in self._task_ids:
            logger.warning(f"Task {task.task_id} already in queue")
            return False

        task.state = TaskState.QUEUED
        self._queue.append(task)
        self._task_ids.add(task.task_id)
        return True

    def dequeue(self) -> Optional[AutonomousTask]:
        """Get the next task from the queue."""
        if not self._queue:
            return None

        task = self._queue.popleft()
        self._task_ids.discard(task.task_id)
        return task

    def peek(self) -> Optional[AutonomousTask]:
        """Look at the next task without removing it."""
        if not self._queue:
            return None
        return self._queue[0]

    def remove(self, task_id: str) -> bool:
        """Remove a specific task from the queue."""
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                self._queue.remove(task)
                self._task_ids.discard(task_id)
                return True
        return False

    def size(self) -> int:
        """Get the current queue size."""
        return len(self._queue)

    def list_tasks(self) -> List[AutonomousTask]:
        """List all tasks in the queue."""
        return list(self._queue)

    def clear(self):
        """Clear all tasks from the queue."""
        self._queue.clear()
        self._task_ids.clear()


class TaskScheduler:
    """Scheduler for delayed and recurring autonomous tasks."""

    def __init__(self):
        self._scheduled: Dict[str, AutonomousTask] = {}
        self._sorted_times: List[tuple[float, str]] = []
        self._lock = asyncio.Lock()

    async def schedule(
        self,
        task: AutonomousTask,
        delay_seconds: float = 0
    ) -> str:
        """Schedule a task for future execution."""
        async with self._lock:
            task.scheduled_for = time.time() + delay_seconds
            self._scheduled[task.task_id] = task
            self._update_sorted_times()
            return task.task_id

    async def schedule_at(
        self,
        task: AutonomousTask,
        timestamp: float
    ) -> str:
        """Schedule a task for specific timestamp."""
        async with self._lock:
            task.scheduled_for = timestamp
            self._scheduled[task.task_id] = task
            self._update_sorted_times()
            return task.task_id

    def _update_sorted_times(self):
        """Update the sorted list of scheduled times."""
        self._sorted_times = sorted(
            [(t.scheduled_for or 0, t.task_id) for t in self._scheduled.values() if t.scheduled_for]
        )

    async def get_due_tasks(self) -> List[AutonomousTask]:
        """Get all tasks that are due for execution."""
        now = time.time()
        due_tasks = []

        async with self._lock:
            while self._sorted_times and self._sorted_times[0][0] <= now:
                scheduled_time, task_id = self._sorted_times.pop(0)
                if task_id in self._scheduled:
                    task = self._scheduled.pop(task_id)
                    due_tasks.append(task)

        return due_tasks

    async def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        async with self._lock:
            if task_id in self._scheduled:
                task = self._scheduled.pop(task_id)
                task.state = TaskState.CANCELLED
                self._update_sorted_times()
                return True
        return False

    def list_scheduled(self) -> List[AutonomousTask]:
        """List all scheduled tasks."""
        return list(self._scheduled.values())


class TaskEngine:
    """
    Core engine for autonomous task management and execution.

    Responsibilities:
    - Create tasks from trigger events
    - Queue and schedule tasks
    - Execute tasks through the orchestrator
    - Manage task lifecycle and state transitions
    - Handle retries and failures
    - Maintain task history and telemetry
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        max_concurrent_tasks: int = 10
    ):
        self.state_store = state_store
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(__name__)

        # Task management
        self._queue = TaskQueue()
        self._scheduler = TaskScheduler()
        self._running_tasks: Dict[str, AutonomousTask] = {}
        self._completed_tasks: Dict[str, AutonomousTask] = {}

        # Execution callbacks
        self._executor: Optional[Callable] = None

        # Background processing
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the task engine."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue())
        self._scheduler_task = asyncio.create_task(self._process_scheduler())
        self.logger.info("Task engine started")

    async def stop(self):
        """Stop the task engine."""
        self._running = False

        # Cancel background tasks
        if self._processor_task:
            self._processor_task.cancel()
        if self._scheduler_task:
            self._scheduler_task.cancel()

        # Wait for tasks to complete
        try:
            await asyncio.gather(self._processor_task, self._scheduler_task, return_exceptions=True)
        except Exception:
            pass

        self.logger.info("Task engine stopped")

    def set_executor(self, executor: Callable):
        """Set the executor callback for running tasks."""
        self._executor = executor

    async def _process_queue(self):
        """Background loop that processes the task queue."""
        while self._running:
            try:
                # Wait for available slot
                while len(self._running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)

                # Get next task
                task = self._queue.dequeue()
                if task:
                    await self._execute_task(task)
                else:
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing queue: {e}")

    async def _process_scheduler(self):
        """Background loop that processes scheduled tasks."""
        while self._running:
            try:
                due_tasks = await self._scheduler.get_due_tasks()
                for task in due_tasks:
                    self._queue.enqueue(task)

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing scheduler: {e}")

    async def create_task(
        self,
        name: str,
        execution_mode: ExecutionMode,
        trigger_event: Optional[TriggerEvent] = None,
        monitor_id: Optional[str] = None,
        agents: Optional[List[str]] = None,
        prompt_template: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
        environment: Optional[str] = None,
        scheduled_for: Optional[float] = None
    ) -> AutonomousTask:
        """
        Create a new autonomous task.

        Args:
            name: Task name
            execution_mode: OBSERVE, PREPARE, or EXECUTE
            trigger_event: Event that triggered this task
            monitor_id: Monitor that created this task
            agents: List of specialist agents to use
            prompt_template: Template for the prompt
            parameters: Additional task parameters
            workspace_id: Workspace scope
            environment: Environment scope
            scheduled_for: Optional scheduled execution time

        Returns:
            Created AutonomousTask
        """
        task = AutonomousTask(
            name=name,
            execution_mode=execution_mode,
            event_id=trigger_event.event_id if trigger_event else None,
            monitor_id=monitor_id,
            agents=agents or [],
            prompt_template=prompt_template,
            parameters=parameters or {},
            workspace_id=workspace_id,
            environment=environment
        )

        # Add trigger context if available
        if trigger_event:
            task.parameters["trigger_event"] = trigger_event.model_dump()
            task.risk_level = self._determine_risk_from_event(trigger_event)

        # Schedule or queue the task
        if scheduled_for and scheduled_for > time.time():
            await self._scheduler.schedule_at(task, scheduled_for)
        else:
            self._queue.enqueue(task)

        # Persist task
        await self._save_task_state(task)

        self.logger.info(f"Created task: {task.task_id} - {task.name}")
        return task

    def _determine_risk_from_event(self, event: TriggerEvent) -> str:
        """Determine risk level from trigger event."""
        severity_map = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical"
        }
        return severity_map.get(event.severity, "low")

    async def _execute_task(self, task: AutonomousTask):
        """Execute a task through the orchestrator."""
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._running_tasks[task.task_id] = task

        await self._save_task_state(task)

        try:
            self.logger.info(f"Executing task: {task.task_id}")

            # Check if executor is set
            if self._executor is None:
                raise RuntimeError("No executor configured")

            # Execute through orchestrator
            result = await self._executor(task)

            # Process result
            task.state = TaskState.SUCCEEDED
            task.completed_at = time.time()
            task.execution_time = task.completed_at - task.started_at
            task.result = result.get("content", "")
            task.data = result.get("data", {})
            task.agent_results = result.get("agent_results", [])

            self.logger.info(f"Task succeeded: {task.task_id}")

        except Exception as e:
            self.logger.error(f"Task failed: {task.task_id} - {e}")
            task.state = TaskState.FAILED
            task.completed_at = time.time()
            task.execution_time = task.completed_at - task.started_at
            task.error = str(e)

            # Schedule retry if allowed
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRY_SCHEDULED

                # Exponential backoff: 2^retry_count * 60 seconds
                retry_delay = (2 ** task.retry_count) * 60
                retry_time = time.time() + retry_delay

                await self._scheduler.schedule_at(task, retry_time)
                self.logger.info(f"Scheduled retry {task.retry_count} for task {task.task_id} in {retry_delay}s")

        finally:
            # Move from running to completed
            self._running_tasks.pop(task.task_id, None)

            if task.is_finished:
                self._completed_tasks[task.task_id] = task

            await self._save_task_state(task)

    async def _save_task_state(self, task: AutonomousTask):
        """Save task state to persistent storage."""
        if self.state_store:
            record = TaskStateRecord(
                task_id=task.task_id,
                state=task.state,
                timestamp=time.time(),
                data={
                    "task": task.model_dump(),
                    "result": task.result,
                    "error": task.error
                }
            )
            await self.state_store.save_task_state(record)

    async def get_task(self, task_id: str) -> Optional[AutonomousTask]:
        """Get a task by ID."""
        # Check running tasks
        if task_id in self._running_tasks:
            return self._running_tasks[task_id]

        # Check completed tasks
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]

        # Check scheduled tasks
        scheduled = self._scheduler.list_scheduled()
        for task in scheduled:
            if task.task_id == task_id:
                return task

        # Check queued tasks
        for task in self._queue.list_tasks():
            if task.task_id == task_id:
                return task

        return None

    def list_tasks(
        self,
        state: Optional[TaskState] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AutonomousTask]:
        """List tasks with optional filtering."""
        all_tasks = []

        # Collect from all sources
        all_tasks.extend(self._running_tasks.values())
        all_tasks.extend(self._completed_tasks.values())
        all_tasks.extend(self._scheduler.list_scheduled())
        all_tasks.extend(self._queue.list_tasks())

        # Filter by state
        if state:
            all_tasks = [t for t in all_tasks if t.state == state]

        # Filter by workspace
        if workspace_id:
            all_tasks = [t for t in all_tasks if t.workspace_id == workspace_id]

        # Sort by created_at (newest first) and limit
        all_tasks.sort(key=lambda t: t.created_at, reverse=True)
        return all_tasks[:limit]

    async def pause_task(self, task_id: str) -> bool:
        """Pause a task."""
        task = await self.get_task(task_id)
        if task and task.state in [TaskState.CREATED, TaskState.QUEUED, TaskState.RETRY_SCHEDULED]:
            task.state = TaskState.PAUSED
            await self._save_task_state(task)

            # Remove from queue or scheduler
            self._queue.remove(task_id)
            await self._scheduler.cancel(task_id)

            return True
        return False

    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        task = await self.get_task(task_id)
        if task and task.state == TaskState.PAUSED:
            task.state = TaskState.QUEUED
            self._queue.enqueue(task)
            await self._save_task_state(task)
            return True
        return False

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = await self.get_task(task_id)
        if task:
            task.state = TaskState.CANCELLED
            await self._save_task_state(task)

            # Remove from queue or scheduler
            self._queue.remove(task_id)
            await self._scheduler.cancel(task_id)

            # Remove from running if it's running
            self._running_tasks.pop(task_id, None)

            return True
        return False

    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return self._queue.size()

    def get_running_count(self) -> int:
        """Get the number of currently running tasks."""
        return len(self._running_tasks)

    def get_metrics(self) -> Dict[str, Any]:
        """Get task engine metrics."""
        return {
            "queue_size": self._queue.size(),
            "running_count": len(self._running_tasks),
            "scheduled_count": len(self._scheduler.list_scheduled()),
            "completed_count": len(self._completed_tasks),
            "total_processed": len(self._completed_tasks),
            "is_running": self._running
        }


# Singleton instance
_task_engine: Optional[TaskEngine] = None


def get_task_engine(state_store=None) -> TaskEngine:
    """Get the singleton task engine instance."""
    global _task_engine
    if _task_engine is None:
        _task_engine = TaskEngine(state_store=state_store)
    return _task_engine

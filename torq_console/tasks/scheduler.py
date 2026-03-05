"""
Scheduler for Task Graph Engine.

Handles scheduling of workflow executions.
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable
from uuid import UUID, uuid4

from .models import TriggerType, ExecutionCreate


logger = logging.getLogger(__name__)


class ScheduleTrigger:
    """A scheduled trigger for workflow execution."""

    def __init__(
        self,
        trigger_id: UUID,
        graph_id: UUID,
        trigger_type: TriggerType,
        schedule: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
    ):
        self.trigger_id = trigger_id
        self.graph_id = graph_id
        self.trigger_type = trigger_type
        self.schedule = schedule or {}
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

    def should_run(self, now: datetime) -> bool:
        """Check if trigger should run at given time."""
        if not self.enabled:
            return False

        if self.next_run and now < self.next_run:
            return False

        return True

    def calculate_next_run(self, last_run: datetime) -> Optional[datetime]:
        """Calculate next run time based on schedule."""
        if not self.schedule:
            return None

        schedule_type = self.schedule.get("type")

        if schedule_type == "interval":
            # Run every N seconds
            interval_seconds = self.schedule.get("seconds", 3600)
            return last_run + timedelta(seconds=interval_seconds)

        elif schedule_type == "cron":
            # TODO: Implement cron parsing
            # For now, simple hourly/daily/weekly
            frequency = self.schedule.get("frequency", "hourly")
            if frequency == "hourly":
                return last_run + timedelta(hours=1)
            elif frequency == "daily":
                return last_run + timedelta(days=1)
            elif frequency == "weekly":
                return last_run + timedelta(weeks=1)

        return None


class Scheduler:
    """
    Schedules and triggers workflow executions.

    Supports:
    - Manual triggers
    - Timer-based triggers (intervals, cron)
    - Webhook triggers
    - Event-based triggers
    """

    def __init__(self, supabase_client=None, executor=None):
        """
        Initialize the scheduler.

        Args:
            supabase_client: Supabase client for persistence
            executor: Execution engine to run workflows
        """
        self.supabase = supabase_client
        self.executor = executor
        self.triggers: Dict[UUID, ScheduleTrigger] = {}
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def register_trigger(
        self,
        graph_id: UUID,
        trigger_type: TriggerType,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Register a new trigger.

        Args:
            graph_id: Graph to trigger
            trigger_type: Type of trigger
            schedule: Schedule configuration

        Returns:
            Trigger ID
        """
        trigger_id = uuid4()

        trigger = ScheduleTrigger(
            trigger_id=trigger_id,
            graph_id=graph_id,
            trigger_type=trigger_type,
            schedule=schedule,
        )

        # Calculate next run for timer triggers
        if trigger_type == TriggerType.TIMER and schedule:
            trigger.next_run = trigger.calculate_next_run(datetime.now(timezone.utc))

        self.triggers[trigger_id] = trigger

        # Persist to database
        if self.supabase:
            self.supabase.table("task_triggers").insert({
                "trigger_id": str(trigger_id),
                "graph_id": str(graph_id),
                "trigger_type": trigger_type.value,
                "schedule": schedule,
                "enabled": True,
                "next_run": trigger.next_run.isoformat() if trigger.next_run else None,
            }).execute()

        logger.info(f"Registered trigger {trigger_id} for graph {graph_id} ({trigger_type.value})")

        return trigger_id

    async def unregister_trigger(self, trigger_id: UUID) -> bool:
        """
        Unregister a trigger.

        Args:
            trigger_id: Trigger ID

        Returns:
            True if unregistered
        """
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]

            if self.supabase:
                self.supabase.table("task_triggers").delete().eq("trigger_id", str(trigger_id)).execute()

            return True
        return False

    async def trigger_graph(
        self,
        graph_id: UUID,
        trigger_type: TriggerType = TriggerType.MANUAL,
        trigger_source: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Manually trigger a graph execution.

        Args:
            graph_id: Graph to execute
            trigger_type: Type of trigger
            trigger_source: Source of trigger
            input_data: Input data for execution

        Returns:
            Execution ID
        """
        from .graph_engine import TaskGraphEngine
        from .executor import ExecutionEngine

        if not self.executor:
            raise RuntimeError("Executor not configured")

        # Load graph
        engine = TaskGraphEngine(self.supabase)
        graph = await engine.get_graph(graph_id)

        if not graph:
            raise ValueError(f"Graph {graph_id} not found")

        # Create execution request
        execution_request = ExecutionCreate(
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            input_data=input_data or {},
        )

        # Execute graph (in background)
        async def execute():
            return await self.executor.execute_graph(graph, execution_request)

        # Run execution asynchronously
        task = asyncio.create_task(execute())
        return await task  # Wait for result for now, could be made async

    async def start(self):
        """Start the scheduler background task."""
        if self.running:
            return

        self.running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now(timezone.utc)

                for trigger_id, trigger in self.triggers.items():
                    if trigger.should_run(now):
                        logger.info(f"Triggering graph {trigger.graph_id} via {trigger.trigger_type.value}")

                        try:
                            # TODO: Handle execution asynchronously
                            await self.trigger_graph(
                                graph_id=trigger.graph_id,
                                trigger_type=trigger.trigger_type,
                                trigger_source=f"scheduler:{trigger_id}",
                            )

                            trigger.last_run = now

                            # Calculate next run
                            if trigger.trigger_type == TriggerType.TIMER:
                                trigger.next_run = trigger.calculate_next_run(now)

                        except Exception as e:
                            logger.error(f"Failed to execute triggered graph: {e}")

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    async def handle_webhook(self, graph_id: UUID, payload: Dict[str, Any]) -> UUID:
        """
        Handle webhook trigger.

        Args:
            graph_id: Graph to execute
            payload: Webhook payload

        Returns:
            Execution ID
        """
        return await self.trigger_graph(
            graph_id=graph_id,
            trigger_type=TriggerType.WEBHOOK,
            trigger_source="webhook",
            input_data=payload,
        )

    def get_scheduled_triggers(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled triggers.

        Returns:
            List of trigger info
        """
        return [
            {
                "trigger_id": str(t.trigger_id),
                "graph_id": str(t.graph_id),
                "trigger_type": t.trigger_type.value,
                "enabled": t.enabled,
                "next_run": t.next_run.isoformat() if t.next_run else None,
                "last_run": t.last_run.isoformat() if t.last_run else None,
            }
            for t in self.triggers.values()
            if t.enabled
        ]

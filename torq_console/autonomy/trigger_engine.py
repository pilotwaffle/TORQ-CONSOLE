"""
Trigger Engine - Evaluates events and detects trigger conditions.

The Trigger Engine is responsible for:
- Evaluating incoming events against trigger conditions
- Comparing state against thresholds
- Determining whether trigger conditions are met
- Suppressing duplicates/noise
- Emitting actionable events
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    Monitor, MonitorType, TriggerEvent, TriggerType,
    MonitorState
)


logger = logging.getLogger(__name__)


class TriggerEvaluator:
    """
    Evaluates whether a trigger condition has been met.

    Supports various trigger types:
    - Threshold: numeric value crosses boundary
    - Status change: state transitions
    - Absence: expected event doesn't occur
    - Anomaly: deviation from baseline
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._baselines: Dict[str, Any] = {}

    def evaluate(
        self,
        monitor: Monitor,
        current_value: Any,
        previous_value: Optional[Any] = None,
        monitor_state: Optional[MonitorState] = None
    ) -> Optional[TriggerEvent]:
        """
        Evaluate a monitor's trigger condition.

        Args:
            monitor: The monitor to evaluate
            current_value: Current observed value
            previous_value: Previous value for comparison
            monitor_state: Current monitor state

        Returns:
            TriggerEvent if condition is met, None otherwise
        """
        condition = monitor.trigger_condition

        if not condition:
            return None

        trigger_type = condition.get("type")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        # Check for cooldown
        if monitor.is_in_cooldown:
            self.logger.debug(f"Monitor {monitor.monitor_id} in cooldown, skipping")
            return None

        # Evaluate based on trigger type
        if trigger_type == "threshold":
            return self._evaluate_threshold(
                monitor, current_value, operator, expected_value, condition
            )
        elif trigger_type == "status_change":
            return self._evaluate_status_change(
                monitor, current_value, previous_value, expected_value
            )
        elif trigger_type == "absence":
            return self._evaluate_absence(
                monitor, current_value, monitor_state
            )
        elif trigger_type == "anomaly":
            return self._evaluate_anomaly(
                monitor, current_value, condition
            )
        elif trigger_type == "keyword_match":
            # Support both 'keywords' and 'value' keys for keyword matching
            keywords_value = condition.get("keywords") or expected_value or []
            return self._evaluate_keyword_match(
                monitor, str(current_value), keywords_value
            )
        else:
            self.logger.warning(f"Unknown trigger type: {trigger_type}")
            return None

    def _evaluate_threshold(
        self,
        monitor: Monitor,
        current_value: Any,
        operator: str,
        expected_value: Any,
        condition: Optional[Dict[str, Any]] = None
    ) -> Optional[TriggerEvent]:
        """Evaluate numeric threshold condition."""
        try:
            current = float(current_value)
            expected = float(expected_value)

            triggered = False
            if operator == ">":
                triggered = current > expected
            elif operator == ">=":
                triggered = current >= expected
            elif operator == "<":
                triggered = current < expected
            elif operator == "<=":
                triggered = current <= expected
            elif operator == "==":
                triggered = current == expected
            elif operator == "!=":
                triggered = current != expected
            else:
                self.logger.warning(f"Unknown operator: {operator}")
                return None

            if triggered:
                return TriggerEvent(
                    monitor_id=monitor.monitor_id,
                    event_type=TriggerType.THRESHOLD_CROSSED,
                    severity=self._get_severity(monitor, "threshold"),
                    payload={
                        "field": condition.get("field", "value") if condition else "value",
                        "current": current,
                        "operator": operator,
                        "threshold": expected,
                        "target": monitor.target
                    },
                    workspace_id=monitor.workspace_id,
                    environment=monitor.environment
                )
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error evaluating threshold: {e}")

        return None

    def _evaluate_status_change(
        self,
        monitor: Monitor,
        current_value: Any,
        previous_value: Optional[Any],
        expected_value: Any
    ) -> Optional[TriggerEvent]:
        """Evaluate status change condition."""
        if previous_value is None:
            # First run, establish baseline
            return None

        if current_value != previous_value:
            # Check if transition matches expected
            if expected_value is None or current_value == expected_value:
                return TriggerEvent(
                    monitor_id=monitor.monitor_id,
                    event_type=TriggerType.STATUS_CHANGED,
                    severity=self._get_severity(monitor, "status"),
                    payload={
                        "previous_status": previous_value,
                        "current_status": current_value,
                        "target": monitor.target
                    },
                    workspace_id=monitor.workspace_id,
                    environment=monitor.environment
                )

        return None

    def _evaluate_absence(
        self,
        monitor: Monitor,
        current_value: Any,
        monitor_state: Optional[MonitorState]
    ) -> Optional[TriggerEvent]:
        """Evaluate absence/missing heartbeat condition."""
        # Check if we're past the expected time window
        if monitor_state and monitor_state.last_check:
            time_since_last = time.time() - monitor_state.last_check
            expected_interval = monitor.trigger_condition.get("interval_seconds", monitor.interval_seconds)

            if time_since_last > expected_interval * 2:  # 2x interval = missed
                return TriggerEvent(
                    monitor_id=monitor.monitor_id,
                    event_type=TriggerType.HEARTBEAT_MISSED,
                    severity=self._get_severity(monitor, "absence"),
                    payload={
                        "last_check": monitor_state.last_check,
                        "time_since_last": time_since_last,
                        "expected_interval": expected_interval
                    },
                    workspace_id=monitor.workspace_id,
                    environment=monitor.environment
                )

        return None

    def _evaluate_anomaly(
        self,
        monitor: Monitor,
        current_value: Any,
        condition: Dict[str, Any]
    ) -> Optional[TriggerEvent]:
        """Evaluate anomaly detection condition."""
        try:
            current = float(current_value)
            field = condition.get("field", "value")
            threshold_percent = condition.get("threshold_percent", 50)

            # Get or establish baseline
            baseline_key = f"{monitor.monitor_id}:{field}"
            baseline = self._baselines.get(baseline_key)

            if baseline is None:
                # Establish baseline
                self._baselines[baseline_key] = current
                return None

            # Check for deviation
            if baseline != 0:
                deviation = abs((current - baseline) / baseline) * 100
            else:
                deviation = abs(current) * 100

            if deviation > threshold_percent:
                return TriggerEvent(
                    monitor_id=monitor.monitor_id,
                    event_type=TriggerType.ANOMALY_DETECTED,
                    severity=self._get_severity(monitor, "anomaly"),
                    payload={
                        "field": field,
                        "current": current,
                        "baseline": baseline,
                        "deviation_percent": round(deviation, 2)
                    },
                    workspace_id=monitor.workspace_id,
                    environment=monitor.environment
                )
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error evaluating anomaly: {e}")

        return None

    def _evaluate_keyword_match(
        self,
        monitor: Monitor,
        text: str,
        keywords: Any
    ) -> Optional[TriggerEvent]:
        """Evaluate keyword/topic match condition."""
        if not isinstance(keywords, list):
            keywords = [keywords]

        text_lower = text.lower()
        matched_keywords = [kw for kw in keywords if kw.lower() in text_lower]

        if matched_keywords:
            return TriggerEvent(
                monitor_id=monitor.monitor_id,
                event_type=TriggerType.TOPIC_MATCHED,
                severity=self._get_severity(monitor, "topic"),
                payload={
                    "text": text[:500],  # Truncate for storage
                    "matched_keywords": matched_keywords
                },
                workspace_id=monitor.workspace_id,
                environment=monitor.environment
            )

        return None

    def _get_severity(self, monitor: Monitor, trigger_type: str) -> str:
        """Determine event severity."""
        # Can be overridden by monitor config
        severity_map = {
            "threshold": "medium",
            "status": "high",
            "absence": "high",
            "anomaly": "medium",
            "topic": "low"
        }
        return severity_map.get(trigger_type, "medium")


class TriggerEngine:
    """
    Engine for managing trigger evaluation and event generation.

    Responsibilities:
    - Register and manage monitors
    - Evaluate monitors on schedule
    - Generate trigger events
    - Suppress duplicate/noisy triggers
    - Route events to task engine
    """

    def __init__(self, state_store=None):
        self.state_store = state_store
        self.evaluator = TriggerEvaluator()
        self.logger = logging.getLogger(__name__)

        # Monitor registry
        self._monitors: Dict[str, Monitor] = {}
        self._monitor_states: Dict[str, MonitorState] = {}

        # Event handlers
        self._event_handlers: List[Callable] = []

        # Background task
        self._running = False
        self._evaluation_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the trigger engine background evaluation."""
        if self._running:
            return

        self._running = True
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        self.logger.info("Trigger engine started")

    async def stop(self):
        """Stop the trigger engine."""
        self._running = False
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Trigger engine stopped")

    async def _evaluation_loop(self):
        """Background loop that evaluates monitors."""
        while self._running:
            try:
                await self._evaluate_monitors()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in evaluation loop: {e}")

    async def _evaluate_monitors(self):
        """Evaluate all due monitors."""
        now = time.time()

        for monitor_id, monitor in self._monitors.items():
            if not monitor.enabled:
                continue

            if monitor.is_due:
                await self._evaluate_monitor(monitor)

    async def _evaluate_monitor(self, monitor: Monitor):
        """Evaluate a single monitor."""
        self.logger.debug(f"Evaluating monitor: {monitor.monitor_id}")

        # Get current state
        state = self._monitor_states.get(monitor.monitor_id)
        if state is None:
            state = MonitorState(monitor_id=monitor.monitor_id)
            self._monitor_states[monitor.monitor_id] = state

        # Get current value (would fetch from target in real implementation)
        current_value = await self._fetch_monitor_value(monitor)
        previous_value = state.last_result.get("value") if state.last_result else None

        # Evaluate trigger condition
        event = self.evaluator.evaluate(
            monitor, current_value, previous_value, state
        )

        # Update state
        state.last_check = time.time()
        if current_value is not None:
            state.last_result = {"value": current_value, "timestamp": state.last_check}

        if event:
            state.last_trigger = event.detected_at
            state.trigger_count += 1

            # Save state and emit event
            await self._emit_event(event)
            await self._save_state(monitor.monitor_id, state)

    async def _fetch_monitor_value(self, monitor: Monitor) -> Any:
        """
        Fetch current value from monitor target.

        In real implementation, this would:
        - Make HTTP request to health endpoint
        - Query database
        - Check message queue
        - Fetch from API
        """
        # For Phase 5A, return a mock value
        # In production, this would actually call the target
        return None

    async def _emit_event(self, event: TriggerEvent):
        """Emit a trigger event to registered handlers."""
        self.logger.info(f"Emitting event: {event.event_id} from {event.monitor_id}")

        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")

    async def _save_state(self, monitor_id: str, state: MonitorState):
        """Save monitor state to persistent storage."""
        if self.state_store:
            await self.state_store.save_monitor_state(monitor_id, state)

    def register_monitor(self, monitor: Monitor) -> bool:
        """Register a new monitor."""
        self._monitors[monitor.monitor_id] = monitor
        self.logger.info(f"Registered monitor: {monitor.monitor_id}")
        return True

    def unregister_monitor(self, monitor_id: str) -> bool:
        """Unregister a monitor."""
        if monitor_id in self._monitors:
            del self._monitors[monitor_id]
            if monitor_id in self._monitor_states:
                del self._monitor_states[monitor_id]
            self.logger.info(f"Unregistered monitor: {monitor_id}")
            return True
        return False

    def get_monitor(self, monitor_id: str) -> Optional[Monitor]:
        """Get a registered monitor."""
        return self._monitors.get(monitor_id)

    def list_monitors(self, workspace_id: Optional[str] = None) -> List[Monitor]:
        """List all monitors, optionally filtered by workspace."""
        monitors = list(self._monitors.values())
        if workspace_id:
            monitors = [m for m in monitors if m.workspace_id == workspace_id]
        return monitors

    def add_event_handler(self, handler: Callable):
        """Add an event handler callback."""
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable):
        """Remove an event handler callback."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    def get_monitor_state(self, monitor_id: str) -> Optional[MonitorState]:
        """Get the current state of a monitor."""
        return self._monitor_states.get(monitor_id)


# Singleton instance
_trigger_engine: Optional[TriggerEngine] = None


def get_trigger_engine(state_store=None) -> TriggerEngine:
    """Get the singleton trigger engine instance."""
    global _trigger_engine
    if _trigger_engine is None:
        _trigger_engine = TriggerEngine(state_store=state_store)
    return _trigger_engine

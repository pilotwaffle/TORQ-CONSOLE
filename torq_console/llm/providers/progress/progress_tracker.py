"""
Progress Tracker

Real-time progress monitoring for long-running research operations.
"""

import time
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProgressStatus:
    """Container for progress status information."""
    operation: str
    stage: str
    percent: float  # 0.0 to 100.0
    message: str
    items_done: int = 0
    items_total: int = 0
    elapsed_seconds: float = 0.0
    eta_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """
    Track progress of long-running operations with real-time updates.

    Features:
    - Stage-based progress tracking
    - Percentage calculation
    - ETA estimation
    - Event callbacks
    - Timing information
    """

    # Progress stages for search operations
    STAGE_SEARCHING = "searching"
    STAGE_EXTRACTING = "extracting"
    STAGE_SCORING = "scoring"
    STAGE_SYNTHESIZING = "synthesizing"
    STAGE_FINALIZING = "finalizing"

    # Stage weight distribution (totals to 100%)
    STAGE_WEIGHTS = {
        STAGE_SEARCHING: 20,      # 0-20%
        STAGE_EXTRACTING: 30,     # 20-50%
        STAGE_SCORING: 20,        # 50-70%
        STAGE_SYNTHESIZING: 25,   # 70-95%
        STAGE_FINALIZING: 5       # 95-100%
    }

    def __init__(self, operation_name: str = "Research"):
        """
        Initialize progress tracker.

        Args:
            operation_name: Name of the operation being tracked
        """
        self.operation_name = operation_name
        self.logger = logging.getLogger(__name__)

        # Progress state
        self.current_stage = None
        self.start_time = None
        self.stage_start_time = None
        self.items_done = 0
        self.items_total = 0
        self.metadata = {}

        # Callbacks
        self.callbacks = []

        # History
        self.stage_history = []

    def start(self):
        """Start tracking progress."""
        self.start_time = time.time()
        self.logger.info(f"[PROGRESS] Started tracking: {self.operation_name}")

    def update_stage(
        self,
        stage: str,
        message: str = "",
        items_total: int = 0
    ):
        """
        Update to a new stage.

        Args:
            stage: Stage identifier
            message: Status message
            items_total: Total items for this stage
        """
        # Save previous stage to history
        if self.current_stage:
            self.stage_history.append({
                'stage': self.current_stage,
                'duration': time.time() - self.stage_start_time
            })

        self.current_stage = stage
        self.stage_start_time = time.time()
        self.items_done = 0
        self.items_total = items_total

        # Calculate percentage
        percent = self._calculate_percent()

        # Create status
        status = ProgressStatus(
            operation=self.operation_name,
            stage=stage,
            percent=percent,
            message=message or f"Started {stage}",
            items_done=0,
            items_total=items_total,
            elapsed_seconds=time.time() - self.start_time if self.start_time else 0,
            eta_seconds=self._estimate_eta(percent),
            metadata=self.metadata.copy()
        )

        # Notify callbacks
        self._notify(status)

    def update_progress(
        self,
        items_done: Optional[int] = None,
        message: str = ""
    ):
        """
        Update progress within current stage.

        Args:
            items_done: Number of items completed (increments if None)
            message: Status message
        """
        if items_done is not None:
            self.items_done = items_done
        else:
            self.items_done += 1

        # Calculate percentage
        percent = self._calculate_percent()

        # Create status
        status = ProgressStatus(
            operation=self.operation_name,
            stage=self.current_stage or "unknown",
            percent=percent,
            message=message or f"Processing {self.items_done}/{self.items_total}",
            items_done=self.items_done,
            items_total=self.items_total,
            elapsed_seconds=time.time() - self.start_time if self.start_time else 0,
            eta_seconds=self._estimate_eta(percent),
            metadata=self.metadata.copy()
        )

        # Notify callbacks
        self._notify(status)

    def complete(self, message: str = "Complete"):
        """Mark operation as complete."""
        # Update internal state
        self.current_stage = "complete"
        self.items_done = self.items_total

        status = ProgressStatus(
            operation=self.operation_name,
            stage="complete",
            percent=100.0,
            message=message,
            items_done=self.items_total,
            items_total=self.items_total,
            elapsed_seconds=time.time() - self.start_time if self.start_time else 0,
            eta_seconds=0,
            metadata=self.metadata.copy()
        )

        self._notify(status)
        self.logger.info(f"[PROGRESS] Completed: {self.operation_name}")

    def on_progress(self, callback: Callable[[ProgressStatus], None]):
        """
        Register a callback for progress updates.

        Args:
            callback: Function to call with ProgressStatus
        """
        self.callbacks.append(callback)

    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value

    def _calculate_percent(self) -> float:
        """Calculate current progress percentage."""
        if not self.current_stage:
            return 0.0

        # Get stage weight
        stage_weight = self.STAGE_WEIGHTS.get(self.current_stage, 10)

        # Get base percentage (start of this stage) - sum of completed stages
        base_percent = 0.0
        for stage_name, _ in self.stage_history:
            base_percent += self.STAGE_WEIGHTS.get(stage_name, 10)

        # Calculate progress within current stage
        if self.items_total > 0:
            # Progress based on items completed
            stage_progress = (self.items_done / self.items_total) * stage_weight
        else:
            # No items specified - assume we're at the start of this stage
            stage_progress = 0.0

        total_percent = base_percent + stage_progress
        return min(100.0, total_percent)

    def _estimate_eta(self, current_percent: float) -> Optional[float]:
        """Estimate time to completion."""
        if not self.start_time or current_percent <= 0:
            return None

        elapsed = time.time() - self.start_time
        if current_percent >= 100:
            return 0.0

        # Avoid division by zero for very fast operations
        if elapsed < 0.01:  # Less than 10ms
            return None

        # Estimate based on current progress rate
        rate = current_percent / elapsed  # percent per second
        remaining_percent = 100.0 - current_percent
        eta = remaining_percent / rate if rate > 0 else None

        return eta

    def _notify(self, status: ProgressStatus):
        """Notify all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"[PROGRESS] Callback error: {e}")

    def get_status(self) -> ProgressStatus:
        """Get current status."""
        # Special case: if stage is "complete", always return 100%
        if self.current_stage == "complete":
            percent = 100.0
        else:
            percent = self._calculate_percent()

        return ProgressStatus(
            operation=self.operation_name,
            stage=self.current_stage or "not_started",
            percent=percent,
            message="",
            items_done=self.items_done,
            items_total=self.items_total,
            elapsed_seconds=time.time() - self.start_time if self.start_time else 0,
            eta_seconds=self._estimate_eta(percent),
            metadata=self.metadata.copy()
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        return {
            'operation': self.operation_name,
            'current_stage': self.current_stage,
            'percent': self._calculate_percent(),
            'elapsed_seconds': time.time() - self.start_time if self.start_time else 0,
            'stages_completed': len(self.stage_history),
            'total_stages': len(self.STAGE_WEIGHTS),
            'metadata': self.metadata.copy()
        }

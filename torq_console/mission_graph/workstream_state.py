"""
Execution Fabric - Workstream State Manager

Tracks health, progress, and state for each workstream in a mission.
Provides visibility into parallel work streams and enables coordination.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


logger = logging.getLogger(__name__)


# ============================================================================
# Workstream State Models
# ============================================================================

class WorkstreamPhase(str, Enum):
    """Phases of workstream execution."""
    INITIALIZING = "initializing"
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REVIEW = "review"
    FINALIZING = "finalizing"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class WorkstreamHealth(str, Enum):
    """Health status of a workstream."""
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    STALLED = "stalled"


class BlockerSeverity(str, Enum):
    """Severity of blockers."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Blocker:
    """A blocker preventing workstream progress."""
    id: str = field(default_factory=lambda: str(uuid4()))
    node_id: str = ""
    description: str = ""
    severity: BlockerSeverity = BlockerSeverity.MEDIUM
    blocked_at: datetime = field(default_factory=datetime.now)
    resolution_plan: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolving_node_id: Optional[str] = None


@dataclass
class WorkstreamState:
    """
    Complete state of a workstream during mission execution.

    Tracks progress, health, blockers, and coordination needs.
    """
    workstream_id: str = ""
    mission_id: str = ""

    # Basic status
    phase: WorkstreamPhase = WorkstreamPhase.INITIALIZING
    health: WorkstreamHealth = WorkstreamHealth.HEALTHY
    status: str = "pending"  # pending, running, paused, completed, failed

    # Progress tracking
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    skipped_nodes: int = 0
    progress_percent: float = 0.0

    # Confidence and quality
    confidence_score: float = 0.5  # 0.0 to 1.0
    quality_score: float = 0.5  # 0.0 to 1.0
    contradiction_count: int = 0

    # Blockers and risks
    blockers: List[Blocker] = field(default_factory=list)
    known_risks: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    # Dependencies
    depends_on_workstreams: List[str] = field(default_factory=list)
    waiting_for_dependencies: bool = False
    dependencies_satisfied_at: Optional[datetime] = None

    # Coordination
    needs_input_from: List[str] = field(default_factory=list)  # Workstream IDs
    provides_input_to: List[str] = field(default_factory=list)  # Workstream IDs
    pending_handoffs: int = 0
    completed_handoffs: int = 0

    # Timing
    started_at: Optional[datetime] = None
    phase_started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)

    # Agent assignment
    lead_agent_type: str = ""
    active_agents: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkstreamTransition:
    """Record of a workstream state transition."""
    id: str = field(default_factory=lambda: str(uuid4()))
    workstream_id: str = ""
    from_phase: Optional[WorkstreamPhase] = None
    to_phase: WorkstreamPhase = WorkstreamPhase.INITIALIZING
    from_health: Optional[WorkstreamHealth] = None
    to_health: WorkstreamHealth = WorkstreamHealth.HEALTHY
    reason: str = ""
    triggered_by: str = ""  # node_id, system, or manual
    triggered_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Workstream State Manager
# ============================================================================

class WorkstreamStateManager:
    """
    Manages state for all workstreams in a mission.

    Responsibilities:
    - Track workstream progress and health
    - Detect and manage blockers
    - Coordinate workstream dependencies
    - Emit state transition events
    """

    def __init__(self, supabase_client, context_bus=None):
        self.supabase = supabase_client
        self.context_bus = context_bus

        # In-memory cache of workstream states
        self._states: Dict[str, WorkstreamState] = {}

    async def initialize_workstream(
        self,
        workstream_id: str,
        mission_id: str,
        lead_agent_type: str,
        node_ids: List[str],
        depends_on: List[str]
    ) -> WorkstreamState:
        """Initialize a new workstream state."""
        state = WorkstreamState(
            workstream_id=workstream_id,
            mission_id=mission_id,
            lead_agent_type=lead_agent_type,
            total_nodes=len(node_ids),
            depends_on_workstreams=depends_on,
            waiting_for_dependencies=len(depends_on) > 0
        )

        # Store in cache and database
        self._states[workstream_id] = state
        await self._persist_state(state)

        logger.info(f"Initialized workstream {workstream_id} with {len(node_ids)} nodes")

        return state

    async def update_progress(
        self,
        workstream_id: str,
        completed_node_id: str,
        node_status: str
    ) -> WorkstreamState:
        """Update workstream progress after node completion."""
        state = self._get_state(workstream_id)

        if node_status == "completed":
            state.completed_nodes += 1
        elif node_status == "failed":
            state.failed_nodes += 1
        elif node_status == "skipped":
            state.skipped_nodes += 1

        # Recalculate progress
        state.progress_percent = (
            (state.completed_nodes + state.skipped_nodes) / state.total_nodes * 100
            if state.total_nodes > 0 else 0
        )

        # Update last activity
        state.last_activity = datetime.now()
        state.updated_at = datetime.now()

        # Check for phase transition
        await self._check_phase_transition(state)

        # Persist and emit event
        await self._persist_state(state)
        await self._emit_progress_event(state, completed_node_id)

        return state

    async def add_blocker(
        self,
        workstream_id: str,
        node_id: str,
        description: str,
        severity: BlockerSeverity = BlockerSeverity.MEDIUM,
        resolution_plan: Optional[str] = None
    ) -> Blocker:
        """Add a blocker to a workstream."""
        state = self._get_state(workstream_id)

        blocker = Blocker(
            node_id=node_id,
            description=description,
            severity=severity,
            resolution_plan=resolution_plan
        )

        state.blockers.append(blocker)

        # Update health based on blocker severity
        if severity == BlockerSeverity.CRITICAL:
            state.health = WorkstreamHealth.CRITICAL
            state.phase = WorkstreamPhase.BLOCKED
        elif severity == BlockerSeverity.HIGH and state.health == WorkstreamHealth.HEALTHY:
            state.health = WorkstreamHealth.AT_RISK

        state.updated_at = datetime.now()

        # Persist and emit
        await self._persist_state(state)
        await self._emit_blocker_event(state, blocker)

        logger.warning(f"Blocker added to workstream {workstream_id}: {description}")

        return blocker

    async def resolve_blocker(
        self,
        workstream_id: str,
        blocker_id: str,
        resolving_node_id: str
    ) -> Optional[Blocker]:
        """Resolve a blocker."""
        state = self._get_state(workstream_id)

        for blocker in state.blockers:
            if blocker.id == blocker_id:
                blocker.resolved_at = datetime.now()
                blocker.resolving_node_id = resolving_node_id
                await self._emit_blocker_resolved_event(state, blocker)
                return blocker

        return None

    async def update_health(
        self,
        workstream_id: str,
        health: WorkstreamHealth,
        reason: str
    ) -> WorkstreamState:
        """Update workstream health status."""
        state = self._get_state(workstream_id)

        old_health = state.health
        state.health = health
        state.updated_at = datetime.now()

        # Record transition
        transition = WorkstreamTransition(
            workstream_id=workstream_id,
            from_health=old_health,
            to_health=health,
            reason=reason,
            triggered_by="system"
        )

        # Persist and emit
        await self._persist_state(state)
        await self._emit_health_transition_event(state, transition)

        logger.info(f"Workstream {workstream_id} health: {old_health} -> {health}")

        return state

    async def transition_phase(
        self,
        workstream_id: str,
        new_phase: WorkstreamPhase,
        reason: str,
        triggered_by: str = "system"
    ) -> WorkstreamState:
        """Transition workstream to a new phase."""
        state = self._get_state(workstream_id)

        old_phase = state.phase
        state.phase = new_phase
        state.phase_started_at = datetime.now()
        state.updated_at = datetime.now()

        # Record transition
        transition = WorkstreamTransition(
            workstream_id=workstream_id,
            from_phase=old_phase,
            to_phase=new_phase,
            reason=reason,
            triggered_by=triggered_by
        )

        # Persist and emit
        await self._persist_state(state)
        await self._emit_phase_transition_event(state, transition)

        logger.info(f"Workstream {workstream_id} phase: {old_phase} -> {new_phase}")

        return state

    async def get_state(self, workstream_id: str) -> WorkstreamState:
        """Get current state of a workstream."""
        return self._get_state(workstream_id)

    async def get_all_states(self, mission_id: str) -> List[WorkstreamState]:
        """Get all workstream states for a mission."""
        try:
            result = self.supabase.table("workstream_states").select("*").eq("mission_id", mission_id).execute()

            states = []
            for record in result.data:
                state = await self._load_state_from_record(record)
                # Update cache
                self._states[state.workstream_id] = state
                states.append(state)

            return states

        except Exception as e:
            logger.error(f"Error loading workstream states: {e}")
            return []

    async def get_blocked_workstreams(self, mission_id: str) -> List[WorkstreamState]:
        """Get all workstreams that are blocked or at risk."""
        states = await self.get_all_states(mission_id)
        return [s for s in states if s.phase == WorkstreamPhase.BLOCKED or s.health in [WorkstreamHealth.AT_RISK, WorkstreamHealth.CRITICAL]]

    async def check_dependencies(
        self,
        workstream_id: str,
        completed_workstream_id: str
    ) -> Optional[WorkstreamState]:
        """Check if a workstream's dependencies are satisfied and unblock if so."""
        state = self._get_state(workstream_id)

        if completed_workstream_id in state.depends_on_workstreams:
            # Remove from dependencies
            state.depends_on_workstreams.remove(completed_workstream_id)

            # Check if all dependencies satisfied
            if len(state.depends_on_workstreams) == 0 and state.waiting_for_dependencies:
                state.waiting_for_dependencies = False
                state.dependencies_satisfied_at = datetime.now()

                # Transition to discovery phase if still initializing
                if state.phase == WorkstreamPhase.INITIALIZING:
                    await self.transition_phase(
                        workstream_id,
                        WorkstreamPhase.DISCOVERY,
                        "Dependencies satisfied",
                        "dependency_check"
                    )

                await self._persist_state(state)
                await self._emit_dependencies_satisfied_event(state)

                logger.info(f"Workstream {workstream_id} dependencies satisfied, unblocking")

                return state

        return None

    # ========================================================================
    # Internal Methods
    # ========================================================================

    def _get_state(self, workstream_id: str) -> WorkstreamState:
        """Get state from cache or load from database."""
        if workstream_id in self._states:
            return self._states[workstream_id]

        # Load from database
        try:
            result = self.supabase.table("workstream_states").select("*").eq("workstream_id", workstream_id).execute()

            if result.data:
                import asyncio
                state = asyncio.create_task(self._load_state_from_record(result.data[0]))
                self._states[workstream_id] = state
                return state

        except Exception as e:
            logger.error(f"Error loading workstream state: {e}")

        # Return empty state if not found
        return WorkstreamState(workstream_id=workstream_id)

    async def _check_phase_transition(self, state: WorkstreamState):
        """Check if workstream should transition to a new phase."""
        if state.phase == WorkstreamPhase.INITIALIZING:
            if not state.waiting_for_dependencies:
                await self.transition_phase(
                    state.workstream_id,
                    WorkstreamPhase.DISCOVERY,
                    "Initialization complete"
                )

        elif state.phase == WorkstreamPhase.DISCOVERY:
            # Transition to analysis when 25% complete
            if state.progress_percent >= 25:
                await self.transition_phase(
                    state.workstream_id,
                    WorkstreamPhase.ANALYSIS,
                    "Discovery phase complete"
                )

        elif state.phase == WorkstreamPhase.ANALYSIS:
            # Transition to synthesis when 75% complete
            if state.progress_percent >= 75:
                await self.transition_phase(
                    state.workstream_id,
                    WorkstreamPhase.SYNTHESIS,
                    "Analysis phase complete"
                )

        elif state.phase == WorkstreamPhase.SYNTHESIS:
            # Transition to review when 95% complete
            if state.progress_percent >= 95:
                await self.transition_phase(
                    state.workstream_id,
                    WorkstreamPhase.REVIEW,
                    "Synthesis phase complete"
                )

        elif state.phase == WorkstreamPhase.REVIEW:
            # Transition to finalizing when all nodes complete
            if state.progress_percent >= 100:
                await self.transition_phase(
                    state.workstream_id,
                    WorkstreamPhase.FINALIZING,
                    "All nodes complete"
                )

    async def _persist_state(self, state: WorkstreamState):
        """Persist workstream state to database."""
        try:
            self.supabase.table("workstream_states").upsert({
                "workstream_id": state.workstream_id,
                "mission_id": state.mission_id,
                "phase": state.phase.value,
                "health": state.health.value,
                "status": state.status,
                "total_nodes": state.total_nodes,
                "completed_nodes": state.completed_nodes,
                "failed_nodes": state.failed_nodes,
                "skipped_nodes": state.skipped_nodes,
                "progress_percent": state.progress_percent,
                "confidence_score": state.confidence_score,
                "quality_score": state.quality_score,
                "contradiction_count": state.contradiction_count,
                "blockers": [
                    {
                        "id": b.id,
                        "node_id": b.node_id,
                        "description": b.description,
                        "severity": b.severity.value,
                        "blocked_at": b.blocked_at.isoformat(),
                        "resolution_plan": b.resolution_plan,
                        "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
                        "resolving_node_id": b.resolving_node_id
                    }
                    for b in state.blockers
                ],
                "known_risks": state.known_risks,
                "open_questions": state.open_questions,
                "depends_on_workstreams": state.depends_on_workstreams,
                "waiting_for_dependencies": state.waiting_for_dependencies,
                "dependencies_satisfied_at": state.dependencies_satisfied_at.isoformat() if state.dependencies_satisfied_at else None,
                "needs_input_from": state.needs_input_from,
                "provides_input_to": state.provides_input_to,
                "pending_handoffs": state.pending_handoffs,
                "completed_handoffs": state.completed_handoffs,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "phase_started_at": state.phase_started_at.isoformat() if state.phase_started_at else None,
                "estimated_completion": state.estimated_completion.isoformat() if state.estimated_completion else None,
                "last_activity": state.last_activity.isoformat(),
                "lead_agent_type": state.lead_agent_type,
                "active_agents": state.active_agents,
                "metadata": state.metadata,
                "updated_at": state.updated_at.isoformat()
            }).execute()

        except Exception as e:
            logger.error(f"Error persisting workstream state: {e}")

    async def _load_state_from_record(self, record: Dict[str, Any]) -> WorkstreamState:
        """Load WorkstreamState from database record."""
        from datetime import datetime

        blockers = []
        for b in record.get("blockers", []):
            blockers.append(Blocker(
                id=b["id"],
                node_id=b["node_id"],
                description=b["description"],
                severity=BlockerSeverity(b["severity"]),
                blocked_at=datetime.fromisoformat(b["blocked_at"]),
                resolution_plan=b.get("resolution_plan"),
                resolved_at=datetime.fromisoformat(b["resolved_at"]) if b.get("resolved_at") else None,
                resolving_node_id=b.get("resolving_node_id")
            ))

        return WorkstreamState(
            workstream_id=record["workstream_id"],
            mission_id=record["mission_id"],
            phase=WorkstreamPhase(record["phase"]),
            health=WorkstreamHealth(record["health"]),
            status=record["status"],
            total_nodes=record["total_nodes"],
            completed_nodes=record["completed_nodes"],
            failed_nodes=record["failed_nodes"],
            skipped_nodes=record["skipped_nodes"],
            progress_percent=float(record["progress_percent"]),
            confidence_score=float(record.get("confidence_score", 0.5)),
            quality_score=float(record.get("quality_score", 0.5)),
            contradiction_count=record.get("contradiction_count", 0),
            blockers=blockers,
            known_risks=record.get("known_risks", []),
            open_questions=record.get("open_questions", []),
            depends_on_workstreams=record.get("depends_on_workstreams", []),
            waiting_for_dependencies=record.get("waiting_for_dependencies", False),
            dependencies_satisfied_at=datetime.fromisoformat(record["dependencies_satisfied_at"]) if record.get("dependencies_satisfied_at") else None,
            needs_input_from=record.get("needs_input_from", []),
            provides_input_to=record.get("provides_input_to", []),
            pending_handoffs=record.get("pending_handoffs", 0),
            completed_handoffs=record.get("completed_handoffs", 0),
            started_at=datetime.fromisoformat(record["started_at"]) if record.get("started_at") else None,
            phase_started_at=datetime.fromisoformat(record["phase_started_at"]) if record.get("phase_started_at") else None,
            estimated_completion=datetime.fromisoformat(record["estimated_completion"]) if record.get("estimated_completion") else None,
            last_activity=datetime.fromisoformat(record["last_activity"]),
            lead_agent_type=record.get("lead_agent_type", ""),
            active_agents=record.get("active_agents", []),
            metadata=record.get("metadata", {}),
            updated_at=datetime.fromisoformat(record["updated_at"])
        )

    # ========================================================================
    # Event Emission
    # ========================================================================

    async def _emit_progress_event(self, state: WorkstreamState, node_id: str):
        """Emit workstream progress event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type=MissionEventType.WORKSTREAM_PHASE_COMPLETE,
            payload={
                "workstream_id": state.workstream_id,
                "node_id": node_id,
                "progress_percent": state.progress_percent,
                "completed_nodes": state.completed_nodes,
                "total_nodes": state.total_nodes
            },
            source_workstream_id=state.workstream_id
        ))

    async def _emit_blocker_event(self, state: WorkstreamState, blocker: Blocker):
        """Emit blocker identified event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type=MissionEventType.BLOCKER_IDENTIFIED,
            payload={
                "workstream_id": state.workstream_id,
                "blocker_id": blocker.id,
                "node_id": blocker.node_id,
                "description": blocker.description,
                "severity": blocker.severity.value
            },
            source_node_id=blocker.node_id,
            source_workstream_id=state.workstream_id,
            priority="high" if blocker.severity in [BlockerSeverity.HIGH, BlockerSeverity.CRITICAL] else "normal"
        ))

    async def _emit_blocker_resolved_event(self, state: WorkstreamState, blocker: Blocker):
        """Emit blocker resolved event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type=MissionEventType.BLOCKER_RESOLVED,
            payload={
                "workstream_id": state.workstream_id,
                "blocker_id": blocker.id,
                "node_id": blocker.node_id,
                "resolving_node_id": blocker.resolving_node_id
            },
            source_node_id=blocker.resolving_node_id,
            source_workstream_id=state.workstream_id
        ))

    async def _emit_health_transition_event(self, state: WorkstreamState, transition: WorkstreamTransition):
        """Emit health transition event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type="workstream.health_changed",
            payload={
                "workstream_id": state.workstream_id,
                "from_health": transition.from_health.value if transition.from_health else None,
                "to_health": transition.to_health.value,
                "reason": transition.reason
            },
            source_workstream_id=state.workstream_id
        ))

    async def _emit_phase_transition_event(self, state: WorkstreamState, transition: WorkstreamTransition):
        """Emit phase transition event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type=MissionEventType.WORKSTREAM_PHASE_COMPLETE,
            payload={
                "workstream_id": state.workstream_id,
                "from_phase": transition.from_phase.value if transition.from_phase else None,
                "to_phase": transition.to_phase.value,
                "reason": transition.reason,
                "triggered_by": transition.triggered_by
            },
            source_workstream_id=state.workstream_id
        ))

    async def _emit_dependencies_satisfied_event(self, state: WorkstreamState):
        """Emit dependencies satisfied event."""
        if not self.context_bus:
            return

        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(state.mission_id)
        await bus.emit(MissionEvent(
            mission_id=state.mission_id,
            event_type=MissionEventType.WORKSTREAM_UNBLOCKED,
            payload={
                "workstream_id": state.workstream_id,
                "dependencies_satisfied_at": state.dependencies_satisfied_at.isoformat() if state.dependencies_satisfied_at else None
            },
            source_workstream_id=state.workstream_id
        ))


# ============================================================================
# Quick Start Functions
# ============================================================================

async def create_workstream_manager(supabase_client, mission_id: str) -> WorkstreamStateManager:
    """Quick helper: Create and initialize a workstream state manager."""
    from .context_bus import ContextBusManager
    bus = ContextBusManager.get_bus(mission_id, supabase_client)
    return WorkstreamStateManager(supabase_client, bus)


async def track_workstream_progress(
    workstream_id: str,
    mission_id: str,
    completed_node_id: str,
    node_status: str,
    supabase_client
) -> WorkstreamState:
    """Quick helper: Track progress for a workstream."""
    manager = await create_workstream_manager(supabase_client, mission_id)
    return await manager.update_progress(workstream_id, completed_node_id, node_status)


async def report_workstream_blocker(
    workstream_id: str,
    mission_id: str,
    node_id: str,
    description: str,
    severity: str = "medium",
    supabase_client=None
) -> Blocker:
    """Quick helper: Report a blocker for a workstream."""
    manager = await create_workstream_manager(supabase_client, mission_id)
    return await manager.add_blocker(
        workstream_id,
        node_id,
        description,
        BlockerSeverity(severity)
    )

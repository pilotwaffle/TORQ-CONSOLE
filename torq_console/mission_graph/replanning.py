"""
Execution Fabric - Replanning Engine

Handles dynamic graph mutation under controlled conditions.

Replanning is triggered when:
- Evidence quality drops below threshold
- Contradiction count spikes
- Critical node failures occur
- Human requests revision
- External conditions change
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
import copy


logger = logging.getLogger(__name__)


# ============================================================================
# Replanning Triggers
# ============================================================================

class ReplanTriggerType(str, Enum):
    """Types of events that trigger replanning."""
    EVIDENCE_DROP = "evidence_drop"
    CONTRADICTION_SPIKE = "contradiction_spike"
    NODE_FAILURE = "node_failure"
    HUMAN_REQUEST = "human_request"
    EXTERNAL_CHANGE = "external_change"
    BLOCKER_UNRESOLVED = "blocker_unresolved"
    CONFIDENCE_LOW = "confidence_low"
    TIMEOUT = "timeout"


class ReplanScope(str, Enum):
    """Scope of replanning operation."""
    MINOR = "minor"  # Adjust node parameters, add optional nodes
    MODERATE = "moderate"  # Add/remove nodes, restructure subgraph
    MAJOR = "major"  # Rebuild significant portions, new workstreams
    FULL = "full"  # Complete graph rebuild


class ReplanStatus(str, Enum):
    """Status of a replanning operation."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Replanning Models
# ============================================================================

@dataclass
class ReplanTrigger:
    """A condition that triggered replanning."""
    trigger_type: ReplanTriggerType
    description: str
    source_node_id: Optional[str] = None
    source_workstream_id: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    triggered_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReplanAction:
    """A proposed change to the mission graph."""
    action_type: str  # add_node, remove_node, modify_node, add_edge, remove_edge
    target_id: str
    description: str
    changes: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class ReplanProposal:
    """A proposal to modify the mission graph."""
    id: str = field(default_factory=lambda: str(uuid4()))
    mission_id: str = ""
    graph_id: str = ""

    # Trigger
    trigger: ReplanTrigger = None

    # Proposed changes
    scope: ReplanScope = ReplanScope.MINOR
    actions: List[ReplanAction] = field(default_factory=list)
    estimated_impact: str = ""  # Description of expected impact

    # Analysis
    reasoning: str = ""
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

    # Decision
    status: ReplanStatus = ReplanStatus.PROPOSED
    approved_by: Optional[str] = None  # agent_type or "human"
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Execution
    execution_started_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None
    new_graph_id: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplanConfig:
    """Configuration for replanning behavior."""
    # Thresholds
    evidence_confidence_threshold: float = 0.5
    contradiction_count_threshold: int = 5
    node_failure_threshold: int = 3  # Max failures before replan
    confidence_low_threshold: float = 0.3

    # Timeouts
    node_timeout_seconds: int = 3600  # 1 hour
    workstream_stalled_threshold_seconds: int = 7200  # 2 hours

    # Replanning limits
    max_replans_per_mission: int = 5
    replan_cooldown_seconds: int = 300  # 5 minutes

    # Approval requirements
    minor_requires_approval: bool = False
    moderate_requires_approval: bool = True
    major_requires_approval: bool = True
    full_requires_approval: bool = True


# ============================================================================
# Replanning Engine
# ============================================================================

class ReplanningEngine:
    """
    Handles dynamic mission graph mutation under controlled conditions.

    Responsibilities:
    - Monitor triggers that may require replanning
    - Generate replanning proposals
    - Execute approved replans
    - Track replanning history
    """

    def __init__(self, supabase_client, config: Optional[ReplanConfig] = None):
        self.supabase = supabase_client
        self.config = config or ReplanConfig()

        # Track replan count per mission
        self._replan_counts: Dict[str, int] = {}
        self._last_replan_time: Dict[str, datetime] = {}

    async def check_replan_needed(
        self,
        mission_id: str,
        graph_state: Dict[str, Any],
        workstream_states: List[Dict[str, Any]]
    ) -> Optional[ReplanTrigger]:
        """
        Check if conditions trigger replanning.

        Returns a ReplanTrigger if replanning is needed, None otherwise.
        """
        triggers = []

        # Check evidence quality
        evidence_trigger = await self._check_evidence_quality(graph_state)
        if evidence_trigger:
            triggers.append(evidence_trigger)

        # Check contradiction spike
        contradiction_trigger = await self._check_contradictions(graph_state)
        if contradiction_trigger:
            triggers.append(contradiction_trigger)

        # Check node failures
        failure_trigger = await self._check_node_failures(graph_state)
        if failure_trigger:
            triggers.append(failure_trigger)

        # Check confidence levels
        confidence_trigger = await self._check_confidence(graph_state)
        if confidence_trigger:
            triggers.append(confidence_trigger)

        # Check stalled workstreams
        stalled_trigger = await self._check_stalled_workstreams(workstream_states)
        if stalled_trigger:
            triggers.append(stalled_trigger)

        # Return highest priority trigger
        if triggers:
            return self._prioritize_triggers(triggers)

        return None

    async def create_proposal(
        self,
        mission_id: str,
        graph_id: str,
        trigger: ReplanTrigger,
        current_graph: Dict[str, Any]
    ) -> ReplanProposal:
        """
        Create a replanning proposal based on the trigger.

        Analyzes the situation and proposes specific graph changes.
        """
        # Determine scope
        scope = await self._determine_scope(trigger, current_graph)

        # Generate actions
        actions = await self._generate_actions(trigger, scope, current_graph)

        # Analyze impact
        reasoning, risks, benefits = await self._analyze_impact(
            trigger, scope, actions, current_graph
        )

        proposal = ReplanProposal(
            mission_id=mission_id,
            graph_id=graph_id,
            trigger=trigger,
            scope=scope,
            actions=actions,
            reasoning=reasoning,
            risks=risks,
            benefits=benefits
        )

        # Persist proposal
        await self._persist_proposal(proposal)

        logger.info(f"Created replanning proposal {proposal.id} for mission {mission_id}")

        return proposal

    async def approve_proposal(
        self,
        proposal_id: str,
        approved_by: str
    ) -> ReplanProposal:
        """Approve a replanning proposal."""
        proposal = await self._load_proposal(proposal_id)

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status != ReplanStatus.PROPOSED:
            raise ValueError(f"Proposal {proposal_id} is not in PROPOSED status")

        proposal.status = ReplanStatus.APPROVED
        proposal.approved_by = approved_by
        proposal.approved_at = datetime.now()

        await self._persist_proposal(proposal)

        logger.info(f"Approved replanning proposal {proposal_id}")

        return proposal

    async def reject_proposal(
        self,
        proposal_id: str,
        reason: str
    ) -> ReplanProposal:
        """Reject a replanning proposal."""
        proposal = await self._load_proposal(proposal_id)

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal.status = ReplanStatus.REJECTED
        proposal.rejection_reason = reason

        await self._persist_proposal(proposal)

        logger.info(f"Rejected replanning proposal {proposal_id}: {reason}")

        return proposal

    async def execute_proposal(
        self,
        proposal_id: str,
        current_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an approved replanning proposal.

        Returns the new graph state.
        """
        proposal = await self._load_proposal(proposal_id)

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status != ReplanStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id} is not approved")

        # Check replan limits
        if not await self._can_replan(proposal.mission_id):
            raise ValueError(f"Replanning limit reached for mission {proposal.mission_id}")

        proposal.status = ReplanStatus.IN_PROGRESS
        proposal.execution_started_at = datetime.now()
        await self._persist_proposal(proposal)

        try:
            # Apply changes to graph
            new_graph = await self._apply_changes(current_graph, proposal.actions)

            # Create new graph version
            new_graph_id = await self._create_graph_version(proposal.mission_id, new_graph)

            proposal.status = ReplanStatus.COMPLETED
            proposal.execution_completed_at = datetime.now()
            proposal.new_graph_id = new_graph_id

            await self._persist_proposal(proposal)

            # Update tracking
            self._replan_counts[proposal.mission_id] = self._replan_counts.get(proposal.mission_id, 0) + 1
            self._last_replan_time[proposal.mission_id] = datetime.now()

            # Emit event
            await self._emit_replan_complete_event(proposal)

            logger.info(f"Executed replanning proposal {proposal_id}, created graph {new_graph_id}")

            return new_graph

        except Exception as e:
            proposal.status = ReplanStatus.FAILED
            await self._persist_proposal(proposal)
            logger.error(f"Failed to execute replanning proposal {proposal_id}: {e}")
            raise

    async def get_proposal_history(
        self,
        mission_id: str,
        limit: int = 50
    ) -> List[ReplanProposal]:
        """Get replanning proposal history for a mission."""
        try:
            result = self.supabase.table("replan_proposals").select("*").eq(
                "mission_id", mission_id
            ).order("created_at", desc=True).limit(limit).execute()

            proposals = []
            for record in result.data:
                proposals.append(await self._load_proposal_from_record(record))

            return proposals

        except Exception as e:
            logger.error(f"Error loading proposal history: {e}")
            return []

    # ========================================================================
    # Trigger Checks
    # ========================================================================

    async def _check_evidence_quality(self, graph_state: Dict[str, Any]) -> Optional[ReplanTrigger]:
        """Check if evidence quality has dropped below threshold."""
        nodes = graph_state.get("nodes", [])

        for node in nodes:
            if node.get("node_type") == "evidence":
                confidence = node.get("confidence_score", 1.0)
                if confidence < self.config.evidence_confidence_threshold:
                    return ReplanTrigger(
                        trigger_type=ReplanTriggerType.EVIDENCE_DROP,
                        description=f"Evidence node {node['id']} has low confidence: {confidence}",
                        source_node_id=node.get("id"),
                        metric_name="confidence_score",
                        threshold_value=self.config.evidence_confidence_threshold,
                        actual_value=confidence
                    )

        return None

    async def _check_contradictions(self, graph_state: Dict[str, Any]) -> Optional[ReplanTrigger]:
        """Check if contradiction count has spiked."""
        total_contradictions = sum(
            node.get("contradiction_count", 0)
            for node in graph_state.get("nodes", [])
        )

        if total_contradictions >= self.config.contradiction_count_threshold:
            return ReplanTrigger(
                trigger_type=ReplanTriggerType.CONTRADICTION_SPIKE,
                description=f"High contradiction count: {total_contradictions}",
                metric_name="contradiction_count",
                threshold_value=float(self.config.contradiction_count_threshold),
                actual_value=float(total_contradictions)
            )

        return None

    async def _check_node_failures(self, graph_state: Dict[str, Any]) -> Optional[ReplanTrigger]:
        """Check if too many nodes have failed."""
        failed_count = sum(
            1 for node in graph_state.get("nodes", [])
            if node.get("status") == "failed"
        )

        if failed_count >= self.config.node_failure_threshold:
            return ReplanTrigger(
                trigger_type=ReplanTriggerType.NODE_FAILURE,
                description=f"High node failure count: {failed_count}",
                metric_name="failed_nodes",
                threshold_value=float(self.config.node_failure_threshold),
                actual_value=float(failed_count)
            )

        return None

    async def _check_confidence(self, graph_state: Dict[str, Any]) -> Optional[ReplanTrigger]:
        """Check if overall confidence is low."""
        nodes = graph_state.get("nodes", [])
        if not nodes:
            return None

        avg_confidence = sum(
            node.get("confidence_score", 0.5)
            for node in nodes
            if "confidence_score" in node
        ) / len(nodes)

        if avg_confidence < self.config.confidence_low_threshold:
            return ReplanTrigger(
                trigger_type=ReplanTriggerType.CONFIDENCE_LOW,
                description=f"Low average confidence: {avg_confidence:.2f}",
                metric_name="avg_confidence",
                threshold_value=self.config.confidence_low_threshold,
                actual_value=avg_confidence
            )

        return None

    async def _check_stalled_workstreams(
        self,
        workstream_states: List[Dict[str, Any]]
    ) -> Optional[ReplanTrigger]:
        """Check if any workstreams are stalled."""
        now = datetime.now()

        for ws in workstream_states:
            last_activity = ws.get("last_activity")
            if last_activity:
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity)

                stalled_seconds = (now - last_activity).total_seconds()

                if stalled_seconds > self.config.workstream_stalled_threshold_seconds:
                    return ReplanTrigger(
                        trigger_type=ReplanTriggerType.TIMEOUT,
                        description=f"Workstream {ws.get('workstream_id')} stalled for {stalled_seconds:.0f}s",
                        source_workstream_id=ws.get("workstream_id"),
                        metric_name="stalled_seconds",
                        threshold_value=float(self.config.workstream_stalled_threshold_seconds),
                        actual_value=stalled_seconds
                    )

        return None

    def _prioritize_triggers(self, triggers: List[ReplanTrigger]) -> ReplanTrigger:
        """Return highest priority trigger."""
        priority_order = [
            ReplanTriggerType.NODE_FAILURE,
            ReplanTriggerType.CONTRADICTION_SPIKE,
            ReplanTriggerType.BLOCKER_UNRESOLVED,
            ReplanTriggerType.EVIDENCE_DROP,
            ReplanTriggerType.CONFIDENCE_LOW,
            ReplanTriggerType.TIMEOUT,
            ReplanTriggerType.HUMAN_REQUEST,
            ReplanTriggerType.EXTERNAL_CHANGE,
        ]

        for trigger_type in priority_order:
            for trigger in triggers:
                if trigger.trigger_type == trigger_type:
                    return trigger

        return triggers[0]

    # ========================================================================
    # Proposal Generation
    # ========================================================================

    async def _determine_scope(
        self,
        trigger: ReplanTrigger,
        current_graph: Dict[str, Any]
    ) -> ReplanScope:
        """Determine scope of replanning needed."""
        # Critical triggers require major or full replan
        if trigger.trigger_type in [
            ReplanTriggerType.NODE_FAILURE,
            ReplanTriggerType.CONTRADICTION_SPIKE
        ]:
            return ReplanScope.MODERATE

        # Human request or external change could be any scope
        if trigger.trigger_type in [
            ReplanTriggerType.HUMAN_REQUEST,
            ReplanTriggerType.EXTERNAL_CHANGE
        ]:
            return ReplanScope.MINOR

        # Evidence drop or low confidence = moderate
        if trigger.trigger_type in [
            ReplanTriggerType.EVIDENCE_DROP,
            ReplanTriggerType.CONFIDENCE_LOW
        ]:
            return ReplanScope.MODERATE

        return ReplanScope.MINOR

    async def _generate_actions(
        self,
        trigger: ReplanTrigger,
        scope: ReplanScope,
        current_graph: Dict[str, Any]
    ) -> List[ReplanAction]:
        """Generate specific actions for the proposal."""
        actions = []

        if trigger.trigger_type == ReplanTriggerType.EVIDENCE_DROP:
            actions.append(ReplanAction(
                action_type="add_node",
                target_id="validation_node",
                description="Add evidence validation node",
                changes={
                    "node_type": "task",
                    "title": "Validate evidence quality",
                    "agent_type": "risk_qa"
                },
                reasoning="Ensure evidence meets quality threshold before proceeding"
            ))

        elif trigger.trigger_type == ReplanTriggerType.CONTRADICTION_SPIKE:
            actions.append(ReplanAction(
                action_type="add_node",
                target_id="contradiction_resolution",
                description="Add contradiction resolution node",
                changes={
                    "node_type": "task",
                    "title": "Resolve contradictions",
                    "agent_type": "synthesizer"
                },
                reasoning="Address contradictions before synthesis"
            ))

        elif trigger.trigger_type == ReplanTriggerType.NODE_FAILURE:
            actions.append(ReplanAction(
                action_type="add_node",
                target_id="retry_with_alt_approach",
                description="Add alternative approach node",
                changes={
                    "node_type": "task",
                    "title": "Retry with alternative strategy",
                    "reasoning_strategy": "hypothesis_driven"
                },
                reasoning="Try different approach after failure"
            ))

        elif trigger.trigger_type == ReplanTriggerType.CONFIDENCE_LOW:
            actions.append(ReplanAction(
                action_type="add_node",
                target_id="deep_dive_analysis",
                description="Add deep analysis node",
                changes={
                    "node_type": "task",
                    "title": "Deep dive on low-confidence areas",
                    "agent_type": "specialist"
                },
                reasoning="Investigate areas causing low confidence"
            ))

        return actions

    async def _analyze_impact(
        self,
        trigger: ReplanTrigger,
        scope: ReplanScope,
        actions: List[ReplanAction],
        current_graph: Dict[str, Any]
    ) -> tuple[str, List[str], List[str]]:
        """Analyze the impact of proposed changes."""
        reasoning = f"Replanning triggered by {trigger.trigger_type.value}: {trigger.description}"

        risks = []
        benefits = []

        # Common risks
        if scope in [ReplanScope.MAJOR, ReplanScope.FULL]:
            risks.append("Significant changes may invalidate previous work")
            risks.append("Extended timeline due to rework")

        if len(actions) > 5:
            risks.append("Complex changes may introduce new issues")

        # Common benefits
        benefits.append(f"Addresses trigger: {trigger.description}")
        benefits.append("Improves overall mission success probability")

        # Action-specific risks/benefits
        for action in actions:
            if action.action_type == "add_node":
                benefits.append(f"Adds {action.changes.get('title', 'new node')} to address issue")
                risks.append("Additional node increases execution time")

        return reasoning, risks, benefits

    # ========================================================================
    # Proposal Execution
    # ========================================================================

    async def _apply_changes(
        self,
        current_graph: Dict[str, Any],
        actions: List[ReplanAction]
    ) -> Dict[str, Any]:
        """Apply actions to create new graph version."""
        # Deep copy to avoid mutation
        new_graph = copy.deepcopy(current_graph)

        for action in actions:
            if action.action_type == "add_node":
                new_node = {
                    "id": f"node_{uuid4().hex[:8]}",
                    **action.changes,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }
                new_graph.setdefault("nodes", []).append(new_node)

            elif action.action_type == "remove_node":
                new_graph["nodes"] = [
                    n for n in new_graph.get("nodes", [])
                    if n["id"] != action.target_id
                ]

            elif action.action_type == "modify_node":
                for node in new_graph.get("nodes", []):
                    if node["id"] == action.target_id:
                        node.update(action.changes)

            elif action.action_type == "add_edge":
                new_edge = {
                    "id": f"edge_{uuid4().hex[:8]}",
                    **action.changes,
                    "created_at": datetime.now().isoformat()
                }
                new_graph.setdefault("edges", []).append(new_edge)

            elif action.action_type == "remove_edge":
                new_graph["edges"] = [
                    e for e in new_graph.get("edges", [])
                    if e["id"] != action.target_id
                ]

        # Update metadata
        new_graph["updated_at"] = datetime.now().isoformat()
        new_graph["replan_count"] = new_graph.get("replan_count", 0) + 1

        return new_graph

    async def _create_graph_version(
        self,
        mission_id: str,
        graph_data: Dict[str, Any]
    ) -> str:
        """Create a new graph version in the database."""
        from .models import MissionGraph

        # Create new graph record
        result = self.supabase.table("mission_graphs").insert({
            "mission_id": mission_id,
            "version": f"1.{graph_data.get('replan_count', 0)}",
            "status": "validated",
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
            "graph_metadata": graph_data.get("metadata", {})
        }).execute()

        if not result.data:
            raise ValueError("Failed to create graph version")

        graph_id = result.data[0]["id"]

        # Store nodes
        for node in graph_data.get("nodes", []):
            self.supabase.table("mission_nodes").insert({
                **node,
                "graph_id": graph_id,
                "mission_id": mission_id
            }).execute()

        # Store edges
        for edge in graph_data.get("edges", []):
            self.supabase.table("mission_edges").insert({
                **edge,
                "graph_id": graph_id,
                "mission_id": mission_id
            }).execute()

        return graph_id

    async def _can_replan(self, mission_id: str) -> bool:
        """Check if mission can undergo another replan."""
        # Check count limit
        count = self._replan_counts.get(mission_id, 0)
        if count >= self.config.max_replans_per_mission:
            return False

        # Check cooldown
        last_replan = self._last_replan_time.get(mission_id)
        if last_replan:
            elapsed = (datetime.now() - last_replan).total_seconds()
            if elapsed < self.config.replan_cooldown_seconds:
                return False

        return True

    # ========================================================================
    # Persistence
    # ========================================================================

    async def _persist_proposal(self, proposal: ReplanProposal):
        """Persist proposal to database."""
        try:
            self.supabase.table("replan_proposals").upsert({
                "id": proposal.id,
                "mission_id": proposal.mission_id,
                "graph_id": proposal.graph_id,
                "trigger_type": proposal.trigger.trigger_type.value if proposal.trigger else None,
                "trigger_description": proposal.trigger.description if proposal.trigger else "",
                "source_node_id": proposal.trigger.source_node_id if proposal.trigger else None,
                "scope": proposal.scope.value,
                "actions": [
                    {
                        "action_type": a.action_type,
                        "target_id": a.target_id,
                        "description": a.description,
                        "changes": a.changes,
                        "reasoning": a.reasoning
                    }
                    for a in proposal.actions
                ],
                "estimated_impact": proposal.estimated_impact,
                "reasoning": proposal.reasoning,
                "risks": proposal.risks,
                "benefits": proposal.benefits,
                "alternatives": proposal.alternatives,
                "status": proposal.status.value,
                "approved_by": proposal.approved_by,
                "approved_at": proposal.approved_at.isoformat() if proposal.approved_at else None,
                "rejection_reason": proposal.rejection_reason,
                "execution_started_at": proposal.execution_started_at.isoformat() if proposal.execution_started_at else None,
                "execution_completed_at": proposal.execution_completed_at.isoformat() if proposal.execution_completed_at else None,
                "new_graph_id": proposal.new_graph_id,
                "created_at": proposal.created_at.isoformat(),
                "metadata": proposal.metadata
            }).execute()

        except Exception as e:
            logger.error(f"Error persisting proposal: {e}")

    async def _load_proposal(self, proposal_id: str) -> Optional[ReplanProposal]:
        """Load proposal from database."""
        try:
            result = self.supabase.table("replan_proposals").select("*").eq(
                "id", proposal_id
            ).execute()

            if result.data:
                return await self._load_proposal_from_record(result.data[0])

        except Exception as e:
            logger.error(f"Error loading proposal: {e}")

        return None

    async def _load_proposal_from_record(self, record: Dict[str, Any]) -> ReplanProposal:
        """Load ReplanProposal from database record."""
        trigger = ReplanTrigger(
            trigger_type=ReplanTriggerType(record["trigger_type"]),
            description=record["trigger_description"],
            source_node_id=record.get("source_node_id")
        )

        actions = []
        for a in record.get("actions", []):
            actions.append(ReplanAction(
                action_type=a["action_type"],
                target_id=a["target_id"],
                description=a["description"],
                changes=a.get("changes", {}),
                reasoning=a.get("reasoning", "")
            ))

        return ReplanProposal(
            id=record["id"],
            mission_id=record["mission_id"],
            graph_id=record["graph_id"],
            trigger=trigger,
            scope=ReplanScope(record["scope"]),
            actions=actions,
            estimated_impact=record.get("estimated_impact", ""),
            reasoning=record.get("reasoning", ""),
            risks=record.get("risks", []),
            benefits=record.get("benefits", []),
            alternatives=record.get("alternatives", []),
            status=ReplanStatus(record["status"]),
            approved_by=record.get("approved_by"),
            approved_at=datetime.fromisoformat(record["approved_at"]) if record.get("approved_at") else None,
            rejection_reason=record.get("rejection_reason"),
            execution_started_at=datetime.fromisoformat(record["execution_started_at"]) if record.get("execution_started_at") else None,
            execution_completed_at=datetime.fromisoformat(record["execution_completed_at"]) if record.get("execution_completed_at") else None,
            new_graph_id=record.get("new_graph_id"),
            created_at=datetime.fromisoformat(record["created_at"]),
            metadata=record.get("metadata", {})
        )

    # ========================================================================
    # Events
    # ========================================================================

    async def _emit_replan_complete_event(self, proposal: ReplanProposal):
        """Emit replanning complete event."""
        from .context_bus import MissionEvent, MissionEventType, ContextBusManager

        bus = ContextBusManager.get_bus(proposal.mission_id, self.supabase)

        await bus.emit(MissionEvent(
            mission_id=proposal.mission_id,
            event_type=MissionEventType.MISSION_REPLANNING,
            payload={
                "proposal_id": proposal.id,
                "scope": proposal.scope.value,
                "trigger_type": proposal.trigger.trigger_type.value if proposal.trigger else None,
                "new_graph_id": proposal.new_graph_id,
                "actions_count": len(proposal.actions)
            },
            priority="high" if proposal.scope in [ReplanScope.MAJOR, ReplanScope.FULL] else "normal"
        ))


# ============================================================================
# Quick Start Functions
# ============================================================================

async def check_and_replan(
    mission_id: str,
    graph_state: Dict[str, Any],
    workstream_states: List[Dict[str, Any]],
    supabase_client
) -> Optional[str]:
    """
    Quick helper: Check if replanning is needed and create proposal.

    Returns proposal ID if replanning needed, None otherwise.
    """
    engine = ReplanningEngine(supabase_client)

    trigger = await engine.check_replan_needed(mission_id, graph_state, workstream_states)

    if trigger:
        proposal = await engine.create_proposal(
            mission_id,
            graph_state.get("id", ""),
            trigger,
            graph_state
        )
        return proposal.id

    return None

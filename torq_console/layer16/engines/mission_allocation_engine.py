"""TORQ Layer 16 - Mission Allocation Engine

This engine handles mission bidding and allocation to agents
based on capabilities, costs, and expected value.
"""

from typing import List

from ..models import (
    MissionBid,
    MissionRequirements,
    MissionAllocation,
    AgentCapabilities,
)


# =============================================================================
# MISSION ALLOCATION ENGINE
# =============================================================================


class MissionAllocationEngine:
    """Engine for allocating missions to bidding agents.

    Evaluates:
    - Bid cost vs mission value
    - Agent capability fit
    - Completion probability
    - Specialization matching
    - Expected value to network
    """

    def __init__(self):
        """Initialize the mission allocation engine."""
        self._pending_missions: dict[str, MissionRequirements] = {}
        self._active_bids: dict[str, List[MissionBid]] = {}

    async def submit_mission(self, mission: MissionRequirements) -> str:
        """Submit a mission for bidding.

        Args:
            mission: Mission requirements

        Returns:
            Mission ID
        """
        self._pending_missions[mission.mission_id] = mission
        self._active_bids[mission.mission_id] = []
        return mission.mission_id

    async def submit_bid(self, bid: MissionBid) -> bool:
        """Submit a bid for a mission.

        Args:
            bid: Mission bid

        Returns:
            True if bid accepted
        """
        mission_id = bid.mission_id

        if mission_id not in self._pending_missions:
            return False  # Mission not found

        self._active_bids[mission_id].append(bid)
        return True

    async def allocate_mission(
        self,
        mission_id: str,
        registered_agents: dict[str, AgentCapabilities],
    ) -> MissionAllocation | None:
        """Allocate a mission to the best agent.

        Args:
            mission_id: Mission to allocate
            registered_agents: Available agents

        Returns:
            MissionAllocation if allocated, None if no suitable bids
        """
        if mission_id not in self._pending_missions:
            return None

        mission = self._pending_missions[mission_id]
        bids = self._active_bids.get(mission_id, [])

        if not bids:
            return None

        # Filter qualified bids
        qualified_bids = []
        for bid in bids:
            agent = registered_agents.get(bid.agent_id)
            if not agent:
                continue

            if not self._is_bid_qualified(bid, mission, agent):
                continue

            qualified_bids.append(bid)

        if not qualified_bids:
            return None

        # Score each bid
        scored_bids = []
        for bid in qualified_bids:
            score = self._score_bid(bid, mission)
            scored_bids.append((score, bid))

        # Sort by score (highest first)
        scored_bids.sort(key=lambda x: x[0], reverse=True)

        # Select best bid
        best_score, best_bid = scored_bids[0]

        # Calculate allocation metrics
        agent = registered_agents[best_bid.agent_id]
        allocation_score = best_score
        resource_utilization = self._calculate_resource_utilization(best_bid, agent)

        return MissionAllocation(
            mission_id=mission_id,
            allocated_agent=best_bid.agent_id,
            allocation_cost=best_bid.bid_cost,
            expected_value=best_bid.expected_value,
            completion_probability=best_bid.completion_probability,
            total_bids=len(bids),
            qualified_bids=len(qualified_bids),
            allocation_score=allocation_score,
            resource_utilization=resource_utilization,
        )

    def _is_bid_qualified(
        self,
        bid: MissionBid,
        mission: MissionRequirements,
        agent: AgentCapabilities,
    ) -> bool:
        """Check if a bid meets minimum qualifications.

        Args:
            bid: Mission bid
            mission: Mission requirements
            agent: Agent capabilities

        Returns:
            True if qualified
        """
        # Check cost constraint
        if bid.bid_cost > mission.max_cost:
            return False

        # Check deadline
        if mission.deadline and bid.can_complete_by:
            if bid.can_complete_by > mission.deadline:
                return False

        # Check capability requirements
        if mission.requires_inference and not agent.can_inference:
            return False
        if mission.requires_planning and not agent.can_plan:
            return False
        if mission.requires_execution and not agent.can_execute:
            return False
        if mission.requires_monitoring and not agent.can_monitor:
            return False

        # Check specializations
        if mission.required_specializations:
            has_specialization = any(
                s in agent.specializations
                for s in mission.required_specializations
            )
            if not has_specialization:
                return False

        # Check resource availability
        if bid.cpu_usage > agent.cpu_capacity * (1 - agent.current_load):
            return False
        if bid.memory_usage > agent.memory_capacity * (1 - agent.current_load):
            return False

        return True

    def _score_bid(
        self,
        bid: MissionBid,
        mission: MissionRequirements,
    ) -> float:
        """Score a bid for allocation selection.

        Higher is better.

        Args:
            bid: Mission bid
            mission: Mission requirements

        Returns:
            Bid score (0.0 to 1.0)
        """
        score = 0.0

        # Value for money (0.3 weight)
        value_ratio = mission.expected_value / max(bid.bid_cost, 1)
        value_score = min(1.0, value_ratio / 5.0)  # 5x value is max
        score += value_score * 0.3

        # Completion probability (0.3 weight)
        score += bid.completion_probability * 0.3

        # Specialization match (0.2 weight)
        score += bid.specialization_match * 0.2

        # Capability coverage (0.1 weight)
        score += bid.capability_coverage * 0.1

        # Duration efficiency (0.1 weight) - shorter is better
        # Assume 1 hour is baseline
        duration_hours = bid.estimated_duration.total_seconds() / 3600
        duration_score = max(0.0, 1.0 - (duration_hours / 24.0))  # 24 hours = 0 score
        score += duration_score * 0.1

        return min(1.0, score)

    def _calculate_resource_utilization(
        self,
        bid: MissionBid,
        agent: AgentCapabilities,
    ) -> float:
        """Calculate expected resource utilization for this allocation.

        Args:
            bid: Mission bid
            agent: Agent capabilities

        Returns:
            Utilization score (0.0 to 1.0)
        """
        # Calculate utilization of each resource
        cpu_util = bid.cpu_usage / max(agent.cpu_capacity, 1)
        memory_util = bid.memory_usage / max(agent.memory_capacity, 1)

        # Average utilization
        return (cpu_util + memory_util) / 2.0

    async def close_mission(self, mission_id: str):
        """Close a mission and remove from pending.

        Args:
            mission_id: Mission to close
        """
        if mission_id in self._pending_missions:
            del self._pending_missions[mission_id]
        if mission_id in self._active_bids:
            del self._active_bids[mission_id]

    def get_pending_missions(self) -> List[str]:
        """Get list of pending mission IDs.

        Returns:
            List of mission IDs
        """
        return list(self._pending_missions.keys())

    def get_bids_for_mission(self, mission_id: str) -> List[MissionBid]:
        """Get all bids for a mission.

        Args:
            mission_id: Mission ID

        Returns:
            List of bids
        """
        return self._active_bids.get(mission_id, []).copy()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_mission_allocation_engine() -> MissionAllocationEngine:
    """Factory function to create a mission allocation engine.

    Returns:
        Configured MissionAllocationEngine instance
    """
    return MissionAllocationEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "MissionAllocationEngine",
    "create_mission_allocation_engine",
]

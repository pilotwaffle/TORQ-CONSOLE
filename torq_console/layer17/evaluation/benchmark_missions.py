"""TORQ Layer 17 - Benchmark Missions

This module defines the benchmark missions for agent genome evaluation.
Uses ONLY verified MissionRequirements field names from VERIFIED_L16_MODELS.md.

Verified MissionRequirements fields (from VERIFIED_L16_MODELS.md):
    mission_id, mission_type, required_cpu, required_memory, required_storage,
    required_network, requires_inference, requires_planning, requires_execution,
    requires_monitoring, required_specializations, max_cost, deadline, priority,
    expected_value

Verified priority values: Literal["low", "medium", "high", "critical"]
"""

from datetime import datetime, timedelta

from torq_console.layer16.models import MissionRequirements


# =============================================================================
# BENCHMARK MISSIONS
# =============================================================================


def get_benchmark_missions() -> list[MissionRequirements]:
    """Get the 5 minimum benchmark missions for genome evaluation.

    All missions use ONLY verified fields from VERIFIED_L16_MODELS.md:
    - mission_id: str
    - mission_type: str
    - required_cpu: float
    - required_memory: float
    - required_storage: float
    - required_network: float
    - requires_inference: bool
    - requires_planning: bool
    - requires_execution: bool
    - requires_monitoring: bool
    - required_specializations: list[str]
    - max_cost: float
    - deadline: datetime | None
    - priority: Literal["low", "medium", "high", "critical"]
    - expected_value: float

    Returns:
        List of MissionRequirements using verified field names
    """
    return [
        # Benchmark 1: Web Research Mission
        # Tests: Planning capability, network usage
        MissionRequirements(
            mission_id="benchmark_web_research",
            mission_type="research",
            required_cpu=10.0,
            required_memory=2.0,
            required_storage=1.0,
            required_network=100.0,
            requires_inference=False,
            requires_planning=True,
            requires_execution=False,
            requires_monitoring=False,
            required_specializations=[],
            max_cost=200.0,
            deadline=None,
            priority="medium",
            expected_value=500.0,
        ),

        # Benchmark 2: Code Execution Mission
        # Tests: Execution capability, CPU usage
        MissionRequirements(
            mission_id="benchmark_code_execute",
            mission_type="development",
            required_cpu=50.0,
            required_memory=4.0,
            required_storage=5.0,
            required_network=50.0,
            requires_inference=False,
            requires_planning=False,
            requires_execution=True,
            requires_monitoring=False,
            required_specializations=[],
            max_cost=300.0,
            deadline=None,
            priority="high",
            expected_value=800.0,
        ),

        # Benchmark 3: Data Analysis Mission
        # Tests: Inference capability, memory usage
        MissionRequirements(
            mission_id="benchmark_data_analysis",
            mission_type="analytics",
            required_cpu=30.0,
            required_memory=8.0,
            required_storage=10.0,
            required_network=50.0,
            requires_inference=True,
            requires_planning=False,
            requires_execution=False,
            requires_monitoring=False,
            required_specializations=[],
            max_cost=250.0,
            deadline=None,
            priority="medium",
            expected_value=600.0,
        ),

        # Benchmark 4: API Integration Mission
        # Tests: Execution + monitoring, network usage
        MissionRequirements(
            mission_id="benchmark_api_integration",
            mission_type="integration",
            required_cpu=20.0,
            required_memory=2.0,
            required_storage=1.0,
            required_network=200.0,
            requires_inference=False,
            requires_planning=False,
            requires_execution=True,
            requires_monitoring=True,
            required_specializations=[],
            max_cost=400.0,
            deadline=None,
            priority="high",
            expected_value=1000.0,
        ),

        # Benchmark 5: Documentation Mission
        # Tests: Low resource baseline
        MissionRequirements(
            mission_id="benchmark_documentation",
            mission_type="documentation",
            required_cpu=15.0,
            required_memory=2.0,
            required_storage=2.0,
            required_network=50.0,
            requires_inference=False,
            requires_planning=False,
            requires_execution=False,
            requires_monitoring=False,
            required_specializations=[],
            max_cost=150.0,
            deadline=None,
            priority="low",
            expected_value=300.0,
        ),
    ]


# =============================================================================
# VERIFIED CONSTRUCTORS
# =============================================================================

def create_specialist_mission(
    mission_id: str,
    specialization: str,
) -> MissionRequirements:
    """Create a mission requiring a specific specialization.

    Uses verified required_specializations field.

    Args:
        mission_id: Unique mission identifier
        specialization: Required specialization (e.g., "trading", "analysis")

    Returns:
        MissionRequirements with specialization requirement
    """
    return MissionRequirements(
        mission_id=mission_id,
        mission_type="specialized_task",
        required_cpu=20.0,
        required_memory=4.0,
        required_storage=5.0,
        required_network=100.0,
        requires_inference=False,
        requires_planning=True,
        requires_execution=True,
        requires_monitoring=False,
        required_specializations=[specialization],
        max_cost=500.0,
        deadline=None,
        priority="high",
        expected_value=1000.0,
    )


def create_deadline_mission(
    mission_id: str,
    hours_from_now: float,
) -> MissionRequirements:
    """Create a mission with a deadline.

    Uses verified deadline field (datetime | None).

    Args:
        mission_id: Unique mission identifier
        hours_from_now: Deadline offset in hours

    Returns:
        MissionRequirements with deadline constraint
    """
    deadline = datetime.utcnow() + timedelta(hours=hours_from_now)

    return MissionRequirements(
        mission_id=mission_id,
        mission_type="time_critical",
        required_cpu=30.0,
        required_memory=6.0,
        required_storage=8.0,
        required_network=100.0,
        requires_inference=False,
        requires_planning=True,
        requires_execution=True,
        requires_monitoring=False,
        required_specializations=[],
        max_cost=600.0,
        deadline=deadline,
        priority="critical",
        expected_value=1500.0,
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "get_benchmark_missions",
    "create_specialist_mission",
    "create_deadline_mission",
]

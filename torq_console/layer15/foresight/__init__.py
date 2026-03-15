"""TORQ Layer 15 - Foresight Engines Package

This module contains all strategic foresight engines for Layer 15.
"""

from .scenario_projection_engine import (
    ScenarioProjectionEngine,
    create_scenario_projection_engine,
)

from .strategic_branch_comparator import (
    StrategicBranchComparator,
    create_strategic_branch_comparator,
)

from .second_order_consequence_analyzer import (
    SecondOrderConsequenceAnalyzer,
    create_second_order_consequence_analyzer,
)

from .optionality_preservation_engine import (
    OptionalityPreservationEngine,
    create_optionality_preservation_engine,
)

from .horizon_alignment_engine import (
    HorizonAlignmentEngine,
    create_horizon_alignment_engine,
)


__all__ = [
    "ScenarioProjectionEngine",
    "create_scenario_projection_engine",
    "StrategicBranchComparator",
    "create_strategic_branch_comparator",
    "SecondOrderConsequenceAnalyzer",
    "create_second_order_consequence_analyzer",
    "OptionalityPreservationEngine",
    "create_optionality_preservation_engine",
    "HorizonAlignmentEngine",
    "create_horizon_alignment_engine",
]

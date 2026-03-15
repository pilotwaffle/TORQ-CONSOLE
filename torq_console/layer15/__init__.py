"""TORQ Layer 15 - Strategic Foresight

Layer 15 provides TORQ with strategic foresight - the ability to evaluate
future paths, second-order consequences, and long-term mission alignment
before execution.

## Architecture

Layer 15 acts as the strategic evaluation layer between legitimacy
and execution recommendation:

1. **Scenario Projection** - Generate plausible future scenarios
2. **Branch Comparison** - Compare strategic paths by expected value
3. **Second-Order Analysis** - Evaluate downstream effects
4. **Optionality Preservation** - Assess reversibility and lock-in risk
5. **Horizon Alignment** - Score short/medium/long-term alignment

## Execution Flow

    Layer 14 Constitutional Legitimacy
            ↓
    Layer 15 Strategic Foresight (EVALUATION, NOT OVERRIDE)
            ↓
    Execution Recommendation

Layer 15 does NOT override Layer 14 legitimacy.
It evaluates the time-sequenced strategic quality of already-legitimate options.

## Key Principle

> Every action has second-order effects. TORQ should understand them
> before executing, not after experiencing them.

## Version

**Version:** 0.15.0-planning
**Status:** STRATEGIC FORESIGHT SCAFFOLD
**Depends On:** Layer 14 (Constitutional Governance) - Complete
"""

from .models import (
    ScenarioProjection,
    BranchComparison,
    ConsequenceAnalysis,
    OptionalityAssessment,
    HorizonAlignmentResult,
    StrategicForesightResult,
    DecisionPacket,
)

from .foresight import (
    ScenarioProjectionEngine,
    StrategicBranchComparator,
    SecondOrderConsequenceAnalyzer,
    OptionalityPreservationEngine,
    HorizonAlignmentEngine,
)

from .services import (
    StrategicForesightService,
)


__all__ = [
    # Models
    "ScenarioProjection",
    "BranchComparison",
    "ConsequenceAnalysis",
    "OptionalityAssessment",
    "HorizonAlignmentResult",
    "StrategicForesightResult",
    "DecisionPacket",
    # Foresight Engines
    "ScenarioProjectionEngine",
    "StrategicBranchComparator",
    "SecondOrderConsequenceAnalyzer",
    "OptionalityPreservationEngine",
    "HorizonAlignmentEngine",
    # Services
    "StrategicForesightService",
]


__version__ = "0.15.0-planning"

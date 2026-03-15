# Layer 13 Economic Intelligence - Agent 1 Task Brief

## Mission

Design and implement the core architecture for TORQ's economic intelligence layer, enabling the system to make resource-aware decisions about what actions deserve investment.

## Context

**Layer 12 Status:** CLOSED (v0.12-final)
**Layer 13 Status:** NEW - Architecture & Scaffold Phase

TORQ now has distributed reasoning and federated validation (Layer 12). Layer 13 adds economic intelligence to decide:
- What actions deserve resources
- How to allocate constrained budget
- How to value opportunity costs
- How to prioritize competing missions

## Your Responsibilities

### Core Architecture Design

Design how Layer 13 integrates with existing TORQ execution flow without breaking Layer 12.

**Key Questions:**
- How does economic scoring plug into mission execution?
- How do recommendations become resource-ranked actions?
- How do costs, value, urgency, and confidence combine?
- How does Layer 13 consume outputs from Layers 8-12?

**Deliverable:** `docs/layer13/LAYER13_ARCHITECTURE.md`

### Engine Scaffolds

Create file scaffolds with stubbed implementations and typed models:

1. **`economic_evaluation_engine.py`**
   - Evaluate proposals for economic viability
   - Input: mission proposals, resource requirements, expected outcomes
   - Output: economic scores, ROI projections

2. **`resource_allocation_engine.py`**
   - Allocate constrained resources across competing priorities
   - Input: budget constraints, prioritized actions
   - Output: resource assignments, budget remainder

3. **`opportunity_cost_model.py`**
   - Calculate cost of foregone alternatives
   - Input: chosen action, rejected alternatives
   - Output: opportunity cost scores

4. **`budget_aware_prioritization.py`**
   - Rank actions by economic value within budget constraints
   - Input: candidate actions, budget limits
   - Output: prioritized action list

5. **Models file** (`models.py` or similar)
   - `EconomicEvaluationInput` - mission proposals, resource costs
   - `ResourceConstraints` - budget, time, compute limits
   - `ActionScore` - combined economic score
   - `AllocationResult` - resource assignments
   - `OpportunityCostResult` - cost of alternatives

**Deliverable:** All scaffold files with type hints, docstrings, and stub methods

### Integration Contracts

Define how Layer 13 connects to Layers 8-12:

**Input Contracts:**
- From Layer 8 (Mission Control): Mission definitions and requirements
- From Layer 9 (Capability Registry): Resource requirements and availability
- From Layer 11 (Claim Processing): Validated federation results

**Output Contracts:**
- To Layer 8: Prioritized mission queue with resource assignments
- To Layer 14 (when built): Economic metrics for dashboard

## Technical Approach

1. **Preserve Layer 12:** Your changes must not break existing federation functionality
2. **Type Safety:** Use Pydantic models for all economic inputs/outputs
3. **Simulation-First:** Design for both simulation and production modes
4. **Extensibility:** Allow new scoring criteria without major refactoring

## Best First Milestone

**Deliverable:** Complete Layer 13 architecture + file scaffold

**Definition of Done:**
- Architecture document approved by stakeholder
- All 4 engine files created with type hints and docstrings
- Models file with all core data structures
- Integration points documented
- No breaking changes to Layer 12

## Constraints

- DO NOT modify Layer 12 code unless fixing a regression
- DO NOT start full implementation until architecture is approved
- Coordinate with Agent 2 on shared model definitions

## Success Criteria

- Architecture enables economic decision-making without breaking federation
- Models can represent real-world economic constraints
- Scaffolds are ready for Agent 2's validation scenarios
- Integration points are clearly defined

## Commands

Create architecture document:
```
mkdir -p docs/layer13
# Create LAYER13_ARCHITECTURE.md
```

Create engine scaffolds:
```
mkdir -p torq_console/layer13/economic
# Create engine files with stub implementations
```

## Timeline

- Week 1: Architecture design + models
- Week 2: Engine scaffolds + integration contracts
- Week 3: Review & approval checkpoint

---

**Start after Layer 12 closure is confirmed. Do not begin without architecture approval.**

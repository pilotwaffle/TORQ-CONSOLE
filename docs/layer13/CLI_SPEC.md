# Layer 13 CLI Specification
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** CLI SPEC DEFINED
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document specifies the CLI interface for Layer 13 Economic Intelligence. The CLI provides commands for running economic prioritization, validation tests, and analysis.

---

## Core Commands

### Command: `torq-layer13 prioritize`

Run economic prioritization on a set of mission proposals.

#### Usage

```bash
python -m torq_console.layer13.economic.run_prioritization \
    --budget BUDGET \
    --missions MISSIONS_FILE \
    --constraints CONSTRAINTS_FILE \
    [--output OUTPUT_FILE] \
    [--format FORMAT] \
    [--verbose]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--budget` | float | Yes | Total budget available for allocation |
| `--missions` | path | Yes | JSON file containing mission proposals |
| `--constraints` | path | No | JSON file containing resource constraints |
| `--output` | path | No | Output file for allocation results |
| `--format` | string | No | Output format: `json` (default) or `table` |
| `--verbose` | flag | No | Enable verbose output |

#### Input Format

**missions.json:**
```json
{
    "missions": [
        {
            "mission_id": "data_pipeline_001",
            "mission_type": "data_ingestion",
            "description": "Ingest customer data",
            "user_value": 0.8,
            "urgency": 0.5,
            "strategic_fit": 0.7,
            "estimated_cost": 300.0,
            "estimated_duration_seconds": 3600,
            "requires_validation": true
        }
    ]
}
```

**constraints.json:**
```json
{
    "total_budget": 1000.0,
    "budget_remaining": 1000.0,
    "require_federation_validation": true,
    "min_confidence_threshold": 0.5,
    "required_mission_types": ["security"],
    "forbidden_mission_types": []
}
```

#### Output Format

```json
{
    "funded_mission_ids": ["m1", "m2", "m3"],
    "funded_total_cost": 850.0,
    "funded_total_value": 1.95,
    "queued_mission_ids": ["m4"],
    "queued_total_cost": 200.0,
    "rejected_mission_ids": ["m5"],
    "rejected_reasons": {
        "m5": "Confidence below threshold"
    },
    "budget_utilization": 0.85,
    "remaining_budget": 150.0,
    "allocation_efficiency": 2.29,
    "regret_score": 0.3,
    "opportunity_costs": {
        "m4": {
            "rejected_mission_id": "m4",
            "rejected_mission_value": 0.65,
            "best_accepted_alternative_id": "m2",
            "best_accepted_alternative_value": 0.7,
            "opportunity_cost": 0.05,
            "opportunity_cost_ratio": 0.2,
            "strategic_impact": "low"
        }
    }
}
```

#### Example

```bash
python -m torq_console.layer13.economic.run_prioritization \
    --budget 1000 \
    --missions data/missions.json \
    --constraints data/constraints.json \
    --output data/allocation.json \
    --verbose
```

#### Output

```
Layer 13 Economic Prioritization
================================

Budget: 1000.00
Missions: 5
Constraints: data/constraints.json

Running Layers 1-3: Evaluation...
  ✓ m1: base_value=0.67, quality_adjusted_value=0.75
  ✓ m2: base_value=0.55, quality_adjusted_value=0.60
  ✗ m3: REJECTED - Confidence below threshold (0.35 < 0.50)
  ✓ m4: base_value=0.72, quality_adjusted_value=0.78
  ✓ m5: base_value=0.48, quality_adjusted_value=0.48

Running Layer 4: Prioritization...
  Ranking by efficiency:
    1. m5: efficiency=0.0048
    2. m1: efficiency=0.0025
    3. m4: efficiency=0.00195
    4. m2: efficiency=0.0012

Running Layer 5: Allocation...
  Funded: m5, m1, m4 (cost: 650.00)
  Queued: m2 (cost: 500.00, doesn't fit)
  Rejected: m3

Results:
  Budget Utilization: 65.00%
  Remaining Budget: 350.00
  Allocation Efficiency: 2.85 value/dollar
  Regret Score: 0.12

Output written to: data/allocation.json
```

---

### Command: `torq-layer13 validate`

Run the validation test suite.

#### Usage

```bash
python -m torq_console.layer13.economic.run_validation \
    [--scenarios SCENARIOS] \
    [--verbose] \
    [--coverage] \
    [--report REPORT_FILE]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--scenarios` | list | No | Comma-separated scenario names (default: all) |
| `--verbose` | flag | No | Enable verbose output |
| `--coverage` | flag | No | Generate coverage report |
| `--report` | path | No | Output report file |

#### Available Scenarios

| Scenario | Description |
|----------|-------------|
| `budget_constrained` | Fixed budget across competing missions |
| `value_urgency_tradeoff` | High-value vs high-urgency decisions |
| `opportunity_cost` | Mutually exclusive alternatives |
| `low_confidence_rejection` | Risky expensive proposal filtering |
| `resource_starvation` | Minimal resource stress test |
| `strategic_constraints` | Required mission type prioritization |
| `federation_confidence` | Federation confidence impact |

#### Example

```bash
# Run all scenarios
python -m torq_console.layer13.economic.run_validation

# Run specific scenarios
python -m torq_console.layer13.economic.run_validation \
    --scenarios budget_constrained,opportunity_cost

# Run with coverage
python -m torq_console.layer13.economic.run_validation \
    --coverage --report validation_report.html
```

#### Output

```
Layer 13 Validation Suite
=========================

Running 7 scenarios...

Scenario 1: Constrained Budget Allocation
  ✓ S1-1: Budget exhaustion
  ✓ S1-2: Efficiency ordering
  ✓ S1-3: No double allocation
  PASSED (3/3)

Scenario 2: Value vs Urgency Tradeoffs
  ✓ S2-1: Urgency as component
  ✓ S2-2: Deadline enforcement
  ✓ S2-3: Both funded when budget allows
  PASSED (3/3)

Scenario 3: Opportunity Cost Comparisons
  ✓ S3-1: Opportunity cost calculation
  ✓ S3-2: Best alternative identification
  ✓ S3-3: Cost ratio calculation
  ✓ S3-4: Strategic impact assessment
  PASSED (4/4)

...

Summary:
  Total Tests: 24
  Passed: 24
  Failed: 0
  Success Rate: 100%

Coverage:
  Statements: 87.5%
  Branches: 82.3%
  Functions: 91.7%

Validation complete!
```

---

### Command: `torq-layer13 analyze`

Compare allocation strategies and analyze economic decisions.

#### Usage

```bash
python -m torq_console.layer13.economic.run_analysis \
    --missions MISSIONS_FILE \
    --baseline BASELINE_STRATEGY \
    --test_strategy TEST_STRATEGY \
    [--output OUTPUT_FILE]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--missions` | path | Yes | JSON file containing mission proposals |
| `--baseline` | string | Yes | Baseline strategy: `equal_allocation`, `value_only`, `cost_only` |
| `--test_strategy` | string | No | Test strategy: `layer13_economic` (default) |
| `--output` | path | No | Output comparison file |

#### Baseline Strategies

| Strategy | Description |
|----------|-------------|
| `equal_allocation` | Fund missions equally until budget exhausted |
| `value_only` | Fund by base value, ignoring cost |
| `cost_only` | Fund by lowest cost first |
| `layer13_economic` | Full five-layer economic evaluation |

#### Example

```bash
python -m torq_console.layer13.economic.run_analysis \
    --missions data/missions.json \
    --baseline value_only \
    --test_strategy layer13_economic \
    --output data/comparison.json
```

#### Output

```
Strategy Comparison
===================

Missions: 10
Budget: 1000.00

Baseline: value_only
  Funded: 2 missions
  Total Cost: 900.00
  Total Value: 1.5
  Efficiency: 1.67 value/dollar

Test: layer13_economic
  Funded: 4 missions
  Total Cost: 950.00
  Total Value: 2.1
  Efficiency: 2.21 value/dollar

Improvement:
  Value: +40.0%
  Efficiency: +32.3%
  Budget Utilization: +5.0%

Recommendation: Use layer13_economic strategy

Output written to: data/comparison.json
```

---

### Command: `torq-layer13 score`

Score a single mission proposal without running full allocation.

#### Usage

```bash
python -m torq_console.layer13.economic.run_score \
    --mission MISSION_JSON \
    [--federation FEDERATION_JSON] \
    [--constraints CONSTRAINTS_JSON]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--mission` | json | Yes | Mission proposal as JSON string or file |
| `--federation` | json | No | Federation result as JSON string or file |
| `--constraints` | json | No | Resource constraints as JSON string or file |

#### Example

```bash
python -m torq_console.layer13.economic.run_score \
    --mission '{
        "mission_id": "test_001",
        "mission_type": "test",
        "user_value": 0.8,
        "urgency": 0.5,
        "strategic_fit": 0.7,
        "estimated_cost": 200.0
    }'
```

#### Output

```
Mission Score Analysis
======================

Mission: test_001
Type: test
Cost: 200.00

Layer 1: Feasibility Gate
  ✓ Budget check (200.00 <= 1000.00)
  ✓ No deadline constraint
  ✓ No federation requirement
  Status: ELIGIBLE

Layer 2: Base Value
  User Value (60%): 0.8 * 0.6 = 0.48
  Urgency (30%): 0.5 * 0.3 = 0.15
  Strategic Fit (10%): 0.7 * 0.1 = 0.07
  Base Value: 0.67

Layer 3: Execution Quality
  Confidence: N/A (no federation)
  Historical: N/A (no history)
  Execution Modifier: 1.00
  Quality Adjusted Value: 0.67

Layer 4: Efficiency
  Efficiency: 0.67 / 200.00 = 0.00335

Summary:
  Eligible: Yes
  Base Value: 0.67
  Quality Adjusted: 0.67
  Efficiency: 0.00335
```

---

### Command: `torq-layer13 batch`

Score multiple mission proposals from a file.

#### Usage

```bash
python -m torq_console.layer13.economic.run_batch \
    --input INPUT_FILE \
    --output OUTPUT_FILE \
    [--format FORMAT]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--input` | path | Yes | Input file with mission proposals |
| `--output` | path | Yes | Output file for scores |
| `--format` | string | No | Format: `json` (default) or `csv` |

#### Example

```bash
python -m torq_console.layer13.economic.run_batch \
    --input data/proposals.json \
    --output data/scores.json \
    --format json
```

---

### Command: `torq-layer13 config`

Manage Layer 13 configuration.

#### Usage

```bash
python -m torq_console.layer13.economic.run_config \
    [show | set | validate] \
    [KEY] \
    [VALUE]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| `show` | Display current configuration |
| `set KEY VALUE` | Set configuration value |
| `validate` | Validate configuration file |

#### Example

```bash
# Show configuration
python -m torq_console.layer13.economic.run_config show

# Set confidence weight
python -m torq_console.layer13.economic.run_config set confidence_weight 0.6

# Validate configuration
python -m torq_console.layer13.economic.run_config validate
```

---

## Configuration File

Layer 13 can be configured via a YAML configuration file.

**Location:** `config/layer13.yaml`

```yaml
# Layer 13 Economic Intelligence Configuration

# Layer 2: Base Value Weights
base_value_weights:
  user_value: 0.6
  urgency: 0.3
  strategic_fit: 0.1

# Layer 3: Confidence Weights
confidence:
  weight: 0.5
  threshold: 0.5

# Layer 4: Efficiency
efficiency:
  cost_epsilon: 0.01

# Layer 5: Strategic Bonus
strategic:
  bonus_cap: 0.5
  required_types: []

# General settings
logging:
  level: INFO
  log_all_scores: false

performance:
  enable_parallel: false
  max_workers: 4
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TORQ_LAYER13_CONFIG` | Path to configuration file | `config/layer13.yaml` |
| `TORQ_LAYER13_LOG_LEVEL` | Logging level | `INFO` |
| `TORQ_LAYER13_OUTPUT_DIR` | Default output directory | `./output` |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid input |
| 3 | Configuration error |
| 4 | Validation failure |
| 5 | Budget exceeded |

---

## Integration with TORQ CLI

Layer 13 commands can be invoked from the main TORQ CLI:

```bash
# Using TORQ CLI
torq layer13 prioritize --budget 1000 --missions data/missions.json
torq layer13 validate --scenarios budget_constrained
torq layer13 analyze --missions data/missions.json --baseline value_only
```

---

## Python API

All CLI commands are also accessible via Python API:

```python
from torq_console.layer13.economic import (
    create_evaluation_engine,
    create_prioritization_engine,
    create_allocation_engine,
    create_opportunity_cost_model,
)
from torq_console.layer13.economic.models import (
    MissionProposal,
    ResourceConstraints,
)

# Create engines
evaluation_engine = create_evaluation_engine()
prioritization_engine = create_prioritization_engine()
allocation_engine = create_allocation_engine()
opportunity_model = create_opportunity_cost_model()

# Run allocation
proposal = MissionProposal(...)
constraints = ResourceConstraints(total_budget=1000.0)

score = await evaluation_engine.evaluate_proposal(proposal, constraints)
ranked = await prioritization_engine.rank_by_efficiency([score], constraints, {...})
allocation = await allocation_engine.allocate_budget(ranked, constraints, {...})
costs = await opportunity_model.calculate_opportunity_costs(...)
```

---

## Help Command

```bash
python -m torq_console.layer13.economic --help
```

Output:
```
Layer 13 Economic Intelligence CLI

Commands:
  prioritize    Run economic prioritization
  validate       Run validation tests
  analyze        Compare allocation strategies
  score          Score a single mission
  batch          Score multiple missions
  config         Manage configuration

Global Options:
  --help         Show this help message
  --version      Show version information
  --verbose      Enable verbose output

For command-specific help:
  python -m torq_console.layer13.economic COMMAND --help
```

---

**Document Status:** COMPLETE
**Agent 2 Status:** ALL DELIVERABLES COMPLETE

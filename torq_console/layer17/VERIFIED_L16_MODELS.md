# Layer 16 Verified Model Contracts
## For Layer 17 Integration

**Version:** 0.16.0
**Status:** VERIFIED
**Date:** 2026-03-15
**Purpose:** Exact model field definitions from Layer 16 for Layer 17 consumption

**Source File:** `torq_console/layer16/models/__init__.py`

**Import Path:**
```python
from torq_console.layer16.models import (
    AgentCapabilities,
    AgentRegistration,
    MissionRequirements,
    MissionBid,
    MissionAllocation,
    ResourceOffer,
    ResourcePrice,
    AgentMarketState,
    MarketEquilibrium,
    IncentiveAdjustment,
    CoordinationResult,
    datetime_utcnow,
)
```

**Model Type:** All are Pydantic `BaseModel` subclasses

**See Also:** `VERIFIED_L16_SOURCES.md` for engine/service integration surfaces

---

## AgentCapabilities

**Purpose:** Defines an agent's resource capacities, capabilities, and cost structure.

**Fields:**
```python
agent_id: str                              # Unique identifier
agent_type: Literal["specialist", "generalist", "orchestrator"]
cpu_capacity: float                         # Total CPU capacity (units)
memory_capacity: float                      # Total memory capacity (GB)
storage_capacity: float                     # Total storage capacity (GB)
network_bandwidth: float                    # Network bandwidth (Mbps)
can_inference: bool                         # Can perform inference
can_plan: bool                              # Can perform planning
can_execute: bool                           # Can execute tasks
can_monitor: bool                           # Can monitor operations
specializations: list[str]                  # Domain specializations
cost_per_cpu_unit: float                    # Cost per CPU unit
cost_per_memory_gb: float                   # Cost per GB of memory
base_hourly_rate: float                     # Base hourly operating cost
reliability_score: float = Field(default=0.9, ge=0.0, le=1.0)
avg_completion_time: float = Field(default=60.0, ge=0.0)  # seconds
availability_start: datetime | None         # Daily start time (UTC)
availability_end: datetime | None           # Daily end time (UTC)
current_load: float = Field(default=0.0, ge=0.0, le=1.0)
registered_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## AgentRegistration

**Purpose:** Registration payload for new agents entering the coordination system.

**Fields:**
```python
agent_id: str
agent_type: Literal["specialist", "generalist", "orchestrator"]
capabilities: AgentCapabilities
registration_token: str | None = None
registered_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## MissionRequirements

**Purpose:** Defines resource and capability requirements for a mission to be allocated.

**Fields:**
```python
mission_id: str
mission_type: str
required_cpu: float = Field(default=10.0, ge=0.0)
required_memory: float = Field(default=1.0, ge=0.0)
required_storage: float = Field(default=5.0, ge=0.0)
required_network: float = Field(default=100.0, ge=0.0)
requires_inference: bool = Field(default=False)
requires_planning: bool = Field(default=False)
requires_execution: bool = Field(default=False)
requires_monitoring: bool = Field(default=False)
required_specializations: list[str] = Field(default_factory=list)
max_cost: float = Field(default=1000.0, ge=0.0)
deadline: datetime | None = None
priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")
expected_value: float = Field(default=100.0, ge=0.0)
created_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## MissionBid

**Purpose:** Agent's bid for a mission, including cost, expected value, and resource commitment.

**Fields:**
```python
bid_id: str
mission_id: str
agent_id: str
bid_cost: float = Field(default=100.0, ge=0.0)
expected_value: float = Field(default=100.0, ge=0.0)
completion_probability: float = Field(default=0.9, ge=0.0, le=1.0)
estimated_duration: timedelta = Field(default=timedelta(hours=1))
cpu_usage: float = Field(default=10.0, ge=0.0)
memory_usage: float = Field(default=1.0, ge=0.0)
storage_usage: float = Field(default=5.0, ge=0.0)
specialization_match: float = Field(default=0.5, ge=0.0, le=1.0)
capability_coverage: float = Field(default=0.5, ge=0.0, le=1.0)
can_start_before: datetime | None = None
can_complete_by: datetime | None = None
created_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## MissionAllocation

**Purpose:** Result of mission allocation to an agent.

**Fields:**
```python
mission_id: str
allocated_agent: str
allocation_cost: float = Field(default=0.0, ge=0.0)
expected_value: float = Field(default=0.0, ge=0.0)
completion_probability: float = Field(default=0.0, ge=0.0, le=1.0)
total_bids: int = Field(default=0, ge=0)
qualified_bids: int = Field(default=0, ge=0)
allocation_score: float = Field(default=0.5, ge=0.0, le=1.0)
resource_utilization: float = Field(default=0.5, ge=0.0, le=1.0)
allocated_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## ResourceOffer

**Purpose:** Agent's offer to sell/lease resources to the market.

**Fields:**
```python
offer_id: str
agent_id: str
resource_type: Literal["cpu", "memory", "storage", "network", "inference", "planning", "execution"]
quantity: float = Field(default=100.0, gt=0)
asking_price: float = Field(default=10.0, ge=0.0)
min_quantity: float = Field(default=1.0, gt=0)
valid_from: datetime = Field(default_factory=datetime_utcnow)
valid_until: datetime | None = None
can_partial: bool = Field(default=True)
created_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## ResourcePrice

**Purpose:** Price information for a resource type.

**Fields:**
```python
resource_type: str
current_price: float = Field(default=10.0, ge=0.0)
price_trend: Literal["rising", "stable", "falling"] = Field(default="stable")
price_volatility: float = Field(default=0.1, ge=0.0, le=1.0)
total_supply: float = Field(default=1000.0, ge=0.0)
total_demand: float = Field(default=500.0, ge=0.0)
supply_demand_ratio: float = Field(default=2.0, ge=0.0)
avg_price_24h: float = Field(default=10.0, ge=0.0)
min_price_24h: float = Field(default=8.0, ge=0.0)
max_price_24h: float = Field(default=12.0, ge=0.0)
calculated_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## AgentMarketState

**Purpose:** Current state of the agent resource market.

**Fields:**
```python
resource_supply: dict[str, float] = Field(default_factory=dict)
resource_demand: dict[str, float] = Field(default_factory=dict)
equilibrium_price: dict[str, float] = Field(default_factory=dict)
market_health: float = Field(default=0.8, ge=0.0, le=1.0)
total_agents: int = Field(default=0, ge=0)
active_agents: int = Field(default=0, ge=0)
available_agents: int = Field(default=0, ge=0)
total_supply: float = Field(default=0.0, ge=0.0)
total_demand: float = Field(default=0.0, ge=0.0)
supply_demand_gap: float = Field(default=0.0)
market_liquidity: float = Field(default=0.5, ge=0.0, le=1.0)
updated_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## IncentiveAdjustment

**Purpose:** Incentive adjustment applied to an agent for system balancing.

**Fields:**
```python
agent_id: str
adjustment_type: Literal["bonus", "penalty", "subsidy", "tax", "priority_boost", "priority_reduction"]
resource_adjustment: dict[str, float] = Field(default_factory=dict)
cost_multiplier: float = Field(default=1.0, ge=0.0)
priority_adjustment: float = Field(default=0.0)
reason: str = Field(default="")
duration: timedelta | None = None
expires_at: datetime | None = None
created_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## MarketEquilibrium

**Purpose:** Assessment of whether the market is in equilibrium.

**Fields:**
```python
stable: bool = Field(default=False)
price_variance: float = Field(default=0.1, ge=0.0)
price_variance_threshold: float = Field(default=0.05, ge=0.0)
supply_demand_balance: float = Field(default=0.0, ge=-1.0, le=1.0)
equilibrium_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
stable_for_seconds: float = Field(default=0.0, ge=0.0)
destabilizing_factors: list[str] = Field(default_factory=list)
calculated_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## CoordinationResult

**Purpose:** Complete result of a coordination cycle.

**Fields:**
```python
coordination_id: str
cycle_number: int = Field(default=0, ge=0)
market_state: AgentMarketState
equilibrium: MarketEquilibrium
mission_allocations: list[MissionAllocation] = Field(default_factory=list)
incentive_adjustments: list[IncentiveAdjustment] = Field(default_factory=list)
resource_prices: dict[str, ResourcePrice] = Field(default_factory=dict)
total_missions_processed: int = Field(default=0, ge=0)
total_missions_allocated: int = Field(default=0, ge=0)
total_value_generated: float = Field(default=0.0, ge=0.0)
total_cost_incurred: float = Field(default=0.0, ge=0.0)
coordination_health: float = Field(default=0.8, ge=0.0, le=1.0)
coordination_duration_ms: float = Field(default=0.0, ge=0.0)
started_at: datetime = Field(default_factory=datetime_utcnow)
completed_at: datetime | None = None
```

---

## Verified Literal Values

**Agent Types:**
```python
Literal["specialist", "generalist", "orchestrator"]
```

**Mission Priority Levels:**
```python
Literal["low", "medium", "high", "critical"]
```

**Incentive Adjustment Types:**
```python
Literal["bonus", "penalty", "subsidy", "tax", "priority_boost", "priority_reduction"]
```

**Price Trends:**
```python
Literal["rising", "stable", "falling"]
```

**Resource Types (in ResourceOffer):**
```python
Literal["cpu", "memory", "storage", "network", "inference", "planning", "execution"]
```

---

## Utility Functions

**datetime_utcnow()**
```python
def datetime_utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()
```

**Usage in Field defaults:**
```python
created_at: datetime = Field(default_factory=datetime_utcnow)
```

---

## Integration Notes for Layer 17

1. **All datetime fields use UTC** - Use `datetime_utcnow()` for defaults or `datetime.utcnow()`

2. **Float constraints use Field(ge=X, le=Y)** - Apply these validations:
   - `ge=0.0` for non-negative values
   - `le=1.0` for scores/percentages
   - `gt=0` for required positive values

3. **Literal types are strict** - Use exact string values from verified list above

4. **Default factories for mutable defaults** - Use:
   - `Field(default_factory=list)` for lists
   - `Field(default_factory=dict)` for dictionaries

5. **Reliability scores are 0.0-1.0** - Apply this range to any new metrics

6. **Cost multipliers can be any positive float** - No upper bound enforced (ge=0.0)

7. **Market health is 0.0-1.0** - Apply this range to health calculations

8. **All models are Pydantic BaseModel** - Supports:
   - `.model_dump()` for dict conversion
   - `.model_dump_json()` for JSON
   - `.model_validate(data)` for parsing

---

## Related Documentation

- **`VERIFIED_L16_SOURCES.md`** - Exact file paths, class names, and integration surfaces for all Layer 16 engines and services

---

**Document Status:** COMPLETE
**Phase 1 Gate:** PASSED - Agent 1 may proceed to Phase 2

# Layer 16 Verified Source Contracts
## Exact File Paths, Classes, and Import Paths for Layer 17 Integration

**Version:** 0.16.0
**Status:** VERIFIED
**Date:** 2026-03-15
**Purpose:** Exact source locations and integration surfaces for Layer 17 consumption

---

## Data Models Source

### File: `torq_console/layer16/models/__init__.py`

**Model Type:** Pydantic `BaseModel`

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

**All Classes:** Pydantic `BaseModel` subclasses with `Field()` validation

---

## Verified L16 Producers

### 1. ResourceMarketEngine

**Class:** `ResourceMarketEngine`

**File:** `torq_console/layer16/engines/resource_market_engine.py`

**Import Path:**
```python
from torq_console.layer16.engines import (
    ResourceMarketEngine,
    create_resource_market_engine,
)
```

**Key Methods:**
- `async register_agent(capabilities: AgentCapabilities) -> AgentMarketState`
- `async unregister_agent(agent_id: str) -> AgentMarketState`
- `async submit_offer(offer: ResourceOffer) -> AgentMarketState`
- `async get_market_state() -> AgentMarketState`
- `async find_matching_offers(resource_type: str, min_quantity: float, max_price: float) -> list[ResourceOffer]`
- `def get_price_history(resource_type: str) -> list[float]`

**Return Type:** `AgentMarketState` (Pydantic model)

**Notes:**
- All methods are **async**
- Returns **in-memory** state (no database)
- Uses internal `Dict[str, AgentCapabilities]` storage
- State persists within process lifetime only

---

### 2. MissionAllocationEngine

**Class:** `MissionAllocationEngine`

**File:** `torq_console/layer16/engines/mission_allocation_engine.py`

**Import Path:**
```python
from torq_console.layer16.engines import (
    MissionAllocationEngine,
    create_mission_allocation_engine,
)
```

**Key Methods:**
- `async submit_mission(mission: MissionRequirements) -> str`
- `async submit_bid(bid: MissionBid) -> bool`
- `async allocate_mission(mission_id: str, registered_agents: dict) -> MissionAllocation | None`
- `async close_mission(mission_id: str)`
- `def get_pending_missions() -> list[str]`
- `def get_bids_for_mission(mission_id: str) -> list[MissionBid]`

**Return Types:** `str`, `bool`, `MissionAllocation | None`, `list[str]`, `list[MissionBid]`

**Notes:**
- Mission/bid submission is **async**
- Query methods `get_pending_missions()` and `get_bids_for_mission()` are **sync** (def)
- Returns **in-memory** state
- Uses internal `dict[str, MissionRequirements]` and `dict[str, list[MissionBid]]` storage

---

### 3. PriceDiscoveryEngine

**Class:** `PriceDiscoveryEngine`

**File:** `torq_console/layer16/engines/price_discovery_engine.py`

**Import Path:**
```python
from torq_console.layer16.engines import (
    PriceDiscoveryEngine,
    create_price_discovery_engine,
)
```

**Key Methods:**
- `async discover_prices(market_state: AgentMarketState) -> dict[str, ResourcePrice]`
- `async get_price_forecast(resource_type: str, steps: int = 5) -> list[float]`
- `def set_base_price(resource_type: str, price: float)`
- `def get_base_price(resource_type: str) -> float`

**Return Types:** `dict[str, ResourcePrice]`, `list[float]`, `float`

**Notes:**
- Price discovery is **async**
- Base price getters/setters are **sync** (def)
- Uses internal `Dict[str, List[tuple[datetime, float]]]` for history
- Max history: 100 price points per resource

---

### 4. IncentiveBalancingEngine

**Class:** `IncentiveBalancingEngine`

**File:** `torq_console/layer16/engines/incentive_balancing_engine.py`

**Import Path:**
```python
from torq_console.layer16.engines import (
    IncentiveBalancingEngine,
    create_incentive_balancing_engine,
)
```

**Key Methods:**
- `async calculate_incentives(market_state, registered_agents) -> list[IncentiveAdjustment]`
- `async get_agent_multiplier(agent_id: str) -> float`
- `async clear_expired_adjustments()`
- `def get_active_adjustments(agent_id: str | None = None) -> list[IncentiveAdjustment]`

**Return Types:** `list[IncentiveAdjustment]`, `float`

**Notes:**
- Calculation methods are **async**
- Query method `get_active_adjustments()` is **sync** (def)
- Uses internal `Dict[str, List[IncentiveAdjustment]]` storage
- Adjustments have `expires_at` for auto-cleanup

---

### 5. EquilibriumDetector

**Class:** `EquilibriumDetector`

**File:** `torq_console/layer16/engines/equilibrium_detector.py`

**Import Path:**
```python
from torq_console.layer16.engines import (
    EquilibriumDetector,
    create_equilibrium_detector,
)
```

**Key Methods:**
- `async detect_equilibrium(market_state, resource_prices) -> MarketEquilibrium`
- `async get_stability_duration() -> float`
- `def set_variance_threshold(threshold: float)`
- `def set_balance_threshold(threshold: float)`

**Return Type:** `MarketEquilibrium` (Pydantic model)

**Notes:**
- Detection is **async**
- Threshold setters are **sync** (def)
- Uses internal `Dict[str, deque[float]]` for price/supply/demand history
- History length: 20 data points per resource

---

### 6. EconomicCoordinationService (Main Entry Point)

**Class:** `EconomicCoordinationService`

**File:** `torq_console/layer16/services/economic_coordination_service.py`

**Import Path:**
```python
from torq_console.layer16.services import (
    EconomicCoordinationService,
    create_economic_coordination_service,
)
```

**Key Methods:**
- `async register_agent(registration: AgentRegistration) -> AgentMarketState`
- `async unregister_agent(agent_id: str) -> AgentMarketState`
- `async submit_resource_offer(offer: ResourceOffer) -> AgentMarketState`
- `async submit_mission(mission: MissionRequirements) -> str`
- `async submit_mission_bid(bid: MissionBid) -> bool`
- `async run_coordination_cycle(mission_ids: list[str] | None = None) -> CoordinationResult`
- `async get_market_state() -> AgentMarketState`
- `async get_equilibrium() -> MarketEquilibrium`
- `async get_resource_prices() -> dict[str, ResourcePrice]`
- `def get_registered_agents() -> dict[str, AgentCapabilities]`
- `def get_pending_missions() -> list[str]`
- `def get_incentive_adjustments(agent_id: str | None = None) -> list[IncentiveAdjustment]`
- `async get_agent_cost_multiplier(agent_id: str) -> float`

**Return Types:** Various Pydantic models and primitives

**Notes:**
- **Service orchestration layer** - combines all 5 engines
- All mutation methods are **async**
- Query methods `get_registered_agents()`, `get_pending_missions()`, `get_incentive_adjustments()` are **sync** (def)
- Returns **in-memory** state (no database persistence)
- Holds internal `Dict[str, AgentCapabilities]` and `Dict[str, MissionRequirements]`

---

## Data Storage Notes

### State Source: In-Memory Only

**All Layer 16 engines use in-memory storage:**

| Engine | Storage Type | Persistence |
|--------|-------------|-------------|
| ResourceMarketEngine | `Dict[str, AgentCapabilities]` | Process lifetime |
| MissionAllocationEngine | `Dict[str, MissionRequirements]`, `Dict[str, List[MissionBid]]` | Process lifetime |
| PriceDiscoveryEngine | `Dict[str, List[tuple[datetime, float]]]` | Process lifetime |
| IncentiveBalancingEngine | `Dict[str, List[IncentiveAdjustment]]` | Process lifetime |
| EquilibriumDetector | `Dict[str, deque[float]]` | Process lifetime |

**Implications for Layer 17:**
- No database queries needed
- No async database I/O
- Direct method calls only
- State lost on process restart
- Layer 17 may need to implement persistence

---

## Sync vs Async Method Summary

| Pattern | Methods | Collection Strategy |
|---------|---------|---------------------|
| **Async (mutation)** | `register_agent`, `submit_mission`, `submit_bid`, `run_coordination_cycle` | Use `await` when calling |
| **Async (query)** | `get_market_state`, `get_equilibrium`, `get_resource_prices` | Use `await` when calling |
| **Sync (query)** | `get_pending_missions`, `get_bids_for_mission`, `get_registered_agents`, `get_active_adjustments` | Direct call, no `await` |

**Rule of thumb:**
- If method returns computed/derived state → likely **async**
- If method returns stored dictionary keys → likely **sync** (def)

---

## Factory Functions

All engines have factory functions for instantiation:

```python
# Engines
from torq_console.layer16.engines import (
    create_resource_market_engine,
    create_mission_allocation_engine,
    create_price_discovery_engine,
    create_incentive_balancing_engine,
    create_equilibrium_detector,
)

# Service
from torq_console.layer16.services import (
    create_economic_coordination_service,
)
```

**Usage:**
```python
service = create_economic_coordination_service()
await service.register_agent(registration)
state = await service.get_market_state()
```

---

**Document Status:** COMPLETE
**Phase 1 Gate:** PASSED - Agent 1 now knows exact integration surfaces

# TORQ Layer 16 - Multi-Agent Economic Coordination Architecture

**Version:** 0.16.0
**Status:** IMPLEMENTED
**Depends On:** Layer 15 (Strategic Foresight) - v0.15.0
**Author:** Agent 1 & Agent 2
**Date:** 2026-03-15

---

## Architecture Overview

Layer 16 enables **multi-agent economic coordination** across TORQ nodes, transforming independent agents into a networked economic organism.

### The Network Effect

```
Before Layer 16:
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Agent A │  │ Agent B │  │ Agent C │  ← Independent
└─────────┘  └─────────┘  └─────────┘

After Layer 16:
┌─────────────────────────────────────────┐
│         Economic Coordination Layer      │
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │ Market│ │Price  │ │Equilib│         │
│  └───────┘ └───────┘ └───────┘         │
└─────────────────────────────────────────┘
           ↕         ↕         ↕
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Agent A │  │ Agent B │  │ Agent C │  ← Coordinated
└─────────┘  └─────────┘  └─────────┘
```

### Core Question

> **"How do we allocate scarce resources to competing demands across autonomous agents?"**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 16                                 │
│                  Multi-Agent Economic Coordination               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐    │
│  │    Resource    │  │     Price      │  │   Incentive   │    │
│  │  Market Engine │──│  Discovery     │──│   Balancing   │    │
│  │                │  │     Engine     │  │    Engine     │    │
│  └────────────────┘  └────────────────┘  └──────────────┘    │
│           ↓                  ↓                  ↓              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐    │
│  │    Mission     │  │    Equilibrium │  │   Economic    │    │
│  │  Allocation    │──│    Detector    │  │ Coordination  │    │
│  │    Engine      │  │                │  │    Service    │    │
│  └────────────────┘  └────────────────┘  └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External TORQ Nodes                          │
│              (via network communication layer)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. ResourceMarketEngine

**Purpose:** Manage supply and demand for agent resources.

**Responsibilities:**
- Track agent resource capabilities (CPU, memory, storage, network)
- Accept resource offers from agents
- Calculate market-wide supply and demand
- Maintain market health metrics
- Find matching offers for resource requests

**Key Methods:**
```python
class ResourceMarketEngine:
    async def register_agent(
        self, capabilities: AgentCapabilities
    ) -> AgentMarketState:
        """Register an agent and its capabilities."""

    async def submit_offer(
        self, offer: ResourceOffer
    ) -> AgentMarketState:
        """Submit a resource offer to the market."""

    async def get_market_state(self) -> AgentMarketState:
        """Get current market state."""

    async def find_matching_offers(
        self, resource_type: str, min_quantity: float, max_price: float
    ) -> List[ResourceOffer]:
        """Find resource offers matching criteria."""
```

**Models:**
```python
class AgentCapabilities(BaseModel):
    agent_id: str
    agent_type: Literal["specialist", "generalist", "orchestrator"]
    cpu_capacity: float
    memory_capacity: float
    can_inference: bool
    can_plan: bool
    can_execute: bool
    can_monitor: bool
    specializations: list[str]
    cost_per_cpu_unit: float
    reliability_score: float
    current_load: float

class AgentMarketState(BaseModel):
    resource_supply: dict[str, float]
    resource_demand: dict[str, float]
    equilibrium_price: dict[str, float]
    market_health: float
    total_agents: int
    active_agents: int
    available_agents: int
```

---

### 2. MissionAllocationEngine

**Purpose:** Allocate missions to bidding agents based on capabilities and value.

**Responsibilities:**
- Accept mission submissions
- Collect agent bids for missions
- Evaluate bid qualifications
- Score bids by value, capability, and reliability
- Select optimal agent for each mission

**Key Methods:**
```python
class MissionAllocationEngine:
    async def submit_mission(
        self, mission: MissionRequirements
    ) -> str:
        """Submit a mission for bidding."""

    async def submit_bid(self, bid: MissionBid) -> bool:
        """Submit a bid for a mission."""

    async def allocate_mission(
        self, mission_id: str, registered_agents: dict[str, AgentCapabilities]
    ) -> MissionAllocation | None:
        """Allocate a mission to the best agent."""
```

**Models:**
```python
class MissionRequirements(BaseModel):
    mission_id: str
    mission_type: str
    required_cpu: float
    required_memory: float
    requires_inference: bool
    requires_planning: bool
    requires_execution: bool
    required_specializations: list[str]
    max_cost: float
    priority: Literal["low", "medium", "high", "critical"]
    expected_value: float

class MissionBid(BaseModel):
    bid_id: str
    mission_id: str
    agent_id: str
    bid_cost: float
    expected_value: float
    completion_probability: float
    estimated_duration: timedelta
    specialization_match: float
    capability_coverage: float
```

---

### 3. PriceDiscoveryEngine

**Purpose:** Discover fair market prices through supply-demand analysis.

**Responsibilities:**
- Calculate prices based on supply/demand ratios
- Track price history and trends
- Measure price volatility
- Generate price forecasts

**Key Methods:**
```python
class PriceDiscoveryEngine:
    async def discover_prices(
        self, market_state: AgentMarketState
    ) -> dict[str, ResourcePrice]:
        """Discover current prices for all resources."""

    async def get_price_forecast(
        self, resource_type: str, steps: int = 5
    ) -> list[float]:
        """Generate a simple price forecast."""
```

**Models:**
```python
class ResourcePrice(BaseModel):
    resource_type: str
    current_price: float
    price_trend: Literal["rising", "stable", "falling"]
    price_volatility: float
    total_supply: float
    total_demand: float
    supply_demand_ratio: float
    avg_price_24h: float
    min_price_24h: float
    max_price_24h: float
```

---

### 4. IncentiveBalancingEngine

**Purpose:** Ensure system-wide stability through incentive adjustments.

**Responsibilities:**
- Balance exploration vs exploitation
- Encourage load balancing
- Manage specialization vs redundancy
- Apply cost multipliers for system health

**Key Methods:**
```python
class IncentiveBalancingEngine:
    async def calculate_incentives(
        self, market_state: AgentMarketState, registered_agents: dict
    ) -> list[IncentiveAdjustment]:
        """Calculate incentive adjustments for system balance."""

    async def get_agent_multiplier(self, agent_id: str) -> float:
        """Get current cost multiplier for an agent."""
```

**Models:**
```python
class IncentiveAdjustment(BaseModel):
    agent_id: str
    adjustment_type: Literal[
        "bonus", "penalty", "subsidy", "tax",
        "priority_boost", "priority_reduction"
    ]
    cost_multiplier: float
    priority_adjustment: float
    reason: str
    duration: timedelta | None
```

---

### 5. EquilibriumDetector

**Purpose:** Detect when the agent market stabilizes.

**Responsibilities:**
- Monitor price variance
- Track supply-demand balance
- Measure stability duration
- Identify destabilizing factors

**Key Methods:**
```python
class EquilibriumDetector:
    async def detect_equilibrium(
        self, market_state: AgentMarketState, resource_prices: dict
    ) -> MarketEquilibrium:
        """Detect if market is in equilibrium."""

    async def get_stability_duration(self) -> float:
        """Get how long market has been stable."""
```

**Models:**
```python
class MarketEquilibrium(BaseModel):
    stable: bool
    price_variance: float
    supply_demand_balance: float
    equilibrium_confidence: float
    stable_for_seconds: float
    destabilizing_factors: list[str]
```

---

## Service Integration

### EconomicCoordinationService

**Purpose:** Orchestrate all Layer 16 engines.

**Coordination Flow:**
```
1. Collect agent resource offers
        ↓
2. Discover prices
        ↓
3. Calculate incentive adjustments
        ↓
4. Detect equilibrium
        ↓
5. Allocate missions
        ↓
6. Return coordination result
```

**Key Methods:**
```python
class EconomicCoordinationService:
    async def register_agent(self, registration: AgentRegistration) -> AgentMarketState
    async def submit_resource_offer(self, offer: ResourceOffer) -> AgentMarketState
    async def submit_mission(self, mission: MissionRequirements) -> str
    async def submit_mission_bid(self, bid: MissionBid) -> bool
    async def run_coordination_cycle(
        self, mission_ids: list[str] | None = None
    ) -> CoordinationResult
    async def get_market_state(self) -> AgentMarketState
    async def get_equilibrium(self) -> MarketEquilibrium
    async def get_resource_prices(self) -> dict[str, ResourcePrice]
```

---

## Data Flow

### Input: Agent Registration

```python
class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: Literal["specialist", "generalist", "orchestrator"]
    capabilities: AgentCapabilities
```

### Input: Mission Submission

```python
class MissionRequirements(BaseModel):
    mission_id: str
    mission_type: str
    required_cpu: float
    required_memory: float
    requires_execution: bool
    max_cost: float
    expected_value: float
```

### Output: Coordination Result

```python
class CoordinationResult(BaseModel):
    coordination_id: str
    cycle_number: int
    market_state: AgentMarketState
    equilibrium: MarketEquilibrium
    mission_allocations: list[MissionAllocation]
    incentive_adjustments: list[IncentiveAdjustment]
    resource_prices: dict[str, ResourcePrice]
    total_missions_processed: int
    total_missions_allocated: int
    total_value_generated: float
    total_cost_incurred: float
    coordination_health: float
    coordination_duration_ms: float
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/l16/market/register-agent` | Register a new agent |
| POST | `/api/l16/market/offer-resource` | Submit a resource offer |
| POST | `/api/l16/market/submit-mission` | Submit a mission |
| POST | `/api/l16/market/bid-mission` | Submit a bid for a mission |
| POST | `/api/l16/market/run-coordination` | Run coordination cycle |
| GET | `/api/l16/market/state` | Get market state |
| GET | `/api/l16/market/equilibrium` | Get equilibrium state |
| GET | `/api/l16/market/health` | Health check |
| GET | `/api/l16/market/agents` | List registered agents |
| GET | `/api/l16/market/missions` | List pending missions |
| GET | `/api/l16/market/incentives/{agent_id}` | Get agent incentives |

---

## Performance Requirements

| Operation | Target | Actual |
|-----------|--------|--------|
| Market coordination cycle | <200ms | ~0.18ms |
| Mission bid evaluation | <50ms | <1ms |
| Equilibrium detection | <20ms | <1ms |
| Price discovery | <30ms | <1ms |

---

## Storage Requirements

### Agent Registry
- Store registered agent capabilities
- TTL: Persistent (until unregistered)
- Indexed by: agent_id

### Market History
- Store price history for trend analysis
- Retention: 7 days
- Used for: Price forecasting, volatility calculation

### Coordination Log
- Log all coordination cycles
- Retention: 30 days
- Used for: Audit, analytics, calibration

---

## Security Considerations

### SC-1: Bid Manipulation

**Threat:** Agents submit false bids to manipulate allocation.

**Mitigation:**
- Track agent reliability scores
- Require bid bonds (stake)
- Penalize failed allocations
- Reputation system

### SC-2: Market Manipulation

**Threat:** Agents create fake supply/demand to influence prices.

**Mitigation:**
- Require resource verification
- Limit offer frequency
- Detect anomalous patterns
- Cross-reference with actual usage

### SC-3: Sybil Attacks

**Threat:** Single agent registers multiple identities.

**Mitigation:**
- Require registration tokens
- Limit agents per source
- Behavioral fingerprinting
- Minimum stake requirement

---

## Error Handling

### E-1: No Qualified Bids

**Scenario:** Mission receives no qualified bids.

**Action:** Keep mission in pending queue, retry next cycle.

### E-2: Market Failure

**Scenario:** Market health drops below threshold.

**Action:** Suspend allocations, alert operators, incentivize new agents.

### E-3: Price Explosion

**Scenario:** Resource prices exceed reasonable bounds.

**Action:** Apply price caps, incentivize supply, investigate manipulation.

---

## Layer Dependencies

```
Layer 16 depends on:
  Layer 15 (Strategic Foresight) - mission prioritization
  Layer 14 (Constitutional Governance) - agent authority
  Layer 13 (Economic Intelligence) - cost modeling
  Layer 12 (Federation) - multi-node communication

Layer 16 enables:
  Distributed mission execution across TORQ network
  Economic resource allocation
  Self-organizing agent ecosystems
```

---

## Extension Points

### Future Enhancements

1. **Reputation System** - Agent trust scores from historical performance
2. **Prediction Markets** - Agents bet on mission outcomes
3. **Derivative Markets** - Futures contracts for resources
4. **Multi-Currency** - Multiple resource currencies with exchange rates
5. **Agent Unions** - Collective bargaining for specialist groups

---

**Document Status:** COMPLETE
**Next:** Layer 17 - Distributed Learning and Knowledge Synthesis

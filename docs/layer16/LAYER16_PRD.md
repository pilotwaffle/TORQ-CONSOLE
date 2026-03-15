# Layer 16 PRD
## Multi-Agent Economic Coordination Layer

**Version:** 0.16.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-15

---

## Overview

Layer 16 enables multiple TORQ agents, nodes, or clusters to coordinate resources, priorities, budgets, incentives, and mission allocation through market-based economic coordination.

**Core Transformation:**
- **Without Layer 16:** Agents act independently
- **With Layer 16:** Agents participate in economic coordination markets

---

## Architectural Position

```
Layer 16 — Multi-Agent Economic Coordination
    ↑
Layer 15 — Strategic Foresight
    ↑
Layer 14 — Constitutional Governance
    ↑
Layer 13 — Economic Intelligence
    ↑
Layer 12 — Collective Intelligence Exchange
```

Layer 16 operates **across nodes**, not just inside a single TORQ instance.

---

## Core Purpose

Allow multiple TORQ agents to coordinate:

1. **Resources** — Compute, memory, tool access, planning cycles
2. **Priorities** — Mission ranking and allocation
3. **Budgets** — Resource budgeting across agents
4. **Incentives** — Reward alignment and motivation
5. **Mission Allocation** — Distributing work to optimal agents

---

## Key Questions Layer 16 Answers

| Question | Description |
|----------|-------------|
| Which agent should execute this mission? | Agent selection based on comparative advantage |
| How should resources be priced? | Dynamic price discovery |
| How do we balance incentives across agents? | Incentive equilibrium |
| Is the market functioning efficiently? | Efficiency metrics and monitoring |

---

## Core Capabilities

### 1. Agent Resource Markets

Agents can buy, sell, and trade resources:

- **Compute** — CPU/GPU cycles
- **Planning Cycles** — L5-L7 reasoning capacity
- **Memory** — Working memory and context
- **Tool Access** — API calls, database access, external services
- **Mission Execution** — Completed mission outcomes

### 2. Mission Bidding and Allocation

Missions are posted to a central market where agents bid:

```python
class MissionBid(BaseModel):
    mission_id: str
    agent_id: str
    bid_price: float  # Resources agent requires
    expected_value: float  # Value agent expects to deliver
    confidence: float  # Agent's confidence in delivery
    time_to_complete: timedelta
```

### 3. Resource Price Discovery

Prices emerge from supply and demand:

```python
class ResourcePrice(BaseModel):
    resource_type: str
    current_price: float
    supply: float
    demand: float
    price_history: list[float]
    trend: PriceTrend  # RISING, STABLE, FALLING
```

### 4. Incentive Balancing

Agents are rewarded for:

- **Value Creation** — Missions completed successfully
- **Efficiency** — High value per resource cost
- **Reliability** — Consistent delivery
- **Cooperation** — Positive externalities for other agents

### 5. Multi-Agent Equilibrium Detection

The system monitors for:

- **Market Stability** — Prices not oscillating wildly
- **Allocation Efficiency** — High-value missions prioritized
- **Agent Participation** — All agents have opportunities
- **Resource Utilization** — No chronic shortages or surpluses

---

## Coordination Metrics

### CM-1: Market Efficiency

**Definition:** Value created per resource cost.

```python
market_efficiency = total_value_created / total_resource_cost

where:
    total_value_created = sum(mission.completed_value for mission in missions)
    total_resource_cost = sum(mission.resources_consumed for mission in missions)
```

**Target:** > 1.5 (value exceeds cost by 50%)

### CM-2: Allocation Optimality

**Definition:** Ratio of achieved to theoretical maximum value.

```python
allocation_optimality = achieved_mission_value / theoretical_max_value

where:
    achieved_mission_value = sum(completed_mission_values)
    theoretical_max_value = sum(top_bid_for_each_mission)
```

**Target:** > 0.85 (within 15% of optimal)

### CM-3: Market Stability

**Definition:** Inverse of price variance over time.

```python
market_stability = 1.0 / (1.0 + price_variance)

where:
    price_variance = variance(prices_over_time_window)
```

**Target:** > 0.70 (low volatility)

### CM-4: Coordination Latency

**Definition:** Time from mission posting to allocation.

```python
coordination_latency = time_allocation_decided - time_posted
```

**Target:** < 5 seconds for typical missions

---

## Market Model

### Resource Types

| Resource | Unit | Base Price | Description |
|----------|------|------------|-------------|
| compute | CPU-ms | 0.001 | CPU milliseconds |
| gpu_compute | GPU-ms | 0.01 | GPU milliseconds |
| planning_cycle | cycle | 0.1 | L5-L7 reasoning operation |
| memory_mb | MB-second | 0.0001 | Memory per second |
| tool_call | call | 0.01 | API/tool invocation |
| mission_execution | mission | 1.0 | Completed mission unit |

### Price Discovery Mechanism

**Continuous Double Auction (CDA):**

```python
class ContinuousDoubleAuction:
    """Market where agents submit bids and asks continuously."""

    async def submit_bid(self, agent_id: str, resource: str, price: float, quantity: float):
        """Agent bids to buy resources."""

    async def submit_ask(self, agent_id: str, resource: str, price: float, quantity: float):
        """Agent offers to sell resources."""

    async def match_orders(self) -> list[Trade]:
        """Match compatible bids and asks."""
```

### Agent Budgets

Each agent has:

```python
class AgentBudget(BaseModel):
    agent_id: str
    initial_budget: float
    current_budget: float
    resources_owned: dict[str, float]  # resource_type -> quantity
    earnings: float  # Total earned from missions
    spent: float  # Total spent on resources
```

---

## Decision Policy

Layer 16 **must respect** all lower layers:

```
Layer 13 (Economic Intelligence)
    → Is this mission worth doing?

Layer 14 (Constitutional Governance)
    → Is this mission allowed?

Layer 15 (Strategic Foresight)
    → Is this mission smart over time?

Layer 16 (Multi-Agent Coordination)
    → Which agent should do it and at what price?

Layer 16 CANNOT override L13/L14/L15 decisions.
```

### Example Flow

```python
# Mission is proposed
mission = Mission(
    id="M_001",
    description="Process customer data",
    estimated_value=100,
    required_resources={"compute": 1000, "memory_mb": 500}
)

# Layer 13: Economic viability
if not economic_intelligence.is_viable(mission):
    return REJECT  # Not worth doing

# Layer 14: Constitutional legitimacy
if not governance.is_legitimate(mission):
    return REJECT  # Not allowed

# Layer 15: Strategic foresight
if not foresight.is_strategic(mission):
    return REJECT  # Not smart over time

# Layer 16: Multi-agent allocation
winning_bid = market.allocate_mission(mission)
execute_mission(mission, agent=winning_bid.agent_id, price=winning_bid.price)
```

---

## Integration Points

### With Layer 12 (Collective Intelligence)

- **Provenance Tracking:** Each trade and allocation is recorded
- **Trust Scores:** Agent reputation affects bid weight
- **Federation Support:** Cross-node resource trading

### With Layer 13 (Economic Intelligence)

- **Resource Estimation:** L13 provides cost estimates
- **Value Scoring:** L13 provides mission value scores
- **Budget Tracking:** Shared budget state

### With Layer 14 (Constitutional Governance)

- **Market Rules:** L14 defines fair trading rules
- **Anti-Manipulation:** L14 prevents market abuse
- **Audit Trails:** All trades are audited

### With Layer 15 (Strategic Foresight)

- **Long-Term Planning:** Markets can forecast future demand
- **Optionality Preservation:** Agents can trade future options
- **Strategic Reserves:** Critical resources reserved for strategic missions

---

## Success Criteria

Layer 16 is complete when:

1. ✅ Multiple agents can trade resources
2. ✅ Missions are allocated through competitive bidding
3. ✅ Prices emerge from supply/demand dynamics
4. ✅ Market efficiency exceeds 1.5
5. ✅ Allocation optimality exceeds 0.85
6. ✅ Market stability exceeds 0.70
7. ✅ Coordination latency < 5 seconds
8. ✅ No regression in Layers 13-15

---

## Failure Conditions

Layer 16 must prevent:

- **Agent Monopolies** — Single agent controlling all resources
- **Price Manipulation** — Agents gaming the market
- **Resource Starvation** — Agents unable to obtain critical resources
- **Coordination Deadlock** — No bids for critical missions
- **Market Oscillation** — Prices cycling without convergence

---

## Open Questions

1. **Initial Allocation:** How are initial budgets distributed?
   - *Proposal:* Equal budget, adjusted by historical contribution

2. **Currency Design:** Should agents use real resources or abstract tokens?
   - *Proposal:* Abstract tokens backed by real resources

3. **Price Floor/Ceiling:** Should prices be bounded?
   - *Proposal:* Circuit breakers trigger at extreme prices

4. **Agent Entry/Exit:** How do new agents join or leave?
   - *Proposal:* New agents get starter budget, departing agents settle

---

**Document Status:** DRAFT
**Next:** MARKET_MECHANISM.md

# Layer 16 Validation Scenarios
## Multi-Agent Economic Coordination Test Cases

**Version:** 0.16.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-15

---

## Overview

This document defines validation scenarios for Layer 16 multi-agent economic coordination.

**Total Scenarios:** 6
**Coverage:** All market mechanisms and failure modes

---

## Scenario Definitions

### Scenario 1: Competitive Mission Allocation

**Purpose:** Ensure best agent wins based on value/cost.

**Setup:**
- Mission posted with estimated value = 100
- Agent A bids: price = 40, expected_value = 80, confidence = 0.7
- Agent B bids: price = 30, expected_value = 90, confidence = 0.8
- Agent C bids: price = 50, expected_value = 70, confidence = 0.6

**Expected Results:**
```
Bid Scores:
  Agent A: (80/40)*0.5 + 0.7*0.3 + speed*0.2 = 1.0*0.5 + 0.21 = 0.71
  Agent B: (90/30)*0.5 + 0.8*0.3 + speed*0.2 = 1.5*0.5 + 0.24 = 0.99
  Agent C: (70/50)*0.5 + 0.6*0.3 + speed*0.2 = 0.7*0.5 + 0.18 = 0.53

Winner: Agent B (highest score)
Price: Second-price = max(30, 40) = 40
```

**Validation Checks:**
1. ✅ Agent B wins (highest efficiency)
2. ✅ Winner pays second price (40)
3. ✅ Other agents' budgets unchanged
4. ✅ Mission allocated to winner

**Test Data:**
```python
mission = MissionForAuction(
    mission_id="M_001",
    description="Process customer data",
    required_resources={"compute": 1000},
    estimated_value=100,
    reserve_price=20
)

bids = [
    MissionBid(
        bid_id="B_001_A",
        auction_id="A_001",
        agent_id="agent_a",
        price=40,
        expected_value=80,
        confidence=0.7,
        time_to_complete=timedelta(hours=1)
    ),
    MissionBid(
        bid_id="B_001_B",
        auction_id="A_001",
        agent_id="agent_b",
        price=30,
        expected_value=90,
        confidence=0.8,
        time_to_complete=timedelta(hours=1)
    ),
    MissionBid(
        bid_id="B_001_C",
        auction_id="A_001",
        agent_id="agent_c",
        price=50,
        expected_value=70,
        confidence=0.6,
        time_to_complete=timedelta(hours=1)
    ),
]
```

---

### Scenario 2: Monopoly Breakup

**Purpose:** Ensure incentive engine redistributes monopolized resources.

**Setup:**
- Resource: "compute"
- Agent A owns 90% of supply (900 units)
- Agent B owns 10% of supply (100 units)
- Total demand: 500 units
- Monopoly threshold: 50%

**Expected Results:**
```
MonopolyDetector:
  detects monopoly = True
  dominant_agent = "agent_a"
  market_share = 0.90

IncentiveEngine:
  triggers redistribution = True
  action = "tax dominant agent, subsidize entry"
  tax_rate = 0.2  # Tax 20% of monopoly rents
  subsidy = 180 units to new entrants
```

**Validation Checks:**
1. ✅ Monopoly detected (market_share > 0.5)
2. ✅ Dominant agent identified
3. ✅ Incentive action triggered
4. ✅ Redistribution applied

**Test Data:**
```python
agent_holdings = {
    "agent_a": 900,
    "agent_b": 100
}

market_state = MarketState(
    resource_type="compute",
    current_price=0.001,
    bids=[ResourceBid(quantity=500, max_price=0.002)],
    asks=[
        ResourceAsk(agent_id="agent_a", quantity=450, min_price=0.001),
        ResourceAsk(agent_id="agent_b", quantity=50, min_price=0.001),
    ]
)
```

---

### Scenario 3: Supply Shortage Response

**Purpose:** Verify price discovery during shortage.

**Setup:**
- Resource: "gpu_compute"
- Demand: 1000 units
- Supply: 200 units (shortage!)
- Initial price: 0.01

**Expected Results:**
```
PriceDiscoveryEngine:
  detects shortage = True
  demand_exceeds_supply_by = 800 units
  shortage_severity = 0.8  (critical)

Price adjustment:
  new_price = old_price * (demand / supply) = 0.01 * 5 = 0.05
  price_increase = 400%

Market response:
  high-value missions only (afford higher price)
  low-value missions defer
  supply incentivized to increase
```

**Validation Checks:**
1. ✅ Shortage detected (supply < demand)
2. ✅ Price increases appropriately
3. ✅ Severity calculated correctly
4. ✅ Market adjusts (demand decreases)

**Test Data:**
```python
shortage_state = MarketState(
    resource_type="gpu_compute",
    current_price=0.01,
    bids=[
        ResourceBid(quantity=1000, max_price=0.01)  # High demand at low price
    ],
    asks=[
        ResourceAsk(quantity=200, min_price=0.01)  # Low supply
    ]
)
```

---

### Scenario 4: Excess Capacity Response

**Purpose:** Verify price drops and allocation increases during surplus.

**Setup:**
- Resource: "compute"
- Demand: 100 units
- Supply: 1000 units (surplus!)
- Initial price: 0.01

**Expected Results:**
```
PriceDiscoveryEngine:
  detects surplus = True
  supply_exceeds_demand_by = 900 units
  surplus_severity = 0.9

Price adjustment:
  new_price = old_price * (demand / supply) = 0.01 * 0.1 = 0.001
  price_decrease = 90%

Market response:
  more missions become affordable
  utilization increases
  supply reduces (agents exit)
```

**Validation Checks:**
1. ✅ Surplus detected (supply > demand)
2. ✅ Price decreases appropriately
3. ✅ Allocation increases
4. ✅ Market clears toward equilibrium

**Test Data:**
```python
surplus_state = MarketState(
    resource_type="compute",
    current_price=0.01,
    bids=[
        ResourceBid(quantity=100, max_price=0.01)
    ],
    asks=[
        ResourceAsk(quantity=1000, min_price=0.01)
    ]
)
```

---

### Scenario 5: Strategic Priority Override

**Purpose:** Ensure L15 strategic foresight can override price signals.

**Setup:**
- Mission posted with strategic_priority = HIGH
- Market clearing price: 100
- Only low-tier agents willing to pay 100
- High-tier agent busy with other work, willing only at 200

**Expected Results:**
```
L15 Analysis:
  strategic_importance = HIGH
  long_term_value = 0.9
  cannot_defer = True

Coordination Decision:
  override_price_mechanism = True
  incentive_multiplier = 2.0  # Offer 2x market price
  final_offer = 200

Outcome:
  High-tier agent accepts at premium
  Mission completed strategically
  Note: This is a FEATURE, not a bug
```

**Validation Checks:**
1. ✅ Strategic priority detected
2. ✅ Price override authorized
3. ✅ Incentive adjusted
4. ✅ High-quality agent allocated

**Test Data:**
```python
strategic_mission = MissionForAuction(
    mission_id="M_STRATEGIC",
    description="Critical security patch",
    required_resources={"compute": 500},
    estimated_value=200,
    strategic_priority="HIGH",
    can_defer=False
)

bids = [
    MissionBid(
        bid_id="B_LOW",
        auction_id="A_STRATEGIC",
        agent_id="low_tier_agent",
        price=100,
        expected_value=120,
        confidence=0.7,
        time_to_complete=timedelta(hours=2)
    ),
    # High tier won't bid at 100, needs 200
]
```

---

### Scenario 6: Market Instability Correction

**Purpose:** Ensure equilibrium detector triggers correction.

**Setup:**
- Resource: "compute"
- Price oscillating: 0.001, 0.010, 0.001, 0.010, ...
- Volatility: > 100%
- No trades executing (bid-ask spread too wide)

**Expected Results:**
```
EquilibriumDetector:
  detects instability = True
  price_volatility = 1.0  (100%)
  is_stable = False
  recommendation = "Inject liquidity, narrow spread"

Correction actions:
  1. SystemMarketMaker provides bid/ask
  2. Circuit breaker triggered if > 20% move
  3. Forced auction if no trades in 60 seconds
  4. Price freeze for 5 minutes

Outcome:
  Volatility decreases
  Trades resume
  Stability restored
```

**Validation Checks:**
1. ✅ Instability detected (high volatility)
2. ✅ Circuit breaker considered
3. ✅ Correction actions triggered
4. ✅ Stability improves

**Test Data:**
```python
unstable_prices = [0.001, 0.010, 0.001, 0.010, 0.001, 0.010]

unstable_state = MarketState(
    resource_type="compute",
    current_price=0.010,
    bids=[ResourceBid(quantity=100, max_price=0.001)],
    asks=[ResourceAsk(quantity=100, min_price=0.010)],
    price_history=unstable_prices
)
# Bid-ask spread: 0.010 - 0.001 = 0.009 (90% spread!)
```

---

## Scenario Summary Table

| # | Scenario | Component(s) Tested | Key Metric | Complexity |
|---|----------|---------------------|------------|------------|
| 1 | Competitive Allocation | Auction, Incentive | Bid scoring, winner selection | Medium |
| 2 | Monopoly Breakup | Equilibrium, Incentive | Market share, redistribution | Medium |
| 3 | Supply Shortage | Price Discovery | Price elasticity, severity | Low |
| 4 | Excess Capacity | Price Discovery | Price decrease, utilization | Low |
| 5 | Strategic Override | Coordination, L15 integration | Priority weighting | High |
| 6 | Market Instability | Equilibrium, Circuit Breaker | Volatility, stability | High |

---

## Test Data Models

### MissionForAuction

```python
class MissionForAuction(BaseModel):
    mission_id: str
    description: str
    required_resources: dict[str, float]
    estimated_value: float
    deadline: datetime
    reserve_price: float
    strategic_priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    can_defer: bool
```

### MissionBid

```python
class MissionBid(BaseModel):
    bid_id: str
    auction_id: str
    agent_id: str
    price: float
    expected_value: float
    confidence: float  # 0.0 to 1.0
    time_to_complete: timedelta
```

### MarketState

```python
class MarketState(BaseModel):
    resource_type: str
    current_price: float
    bids: list[ResourceBid]
    asks: list[ResourceAsk]
    last_trade_price: float | None
    price_history: list[float]
```

### AgentHoldings

```python
class AgentHoldings(BaseModel):
    agent_id: str
    resources: dict[str, float]  # resource_type -> quantity
    budget: float
```

---

## Validation Execution

### Running All Scenarios

```bash
python -m pytest tests/layer16/test_market_coordination.py -v
```

### Expected Output

```
============================================================
Layer 16 Validation Results
============================================================

Total Scenarios: 6
Passed: 6
Failed: 0
Success Rate: 100.0%

[PASS] Scenario 1: Competitive Mission Allocation
[PASS] Scenario 2: Monopoly Breakup
[PASS] Scenario 3: Supply Shortage Response
[PASS] Scenario 4: Excess Capacity Response
[PASS] Scenario 5: Strategic Priority Override
[PASS] Scenario 6: Market Instability Correction

============================================================
SUCCESS: All market coordination scenarios passed!
============================================================
```

---

## Success Criteria

Layer 16 validation is complete when:

1. ✅ All 6 scenarios passing
2. ✅ All engines tested (Market, Auction, Price, Incentive, Equilibrium)
3. ✅ Integration with Layer 15 verified
4. ✅ Market mechanism validated
5. ✅ Calibration loop functional
6. ✅ No regression in Layer 13-15

---

**Document Status:** DRAFT
**Next:** FAILURE_MODES.md

# Layer 16 Calibration Plan
## Multi-Agent Market Calibration Framework

**Version:** 0.16.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-15

---

## Overview

This document defines the calibration framework for Layer 16 multi-agent economic coordination.

**Goal:** Ensure markets remain efficient, stable, and fair through continuous learning and adjustment.

---

## Calibration Metrics

### CM-1: Market Efficiency

**Definition:** Value created per resource cost.

```python
market_efficiency = total_value_created / total_resource_cost

where:
    total_value_created = sum(mission.completed_value for mission in completed_missions)
    total_resource_cost = sum(mission.resources_consumed for mission in completed_missions)
```

**Target:** > 1.5 (value exceeds cost by 50%)

### CM-2: Allocation Optimality

**Definition:** Ratio of achieved to theoretical maximum value.

```python
allocation_optimality = achieved_mission_value / theoretical_max_value

where:
    achieved_mission_value = sum(completed_mission_values)
    theoretical_max_value = sum(winning_bid_expected_value for each auction)
```

**Target:** > 0.85 (within 15% of optimal)

### CM-3: Market Stability

**Definition:** Inverse of price variance over time.

```python
market_stability = 1.0 / (1.0 + price_variance)

where:
    price_variance = variance(prices_over_time_window)
    time_window = 100 trades or 1 hour, whichever shorter
```

**Target:** > 0.70 (low volatility)

### CM-4: Coordination Latency

**Definition:** Time from mission posting to allocation.

```python
coordination_latency = time_allocation_decided - time_posted
```

**Target:** < 5 seconds for typical missions

---

## Calibration Data Collection

### Data Points Per Auction

```python
class AuctionRecord(BaseModel):
    auction_id: str
    mission_id: str
    timestamp: datetime

    # Mission details
    estimated_value: float
    required_resources: dict[str, float]

    # Bidding
    bids_received: int
    bidders: list[str]

    # Outcome
    winning_agent: str
    winning_price: float
    second_highest_price: float

    # Execution
    mission_completed: bool
    actual_value: float
    actual_resources_used: dict[str, float]

    # Calibration
    efficiency_score: float | None  # Calculated after execution
    optimal_allocation: bool | None  # Would winner have been different?
```

### Data Points Per Trade

```python
class TradeRecord(BaseModel):
    trade_id: str
    resource_type: str
    timestamp: datetime

    # Parties
    buyer_id: str
    seller_id: str

    # Terms
    quantity: float
    price: float

    # Market Context
    market_price_before: float
    market_price_after: float
    spread_before: float
    spread_after: float

    # Execution
    fulfilled: bool
    fulfillment_time: timedelta
```

### Data Collection Process

```python
async def collect_market_data(time_window: timedelta) -> MarketData:
    """Collect all market data within time window."""

    end_time = datetime.utcnow()
    start_time = end_time - time_window

    # Auction data
    auctions = await auction_db.get_auctions(
        start_time=start_time,
        end_time=end_time
    )

    # Trade data
    trades = await trade_db.get_trades(
        start_time=start_time,
        end_time=end_time
    )

    # Agent performance data
    agent_performance = await performance_db.get_all_agent_stats(
        start_time=start_time,
        end_time=end_time
    )

    return MarketData(
        auctions=auctions,
        trades=trades,
        agent_performance=agent_performance,
        collection_window=time_window
    )
```

---

## Calibration Loop

### Loop Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MARKET OPERATES                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 COLLECT DATA                                    │
│                 • Auction results                               │
│                 • Trade executions                               │
│                 • Agent performance                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CALCULATE METRICS                               │
│                 • Market efficiency                              │
│                 • Allocation optimality                         │
│                 • Price stability                               │
│                 • Coordination latency                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ASSESS & ADJUST                                  │
│                 • Adjust parameters if needed                     │
│                 • Trigger corrections                            │
│                 • Update calibration                             │
└─────────────────────────────────────────────────────────────────┘
```

### Calibration Algorithms

#### CA-1: Efficiency-Based Price Adjustment

```python
async def adjust_prices_based_on_efficiency(
    market_data: MarketData
) -> PriceAdjustment:
    """Adjust prices if market efficiency is off target."""

    efficiency = calculate_market_efficiency(market_data)
    target = 1.5

    if efficiency < target * 0.9:  # More than 10% below target
        # Market undervaluing resources, increase base prices
        adjustment_factor = 1.1  # 10% increase
    elif efficiency > target * 1.1:  # More than 10% above target
        # Market overvaluing resources, decrease base prices
        adjustment_factor = 0.9  # 10% decrease
    else:
        adjustment_factor = 1.0  # No change

    return PriceAdjustment(
        adjustment_factor=adjustment_factor,
        reason=f"Efficiency {efficiency:.2f} vs target {target}",
        resources_affected="all"
    )
```

#### CA-2: Allocation Quality Tracking

```python
async def track_allocation_quality(
    auction_records: list[AuctionRecord]
) -> AllocationQualityReport:
    """Track if markets are allocating to best agents."""

    optimal_count = 0
    suboptimal_count = 0

    for auction in auction_records:
        if not auction.mission_completed:
            continue

        # Was the winner the actual best choice?
        # Compare actual vs expected value
        if auction.actual_value >= auction.winning_bid.expected_value * 0.9:
            optimal_count += 1
        else:
            suboptimal_count += 1

    optimality_rate = optimal_count / (optimal_count + suboptimal_count)

    return AllocationQualityReport(
        optimality_rate=optimality_rate,
        optimal_allocations=optimal_count,
        suboptimal_allocations=suboptimal_count,
        meets_threshold=optimality_rate >= 0.85
    )
```

#### CA-3: Stability-Based Circuit Breaker Adjustment

```python
async def adjust_circuit_breakers(
    price_history: list[float],
    volatility: float
) -> CircuitBreakerAdjustment:
    """Adjust circuit breaker thresholds based on market conditions."""

    target_volatility = 0.1

    if volatility > target_volatility * 2:
        # Very high volatility, tighten breaker
        new_threshold = 0.1  # 10% move triggers halt
        action = "tighten"
    elif volatility < target_volatility * 0.5:
        # Very low volatility, loosen breaker
        new_threshold = 0.3  # 30% move triggers halt
        action = "loosen"
    else:
        new_threshold = 0.2  # Default 20%
        action = "maintain"

    return CircuitBreakerAdjustment(
        new_threshold=new_threshold,
        action=action,
        reason=f"Volatility {volatility:.3f} vs target {target_volatility}"
    )
```

---

## Calibration Triggers

### Automatic Calibration

**Trigger Conditions:**
- Hourly calibration cycle (scheduled)
- Efficiency drops below 1.2
- Stability drops below 0.60
- Allocation optimality below 0.80
- No trades for 5 minutes

### Manual Calibration

**Trigger Conditions:**
- Operator requests calibration
- System performance degraded
- Major market event
- New agent type added

---

## Calibration Phases

### Phase 16A: Single-Node Simulated Market (Days 1-15)

**Goal:** Establish baseline market behavior in controlled environment.

**Activities:**
1. Create simulated agent population
2. Run simulated resource markets
3. Test mission allocation
4. Establish baseline metrics
5. Validate price discovery

**Success Criteria:**
- Simulated agents can trade resources
- Missions allocated through auctions
- Prices emerge from supply/demand
- Baseline metrics measured

### Phase 16B: Multi-Agent Cluster Simulation (Days 16-45)

**Goal:** Test coordination across multiple agent instances.

**Activities:**
1. Deploy multiple TORQ instances
2. Establish inter-node communication
3. Run federation-level auctions
4. Test resource sharing
5. Monitor cross-node metrics

**Success Criteria:**
- Agents across nodes can trade
- Federation-level auctions functional
- Resource sharing works
- Metrics comparable to single-node

### Phase 16C: Real Federated Agent Coordination (Day 46+)

**Goal:** Production deployment across real TORQ federation.

**Activities:**
1. Connect to live TORQ federation
2. Enable real agent coordination
3. Monitor market health
4. Adjust parameters based on live data
5. Scale to full production

**Success Criteria:**
- Live agents coordinating effectively
- Market efficiency > 1.5
- Allocation optimality > 0.85
- Stability > 0.70
- Latency < 5 seconds

---

## Validation of Calibration

### V-1: Efficiency Improves Over Time

**Test:** Compare efficiency at start vs end of calibration period.

**Expected:** Efficiency increases by at least 10%.

```python
efficiency_start = calculate_efficiency(early_data)
efficiency_end = calculate_efficiency(recent_data)

assert efficiency_end > efficiency_start * 1.10
```

### V-2: Allocation Quality Maintained

**Test:** Check if allocation quality stays above threshold.

**Expected:** Optimality rate > 0.85.

```python
quality_report = await track_allocation_quality(auction_records)

assert quality_report.optimality_rate > 0.85
```

### V-3: Stability Improves or Maintained

**Test:** Check if market stability improves.

**Expected:** Stability score > 0.70.

```python
stability = calculate_market_stability(price_history)

assert stability > 0.70
```

### V-4: No Monopolies Emerge

**Test:** Check that no agent monopolizes resources.

**Expected:** All agents have < 50% market share.

```python
for resource in monitored_resources:
    monopoly_report = detect_monopoly(resource, agent_holdings)
    assert monopoly_report.is_monopoly == False
```

---

## Monitoring Dashboard

### CLI Interface

```bash
torq coordination market-status
```

**Output:**
```
Layer 16 Market Status (Last Hour)
---------------------------------------------------------------------------
Market Efficiency: 1.62 (target: >1.5) ✓
Allocation Optimality: 0.89 (target: >0.85) ✓
Market Stability: 0.78 (target: >0.70) ✓
Coordination Latency: 2.3s (target: <5s) ✓

Resource Markets:
  compute:     1234 trades, price: $0.0012, spread: 0.8%
  gpu_compute: 56 trades,   price: $0.0145, spread: 2.1%
  memory_mb:   8902 trades, price: $0.0001, spread: 0.5%

Active Auctions: 12
Unallocated Missions: 3 (all low priority)
Agents Active: 8/8

Status: HEALTHY ✓
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|--------|----------|--------|
| Market Efficiency | < 1.3 | < 1.1 | Trigger price adjustment |
| Allocation Optimality | < 0.80 | < 0.70 | Review auction rules |
| Market Stability | < 0.60 | < 0.50 | Trigger circuit breaker |
| Coordination Latency | > 10s | > 30s | Review allocation algorithm |
| Resource Shortage | Any | Critical | Trigger rationing |

---

## Calibration Report

### Weekly Report Contents

```python
class CalibrationReport(BaseModel):
    report_date: date
    period_start: datetime
    period_end: datetime

    # Metrics
    market_efficiency: float
    allocation_optimality: float
    market_stability: float
    coordination_latency: float

    # Volumes
    total_trades: int
    total_auctions: int
    trade_volume: float

    # Agent Health
    active_agents: int
    starved_agents: int
    monopolies_detected: int

    # Trends
    efficiency_trend: list[float]
    stability_trend: list[float]

    # Recommendations
    recommendations: list[str]
    calibration_actions: list[str]
```

---

## Success Criteria

Layer 16 calibration is complete when:

1. ✅ Baseline metrics established (Phase 16A)
2. ✅ Multi-agent simulation successful (Phase 16B)
3. ✅ Real federated coordination functional (Phase 16C)
4. ✅ All metrics within target ranges
5. ✅ Monitoring dashboard functional
6. ✅ Alert thresholds defined
7. ✅ No regression in Layer 13-15

---

## Integration with Validation

### Calibration in Validation Scenarios

**Scenario 3 (Supply Shortage)** explicitly tests calibration:
- Price discovery responds to shortage
- Prices adjust appropriately
- Market clears toward equilibrium

**Scenario 6 (Market Instability)** tests stability calibration:
- Oscillation detected
- Circuit breaker triggered
- Stability restored

### Validation Uses Calibration Data

```python
# Validation uses calibrated market parameters
calibrated_params = await calibration_engine.get_calibrated_parameters()

# Run validation scenarios
for scenario in validation_scenarios:
    result = await scenario.run_with_calibrated_params(calibrated_params)
```

---

**Document Status:** DRAFT
**Layer 16 Status:** Planning Phase - Complete

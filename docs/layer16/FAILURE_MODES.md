# Layer 16 Failure Modes
## Multi-Agent Economic Coordination Risk Analysis

**Version:** 0.16.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-15

---

## Overview

This document defines failure modes for Layer 16 multi-agent economic coordination, including symptoms, mitigation strategies, and detection methods.

**Goal:** Prevent market failures while preserving economic coordination benefits.

---

## Failure Mode 1: Agent Monopoly

### Description

A single agent controls most of a critical resource, enabling price manipulation and exclusion of other agents.

### Symptoms

- One agent holds >50% of resource supply
- Price artificially inflated
- Other agents unable to compete
- Market entry blocked

### Detection

```python
class MonopolyDetector:
    def detect_monopoly(
        self,
        resource: str,
        agent_holdings: dict[str, float]
    ) -> MonopolyReport:
        """Detect if single agent controls market."""

        total_supply = sum(agent_holdings.values())
        shares = {
            agent: qty / total_supply
            for agent, qty in agent_holdings.items()
        }

        max_share = max(shares.values())
        dominant_agent = max(shares, key=shares.get)

        return MonopolyReport(
            is_monopoly=max_share > 0.5,
            dominant_agent=dominant_agent if max_share > 0.5 else None,
            market_share=max_share
        )
```

### Mitigation Strategies

#### M1-1: Progressive Resource Tax

```python
# Tax resource holdings above threshold
def calculate_monopoly_tax(agent_holdings: dict[str, float]) -> float:
    threshold = 0.3  # 30% market share
    tax_rate = 0.5   # 50% tax on excess

    total = sum(agent_holdings.values())
    for agent, holding in agent_holdings.items():
        share = holding / total
        if share > threshold:
            excess = (share - threshold) * total
            return excess * tax_rate

    return 0.0
```

#### M1-2: Supply Subsidies

```python
# Subsidize new entrants and small holders
def calculate_supply_subsidy(agent_holdings: dict[str, float]) -> float:
    threshold = 0.1  # Below 10% gets subsidy
    subsidy_rate = 0.2  # 20% subsidy

    total = sum(agent_holdings.values())
    for agent, holding in agent_holdings.items():
        share = holding / total
        if share < threshold:
            return holding * subsidy_rate

    return 0.0
```

#### M1-3: Breakup Trigger

```python
# Force redistribution if monopoly > 70%
if market_share > 0.7:
    trigger_forced_redistribution(
        resource=resource,
        from_agent=dominant_agent,
        to_agents=other_agents,
        amount=excess - 0.5 * total_supply
    )
```

### Validation Rule

```python
# Scenario 2 validates this
assert monopoly_detector.detect("compute").is_monopoly == True
assert incentive_engine.redistribute_triggered == True
```

---

## Failure Mode 2: Price Manipulation

### Description

Agents attempt to manipulate prices through fake orders, wash trading, or collusion.

### Symptoms

- Suspicious order patterns (rapid cancel/resubmit)
- Price movement without volume
- Correlated trading between agents
- Prices disconnected from fundamentals

### Detection

```python
class PriceManipulationDetector:
    def detect_manipulation(
        self,
        order_history: list[Order],
        trade_history: list[Trade]
    ) -> ManipulationReport:
        """Detect price manipulation patterns."""

        # Flag 1: Wash trading (same agent both sides)
        wash_trades = self._detect_wash_trades(trade_history)

        # Flag 2: Spoofing (fake orders)
        spoofing = self._detect_spoofing(order_history)

        # Flag 3: Quote stuffing (excessive orders)
        quote_stuffing = self._detect_quote_stuffing(order_history)

        # Flag 4: Momentum ignition
        momentum_ignition = self._detect_momentum_ignition(trade_history)

        return ManipulationReport(
            is_manipulated=any([wash_trades, spoofing, quote_stuffing, momentum_ignition]),
            wash_trades_detected=wash_trades,
            spoofing_detected=spoofing,
            quote_stuffing_detected=quote_stuffing,
            momentum_ignition_detected=momentum_ignition
        )
```

### Mitigation Strategies

#### M2-1: Order Rate Limiting

```python
# Limit order submission rate
class OrderRateLimiter:
    def __init__(self, max_orders_per_second: float = 10):
        self.max_rate = max_orders_per_second
        self.agent_order_counts: dict[str, list[datetime]] = {}

    def can_submit_order(self, agent_id: str) -> bool:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=1)

        # Clean old orders
        if agent_id in self.agent_order_counts:
            self.agent_order_counts[agent_id] = [
                ts for ts in self.agent_order_counts[agent_id]
                if ts > window_start
            ]

        # Check rate
        recent_count = len(self.agent_order_counts.get(agent_id, []))
        return recent_count < self.max_rate
```

#### M2-2: Trade Verification

```python
# Require actual resource transfer for trades
def verify_trade_execution(trade: Trade) -> bool:
    """Verify that traded resources were actually transferred."""

    buyer_resources = get_agent_resources(trade.buyer_id, trade.resource_type)
    seller_resources_before = get_agent_resources(trade.seller_id, trade.resource_type, before=True)
    seller_resources_after = get_agent_resources(trade.seller_id, trade.resource_type, after=True)

    # Verify buyer received resources
    buyer_received = get_resource_delta(trade.buyer_id, trade.resource_type, trade.quantity)

    # Verify seller lost resources
    seller_sent = seller_resources_before - seller_resources_after

    return buyer_received >= trade.quantity * 0.95 and seller_sent >= trade.quantity * 0.95
```

#### M2-3: Pattern Detection Bans

```python
# Ban agents with suspicious patterns
class AgentBanList:
    def __init__(self):
        self.banned_agents: set[str] = set()
        self.warning_count: dict[str, int] = {}

    def flag_suspicious_activity(self, agent_id: str, pattern: str):
        if agent_id not in self.warning_count:
            self.warning_count[agent_id] = 0

        self.warning_count[agent_id] += 1

        # Ban after 3 strikes
        if self.warning_count[agent_id] >= 3:
            self.banned_agents.add(agent_id)
            revoke_market_access(agent_id)
```

---

## Failure Mode 3: Resource Starvation

### Description

Some agents cannot obtain critical resources due to budget constraints or monopolistic practices.

### Symptoms

- Agents have zero budget
- Agents cannot place bids
- Critical missions unallocated
- System efficiency drops

### Detection

```python
class ResourceStarvationDetector:
    def detect_starvation(
        self,
        agent_budgets: dict[str, float],
        market_prices: dict[str, float]
    ) -> StarvationReport:
        """Detect agents starved of resources."""

        starved_agents = []

        for agent_id, budget in agent_budgets.items():
            # Check if agent can afford minimum resource bundle
            min_cost = sum(market_prices.values()) * 0.1  # 10% of market basket

            if budget < min_cost:
                starved_agents.append({
                    "agent_id": agent_id,
                    "budget": budget,
                    "min_required": min_cost,
                    "deficit": min_cost - budget
                })

        return StarvationReport(
            has_starvation=len(starved_agents) > 0,
            starved_agents=starved_agents,
            starvation_rate=len(starved_agents) / len(agent_budgets)
        )
```

### Mitigation Strategies

#### M3-1: Minimum Budget Guarantee

```python
# Ensure every agent has minimum viable budget
MINIMUM_BUDGET = 10.0  # Units of account

async def ensure_minimum_budget(agent_id: str):
    budget = await get_agent_budget(agent_id)

    if budget < MINIMUM_BUDGET:
        transfer = MINIMUM_BUDGET - budget
        await grant_budget(agent_id, transfer, reason="minimum_budget_topup")
```

#### M3-2: Resource Rationing

```python
# Ration scarce resources during shortage
class ResourceRationer:
    def __init__(self, ration_threshold: float = 0.3):
        self.ration_threshold = ration_threshold

    async def ration_resource(
        self,
        resource: str,
        supply: float,
        demand: float
    ) -> RationingPlan:
        """Create rationing plan for scarce resource."""

        if supply / demand >= self.ration_threshold:
            return RationingPlan(rationing_required=False)

        # Calculate fair share per agent
        agents = await list_active_agents()
        fair_share = supply / len(agents)

        return RationingPlan(
            rationing_required=True,
            per_agent_limit=fair_share,
            duration=timedelta(hours=1)
        )
```

#### M3-3: Priority Access for Critical Missions

```python
# Reserve resources for high-priority missions
class ResourceReserve:
    def __init__(self, reserve_percentage: float = 0.2):
        self.reserve_percentage = reserve_percentage

    async def check_reserve_access(
        self,
        mission_priority: str,
        resource_availability: float
    ) -> bool:
        """Check if mission can access reserved resources."""

        if mission_priority == "CRITICAL":
            reserve = resource_availability * self.reserve_percentage
            return reserve > 0

        return False
```

---

## Failure Mode 4: Coordination Deadlock

### Description

No agents bid on critical missions, or all bids are above budget, causing system paralysis.

### Symptoms

- Critical missions receive no bids
- Auctions expire without allocation
- Mission queue grows indefinitely
- System throughput drops

### Detection

```python
class DeadlockDetector:
    def __init__(self, no_bid_threshold: int = 3):
        self.no_bid_threshold = no_bid_threshold
        self.unallocated_missions: list[str] = []

    async def check_deadlock(self) -> DeadlockReport:
        """Check for coordination deadlock."""

        # Count auctions with no bids
        no_bid_auctions = await count_auctionsWithout_bids()

        # Check age of oldest unallocated mission
        if self.unallocated_missions:
            oldest_age = await get_mission_age(self.unallocated_missions[0])
        else:
            oldest_age = timedelta(0)

        return DeadlockReport(
            in_deadlock=no_bid_auctions >= self.no_bid_threshold,
            no_bid_auctions=no_bid_auctions,
            oldest_unallocated_age=oldest_age,
            recommended_action=self._get_recommendation(no_bid_auctions, oldest_age)
        )
```

### Mitigation Strategies

#### M4-1: Forced Allocation

```python
# Force allocate critical missions if no bids
async def force_allocate_critical_mission(mission: MissionForAuction):
    if mission.strategic_priority in ["HIGH", "CRITICAL"]:
        # Select best available agent
        agents = await list_qualified_agents(mission)

        if agents:
            # Pick agent with highest reputation
            best_agent = max(agents, key=lambda a: a.reputation)

            # Force allocation at fair price
            await allocate_mission(
                mission=mission,
                agent=best_agent.agent_id,
                price=fair_price(mission)
            )
```

#### M4-2: Price Incentive

```python
# Increase offered price to attract bids
async def increase_mission_incentive(mission: MissionForAuction):
    multiplier = 1.5  # 50% price increase

    await re_post_mission(
        mission=mission,
        price_multiplier=multiplier,
        reason="no_bids_incentive_increase"
    )
```

#### M4-3: Expand Qualified Agents

```python
# Lower qualification requirements to expand bidder pool
async def expand_qualified_pool(mission: MissionForAuction):
    original_requirements = mission.qualification_requirements

    # Remove non-critical requirements
    relaxed_requirements = [
        req for req in original_requirements
        if not req.endswith("_optional")
    ]

    await re_post_mission(
        mission=mission,
        qualification_requirements=relaxed_requirements,
        reason="expand_bidder_pool"
    )
```

---

## Failure Mode 5: Market Oscillation

### Description

Prices cycle continuously without reaching equilibrium, causing uncertainty and reducing efficiency.

### Symptoms

- Price history shows sine wave pattern
- High volatility persists
- Bid-ask spread remains wide
- No clear trend direction

### Detection

```python
class OscillationDetector:
    def detect_oscillation(
        self,
        price_history: list[float],
        window: int = 10
    ) -> OscillationReport:
        """Detect if market is oscillating."""

        if len(price_history) < window * 2:
            return OscillationReport(is_oscillating=False)

        recent = price_history[-window:]
        earlier = price_history[-window*2:-window]

        # Check for pattern (high-low-high-low)
        direction_changes = 0
        for i in range(1, len(recent)):
            if i > 1:
                prev_change = recent[i-1] - recent[i-2]
                curr_change = recent[i] - recent[i-1]

                if (prev_change > 0 and curr_change < 0) or \
                   (prev_change < 0 and curr_change > 0):
                    direction_changes += 1

        # Oscillation = many direction changes
        is_oscillating = direction_changes >= window // 2

        return OscillationReport(
            is_oscillating=is_oscillating,
            direction_changes=direction_changes,
            frequency=direction_changes / window,
            recommendation="inject_liquidity" if is_oscillating else None
        )
```

### Mitigation Strategies

#### M5-1: Liquidity Injection

```python
# System market maker provides liquidity
async def inject_liquidity(resource: str):
    market_maker = SystemMarketMaker()

    # Get fair price
    fair_price = await calculate_fair_price(resource)

    # Provide bid and ask
    market_maker.provide_market(
        resource=resource,
        fair_price=fair_price,
        depth=100  # 100 units at each price
    )
```

#### M5-2: Price Smoothing

```python
# Apply exponential moving average to prices
class PriceSmoother:
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.ema_price: dict[str, float] = {}

    async def smooth_price(self, resource: str, raw_price: float) -> float:
        if resource not in self.ema_price:
            self.ema_price[resource] = raw_price
            return raw_price

        # Calculate EMA
        ema = self.alpha * raw_price + (1 - self.alpha) * self.ema_price[resource]
        self.ema_price[resource] = ema

        return ema
```

#### M5-3: Circuit Breaker

```python
# Halt trading during extreme volatility
class CircuitBreaker:
    def __init__(self, trigger_threshold: float = 0.2):
        self.trigger_threshold = trigger_threshold
        self.is_tripped: bool = False
        self.trip_time: datetime | None = None

    async def check_and_trip(self, current_price: float, reference_price: float):
        if self.is_tripped:
            return  # Already tripped

        price_change = abs(current_price - reference_price) / reference_price

        if price_change >= self.trigger_threshold:
            self.is_tripped = True
            self.trip_time = datetime.utcnow()
            await halt_trading(reason="circuit_breaker")

    async def reset(self):
        if self.is_tripped:
            await datetime.timedelta(minutes=5)
            self.is_tripped = False
            self.trip_time = None
            await resume_trading()
```

---

## Failure Mode Summary

| # | Failure Mode | Severity | Detection Complexity | Mitigation Complexity |
|---|-------------|----------|---------------------|---------------------|
| 1 | Agent Monopoly | HIGH | Low | Medium |
| 2 | Price Manipulation | HIGH | High | High |
| 3 | Resource Starvation | MEDIUM | Low | Medium |
| 4 | Coordination Deadlock | HIGH | Low | Medium |
| 5 | Market Oscillation | MEDIUM | Medium | Medium |

---

## Detection Integration

### Unified Failure Detector

```python
class MarketFailureDetector:
    def __init__(self):
        self.monopoly_detector = MonopolyDetector()
        self.manipulation_detector = PriceManipulationDetector()
        self.starvation_detector = ResourceStarvationDetector()
        self.deadlock_detector = DeadlockDetector()
        self.oscillation_detector = OscillationDetector()

    async def detect_all(
        self,
        market_state: MarketState,
        agent_budgets: dict[str, float],
        order_history: list[Order],
        trade_history: list[Trade]
    ) -> MarketFailureReport:
        """Detect all market failures."""

        results = {}

        # Monopoly check
        results["monopoly"] = await self.monopoly_detector.detect_monopoly(
            market_state.resource_type,
            market_state.agent_holdings
        )

        # Manipulation check
        results["manipulation"] = await self.manipulation_detector.detect_manipulation(
            order_history,
            trade_history
        )

        # Starvation check
        results["starvation"] = await self.starvation_detector.detect_starvation(
            agent_budgets,
            market_state.current_prices
        )

        # Deadlock check
        results["deadlock"] = await self.deadlock_detector.check_deadlock()

        # Oscillation check
        results["oscillation"] = await self.oscillation_detector.detect_oscillation(
            market_state.price_history
        )

        return MarketFailureReport(
            has_failures=any(r.is_failure for r in results.values()),
            results=results,
            critical_failures=[k for k,v in results.items() if v.is_critical]
        )
```

---

## Recovery Procedures

### Recovery R1: Monopoly Breakup

1. Identify monopolistic resource
2. Calculate excess holdings (>50%)
3. Tax excess at 50%
4. Redistribute to small holders
5. Monitor for re-concentration

### Recovery R2: Price Manipulation Response

1. Identify suspicious agents
2. Freeze trading for affected resource
3. Investigate trading patterns
4. Ban confirmed manipulators
5. Reverse fraudulent trades

### Recovery R3: Resource Starvation Relief

1. Identify starved agents
2. Grant minimum budget top-up
3. Ration scarce resources if needed
4. Reserve resources for critical missions
5. Monitor agent participation

### Recovery R4: Deadlock Resolution

1. Identify unallocated critical missions
2. Force allocate if necessary
3. Increase price incentives
4. Expand qualified agent pool
5. Monitor queue depth

### Recovery R5: Oscillation Stabilization

1. Detect oscillation pattern
2. Inject liquidity
3. Apply price smoothing
4. Trigger circuit breaker if extreme
5. Monitor for stabilization

---

## Prevention Summary

| Failure Mode | Prevention Strategy |
|---------------|-------------------|
| Agent Monopoly | Progressive taxation, supply subsidies, breakup trigger |
| Price Manipulation | Rate limiting, trade verification, pattern bans |
| Resource Starvation | Minimum budget, rationing, priority reserves |
| Coordination Deadlock | Forced allocation, price incentives, pool expansion |
| Market Oscillation | Liquidity injection, price smoothing, circuit breakers |

---

**Document Status:** DRAFT
**Next:** CALIBRATION_PLAN.md

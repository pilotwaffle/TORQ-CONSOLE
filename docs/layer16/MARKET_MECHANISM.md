# Layer 16 Market Mechanism
## Resource Exchange and Mission Auction Design

**Version:** 0.16.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-15

---

## Overview

This document defines the market mechanisms for Layer 16 multi-agent economic coordination.

**Core Principle:** Resources and missions are allocated through competitive, market-based mechanisms.

---

## Resource Market Design

### Market Type: Continuous Double Auction (CDA)

**Why CDA?**
- Continuous trading (no waiting for auction rounds)
- Price discovery from bid-ask matching
- Proven mechanism for financial markets
- Efficient liquidity

### Market Participants

| Role | Description | Incentive |
|------|-------------|-----------|
| **Buyers** | Agents needing resources | Complete missions, earn rewards |
| **Sellers** | Agents with excess capacity | Profit from resource sales |
| **Market Maker** | System-provided liquidity | Earn spread, ensure stability |

### Resource Types

```python
class ResourceType(Enum):
    COMPUTE = "compute"              # CPU milliseconds
    GPU_COMPUTE = "gpu_compute"      # GPU milliseconds
    PLANNING_CYCLE = "planning_cycle"  # L5-L7 reasoning
    MEMORY_MB = "memory_mb"          # Memory per second
    TOOL_CALL = "tool_call"          # API/tool invocation
    MISSION_EXECUTION = "mission"    # Completed mission unit
```

### Order Book Structure

```python
class OrderBook(BaseModel):
    resource_type: str
    bids: list[ResourceBid]  # Buy orders, sorted by price descending
    asks: list[ResourceAsk]  # Sell orders, sorted by price ascending
    last_price: float | None
    bid_volume: float
    ask_volume: float

    def get_spread(self) -> float:
        """Get bid-ask spread."""
        if not self.bids or not self.asks:
            return 0.0
        return self.asks[0].min_price - self.bids[0].max_price

    def get_mid_price(self) -> float:
        """Get mid-price (average of best bid and ask)."""
        if not self.bids or not self.asks:
            return 0.0
        return (self.bids[0].max_price + self.asks[0].min_price) / 2
```

### Order Matching Algorithm

```python
async def match_orders(order_book: OrderBook) -> list[Trade]:
    """Match compatible bids and asks.

    Algorithm:
    1. Take highest bid (willing to pay most)
    2. Take lowest ask (willing to accept least)
    3. If bid price >= ask price, execute trade
    4. Repeat until no more matches
    """
    trades = []

    while order_book.bids and order_book.asks:
        best_bid = order_book.bids[0]
        best_ask = order_book.asks[0]

        # Check if trade is possible
        if best_bid.max_price < best_ask.min_price:
            break  # No more matches possible

        # Calculate trade price (mid-point)
        trade_price = (best_bid.max_price + best_ask.min_price) / 2

        # Calculate trade quantity (min of bid and ask)
        trade_quantity = min(best_bid.quantity, best_ask.quantity)

        # Create trade
        trade = Trade(
            trade_id=generate_trade_id(),
            bid_id=best_bid.bid_id,
            ask_id=best_ask.ask_id,
            resource_type=order_book.resource_type,
            quantity=trade_quantity,
            price=trade_price,
            buyer_id=best_bid.agent_id,
            seller_id=best_ask.agent_id,
            timestamp=datetime.utcnow()
        )
        trades.append(trade)

        # Update quantities
        best_bid.quantity -= trade_quantity
        best_ask.quantity -= trade_quantity

        # Remove fully filled orders
        if best_bid.quantity <= 0:
            order_book.bids.pop(0)
        if best_ask.quantity <= 0:
            order_book.asks.pop(0)

    return trades
```

---

## Price Discovery Mechanism

### Equilibrium Price Calculation

**Supply and Demand Crossing:**

```python
def calculate_equilibrium_price(
    bids: list[ResourceBid],
    asks: list[ResourceAsk]
) -> float:
    """Calculate market clearing price.

    The equilibrium price is where supply equals demand.
    """
    # Sort bids by price descending (demand curve)
    sorted_bids = sorted(bids, key=lambda b: b.max_price, reverse=True)

    # Sort asks by price ascending (supply curve)
    sorted_asks = sorted(asks, key=lambda a: a.min_price)

    # Calculate cumulative supply and demand at each price point
    price_points = set([b.max_price for b in bids] + [a.min_price for a in asks])

    for price in sorted(price_points, reverse=True):
        demand = sum(b.quantity for b in sorted_bids if b.max_price >= price)
        supply = sum(a.quantity for a in sorted_asks if a.min_price <= price)

        if demand <= supply:
            return price

    # If no crossing found, return mid of best bid/ask
    if sorted_bids and sorted_asks:
        return (sorted_bids[0].max_price + sorted_asks[0].min_price) / 2

    return 0.0
```

### Price Trend Detection

```python
def detect_price_trend(
    price_history: list[float],
    window: int = 10
) -> PriceTrend:
    """Detect if price is rising, stable, falling, or volatile."""
    if len(price_history) < window:
        return PriceTrend.STABLE

    recent = price_history[-window:]

    # Calculate linear regression slope
    x = list(range(window))
    slope = covariance(x, recent) / variance(x)

    # Calculate volatility (standard deviation)
    volatility = stdev(recent)
    avg_price = mean(recent)
    relative_volatility = volatility / avg_price if avg_price > 0 else 0

    # Classify trend
    if relative_volatility > 0.2:
        return PriceTrend.VOLATILE
    elif slope > 0.01:
        return PriceTrend.RISING
    elif slope < -0.01:
        return PriceTrend.FALLING
    else:
        return PriceTrend.STABLE
```

---

## Mission Auction Design

### Auction Type: Second-Price Sealed Bid (Vickrey)

**Why Second-Price?**
- Encourages truthful bidding (dominant strategy)
- Winner pays second-highest price
- Prevents winner's curse
- Efficient allocation

### Auction Timeline

```
T0: Auction opens
    → Mission posted to market
    → Agents can submit bids

T1: Bidding phase (duration: mission-specific)
    → Agents submit sealed bids
    → Bids include: price, expected_value, confidence, time_to_complete

T2: Auction closes
    → Bids no longer accepted
    → Winner selected

T3: Winner selection (immediate)
    → Calculate bid scores
    → Select highest score
    → Winner pays second-price

T4: Allocation (immediate)
    → Mission assigned to winner
    → Budget transferred
    → Resources reserved
```

### Bid Scoring Formula

```python
def calculate_bid_score(bid: MissionBid) -> float:
    """Calculate bid score for ranking.

    Higher score = better bid.

    Score considers:
    - Value per resource (efficiency)
    - Confidence (reliability)
    - Speed (time preference)
    """
    # Efficiency: value per resource
    efficiency = bid.expected_value / bid.price if bid.price > 0 else 0

    # Normalize to [0, 1]
    normalized_efficiency = min(1.0, efficiency / 10.0)  # Assuming 10x is excellent

    # Confidence directly in [0, 1]
    confidence = bid.confidence

    # Speed: faster is better
    # Assume 1 hour is baseline, faster = higher score
    time_score = 1.0 / max(1.0, bid.time_to_complete.total_seconds() / 3600)

    # Weighted combination
    score = (
        normalized_efficiency * 0.5 +
        confidence * 0.3 +
        time_score * 0.2
    )

    return score
```

### Winner Selection

```python
async def select_winner(
    auction: MissionAuction
) -> AuctionResult:
    """Select winning bid using second-price mechanism."""

    # Sort bids by score
    sorted_bids = sorted(
        auction.bids,
        key=calculate_bid_score,
        reverse=True
    )

    if not sorted_bids:
        raise NoBidsError(f"No bids received for auction {auction.auction_id}")

    # Winner is highest score
    winner = sorted_bids[0]

    # Second price: price of second-highest score (or reserve price)
    if len(sorted_bids) > 1:
        second_price = sorted_bids[1].price
    else:
        second_price = auction.reserve_price

    # Winner pays max(own_bid, second_price) to ensure minimum revenue
    final_price = max(winner.price, second_price)

    return AuctionResult(
        auction_id=auction.auction_id,
        mission_id=auction.mission_id,
        winning_bid=winner.bid_id,
        winning_agent=winner.agent_id,
        price=final_price,
        total_bids=len(sorted_bids),
        timestamp=datetime.utcnow()
    )
```

---

## Incentive Mechanism

### Reward Calculation

```python
async def calculate_mission_reward(
    mission: MissionForAuction,
    outcome: MissionOutcome,
    bid: MissionBid
) -> float:
    """Calculate reward for completing a mission.

    Reward = Base Reward + Performance Bonus - Penalties
    """
    base_reward = bid.price * 0.1  # 10% of bid price as base

    # Performance bonus based on outcome
    if outcome == MissionOutcome.SUCCESS:
        performance_bonus = base_reward * 0.5  # +50% for success
    elif outcome == MissionOutcome.PARTIAL:
        performance_bonus = base_reward * 0.2  # +20% for partial
    else:
        performance_bonus = 0.0

    # Confidence accuracy bonus
    # If agent was confident and succeeded, bonus
    # If agent was confident and failed, penalty
    if outcome == MissionOutcome.SUCCESS:
        confidence_bonus = bid.confidence * base_reward * 0.3
    else:
        confidence_penalty = bid.confidence * base_reward * -0.3
        confidence_bonus = confidence_penalty

    # Speed bonus
    expected_time = bid.time_to_complete
    actual_time = outcome.actual_duration
    if actual_time < expected_time:
        speed_bonus = base_reward * 0.2 * (expected_time - actual_time) / expected_time
    else:
        speed_bonus = 0.0

    total_reward = base_reward + performance_bonus + confidence_bonus + speed_bonus

    return max(0, total_reward)  # No negative rewards
```

### Budget Adjustment

```python
async def settle_mission(
    agent_id: str,
    bid_price: float,
    reward: float,
    outcome: MissionOutcome
) -> BudgetAdjustment:
    """Settle mission completion with budget adjustment.

    Agent pays bid_price upfront.
    Agent receives reward upon completion.
    """
    # Net result
    net_change = reward - bid_price

    return BudgetAdjustment(
        agent_id=agent_id,
        amount=net_change,
        reason=f"Mission settlement: {outcome.value}",
        timestamp=datetime.utcnow()
    )
```

---

## Equilibrium Detection

### Stability Metrics

```python
class StabilityMetrics(BaseModel):
    price_volatility: float  # Standard deviation of returns
    bid_ask_spread: float  # Current spread as % of price
    volume_trend: str  # INCREASING, STABLE, DECREASING
    market_depth: float  # Total volume near current price

    def is_stable(self) -> bool:
        """Check if market is stable."""
        return (
            self.price_volatility < 0.1 and  # <10% volatility
            self.bid_ask_spread < 0.05 and  # <5% spread
            self.market_depth > 100  # Minimum liquidity
        )
```

### Shortage Detection

```python
def detect_shortage(market_state: MarketState) -> ShortageReport:
    """Detect if resource is in shortage."""

    # Calculate supply-demand balance
    demand = sum(bid.quantity for bid in market_state.bids)
    supply = sum(ask.quantity for ask in market_state.asks)

    balance = supply - demand
    balance_ratio = supply / demand if demand > 0 else float('inf')

    # Classify shortage
    if balance_ratio < 0.5:
        severity = 1.0  # Critical
    elif balance_ratio < 0.75:
        severity = 0.7  # Severe
    elif balance_ratio < 0.9:
        severity = 0.4  # Moderate
    else:
        severity = 0.0  # No shortage

    return ShortageReport(
        resource_type=market_state.resource_type,
        is_shortage=severity > 0.4,
        shortage_severity=severity,
        demand_exceeds_supply_by=max(0, demand - supply),
        estimated_duration=timedelta(hours=1)  # Would be dynamic
    )
```

### Monopoly Detection

```python
def detect_monopoly(
    resource: str,
    agent_holdings: dict[str, float]  # agent_id -> quantity
) -> MonopolyReport:
    """Detect if single agent controls market."""

    total_supply = sum(agent_holdings.values())

    if total_supply == 0:
        return MonopolyReport(
            resource_type=resource,
            is_monopoly=False,
            dominant_agent=None,
            market_share=0.0,
            threshold=0.5
        )

    # Calculate market shares
    shares = {
        agent_id: quantity / total_supply
        for agent_id, quantity in agent_holdings.items()
    }

    # Find largest share
    dominant_agent = max(shares, key=shares.get)
    largest_share = shares[dominant_agent]

    # Monopoly threshold: 50%
    threshold = 0.5

    return MonopolyReport(
        resource_type=resource,
        is_monopoly=largest_share >= threshold,
        dominant_agent=dominant_agent if largest_share >= threshold else None,
        market_share=largest_share,
        threshold=threshold
    )
```

---

## Circuit Breakers

### Price Circuit Breaker

**Purpose:** Halt trading if price moves too rapidly.

```python
class CircuitBreaker:
    def __init__(
        self,
        trigger_threshold: float = 0.2,  # 20% move
        cooldown_period: timedelta = timedelta(minutes=5)
    ):
        self.trigger_threshold = trigger_threshold
        self.cooldown_period = cooldown_period
        self.last_trigger_time = None
        self.last_price = None
        self.is_tripped = False

    def check_price(self, current_price: float) -> bool:
        """Check if circuit breaker should trigger.

        Returns True if trading should halt.
        """
        if self.is_tripped:
            # Check if cooldown period passed
            if (datetime.utcnow() - self.last_trigger_time) > self.cooldown_period:
                self.is_tripped = False
                self.last_price = current_price
                return False  # Trading can resume
            else:
                return True  # Still in cooldown

        # Check for rapid price movement
        if self.last_price is not None:
            price_change = abs(current_price - self.last_price) / self.last_price

            if price_change >= self.trigger_threshold:
                self.is_tripped = True
                self.last_trigger_time = datetime.utcnow()
                return True  # Halt trading

        self.last_price = current_price
        return False
```

---

## Market Making

### System Market Maker

**Purpose:** Provide liquidity when agent participation is low.

```python
class SystemMarketMaker:
    """System-provided market maker for illiquid resources."""

    def __init__(
        self,
        max_position: float = 1000,  # Max units to hold
        spread: float = 0.05  # 5% spread
    ):
        self.max_position = max_position
        self.spread = spread
        self.inventory: dict[str, float] = {}  # resource -> quantity

    async def make_market(
        self,
        resource: str,
        fair_price: float
    ) -> tuple[float, float] | None:
        """Provide bid and ask for a resource.

        Returns (bid_price, ask_price) or None if not making market.
        """
        current_position = self.inventory.get(resource, 0)

        # Don't exceed max position
        if abs(current_position) >= self.max_position:
            return None

        # Calculate bid and ask around fair price
        bid_price = fair_price * (1 - self.spread / 2)
        ask_price = fair_price * (1 + self.spread / 2)

        return (bid_price, ask_price)
```

---

**Document Status:** DRAFT
**Next:** VALIDATION_SCENARIOS.md

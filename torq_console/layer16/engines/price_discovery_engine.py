"""TORQ Layer 16 - Price Discovery Engine

This engine determines fair value for resources through
supply-demand analysis and historical price tracking.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Literal

from ..models import (
    ResourcePrice,
    AgentMarketState,
)


# =============================================================================
# PRICE DISCOVERY ENGINE
# =============================================================================


class PriceDiscoveryEngine:
    """Engine for discovering fair market prices.

    Tracks:
    - Historical prices
    - Price trends
    - Price volatility
    - Supply-demand ratios
    """

    def __init__(self):
        """Initialize the price discovery engine."""
        self._price_history: Dict[str, List[tuple[datetime, float]]] = defaultdict(list)
        self._max_history = 100  # Keep last 100 price points
        self._base_prices: Dict[str, float] = {
            "cpu": 1.0,
            "memory": 0.5,
            "storage": 0.1,
            "network": 0.01,
            "inference": 10.0,
            "planning": 5.0,
            "execution": 2.0,
            "monitoring": 1.0,
        }

    async def discover_prices(
        self,
        market_state: AgentMarketState,
    ) -> Dict[str, ResourcePrice]:
        """Discover current prices for all resources.

        Args:
            market_state: Current market state

        Returns:
            Dictionary mapping resource type to ResourcePrice
        """
        prices = {}

        all_resources = set(
            list(market_state.resource_supply.keys()) +
            list(market_state.resource_demand.keys())
        )

        for resource in all_resources:
            price = await self._discover_resource_price(resource, market_state)
            prices[resource] = price

            # Record in history
            self._price_history[resource].append(
                (datetime.utcnow(), price.current_price)
            )
            if len(self._price_history[resource]) > self._max_history:
                self._price_history[resource].pop(0)

        return prices

    async def _discover_resource_price(
        self,
        resource_type: str,
        market_state: AgentMarketState,
    ) -> ResourcePrice:
        """Discover price for a specific resource.

        Args:
            resource_type: Type of resource
            market_state: Current market state

        Returns:
            ResourcePrice with full analysis
        """
        supply = market_state.resource_supply.get(resource_type, 0)
        demand = market_state.resource_demand.get(resource_type, 0)

        # Calculate current price based on supply/demand
        current_price = self._calculate_price_from_market(resource_type, supply, demand)

        # Get historical prices
        history = self._price_history.get(resource_type, [])

        # Calculate trend
        price_trend = self._calculate_trend(history)

        # Calculate volatility
        price_volatility = self._calculate_volatility(history)

        # Calculate ratio
        supply_demand_ratio = supply / max(demand, 0.01)

        # Calculate statistics
        prices_24h = [
            p for t, p in history
            if t > datetime.utcnow() - timedelta(hours=24)
        ]
        if prices_24h:
            avg_price_24h = sum(prices_24h) / len(prices_24h)
            min_price_24h = min(prices_24h)
            max_price_24h = max(prices_24h)
        else:
            avg_price_24h = current_price
            min_price_24h = current_price
            max_price_24h = current_price

        return ResourcePrice(
            resource_type=resource_type,
            current_price=current_price,
            price_trend=price_trend,
            price_volatility=price_volatility,
            total_supply=supply,
            total_demand=demand,
            supply_demand_ratio=supply_demand_ratio,
            avg_price_24h=avg_price_24h,
            min_price_24h=min_price_24h,
            max_price_24h=max_price_24h,
        )

    def _calculate_price_from_market(
        self,
        resource_type: str,
        supply: float,
        demand: float,
    ) -> float:
        """Calculate price from supply and demand.

        Args:
            resource_type: Type of resource
            supply: Available supply
            demand: Current demand

        Returns:
            Calculated price
        """
        base_price = self._base_prices.get(resource_type, 10.0)

        if supply == 0 and demand == 0:
            return base_price

        if supply == 0:
            # Scarcity - 10x base price
            return base_price * 10.0

        # Price inversely proportional to supply/demand ratio
        ratio = supply / max(demand, 1)

        # Use a sigmoid-like curve for smooth price adjustment
        # Ratio < 1: price increases (demand > supply)
        # Ratio > 1: price decreases (supply > demand)
        if ratio < 1:
            multiplier = 1.0 + (1.0 - ratio) * 2.0  # Up to 3x
        else:
            multiplier = 1.0 / (1.0 + (ratio - 1.0) * 0.5)  # Decreasing

        # Clamp multiplier
        multiplier = max(0.1, min(multiplier, 10.0))

        return base_price * multiplier

    def _calculate_trend(
        self,
        history: List[tuple[datetime, float]],
    ) -> Literal["rising", "stable", "falling"]:
        """Calculate price trend direction.

        Args:
            history: Price history

        Returns:
            Trend direction
        """
        if len(history) < 3:
            return "stable"

        # Get recent prices
        recent = history[-10:] if len(history) >= 10 else history
        prices = [p for _, p in recent]

        # Calculate moving average
        first_half = prices[:len(prices)//2]
        second_half = prices[len(prices)//2:]

        if not first_half or not second_half:
            return "stable"

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        # Determine trend based on 5% threshold
        if avg_second > avg_first * 1.05:
            return "rising"
        elif avg_second < avg_first * 0.95:
            return "falling"
        else:
            return "stable"

    def _calculate_volatility(
        self,
        history: List[tuple[datetime, float]],
    ) -> float:
        """Calculate price volatility.

        Args:
            history: Price history

        Returns:
            Volatility score (0.0 to 1.0)
        """
        if len(history) < 2:
            return 0.0

        prices = [p for _, p in history]

        # Calculate standard deviation relative to mean
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std = variance ** 0.5

        # Volatility is std / mean (coefficient of variation)
        # Clamp to 0-1 range
        volatility = min(1.0, (std / max(mean, 1)) * 2)

        return volatility

    async def get_price_forecast(
        self,
        resource_type: str,
        steps: int = 5,
    ) -> List[float]:
        """Generate a simple price forecast.

        Uses trend extrapolation for short-term forecasting.

        Args:
            resource_type: Type of resource
            steps: Number of steps to forecast

        Returns:
            List of forecasted prices
        """
        history = self._price_history.get(resource_type, [])

        if len(history) < 3:
            base_price = self._base_prices.get(resource_type, 10.0)
            return [base_price] * steps

        prices = [p for _, p in history]

        # Calculate trend
        recent = prices[-10:] if len(prices) >= 10 else prices
        first_avg = sum(recent[:len(recent)//2]) / max(1, len(recent)//2)
        second_avg = sum(recent[len(recent)//2:]) / max(1, len(recent) - len(recent)//2)

        trend_factor = second_avg / max(first_avg, 0.01)

        # Extrapolate
        forecast = []
        last_price = prices[-1]

        for _ in range(steps):
            # Apply trend with dampening (trend weakens over time)
            dampened_trend = 1.0 + (trend_factor - 1.0) * 0.8
            next_price = last_price * dampened_trend

            # Clamp to reasonable bounds (0.1x to 10x base)
            base = self._base_prices.get(resource_type, 10.0)
            next_price = max(base * 0.1, min(next_price, base * 10.0))

            forecast.append(next_price)
            last_price = next_price

        return forecast

    def set_base_price(self, resource_type: str, price: float):
        """Set base price for a resource.

        Args:
            resource_type: Type of resource
            price: New base price
        """
        self._base_prices[resource_type] = max(0.01, price)

    def get_base_price(self, resource_type: str) -> float:
        """Get base price for a resource.

        Args:
            resource_type: Type of resource

        Returns:
            Base price
        """
        return self._base_prices.get(resource_type, 10.0)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_price_discovery_engine() -> PriceDiscoveryEngine:
    """Factory function to create a price discovery engine.

    Returns:
        Configured PriceDiscoveryEngine instance
    """
    return PriceDiscoveryEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "PriceDiscoveryEngine",
    "create_price_discovery_engine",
]

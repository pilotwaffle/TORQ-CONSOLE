"""TORQ Layer 16 - Market Equilibrium Detector

This engine detects when the agent market stabilizes,
monitoring price variance and supply-demand balance.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List

from ..models import (
    MarketEquilibrium,
    AgentMarketState,
    ResourcePrice,
)


# =============================================================================
# MARKET EQUILIBRIUM DETECTOR
# =============================================================================


class EquilibriumDetector:
    """Engine for detecting market equilibrium.

    Monitors:
    - Price variance over time
    - Supply-demand balance
    - Market stability duration
    - Destabilizing factors
    """

    def __init__(self):
        """Initialize the equilibrium detector."""
        self._price_history: Dict[str, deque[float]] = {}
        self._supply_history: Dict[str, deque[float]] = {}
        self._demand_history: Dict[str, deque[float]] = {}
        self._stability_start: datetime | None = None
        self._last_equilibrium_state = False

        # Detection parameters
        self._history_length = 20  # Number of data points to analyze
        self._price_variance_threshold = 0.05  # 5% variance threshold
        self._balance_threshold = 0.1  # 10% balance threshold

    async def detect_equilibrium(
        self,
        market_state: AgentMarketState,
        resource_prices: Dict[str, ResourcePrice],
    ) -> MarketEquilibrium:
        """Detect if market is in equilibrium.

        Args:
            market_state: Current market state
            resource_prices: Current resource prices

        Returns:
            MarketEquilibrium assessment
        """
        # Update histories
        self._update_histories(market_state, resource_prices)

        # Calculate metrics
        price_variance = self._calculate_price_variance()
        supply_demand_balance = self._calculate_balance_score()

        # Determine stability
        stable = self._is_stable(price_variance, supply_demand_balance)

        # Update stability tracking
        if stable:
            if self._stability_start is None:
                self._stability_start = datetime.utcnow()
        else:
            self._stability_start = None

        # Calculate stable duration
        stable_for_seconds = 0.0
        if self._stability_start:
            stable_for_seconds = (datetime.utcnow() - self._stability_start).total_seconds()

        # Calculate confidence
        equilibrium_confidence = self._calculate_confidence(
            price_variance,
            supply_demand_balance,
            stable_for_seconds,
        )

        # Identify destabilizing factors
        destabilizing_factors = self._identify_destabilizing_factors(
            market_state,
            resource_prices,
        )

        # Track state change
        self._last_equilibrium_state = stable

        return MarketEquilibrium(
            stable=stable,
            price_variance=price_variance,
            price_variance_threshold=self._price_variance_threshold,
            supply_demand_balance=supply_demand_balance,
            equilibrium_confidence=equilibrium_confidence,
            stable_for_seconds=stable_for_seconds,
            destabilizing_factors=destabilizing_factors,
        )

    def _update_histories(
        self,
        market_state: AgentMarketState,
        resource_prices: Dict[str, ResourcePrice],
    ):
        """Update historical data for equilibrium detection.

        Args:
            market_state: Current market state
            resource_prices: Current resource prices
        """
        # Initialize queues if needed
        for resource in resource_prices.keys():
            if resource not in self._price_history:
                self._price_history[resource] = deque(maxlen=self._history_length)
            if resource not in self._supply_history:
                self._supply_history[resource] = deque(maxlen=self._history_length)
            if resource not in self._demand_history:
                self._demand_history[resource] = deque(maxlen=self._history_length)

        # Add current data
        for resource, price_data in resource_prices.items():
            self._price_history[resource].append(price_data.current_price)

        for resource, supply in market_state.resource_supply.items():
            self._supply_history[resource].append(supply)

        for resource, demand in market_state.resource_demand.items():
            self._demand_history[resource].append(demand)

    def _calculate_price_variance(self) -> float:
        """Calculate aggregate price variance across all resources.

        Returns:
            Average price variance (0.0 to 1.0)
        """
        if not self._price_history:
            return 0.0

        variances = []

        for resource, prices in self._price_history.items():
            if len(prices) < 2:
                continue

            # Calculate coefficient of variation
            mean = sum(prices) / len(prices)
            if mean == 0:
                continue

            variance = sum((p - mean) ** 2 for p in prices) / len(prices)
            std = variance ** 0.5
            cv = std / mean  # Coefficient of variation

            variances.append(cv)

        if not variances:
            return 0.0

        return sum(variances) / len(variances)

    def _calculate_balance_score(self) -> float:
        """Calculate supply-demand balance score.

        Returns:
            Balance score (-1.0 to 1.0)
        """
        if not self._supply_history or not self._demand_history:
            return 0.0

        balances = []

        for resource in self._supply_history.keys():
            if resource not in self._demand_history:
                continue

            supply = list(self._supply_history[resource])
            demand = list(self._demand_history[resource])

            if not supply or not demand:
                continue

            # Use latest values
            latest_supply = supply[-1]
            latest_demand = demand[-1]

            if latest_supply == 0 and latest_demand == 0:
                balance = 0.0
            elif latest_supply == 0:
                balance = -1.0  # Excess demand
            elif latest_demand == 0:
                balance = 1.0  # Excess supply
            else:
                # Calculate normalized balance
                total = latest_supply + latest_demand
                balance = (latest_supply - latest_demand) / total

            balances.append(balance)

        if not balances:
            return 0.0

        return sum(balances) / len(balances)

    def _is_stable(
        self,
        price_variance: float,
        balance_score: float,
    ) -> bool:
        """Determine if market is stable.

        Args:
            price_variance: Current price variance
            balance_score: Current balance score

        Returns:
            True if stable
        """
        # Check price variance
        if price_variance > self._price_variance_threshold:
            return False

        # Check balance (absolute value should be small)
        if abs(balance_score) > self._balance_threshold:
            return False

        return True

    def _calculate_confidence(
        self,
        price_variance: float,
        balance_score: float,
        stable_duration: float,
    ) -> float:
        """Calculate confidence in equilibrium assessment.

        Args:
            price_variance: Current price variance
            balance_score: Current balance score
            stable_duration: How long market has been stable

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Lower variance = higher confidence
        variance_factor = max(0.0, 1.0 - (price_variance / self._price_variance_threshold))
        confidence += variance_factor * 0.25

        # Better balance = higher confidence
        balance_factor = max(0.0, 1.0 - (abs(balance_score) / self._balance_threshold))
        confidence += balance_factor * 0.25

        # Longer stability = higher confidence (up to 1 hour)
        duration_factor = min(1.0, stable_duration / 3600.0)
        confidence += duration_factor * 0.2

        # Clamp to 0-1
        return max(0.0, min(1.0, confidence))

    def _identify_destabilizing_factors(
        self,
        market_state: AgentMarketState,
        resource_prices: Dict[str, ResourcePrice],
    ) -> List[str]:
        """Identify factors preventing equilibrium.

        Args:
            market_state: Current market state
            resource_prices: Current resource prices

        Returns:
            List of destabilizing factors
        """
        factors = []

        # Check for low liquidity
        if market_state.market_liquidity < 0.2:
            factors.append("Low market liquidity")

        # Check for supply-demand imbalance
        if abs(market_state.supply_demand_gap) > market_state.total_supply * 0.5:
            if market_state.supply_demand_gap > 0:
                factors.append("Significant excess supply")
            else:
                factors.append("Significant excess demand")

        # Check for high volatility
        for resource, price_data in resource_prices.items():
            if price_data.price_volatility > 0.3:
                factors.append(f"High volatility in {resource}")
                break

        # Check for few agents
        if market_state.total_agents < 3:
            factors.append("Low agent count - oligopoly risk")

        # Check for overwhelmed market
        if market_state.market_health < 0.5:
            factors.append("Poor market health")

        return factors

    async def get_stability_duration(self) -> float:
        """Get how long market has been stable.

        Returns:
            Duration in seconds
        """
        if self._stability_start is None:
            return 0.0
        return (datetime.utcnow() - self._stability_start).total_seconds()

    def set_variance_threshold(self, threshold: float):
        """Set the price variance threshold for stability.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        self._price_variance_threshold = max(0.0, min(1.0, threshold))

    def set_balance_threshold(self, threshold: float):
        """Set the supply-demand balance threshold for stability.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        self._balance_threshold = max(0.0, min(1.0, threshold))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_equilibrium_detector() -> EquilibriumDetector:
    """Factory function to create an equilibrium detector.

    Returns:
        Configured EquilibriumDetector instance
    """
    return EquilibriumDetector()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "EquilibriumDetector",
    "create_equilibrium_detector",
]

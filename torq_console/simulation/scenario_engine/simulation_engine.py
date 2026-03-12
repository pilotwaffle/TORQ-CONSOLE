"""
TORQ Layer 10 - Scenario Simulation Engine

L10-M1: Simulates mission execution, workflow changes, and capability
deployments using historical data and organizational intelligence.

The ScenarioSimulationEngine provides:
- Mission outcome simulation
- Readiness probability estimation
- Performance metric prediction
- Multi-iteration Monte Carlo simulation
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    SimulationScenario,
    SimulationResult,
    SimulationStatus,
    SimulatedMissionOutcome,
    SimulationScope,
)


# ============================================================================
# Simulation Context
# ============================================================================

@dataclass
class SimulationContext:
    """Context data for running simulations."""
    historical_success_rate: float = 0.75
    historical_avg_duration: float = 120.0
    historical_avg_quality: float = 0.80
    baseline_readiness: float = 0.70
    volatility_factor: float = 0.10

    # Mission-type specific data
    mission_type_stats: Dict[str, Dict[str, float]] = None

    # Domain-specific data
    domain_stats: Dict[str, Dict[str, float]] = None

    def __post_init__(self):
        if self.mission_type_stats is None:
            self.mission_type_stats = {
                "analysis": {"success_rate": 0.80, "duration": 100.0, "quality": 0.85},
                "code_generation": {"success_rate": 0.70, "duration": 180.0, "quality": 0.75},
                "debugging": {"success_rate": 0.65, "duration": 200.0, "quality": 0.70},
                "research": {"success_rate": 0.85, "duration": 150.0, "quality": 0.80},
            }
        if self.domain_stats is None:
            self.domain_stats = {
                "finance": {"success_rate": 0.75, "duration": 130.0, "quality": 0.78},
                "technology": {"success_rate": 0.80, "duration": 140.0, "quality": 0.82},
                "operations": {"success_rate": 0.70, "duration": 110.0, "quality": 0.75},
            }


# ============================================================================
# Scenario Simulation Engine
# ============================================================================

class ScenarioSimulationEngine:
    """
    Simulates potential future execution outcomes.

    Uses historical data and Monte Carlo simulation to predict
    mission outcomes, readiness changes, and performance metrics.
    """

    def __init__(self):
        """Initialize the simulation engine."""
        self._scenarios: Dict[UUID, SimulationScenario] = {}
        self._results: Dict[UUID, SimulationResult] = {}
        self._context = SimulationContext()

    def set_simulation_context(self, context: SimulationContext) -> None:
        """Set the simulation context data."""
        self._context = context
        logger.debug(f"[SimulationEngine] Updated simulation context")

    async def create_scenario(
        self,
        title: str,
        description: str,
        simulation_scope: SimulationScope,
        **kwargs
    ) -> SimulationScenario:
        """
        Create a new simulation scenario.

        Args:
            title: Scenario title
            description: Scenario description
            simulation_scope: Scope of simulation
            **kwargs: Additional scenario parameters

        Returns:
            Created SimulationScenario
        """
        scenario = SimulationScenario(
            title=title,
            description=description,
            simulation_scope=simulation_scope,
            **kwargs
        )
        self._scenarios[scenario.scenario_id] = scenario

        logger.info(
            f"[SimulationEngine] Created scenario '{title}' "
            f"(scope: {simulation_scope})"
        )

        return scenario

    async def run_simulation(
        self,
        scenario_id: UUID,
        context_override: Optional[SimulationContext] = None,
    ) -> SimulationResult:
        """
        Run a simulation scenario.

        Args:
            scenario_id: ID of scenario to simulate
            context_override: Optional context override

        Returns:
            SimulationResult with predictions
        """
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        context = context_override or self._context

        # Create result
        result = SimulationResult(
            scenario_id=scenario_id,
            status=SimulationStatus.RUNNING,
            started_at=datetime.now(),
        )
        self._results[result.result_id] = result

        logger.info(
            f"[SimulationEngine] Running simulation '{scenario.title}' "
            f"({scenario.iterations} iterations)"
        )

        # Run simulation based on scope
        if scenario.simulation_scope == SimulationScope.SINGLE_MISSION:
            await self._simulate_single_mission(scenario, result, context)
        elif scenario.simulation_scope == SimulationScope.MISSION_TYPE:
            await self._simulate_mission_type(scenario, result, context)
        elif scenario.simulation_scope == SimulationScope.POLICY_CHANGE:
            await self._simulate_policy_change(scenario, result, context)
        else:
            await self._simulate_generic(scenario, result, context)

        # Calculate aggregate metrics
        self._calculate_aggregates(result)

        # Update result
        result.status = SimulationStatus.COMPLETED
        result.completed_at = datetime.now()
        result.confidence = self._calculate_confidence(result, scenario)

        logger.info(
            f"[SimulationEngine] Simulation complete: "
            f"{result.success_rate:.2%} success rate"
        )

        return result

    async def _simulate_single_mission(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
        context: SimulationContext,
    ) -> None:
        """Simulate a single mission across multiple iterations."""
        mission_id = scenario.target_mission_id or "simulated_mission"
        mission_type = scenario.parameters.get("mission_type", "analysis")
        domain = scenario.parameters.get("domain", "general")

        # Get baseline stats
        type_stats = context.mission_type_stats.get(mission_type, {})
        domain_stats = context.domain_stats.get(domain, {})

        base_success_rate = (
            type_stats.get("success_rate", context.historical_success_rate) *
            domain_stats.get("success_rate", 1.0)
        )
        base_duration = (
            type_stats.get("duration", context.historical_avg_duration) *
            domain_stats.get("duration", 1.0) / context.historical_avg_duration
        )
        base_quality = (
            type_stats.get("quality", context.historical_avg_quality) *
            domain_stats.get("quality", 1.0) / context.historical_avg_quality
        )

        # Apply readiness modifier from parameters
        readiness_modifier = scenario.parameters.get("readiness_modifier", 0.0)
        effective_readiness = context.baseline_readiness + readiness_modifier

        # Run iterations
        outcomes = []
        for i in range(scenario.iterations):
            outcome = self._simulate_iteration(
                mission_id,
                base_success_rate,
                base_duration,
                base_quality,
                effective_readiness,
                context.volatility_factor,
            )
            outcomes.append(outcome)

        result.mission_outcomes = outcomes

    async def _simulate_mission_type(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
        context: SimulationContext,
    ) -> None:
        """Simulate all missions of a given type."""
        mission_type = scenario.parameters.get("mission_type", "analysis")

        type_stats = context.mission_type_stats.get(mission_type, {})
        base_success_rate = type_stats.get("success_rate", context.historical_success_rate)
        base_duration = type_stats.get("duration", context.historical_avg_duration)
        base_quality = type_stats.get("quality", context.historical_avg_quality)

        # Simulate multiple representative missions
        outcomes = []
        for i in range(min(scenario.iterations, 100)):
            mission_id = f"{mission_type}_mission_{i+1}"
            outcome = self._simulate_iteration(
                mission_id,
                base_success_rate,
                base_duration,
                base_quality,
                context.baseline_readiness,
                context.volatility_factor,
            )
            outcomes.append(outcome)

        result.mission_outcomes = outcomes

    async def _simulate_policy_change(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
        context: SimulationContext,
    ) -> None:
        """Simulate the impact of a policy change."""
        # Extract policy parameters
        new_readiness_threshold = scenario.parameters.get("new_readiness_threshold", 0.8)
        current_threshold = scenario.parameters.get("current_threshold", 0.7)

        # Simulate missions under new policy
        outcomes = []
        for i in range(scenario.iterations):
            mission_id = f"policy_sim_mission_{i+1}"

            # Under stricter policy, readiness is effectively lower
            effective_readiness = context.baseline_readiness * (current_threshold / new_readiness_threshold)

            outcome = self._simulate_iteration(
                mission_id,
                context.historical_success_rate,
                context.historical_avg_duration,
                context.historical_avg_quality,
                effective_readiness,
                context.volatility_factor,
            )
            outcomes.append(outcome)

        result.mission_outcomes = outcomes

        # Store policy-specific predictions
        result.predicted_outcomes["promotion_rate_change"] = (
            (new_readiness_threshold - current_threshold)
        )

    async def _simulate_generic(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
        context: SimulationContext,
    ) -> None:
        """Run a generic simulation."""
        # Use scenario parameters to modify baseline
        success_modifier = scenario.parameters.get("success_modifier", 0.0)
        duration_modifier = scenario.parameters.get("duration_modifier", 1.0)
        quality_modifier = scenario.parameters.get("quality_modifier", 0.0)

        base_success_rate = context.historical_success_rate + success_modifier
        base_duration = context.historical_avg_duration * duration_modifier
        base_quality = context.historical_avg_quality + quality_modifier

        outcomes = []
        for i in range(scenario.iterations):
            mission_id = f"generic_sim_{i+1}"
            outcome = self._simulate_iteration(
                mission_id,
                base_success_rate,
                base_duration,
                base_quality,
                context.baseline_readiness,
                context.volatility_factor,
            )
            outcomes.append(outcome)

        result.mission_outcomes = outcomes

    def _simulate_iteration(
        self,
        mission_id: str,
        base_success_rate: float,
        base_duration: float,
        base_quality: float,
        readiness: float,
        volatility: float,
    ) -> SimulatedMissionOutcome:
        """
        Simulate a single mission iteration.

        Uses probabilistic modeling based on historical data and current readiness.
        """
        # Readiness affects success probability
        success_prob = base_success_rate * (0.5 + 0.5 * readiness)

        # Add volatility
        success_prob = max(0.0, min(1.0, success_prob + random.uniform(-volatility, volatility)))

        # Determine success
        success = random.random() < success_prob

        # Simulate duration (log-normal distribution)
        duration_factor = random.lognormvariate(0, volatility)
        duration = base_duration * duration_factor

        # Simulate quality (normally distributed)
        quality = base_quality + random.gauss(0, volatility * 0.5)
        quality = max(0.0, min(1.0, quality))

        # Confidence based on readiness
        confidence = readiness

        return SimulatedMissionOutcome(
            mission_id=mission_id,
            success=success,
            success_probability=success_prob,
            expected_duration=duration,
            expected_quality=quality,
            expected_token_usage=int(duration * 10),  # Rough estimate
            readiness_at_execution=readiness,
            confidence=confidence,
        )

    def _calculate_aggregates(self, result: SimulationResult) -> None:
        """Calculate aggregate metrics from simulation outcomes."""
        if not result.mission_outcomes:
            return

        result.total_simulations = len(result.mission_outcomes)

        # Success rate
        successes = sum(1 for o in result.mission_outcomes if o.success)
        result.success_rate = successes / result.total_simulations

        # Average duration and quality
        result.avg_duration = sum(o.expected_duration for o in result.mission_outcomes) / result.total_simulations
        result.avg_quality = sum(o.expected_quality for o in result.mission_outcomes) / result.total_simulations

        # Readiness forecast
        ready_count = sum(1 for o in result.mission_outcomes if o.readiness_at_execution >= 0.7)
        result.readiness_forecast["ready_probability"] = ready_count / result.total_simulations
        result.readiness_forecast["avg_readiness"] = sum(
            o.readiness_at_execution for o in result.mission_outcomes
        ) / result.total_simulations

        # Risk scores
        result.risk_scores["execution_risk"] = 1.0 - result.success_rate
        result.risk_scores["quality_risk"] = max(0, 0.8 - result.avg_quality) / 0.8

        # Predicted outcomes
        result.predicted_outcomes["success_rate"] = result.success_rate
        result.predicted_outcomes["avg_duration"] = result.avg_duration
        result.predicted_outcomes["avg_quality"] = result.avg_quality

    def _calculate_confidence(
        self,
        result: SimulationResult,
        scenario: SimulationScenario,
    ) -> float:
        """Calculate confidence in simulation results."""
        # Base confidence on iteration count
        iteration_confidence = min(1.0, scenario.iterations / 1000.0)

        # Adjust by outcome variance
        if result.mission_outcomes:
            success_variance = sum(
                (o.success_probability - result.success_rate) ** 2
                for o in result.mission_outcomes
            ) / result.total_simulations
            variance_penalty = min(0.3, success_variance)
            iteration_confidence -= variance_penalty

        return max(0.1, min(0.95, iteration_confidence))

    def get_scenario(self, scenario_id: UUID) -> Optional[SimulationScenario]:
        """Get a scenario by ID."""
        return self._scenarios.get(scenario_id)

    def get_result(self, result_id: UUID) -> Optional[SimulationResult]:
        """Get a result by ID."""
        return self._results.get(result_id)

    def list_scenarios(self) -> List[SimulationScenario]:
        """List all scenarios."""
        return list(self._scenarios.values())

    def list_results(self) -> List[SimulationResult]:
        """List all results."""
        return list(self._results.values())


# Global simulation engine instance
_engine: Optional[ScenarioSimulationEngine] = None


def get_simulation_engine() -> ScenarioSimulationEngine:
    """Get the global scenario simulation engine instance."""
    global _engine
    if _engine is None:
        _engine = ScenarioSimulationEngine()
    return _engine

"""
TORQ Layer 10: Strategic Simulation & Decision Forecasting

L10-M1: Enables scenario modeling, policy simulation, strategic forecasting,
and risk assessment for predictive intelligence.

This module provides:
- ScenarioSimulationEngine: Simulate missions, workflows, and capability changes
- PolicyImpactSimulator: Test governance and policy changes safely
- StrategicForecastingEngine: Predict long-term system and organizational outcomes
- RiskModelingService: Quantify operational and strategic risks
- PlanningWorkspaceService: Collaborative scenario planning environment
"""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


# Import models
from .models import (
    # Simulation Scenario
    SimulationScope,
    SimulationStatus,
    SimulationParameter,
    SimulationScenario,
    SimulatedMissionOutcome,
    SimulationResult,
    # Policy Impact
    PolicyChangeType,
    PolicyImpactReport,
    PolicySimulationConfig,
    # Strategic Forecasting
    ForecastType,
    ForecastTrendDirection,
    ForecastDataPoint,
    StrategicForecast,
    # Risk Modeling
    RiskCategory,
    RiskSeverity,
    RiskMitigation,
    RiskAssessment,
    RiskModelReport,
    # Planning Workspace
    PlanningSessionStatus,
    ScenarioComparison,
    PlanningSession,
    # Factory functions
    create_simulation_scenario,
    create_policy_impact_report,
    create_strategic_forecast,
    create_risk_assessment,
    create_planning_session,
    # Enum accessors
    get_all_simulation_scopes,
    get_all_policy_change_types,
    get_all_forecast_types,
    get_all_risk_categories,
    get_all_risk_severities,
)


# Import services
from .scenario_engine.simulation_engine import (
    ScenarioSimulationEngine,
    get_simulation_engine,
)
from .policy_simulation.policy_simulator import (
    PolicyImpactSimulator,
    get_policy_simulator,
)
from .forecasting.forecasting_engine import (
    StrategicForecastingEngine,
    get_forecasting_engine,
)
from .risk_modeling.risk_service import (
    RiskModelingService,
    get_risk_service,
)
from .planning_workspace.planning_workspace_service import (
    PlanningWorkspaceService,
    get_planning_workspace,
)


__all__ = [
    # Models
    "SimulationScope",
    "SimulationStatus",
    "SimulationParameter",
    "SimulationScenario",
    "SimulatedMissionOutcome",
    "SimulationResult",
    "PolicyChangeType",
    "PolicyImpactReport",
    "PolicySimulationConfig",
    "ForecastType",
    "ForecastTrendDirection",
    "ForecastDataPoint",
    "StrategicForecast",
    "RiskCategory",
    "RiskSeverity",
    "RiskMitigation",
    "RiskAssessment",
    "RiskModelReport",
    "PlanningSessionStatus",
    "ScenarioComparison",
    "PlanningSession",
    # Factory functions
    "create_simulation_scenario",
    "create_policy_impact_report",
    "create_strategic_forecast",
    "create_risk_assessment",
    "create_planning_session",
    # Enum accessors
    "get_all_simulation_scopes",
    "get_all_policy_change_types",
    "get_all_forecast_types",
    "get_all_risk_categories",
    "get_all_risk_severities",
    # Services
    "ScenarioSimulationEngine",
    "PolicyImpactSimulator",
    "StrategicForecastingEngine",
    "RiskModelingService",
    "PlanningWorkspaceService",
    "get_simulation_engine",
    "get_policy_simulator",
    "get_forecasting_engine",
    "get_risk_service",
    "get_planning_workspace",
]


def get_layer10_services() -> dict:
    """Get all Layer 10 services for integration."""
    return {
        "simulation_engine": get_simulation_engine(),
        "policy_simulator": get_policy_simulator(),
        "forecasting_engine": get_forecasting_engine(),
        "risk_service": get_risk_service(),
        "planning_workspace": get_planning_workspace(),
    }


# Version info
__version__ = "1.0.0"

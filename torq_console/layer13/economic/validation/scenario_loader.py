"""TORQ Layer 13 - Scenario Loader

This module loads validation scenarios from JSON files or built-in definitions.
"""

import json
from pathlib import Path
from typing import Any

from .scenario_definitions import (
    ScenarioDefinition,
    get_all_scenarios,
    get_scenario_by_name,
)


class ScenarioLoader:
    """Loads validation scenarios from files or built-in definitions."""

    def __init__(self, base_path: str | None = None):
        """Initialize the scenario loader.

        Args:
            base_path: Base path for scenario files (default: tests/layer13/scenarios/)
        """
        if base_path is None:
            base_path = "tests/layer13/scenarios"
        self.base_path = Path(base_path)

    def load_scenario(self, name: str) -> ScenarioDefinition | None:
        """Load a scenario from file or built-in definitions.

        Args:
            name: Scenario name (with or without .json extension)

        Returns:
            ScenarioDefinition or None if not found
        """
        # Try loading from file first
        file_path = self.base_path / f"{name}.json"

        if file_path.exists():
            return self._load_from_file(file_path)

        # Fall back to built-in definitions
        return get_scenario_by_name(name)

    def load_all_scenarios(self) -> dict[str, ScenarioDefinition]:
        """Load all scenarios from files and built-in definitions.

        Returns:
            Dictionary mapping scenario names to ScenarioDefinition instances
        """
        scenarios = get_all_scenarios()

        # Override with any file-based scenarios
        if self.base_path.exists():
            for file_path in self.base_path.glob("*.json"):
                try:
                    with open(file_path) as f:
                        scenario = self._load_from_file(file_path)
                        scenarios[scenario.name] = scenario
                except Exception:
                    # Skip invalid files
                    continue

        return scenarios

    def _load_from_file(self, file_path: Path) -> ScenarioDefinition:
        """Load a scenario from a JSON file.

        Args:
            file_path: Path to scenario JSON file

        Returns:
            ScenarioDefinition instance
        """
        with open(file_path) as f:
            data = json.load(f)

        return self._from_dict(data)

    def save_scenario(self, scenario: ScenarioDefinition, path: str | None = None):
        """Save a scenario to a JSON file.

        Args:
            scenario: ScenarioDefinition to save
            path: Output file path (default: base_path/{name}.json)
        """
        if path is None:
            path = self.base_path / f"{scenario.name}.json"
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._to_dict(scenario), f, indent=2)

    def _from_dict(self, data: dict[str, Any]) -> ScenarioDefinition:
        """Convert dictionary to ScenarioDefinition.

        Args:
            data: Dictionary with scenario data

        Returns:
            ScenarioDefinition instance
        """
        from ..models import (
            EconomicConfiguration,
            FederationResult,
            MissionProposal,
            ResourceConstraints,
        )
        from .scenario_definitions import ScenarioExpectation

        # Parse proposals
        proposals = [
            MissionProposal(**p) for p in data.get("proposals", [])
        ]

        # Parse constraints
        constraints_data = data.get("constraints", {})
        constraints = ResourceConstraints(**constraints_data)

        # Parse federation results
        federation_results = {}
        for mission_id, fr_data in data.get("federation_results", {}).items():
            federation_results[mission_id] = FederationResult(**fr_data)

        # Parse expected results
        expected = None
        if "expected" in data:
            exp_data = data["expected"]
            expected = ScenarioExpectation(
                funded_mission_ids=set(exp_data.get("funded_mission_ids", set())),
                queued_mission_ids=set(exp_data.get("queued_mission_ids", set())),
                rejected_mission_ids=set(exp_data.get("rejected_mission_ids", set())),
                min_budget_utilization=exp_data.get("min_budget_utilization", 0.85),
                max_budget_utilization=exp_data.get("max_budget_utilization", 1.0),
                min_allocation_efficiency=exp_data.get("min_allocation_efficiency", 0.0),
                max_regret_ratio=exp_data.get("max_regret_ratio", 0.15),
            )

        # Parse configuration
        config_data = data.get("configuration", {})
        configuration = EconomicConfiguration(**config_data)

        return ScenarioDefinition(
            name=data["name"],
            description=data["description"],
            budget=data["budget"],
            proposals=proposals,
            constraints=constraints,
            federation_results=federation_results,
            expected=expected,
            configuration=configuration,
        )

    def _to_dict(self, scenario: ScenarioDefinition) -> dict[str, Any]:
        """Convert ScenarioDefinition to dictionary.

        Args:
            scenario: ScenarioDefinition to convert

        Returns:
            Dictionary representation
        """
        result = {
            "name": scenario.name,
            "description": scenario.description,
            "budget": scenario.budget,
            "proposals": [p.model_dump() for p in scenario.proposals],
            "constraints": scenario.constraints.model_dump(),
            "federation_results": {
                k: v.model_dump() for k, v in scenario.federation_results.items()
            },
            "configuration": scenario.configuration.model_dump(),
        }

        if scenario.expected is not None:
            result["expected"] = {
                "funded_mission_ids": list(scenario.expected.funded_mission_ids),
                "queued_mission_ids": list(scenario.expected.queued_mission_ids),
                "rejected_mission_ids": list(scenario.expected.rejected_mission_ids),
                "min_budget_utilization": scenario.expected.min_budget_utilization,
                "max_budget_utilization": scenario.expected.max_budget_utilization,
                "min_allocation_efficiency": scenario.expected.min_allocation_efficiency,
                "max_regret_ratio": scenario.expected.max_regret_ratio,
            }

        return result


__all__ = [
    "ScenarioLoader",
]

"""
Experiment Assignment Engine

Deterministic hash-based traffic assignment for A/B experiments.
Ensures stable, reproducible assignment with full traceability.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Literal, Optional

from .models import (
    AssignmentConfig,
    AssignmentMode,
)


logger = logging.getLogger(__name__)


class ExperimentAssigner:
    """
    Deterministic traffic assignment for experiments.

    Uses hash-based assignment to ensure:
    - Same execution always gets same variant
    - Reproducible assignment
    - Explainable decisions
    """

    def assign(
        self,
        experiment_id: str,
        execution_id: str,
        config: AssignmentConfig,
        context: Optional[dict] = None
    ) -> tuple[Literal["control", "candidate"], str]:
        """
        Determine which variant an execution should receive.

        Returns:
            (variant_name, assignment_reason)
        """
        if config.mode == AssignmentMode.PERCENTAGE_HASH:
            return self._assign_percentage_hash(
                experiment_id, execution_id, config
            )

        elif config.mode == AssignmentMode.WORKFLOW_TYPE:
            return self._assign_workflow_type(
                experiment_id, execution_id, config, context or {}
            )

        elif config.mode == AssignmentMode.TENANT_SCOPE:
            return self._assign_tenant_scope(
                experiment_id, execution_id, config, context or {}
            )

        else:
            logger.warning(f"Unknown assignment mode: {config.mode}, defaulting to control")
            return "control", "unknown_mode"

    def _assign_percentage_hash(
        self,
        experiment_id: str,
        execution_id: str,
        config: AssignmentConfig
    ) -> tuple[Literal["control", "candidate"], str]:
        """
        Hash-based percentage assignment.

        Maps hash(experiment_id + execution_id) to 0-99 bucket.
        If bucket < candidate_percent, assign candidate.
        """
        # Create deterministic hash
        hash_input = f"{experiment_id}:{execution_id}"
        if config.hash_seed:
            hash_input = f"{hash_input}:{config.hash_seed}"

        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        if bucket < config.candidate_percent:
            return "candidate", f"hash_bucket_{bucket}_lt_{config.candidate_percent}"
        else:
            return "control", f"hash_bucket_{bucket}_gte_{config.candidate_percent}"

    def _assign_workflow_type(
        self,
        experiment_id: str,
        execution_id: str,
        config: AssignmentConfig,
        context: dict
    ) -> tuple[Literal["control", "candidate"], str]:
        """
        Assignment by workflow type.

        If workflow_type is in the configured list, use percentage assignment.
        Otherwise, always assign to control.
        """
        workflow_type = context.get("workflow_type") or context.get("workflow_id", "")

        if not config.workflow_types:
            return "control", "no_workflow_types_configured"

        if workflow_type not in config.workflow_types:
            return "control", f"workflow_type_{workflow_type}_not_in_scope"

        # Within scope, use hash-based assignment
        return self._assign_percentage_hash(
            experiment_id, execution_id, config
        )

    def _assign_tenant_scope(
        self,
        experiment_id: str,
        execution_id: str,
        config: AssignmentConfig,
        context: dict
    ) -> tuple[Literal["control", "candidate"], str]:
        """
        Assignment by tenant/environment scope.

        If tenant is in the configured list, use percentage assignment.
        Otherwise, always assign to control.
        """
        tenant = context.get("tenant_id") or context.get("tenant", "default")

        if not config.tenants:
            return "control", "no_tenants_configured"

        if tenant not in config.tenants:
            return "control", f"tenant_{tenant}_not_in_scope"

        # Within scope, use hash-based assignment
        return self._assign_percentage_hash(
            experiment_id, execution_id, config
        )


class AssignmentValidator:
    """Validates assignment configurations and prevents overlapping experiments."""

    def __init__(self):
        self.active_experiments_by_asset: dict[str, list[str]] = {}

    def can_create_experiment(
        self,
        asset_key: str,
        asset_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an experiment can be created for this asset.

        Prevents overlapping experiments on the same asset.
        """
        active = self.active_experiments_by_asset.get(asset_key, [])

        if active:
            return False, f"Asset {asset_key} already has {len(active)} active experiment(s)"

        return True, None

    def register_experiment(self, asset_key: str, experiment_id: str):
        """Register an active experiment."""
        if asset_key not in self.active_experiments_by_asset:
            self.active_experiments_by_asset[asset_key] = []
        self.active_experiments_by_asset[asset_key].append(experiment_id)

    def unregister_experiment(self, asset_key: str, experiment_id: str):
        """Unregister a completed/rolled back experiment."""
        if asset_key in self.active_experiments_by_asset:
            if experiment_id in self.active_experiments_by_asset[asset_key]:
                self.active_experiments_by_asset[asset_key].remove(experiment_id)

            if not self.active_experiments_by_asset[asset_key]:
                del self.active_experiments_by_asset[asset_key]


def compute_assignment_hash(
    experiment_id: str,
    execution_id: str,
    seed: Optional[str] = None
) -> int:
    """
    Compute a deterministic assignment hash.

    Returns a value 0-99 for percentage-based assignment.
    """
    hash_input = f"{experiment_id}:{execution_id}"
    if seed:
        hash_input = f"{hash_input}:{seed}"

    return int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % 100

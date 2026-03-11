"""
Behavior Experiment Service

Orchestrates the experiment lifecycle:
create → start → assign → analyze → promote/rollback
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    BehaviorVersionCreate,
    BehaviorVersionRead,
    BehaviorExperimentCreate,
    BehaviorExperimentRead,
    ExperimentStatus,
    BehaviorVersionStatus,
    AssignmentConfig,
    AssignmentRequest,
    AssignmentResponse,
    ExperimentImpactSummary,
    PromotionDecision,
    RollbackDecision,
)
from .assigner import ExperimentAssigner, AssignmentValidator
from .analyzer import ExperimentImpactAnalyzer


logger = logging.getLogger(__name__)


class BehaviorExperimentService:
    """
    Service for managing behavior experiments.

    Lifecycle:
    1. Approved proposal → create candidate behavior version
    2. Identify current active version as control
    3. Create experiment with control/candidate
    4. Start experiment → begin assignment
    5. Analyze results → generate impact summary
    6. Promote or rollback
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.assigner = ExperimentAssigner()
        self.validator = AssignmentValidator()
        self.analyzer = ExperimentImpactAnalyzer(supabase_client)

    # ========================================================================
    # Behavior Version Management
    # ========================================================================

    async def create_behavior_version(
        self,
        version: BehaviorVersionCreate
    ) -> Optional[BehaviorVersionRead]:
        """Create a new behavior version."""
        try:
            payload = version.model_dump()
            payload["id"] = str(uuid.uuid4())
            payload["status"] = BehaviorVersionStatus.DRAFT.value
            payload["created_at"] = datetime.now().isoformat()

            result = self.supabase.table("behavior_versions").insert(payload).execute()

            if result.data:
                return BehaviorVersionRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error creating behavior version: {e}")

        return None

    async def get_behavior_version(self, version_id: str) -> Optional[BehaviorVersionRead]:
        """Get a behavior version by ID."""
        try:
            result = self.supabase.table("behavior_versions").select("*").eq("id", version_id).limit(1).execute()

            if result.data:
                return BehaviorVersionRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error fetching behavior version: {e}")

        return None

    async def get_active_version(
        self,
        asset_type: str,
        asset_key: str
    ) -> Optional[BehaviorVersionRead]:
        """Get the currently active version for an asset."""
        try:
            result = self.supabase.table("behavior_versions").select("*").eq("asset_type", asset_type).eq("asset_key", asset_key).eq("status", "active").limit(1).execute()

            if result.data:
                return BehaviorVersionRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error fetching active version: {e}")

        return None

    async def set_active_version(
        self,
        version_id: str,
        previous_version_id: Optional[str] = None
    ) -> bool:
        """
        Set a behavior version as active.

        Deactivates the previous active version and activates the new one.
        """
        try:
            version = await self.get_behavior_version(version_id)
            if not version:
                return False

            # Deactivate previous active version for this asset
            await self.supabase.table("behavior_versions").update({
                "status": BehaviorVersionStatus.ARCHIVED.value
            }).eq("asset_type", version.asset_type.value).eq("asset_key", version.asset_key).eq("status", "active").execute()

            # Activate new version
            await self.supabase.table("behavior_versions").update({
                "status": BehaviorVersionStatus.ACTIVE.value
            }).eq("id", version_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error setting active version: {e}")
            return False

    # ========================================================================
    # Experiment Management
    # ========================================================================

    async def create_experiment(
        self,
        experiment: BehaviorExperimentCreate
    ) -> Optional[BehaviorExperimentRead]:
        """
        Create a new experiment from an approved proposal.

        Validates:
        - No overlapping experiments for the asset
        - Control and candidate versions exist
        """
        # Check for overlapping experiments
        can_create, reason = self.validator.can_create_experiment(
            experiment.asset_key, experiment.asset_type.value
        )

        if not can_create:
            logger.warning(f"Cannot create experiment: {reason}")
            return None

        # Verify versions exist
        control = await self.get_behavior_version(experiment.control_version_id)
        candidate = await self.get_behavior_version(experiment.candidate_version_id)

        if not control:
            logger.error(f"Control version not found: {experiment.control_version_id}")
            return None

        if not candidate:
            logger.error(f"Candidate version not found: {experiment.candidate_version_id}")
            return None

        # Create experiment
        try:
            payload = experiment.model_dump()
            payload["id"] = str(uuid.uuid4())
            payload["status"] = ExperimentStatus.DRAFT.value
            payload["created_at"] = datetime.now().isoformat()

            result = self.supabase.table("behavior_experiments").insert(payload).execute()

            if result.data:
                exp_data = result.data[0]
                exp_read = BehaviorExperimentRead.model_validate(exp_data)

                # Register active experiment
                self.validator.register_experiment(experiment.asset_key, exp_read.id)

                # Update candidate version status
                await self.supabase.table("behavior_versions").update({
                    "status": BehaviorVersionStatus.CANDIDATE.value
                }).eq("id", experiment.candidate_version_id).execute()

                return exp_read

        except Exception as e:
            logger.error(f"Error creating experiment: {e}")

        return None

    async def start_experiment(
        self,
        experiment_id: str
    ) -> Optional[BehaviorExperimentRead]:
        """Start an experiment, beginning assignment."""
        try:
            now = datetime.now().isoformat()

            result = self.supabase.table("behavior_experiments").update({
                "status": ExperimentStatus.RUNNING.value,
                "started_at": now
            }).eq("id", experiment_id).execute()

            if result.data:
                return BehaviorExperimentRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error starting experiment: {e}")

        return None

    async def get_experiment(self, experiment_id: str) -> Optional[BehaviorExperimentRead]:
        """Get experiment details."""
        try:
            result = self.supabase.table("behavior_experiments").select("*").eq("id", experiment_id).limit(1).execute()

            if result.data:
                return BehaviorExperimentRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error fetching experiment: {e}")

        return None

    async def list_experiments(
        self,
        asset_key: Optional[str] = None,
        status: Optional[ExperimentStatus] = None,
        limit: int = 100
    ) -> List[BehaviorExperimentRead]:
        """List experiments with filters."""
        try:
            query = self.supabase.table("behavior_experiments").select("*")

            if asset_key:
                query = query.eq("asset_key", asset_key)
            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()

            experiments = []
            for item in result.data or []:
                try:
                    experiments.append(BehaviorExperimentRead.model_validate(item))
                except Exception:
                    continue

            return experiments

        except Exception as e:
            logger.error(f"Error listing experiments: {e}")
            return []

    # ========================================================================
    # Assignment
    # ========================================================================

    async def assign_execution(
        self,
        request: AssignmentRequest
    ) -> Optional[AssignmentResponse]:
        """
        Determine which variant an execution should receive.

        Records the assignment for traceability and returns the
        appropriate behavior content.
        """
        # Fetch experiment
        experiment = await self.get_experiment(request.experiment_id)
        if not experiment:
            logger.warning(f"Experiment not found: {request.experiment_id}")
            return None

        if experiment.status != ExperimentStatus.RUNNING:
            logger.warning(f"Experiment not running: {request.experiment_id}")
            return None

        # Determine assignment
        variant, reason = self.assigner.assign(
            experiment.id,
            request.execution_id,
            experiment.assignment_config,
            request.context
        )

        # Get behavior version ID
        if variant == "control":
            version_id = experiment.control_version_id
        else:
            version_id = experiment.candidate_version_id

        # Fetch behavior content
        version = await self.get_behavior_version(version_id)
        if not version:
            logger.error(f"Behavior version not found: {version_id}")
            return None

        # Record assignment
        await self._record_assignment(
            experiment.id,
            request.execution_id,
            variant,
            version_id,
            reason
        )

        return AssignmentResponse(
            experiment_id=experiment.id,
            execution_id=request.execution_id,
            assigned_variant=variant,
            behavior_version_id=version.id,
            behavior_content=version.content
        )

    async def _record_assignment(
        self,
        experiment_id: str,
        execution_id: str,
        variant: str,
        version_id: str,
        reason: str
    ):
        """Record an assignment for traceability."""
        try:
            self.supabase.table("experiment_assignments").insert({
                "id": str(uuid.uuid4()),
                "experiment_id": experiment_id,
                "execution_id": execution_id,
                "assigned_variant": variant,
                "behavior_version_id": version_id,
                "assignment_reason": reason,
                "created_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error recording assignment: {e}")

    # ========================================================================
    # Analysis and Promotion
    # ========================================================================

    async def analyze_experiment(
        self,
        experiment_id: str
    ) -> Optional[ExperimentImpactSummary]:
        """Generate impact summary for an experiment."""
        return await self.analyzer.analyze_experiment(experiment_id)

    async def promote_experiment(
        self,
        decision: PromotionDecision
    ) -> bool:
        """
        Promote the candidate version to production.

        Sets candidate as active, archives control.
        """
        try:
            experiment = await self.get_experiment(decision.experiment_id)
            if not experiment:
                return False

            # Set candidate as active
            success = await self.set_active_version(
                experiment.candidate_version_id,
                experiment.control_version_id
            )

            if not success:
                return False

            # Update experiment status
            now = datetime.now().isoformat()
            self.supabase.table("behavior_experiments").update({
                "status": ExperimentStatus.PROMOTED.value,
                "completed_at": now,
                "promoted_at": now
            }).eq("id", decision.experiment_id).execute()

            # Unregister active experiment
            self.validator.unregister_experiment(experiment.asset_key, decision.experiment_id)

            logger.info(f"Promoted experiment {decision.experiment_id}: {decision.promotion_reason}")
            return True

        except Exception as e:
            logger.error(f"Error promoting experiment: {e}")
            return False

    async def rollback_experiment(
        self,
        decision: RollbackDecision
    ) -> bool:
        """
        Rollback an experiment.

        Ensures control version is active.
        """
        try:
            experiment = await self.get_experiment(decision.experiment_id)
            if not experiment:
                return False

            # Ensure control is active
            success = await self.set_active_version(
                experiment.control_version_id
            )

            if not success:
                return False

            # Update experiment status
            now = datetime.now().isoformat()
            self.supabase.table("behavior_experiments").update({
                "status": ExperimentStatus.ROLLED_BACK.value,
                "completed_at": now,
                "rolled_back_at": now
            }).eq("id", decision.experiment_id).execute()

            # Unregister active experiment
            self.validator.unregister_experiment(experiment.asset_key, decision.experiment_id)

            logger.info(f"Rolled back experiment {decision.experiment_id}: {decision.rollback_reason}")
            return True

        except Exception as e:
            logger.error(f"Error rolling back experiment: {e}")
            return False

    # ========================================================================
    # Proposal Integration
    # ========================================================================

    async def create_experiment_from_proposal(
        self,
        proposal_id: str,
        hypothesis: Optional[str] = None
    ) -> Optional[BehaviorExperimentRead]:
        """
        Create an experiment from an approved adaptation proposal.

        This is the main integration point with the Adaptation Policy Engine.
        """
        # Fetch proposal
        try:
            result = self.supabase.table("adaptation_proposals").select("*").eq("proposal_id", proposal_id).limit(1).execute()

            if not result.data:
                logger.error(f"Proposal not found: {proposal_id}")
                return None

            proposal = result.data[0]

        except Exception as e:
            logger.error(f"Error fetching proposal: {e}")
            return None

        # Get current active version (control)
        active_version = await self.get_active_version(
            proposal.get("target_asset_type", "agent_prompt"),
            proposal.get("target_key", "default")
        )

        if not active_version:
            logger.warning(f"No active version found for {proposal.get('target_key')}")
            return None

        # Create candidate version from proposal
        candidate_version = BehaviorVersionCreate(
            asset_type=proposal.get("target_asset_type", "agent_prompt"),
            asset_key=proposal.get("target_key", "default"),
            version=proposal.get("candidate_version", f"candidate_{datetime.now().strftime('%Y%m%d')}"),
            content=proposal.get("proposed_change", {}),
            created_from_proposal_id=proposal_id,
            parent_version_id=active_version.id
        )

        candidate = await self.create_behavior_version(candidate_version)
        if not candidate:
            return None

        # Determine success metrics based on adaptation type
        success_metrics = self._default_success_metrics_for_type(
            proposal.get("adaptation_type", "prompt_revision")
        )

        # Create experiment
        experiment = BehaviorExperimentCreate(
            proposal_id=proposal_id,
            asset_type=proposal.get("target_asset_type", "agent_prompt"),
            asset_key=proposal.get("target_key", "default"),
            control_version_id=active_version.id,
            candidate_version_id=candidate.id,
            hypothesis=hypothesis or proposal.get("change_description", "Test candidate behavior"),
            assignment_config=AssignmentConfig(
                mode="percentage_hash",
                candidate_percent=20  # Start with 20% traffic
            ),
            success_metrics=success_metrics,
            minimum_sample_size=30
        )

        return await self.create_experiment(experiment)

    def _default_success_metrics_for_type(self, adaptation_type: str) -> Dict:
        """Get default success metrics for an adaptation type."""
        # Base promotion rule
        promotion_rule = {
            "primary_metric_min_improvement": 0.05,
            "minimum_sample_size": 30,
            "confidence_threshold": 0.90
        }

        if "prompt" in adaptation_type:
            return {
                "primary_metric": "coherence_score",
                "guardrails": [
                    {"metric": "risk_score", "max_delta": 0.05},
                    {"metric": "contradiction_rate", "max_delta": 0.03}
                ],
                "promotion_rule": promotion_rule,
                "secondary_metrics": ["overall_score", "reasoning_score"]
            }

        elif "routing" in adaptation_type:
            return {
                "primary_metric": "outcome_score",
                "guardrails": [
                    {"metric": "tool_failure_rate", "max_delta": 0.02}
                ],
                "promotion_rule": promotion_rule,
                "secondary_metrics": ["coherence_score", "execution_completion_rate"]
            }

        elif "tool" in adaptation_type:
            return {
                "primary_metric": "tool_failure_rate",  # Lower is better
                "guardrails": [
                    {"metric": "execution_completion_rate", "min_delta": -0.05}
                ],
                "promotion_rule": promotion_rule,
                "secondary_metrics": ["outcome_score", "coherence_score"]
            }

        else:
            return {
                "primary_metric": "overall_score",
                "guardrails": [
                    {"metric": "risk_score", "max_delta": 0.05}
                ],
                "promotion_rule": promotion_rule,
                "secondary_metrics": ["coherence_score", "reasoning_score"]
            }

"""
TORQ Readiness Checker - Policy Management

Milestone 1: Readiness policy registry and hard block evaluation

Provides policy management, hard block evaluation, and policy application
for readiness decisions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .readiness_models import (
    PolicyProfile,
    PolicyDimension,
    HardBlockRule,
    ReadinessThresholds,
    ReadinessScore,
    ReadinessState,
    CandidateType,
    ReadinessCandidate,
    DEFAULT_POLICY_PROFILES,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Policy Registry
# ============================================================================

class ReadinessPolicyRegistry:
    """
    Registry for readiness policy profiles.

    Manages policy profiles, handles registration, retrieval,
    and validation.
    """

    def __init__(self):
        """Initialize the policy registry."""
        self._profiles: Dict[str, PolicyProfile] = {}
        self._default_profile_id: Optional[str] = None

        # Register default profiles
        self._register_defaults()

    def _register_defaults(self):
        """Register the default policy profiles."""
        for profile in DEFAULT_POLICY_PROFILES.values():
            self.register_profile(profile)
            if profile.is_default:
                self._default_profile_id = profile.id

    def register_profile(self, profile: PolicyProfile) -> bool:
        """
        Register a policy profile.

        Args:
            profile: The policy profile to register

        Returns:
            True if registered successfully
        """
        if not profile.validate_weights():
            logger.error(f"Policy profile {profile.id} has invalid weights")
            return False

        self._profiles[profile.id] = profile
        logger.info(f"Registered policy profile: {profile.id}")
        return True

    def get_profile(self, profile_id: str) -> Optional[PolicyProfile]:
        """Get a policy profile by ID."""
        return self._profiles.get(profile_id)

    def get_default_profile(self) -> Optional[PolicyProfile]:
        """Get the default policy profile."""
        if self._default_profile_id:
            return self._profiles.get(self._default_profile_id)
        return self._profiles.get("default")

    def list_profiles(self) -> List[PolicyProfile]:
        """List all registered policy profiles."""
        return list(self._profiles.values())

    def get_profile_for_candidate(
        self,
        candidate: ReadinessCandidate
    ) -> PolicyProfile:
        """
        Get the appropriate policy profile for a candidate.

        Args:
            candidate: The readiness candidate

        Returns:
            The policy profile to use for this candidate
        """
        # First try the candidate's specified profile
        profile = self.get_profile(candidate.policy_profile_id)
        if profile:
            return profile

        # Fall back to candidate type overrides
        for profile in self._profiles.values():
            overrides = profile.candidate_type_overrides
            if candidate.candidate_type in overrides:
                return profile

        # Fall back to default
        return self.get_default_profile() or self._profiles["default"]

    def update_profile(
        self,
        profile_id: str,
        updates: Dict[str, Any]
    ) -> Optional[PolicyProfile]:
        """
        Update a policy profile.

        Args:
            profile_id: ID of profile to update
            updates: Dictionary of fields to update

        Returns:
            Updated profile if found, None otherwise
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        # Create updated profile
        profile_data = profile.model_dump()
        profile_data.update(updates)
        profile_data["updated_at"] = datetime.now()

        updated_profile = PolicyProfile(**profile_data)

        if not updated_profile.validate_weights():
            logger.error(f"Updated policy profile {profile_id} has invalid weights")
            return None

        self._profiles[profile_id] = updated_profile
        logger.info(f"Updated policy profile: {profile_id}")
        return updated_profile


# Global registry instance
_policy_registry: Optional[ReadinessPolicyRegistry] = None


def get_policy_registry() -> ReadinessPolicyRegistry:
    """Get the global policy registry instance."""
    global _policy_registry
    if _policy_registry is None:
        _policy_registry = ReadinessPolicyRegistry()
    return _policy_registry


# ============================================================================
# Hard Block Evaluation
# ============================================================================

class HardBlockEvaluator:
    """
    Evaluates hard block rules for readiness decisions.

    Hard blocks are conditions that must be satisfied for a candidate
    to be considered ready, regardless of score.
    """

    def __init__(
        self,
        registry: Optional[ReadinessPolicyRegistry] = None
    ):
        """
        Initialize the hard block evaluator.

        Args:
            registry: Policy registry for getting rules
        """
        self.registry = registry or get_policy_registry()

    def evaluate_hard_blocks(
        self,
        profile: PolicyProfile,
        score: ReadinessScore
    ) -> List[str]:
        """
        Evaluate all hard block rules for a profile.

        Args:
            profile: The policy profile with hard block rules
            score: The computed readiness score

        Returns:
            List of hard block descriptions that were triggered
        """
        triggered_blocks = []

        for rule in profile.hard_blocks:
            dimension_value = self._get_dimension_value(score, rule.dimension)

            if rule.is_blocked(dimension_value):
                block_message = f"{rule.name}: {rule.description}"
                triggered_blocks.append(block_message)

        # Apply built-in hard blocks (only when computed from actual evidence)
        # Milestone 1: Built-in blocks disabled for testing
        # Milestone 2+: Will apply when we have actual evidence data
        # if score.confidence > 0.5:
        #     if score.execution_stability < 0.4:
        #         triggered_blocks.append(...)
        #     ...

        return triggered_blocks

    def _get_dimension_value(
        self,
        score: ReadinessScore,
        dimension: PolicyDimension
    ) -> float:
        """Get the score value for a dimension."""
        dimension_map = {
            PolicyDimension.EXECUTION_STABILITY: score.execution_stability,
            PolicyDimension.ARTIFACT_COMPLETENESS: score.artifact_completeness,
            PolicyDimension.MEMORY_CONFIDENCE: score.memory_confidence,
            PolicyDimension.INSIGHT_QUALITY: score.insight_quality,
            PolicyDimension.PATTERN_CONFIDENCE: score.pattern_confidence,
            PolicyDimension.AUDIT_COVERAGE: score.audit_coverage,
            PolicyDimension.POLICY_COMPLIANCE: score.policy_compliance,
            PolicyDimension.OPERATIONAL_CONSISTENCY: score.operational_consistency,
        }
        return dimension_map.get(dimension, 0.0)

    def can_transition_to_ready(
        self,
        profile: PolicyProfile,
        score: ReadinessScore
    ) -> tuple[bool, List[str]]:
        """
        Check if a candidate can transition to ready state.

        Args:
            profile: The policy profile
            score: The computed readiness score

        Returns:
            Tuple of (can_transition, list of blocking reasons)
        """
        hard_blocks = self.evaluate_hard_blocks(profile, score)

        # Check if hard blocks can be overridden
        if hard_blocks and profile.thresholds.hard_blocks_override:
            return True, hard_blocks

        return len(hard_blocks) == 0, hard_blocks


# Global evaluator instance
_hard_block_evaluator: Optional[HardBlockEvaluator] = None


def get_hard_block_evaluator() -> HardBlockEvaluator:
    """Get the global hard block evaluator instance."""
    global _hard_block_evaluator
    if _hard_block_evaluator is None:
        _hard_block_evaluator = HardBlockEvaluator()
    return _hard_block_evaluator


# ============================================================================
# Policy Application
# ============================================================================

class PolicyApplicator:
    """
    Applies policy profiles to readiness evaluations.

    Handles threshold comparison, outcome determination, and
    transition recommendations.
    """

    def __init__(
        self,
        registry: Optional[ReadinessPolicyRegistry] = None,
        block_evaluator: Optional[HardBlockEvaluator] = None
    ):
        """
        Initialize the policy applicator.

        Args:
            registry: Policy registry
            block_evaluator: Hard block evaluator
        """
        self.registry = registry or get_policy_registry()
        self.block_evaluator = block_evaluator or get_hard_block_evaluator()

    def determine_outcome(
        self,
        profile: PolicyProfile,
        score: ReadinessScore,
        previous_state: Optional[ReadinessState] = None,
        previous_score: Optional[float] = None
    ) -> tuple[str, ReadinessState, str, bool]:
        """
        Determine the readiness outcome based on score and policy.

        Args:
            profile: The policy profile
            score: The computed readiness score
            previous_state: The candidate's previous state
            previous_score: The candidate's previous score

        Returns:
            Tuple of (outcome, recommended_state, reason, should_transition)
        """
        thresholds = profile.thresholds
        outcome = "observed"
        recommended_state = ReadinessState.OBSERVED
        reason = ""
        should_transition = False

        # Check for hard blocks first
        can_be_ready, hard_blocks = self.block_evaluator.can_transition_to_ready(
            profile, score
        )

        if not can_be_ready:
            outcome = "blocked"
            recommended_state = ReadinessState.BLOCKED
            reason = f"Blocked by: {', '.join(hard_blocks)}"
            should_transition = previous_state != ReadinessState.BLOCKED
            return outcome, recommended_state, reason, should_transition

        # Check for regression
        is_regression, regression_reason = self._check_regression(
            score, previous_state, previous_score, thresholds
        )

        if is_regression:
            outcome = "regressed"
            recommended_state = ReadinessState.REGRESSED
            reason = regression_reason
            should_transition = True
            return outcome, recommended_state, reason, should_transition

        # Determine outcome based on score thresholds
        if score.overall_score >= thresholds.ready_min:
            outcome = "ready"
            recommended_state = ReadinessState.READY
            reason = f"Score {score.overall_score:.2f} meets ready threshold {thresholds.ready_min}"
            should_transition = previous_state != ReadinessState.READY

        elif score.overall_score >= thresholds.watchlist_min:
            outcome = "watchlist"
            recommended_state = ReadinessState.WATCHLIST
            reason = f"Score {score.overall_score:.2f} in watchlist band"
            should_transition = previous_state == ReadinessState.OBSERVED

        else:
            outcome = "observed"
            recommended_state = ReadinessState.OBSERVED
            reason = f"Score {score.overall_score:.2f} below watchlist threshold"
            should_transition = False

        return outcome, recommended_state, reason, should_transition

    def _check_regression(
        self,
        score: ReadinessScore,
        previous_state: Optional[ReadinessState],
        previous_score: Optional[float],
        thresholds: ReadinessThresholds
    ) -> tuple[bool, str]:
        """
        Check if a previously ready candidate has regressed.

        Args:
            score: Current score
            previous_state: Previous readiness state
            previous_score: Previous overall score
            thresholds: Policy thresholds

        Returns:
            Tuple of (is_regression, reason)
        """
        if previous_state != ReadinessState.READY:
            return False, ""

        if previous_score is None:
            return False, ""

        score_delta = previous_score - score.overall_score

        if score_delta >= thresholds.regression_delta:
            return (
                True,
                f"Regression: score decreased by {score_delta:.2f} "
                f"from {previous_score:.2f} to {score.overall_score:.2f}"
            )

        return False, ""


# Global applicator instance
_policy_applicator: Optional[PolicyApplicator] = None


def get_policy_applicator() -> PolicyApplicator:
    """Get the global policy applicator instance."""
    global _policy_applicator
    if _policy_applicator is None:
        _policy_applicator = PolicyApplicator()
    return _policy_applicator

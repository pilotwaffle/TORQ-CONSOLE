"""
Adaptation Policy Engine

Evaluates learning signals against governance policies to determine:
1. Whether a signal can become a proposal
2. What risk tier it belongs to
3. What approval mode it requires

Enforces guardrails to prevent unsafe or unstable adaptations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    PolicyConfig,
    PolicyEvaluation,
    RiskTier,
    ApprovalMode,
    GuardrailViolation,
    GUARDRAIL_MIN_EVIDENCE,
    GUARDRAIL_COOLDOWN_ACTIVE,
    GUARDRAIL_MAX_OPEN_PROPOSALS,
    GUARDRAIL_MISSING_ROLLBACK,
    GUARDRAIL_HIGH_RISK_AUTO_APPLY,
    GUARDRAIL_DUPLICATE_PROPOSAL,
    GUARDRAIL_EXPIRED_SIGNAL,
)


logger = logging.getLogger(__name__)


class AdaptationPolicyEngine:
    """
    Evaluates learning signals against governance policies.

    Ensures that only safe, well-evidenced signals become adaptation proposals.
    """

    def __init__(self, config: PolicyConfig):
        self.config = config

    # ========================================================================
    # Policy Evaluation
    # ========================================================================

    def evaluate_signal_eligibility(
        self,
        signal: Dict[str, Any],
        existing_proposals: List[Dict[str, Any]],
        current_time: Optional[datetime] = None
    ) -> PolicyEvaluation:
        """
        Evaluate whether a signal can become an adaptation proposal.

        Checks:
        - Minimum evidence count
        - Signal strength threshold
        - Cooldown period for target asset
        - Max open proposals limit
        - Signal freshness
        """
        if current_time is None:
            current_time = datetime.now()

        violations = []

        # Check minimum evidence
        evidence_count = signal.get("evidence_count", 1)
        if evidence_count < self.config.min_evidence_count:
            violations.append(GuardrailViolation(
                violation_type=GUARDRAIL_MIN_EVIDENCE,
                description=f"Signal has {evidence_count} evidence, minimum is {self.config.min_evidence_count}",
                severity="error",
                affected_field="evidence_count"
            ))

        # Check signal strength
        signal_strength = signal.get("strength", "weak")
        strength_order = {"weak": 0, "moderate": 1, "strong": 2, "conclusive": 3}
        min_strength = strength_order.get(self.config.min_signal_strength, 1)
        actual_strength = strength_order.get(signal_strength, 0)
        if actual_strength < min_strength:
            violations.append(GuardrailViolation(
                violation_type="insufficient_strength",
                description=f"Signal strength '{signal_strength}' below threshold '{self.config.min_signal_strength}'",
                severity="error",
                affected_field="strength"
            ))

        # Check cooldown for target
        target_key = signal.get("target_key", signal.get("scope_id", "unknown"))
        cooldown_violation = self._check_cooldown(target_key, existing_proposals, current_time)
        if cooldown_violation:
            violations.append(cooldown_violation)

        # Check max open proposals
        max_open_violation = self._check_max_open_proposals(target_key, existing_proposals)
        if max_open_violation:
            violations.append(max_open_violation)

        # Check for duplicates
        duplicate_violation = self._check_duplicate_proposal(signal, existing_proposals)
        if duplicate_violation:
            violations.append(duplicate_violation)

        # Check signal freshness
        signal_created = signal.get("created_at")
        if signal_created:
            signal_age = current_time - signal_created
            if signal_age > timedelta(days=self.config.proposal_expiry_days):
                violations.append(GuardrailViolation(
                    violation_type=GUARDRAIL_EXPIRED_SIGNAL,
                    description=f"Signal is {signal_age.days} days old, expired at {self.config.proposal_expiry_days} days",
                    severity="error"
                ))

        # Determine eligibility
        error_violations = [v for v in violations if v.severity == "error"]
        can_propose = len(error_violations) == 0

        # Get suggested risk tier and approval mode
        signal_type = signal.get("signal_type")
        suggested_tier, suggested_mode = self._classify_risk(signal_type, signal)

        reason = self._build_evaluation_reason(can_propose, violations, suggested_tier)

        return PolicyEvaluation(
            can_propose=can_propose,
            reason=reason,
            suggested_risk_tier=suggested_tier,
            suggested_approval_mode=suggested_mode,
            guardrail_violations=[v.model_dump() if hasattr(v, "model_dump") else v.dict() for v in violations]
        )

    def evaluate_proposal_application(
        self,
        proposal: Dict[str, Any],
        policy_config: Optional[PolicyConfig] = None
    ) -> PolicyEvaluation:
        """
        Evaluate whether a proposal can be applied.

        Checks:
        - Approval status matches risk tier requirements
        - Rollback plan present for higher-risk proposals
        - Auto-apply not attempted for high-risk proposals
        """
        config = policy_config or self.config
        violations = []

        risk_tier = proposal.get("risk_tier")
        approval_mode = proposal.get("approval_mode")
        status = proposal.get("status", "draft")

        # Check approval status for risk tier
        if risk_tier == RiskTier.TIER_3_HIGH:
            if status != "approved":
                violations.append(GuardrailViolation(
                    violation_type="approval_required",
                    description="Tier 3 proposals require explicit approval before application",
                    severity="error"
                ))
        elif risk_tier == RiskTier.TIER_2_MEDIUM:
            if config.tier_2_require_approval and status != "approved":
                violations.append(GuardrailViolation(
                    violation_type="approval_required",
                    description="Tier 2 proposals require approval (currently required by policy)",
                    severity="error"
                ))

        # Check rollback plan for Tier 2+
        if config.require_rollback_plan and risk_tier in [RiskTier.TIER_2_MEDIUM, RiskTier.TIER_3_HIGH]:
            if not proposal.get("rollback_plan"):
                violations.append(GuardrailViolation(
                    violation_type=GUARDRAIL_MISSING_ROLLBACK,
                    description=f"Rollback plan required for {risk_tier} proposals",
                    severity="error"
                ))

        # Check for auto-apply attempts on high-risk
        if approval_mode == ApprovalMode.AUTO_LOW_RISK and risk_tier == RiskTier.TIER_3_HIGH:
            violations.append(GuardrailViolation(
                violation_type=GUARDRAIL_HIGH_RISK_AUTO_APPLY,
                description="Cannot auto-apply Tier 3 (high risk) proposals",
                severity="error"
            ))

        can_apply = len([v for v in violations if v.severity == "error"]) == 0

        return PolicyEvaluation(
            can_propose=can_apply,
            reason=self._build_application_reason(can_apply, violations),
            guardrail_violations=[v.model_dump() if hasattr(v, "model_dump") else v.dict() for v in violations]
        )

    # ========================================================================
    # Risk Classification
    # ========================================================================

    def _classify_risk(
        self,
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> tuple[RiskTier, ApprovalMode]:
        """
        Classify the risk tier and approval mode for a signal.

        Uses signal-to-proposal mapping as baseline, then adjusts based on:
        - Evidence count (higher evidence → slightly lower risk for same type)
        - Signal strength (conclusive signals may still be high risk if type is sensitive)
        - Target scope (global changes are higher risk than agent-specific)
        """
        from .models import get_signal_mapping

        mapping = get_signal_mapping(signal_type)

        if mapping:
            base_tier = RiskTier(mapping["default_risk_tier"])
            base_mode = ApprovalMode(mapping["default_approval_mode"])
        else:
            # Default to conservative for unknown signals
            base_tier = RiskTier.TIER_2_MEDIUM
            base_mode = ApprovalMode.HUMAN_REVIEW

        # Adjust based on target scope
        target_scope = signal_data.get("scope_type", "agent")
        if target_scope == "global":
            # Global changes are always higher risk
            if base_tier == RiskTier.TIER_1_LOW:
                base_tier = RiskTier.TIER_2_MEDIUM
            elif base_tier == RiskTier.TIER_2_MEDIUM:
                base_tier = RiskTier.TIER_3_HIGH
                base_mode = ApprovalMode.RESTRICTED

        # Adjust based on evidence strength
        evidence_count = signal_data.get("evidence_count", 1)
        if evidence_count >= 10 and base_tier == RiskTier.TIER_3_HIGH:
            # Very strong evidence might allow Tier 3 → Tier 2
            # But still requires human review
            base_tier = RiskTier.TIER_2_MEDIUM
            base_mode = ApprovalMode.HUMAN_REVIEW

        # Check for sensitive target types
        target_asset = signal_data.get("target_asset_type", "")
        if target_asset in ["safety_policy", "audit_behavior_change", "memory_rule_change"]:
            base_tier = RiskTier.TIER_3_HIGH
            base_mode = ApprovalMode.RESTRICTED

        return base_tier, base_mode

    # ========================================================================
    # Guardrail Checks
    # ========================================================================

    def _check_cooldown(
        self,
        target_key: str,
        existing_proposals: List[Dict[str, Any]],
        current_time: datetime
    ) -> Optional[GuardrailViolation]:
        """Check if target asset is in cooldown period."""
        cutoff_time = current_time - timedelta(hours=self.config.proposal_cooldown_hours)

        recent_proposals = [
            p for p in existing_proposals
            if p.get("target_key") == target_key
            and p.get("created_at")
            and p["created_at"] > cutoff_time
        ]

        if recent_proposals:
            most_recent = max(recent_proposals, key=lambda p: p.get("created_at", datetime.min))
            wait_hours = self.config.proposal_cooldown_hours - int(
                (current_time - most_recent["created_at"]).total_seconds() / 3600
            )
            return GuardrailViolation(
                violation_type=GUARDRAIL_COOLDOWN_ACTIVE,
                description=f"Target {target_key} has {len(recent_proposals)} recent proposal(s). Wait {wait_hours}h.",
                severity="warning",
                affected_field="target_key"
            )
        return None

    def _check_max_open_proposals(
        self,
        target_key: str,
        existing_proposals: List[Dict[str, Any]]
    ) -> Optional[GuardrailViolation]:
        """Check if target has too many open proposals."""
        open_statuses = ["draft", "pending_review", "approved"]
        open_proposals = [
            p for p in existing_proposals
            if p.get("target_key") == target_key
            and p.get("status") in open_statuses
        ]

        if len(open_proposals) >= self.config.max_open_proposals_per_asset:
            return GuardrailViolation(
                violation_type=GUARDRAIL_MAX_OPEN_PROPOSALS,
                description=f"Target {target_key} has {len(open_proposals)} open proposals (max: {self.config.max_open_proposals_per_asset})",
                severity="warning",
                affected_field="target_key"
            )
        return None

    def _check_duplicate_proposal(
        self,
        signal: Dict[str, Any],
        existing_proposals: List[Dict[str, Any]]
    ) -> Optional[GuardrailViolation]:
        """Check for substantially similar existing proposals."""
        signal_type = signal.get("signal_type")
        scope_id = signal.get("scope_id")

        similar = [
            p for p in existing_proposals
            if p.get("signal_type") == signal_type
            and p.get("scope_id") == scope_id
            and p.get("status") in ["draft", "pending_review"]
        ]

        if similar:
            return GuardrailViolation(
                violation_type=GUARDRAIL_DUPLICATE_PROPOSAL,
                description=f"Found {len(similar)} similar proposal(s) for {signal_type} on {scope_id}",
                severity="warning",
                affected_field="signal_type"
            )
        return None

    # ========================================================================
    # Reason Building
    # ========================================================================

    def _build_evaluation_reason(
        self,
        can_propose: bool,
        violations: List[GuardrailViolation],
        risk_tier: RiskTier
    ) -> str:
        """Build human-readable evaluation reason."""
        if can_propose:
            return f"Signal eligible for proposal. Classified as {risk_tier.value} risk."

        error_violations = [v for v in violations if v.severity == "error"]
        error_descriptions = [v.description for v in error_violations]
        return f"Signal not eligible: " + "; ".join(error_descriptions)

    def _build_application_reason(
        self,
        can_apply: bool,
        violations: List[GuardrailViolation]
    ) -> str:
        """Build human-readable application reason."""
        if can_apply:
            return "Proposal meets all requirements for application."

        error_violations = [v for v in violations if v.severity == "error"]
        error_descriptions = [v.description for v in error_violations]
        return f"Cannot apply: " + "; ".join(error_descriptions)

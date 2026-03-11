"""
Signal-to-Proposal Mapper

Converts learning signals into structured adaptation proposals.
Handles the translation from observation to actionable change.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import (
    AdaptationProposalCreate,
    AdaptationType,
    TargetAssetType,
    RiskTier,
    ApprovalMode,
    get_signal_mapping,
    get_adaptation_type,
)


logger = logging.getLogger(__name__)


class SignalToProposalMapper:
    """
    Maps learning signals to adaptation proposals.

    Each signal type translates to a specific adaptation type with
    structured proposed changes and rollback guidance.
    """

    def map_signal_to_proposal(
        self,
        signal: Dict[str, Any],
        target_scope: str,
        candidate_version: str
    ) -> Optional[AdaptationProposalCreate]:
        """
        Convert a learning signal into an adaptation proposal.

        Args:
            signal: Learning signal data
            target_scope: Scope for the adaptation (agent_id, workflow_id, etc.)
            candidate_version: Version identifier for the proposed change

        Returns:
            AdaptationProposalCreate if mapping exists, None otherwise
        """
        signal_type = signal.get("signal_type")
        if not signal_type:
            logger.warning("Signal missing signal_type")
            return None

        mapping = get_signal_mapping(signal_type)
        if not mapping:
            logger.warning(f"No mapping found for signal type: {signal_type}")
            return None

        # Get adaptation type
        adaptation_type = get_adaptation_type(signal_type)
        if not adaptation_type:
            logger.warning(f"Could not determine adaptation type for: {signal_type}")
            return None

        # Determine target asset type
        target_asset_type = self._determine_target_asset_type(signal)

        # Generate proposed change structure
        proposed_change = self._generate_proposed_change(signal, adaptation_type)

        # Generate change description
        change_description = self._generate_change_description(signal, mapping)

        # Generate evidence summary
        evidence_summary = self._generate_evidence_summary(signal)

        # Determine target key
        target_key = self._determine_target_key(signal, target_asset_type)

        # Get current version if available
        current_version = signal.get("metadata", {}).get("current_version")

        # Get risk tier and approval mode
        risk_tier = RiskTier(mapping["default_risk_tier"])
        approval_mode = ApprovalMode(mapping["default_approval_mode"])

        # Generate rollback plan
        rollback_plan = self._generate_rollback_plan(adaptation_type, risk_tier)

        # Expected improvement
        expected_improvement = self._generate_expected_improvement(signal, adaptation_type)

        return AdaptationProposalCreate(
            learning_signal_id=signal.get("signal_id", ""),
            adaptation_type=adaptation_type,
            target_asset_type=target_asset_type,
            target_scope=target_scope,
            target_key=target_key,
            proposed_change=proposed_change,
            change_description=change_description,
            evidence_summary=evidence_summary,
            evidence_count=signal.get("evidence_count", 1),
            supporting_execution_ids=signal.get("supporting_execution_ids", []),
            risk_tier=risk_tier,
            approval_mode=approval_mode,
            current_version=current_version,
            candidate_version=candidate_version,
            expected_improvement=expected_improvement,
            rollback_plan=rollback_plan
        )

    def _determine_target_asset_type(self, signal: Dict[str, Any]) -> TargetAssetType:
        """Determine what type of asset the signal targets."""
        signal_type = signal.get("signal_type", "")

        # Prompt-related signals target prompts
        if "prompt" in signal_type:
            return TargetAssetType.AGENT_PROMPT

        # Routing signals target routing profile
        if "routing" in signal_type:
            return TargetAssetType.ROUTING_PROFILE

        # Tool signals target tool preferences
        if "tool" in signal_type:
            return TargetAssetType.TOOL_PREFERENCES

        # Risk signals may target safety policy
        if "risk" in signal_type:
            return TargetAssetType.SAFETY_POLICY

        # Default to agent prompt
        return TargetAssetType.AGENT_PROMPT

    def _determine_target_key(self, signal: Dict[str, Any], asset_type: TargetAssetType) -> str:
        """Determine the specific key for the target asset."""
        scope_id = signal.get("scope_id", signal.get("agent_id", "unknown"))

        if asset_type == TargetAssetType.AGENT_PROMPT:
            return f"{scope_id}_prompt"
        elif asset_type == TargetAssetType.ROUTING_PROFILE:
            return f"{scope_id}_routing"
        elif asset_type == TargetAssetType.TOOL_PREFERENCES:
            return f"{scope_id}_tools"
        else:
            return scope_id

    def _generate_proposed_change(
        self,
        signal: Dict[str, Any],
        adaptation_type: AdaptationType
    ) -> Dict[str, Any]:
        """Generate structured proposed change based on adaptation type."""
        base_change = {
            "adaptation_type": adaptation_type.value,
            "signal_metadata": signal.get("metadata", {}),
            "signal_strength": signal.get("strength", "unknown"),
        }

        # Add type-specific change structure
        if adaptation_type == AdaptationType.PROMPT_REVISION:
            base_change.update({
                "change_type": "prompt_structure",
                "affected_sections": ["instructions", "context"],
                "suggested_modifications": self._extract_prompt_modifications(signal)
            })

        elif adaptation_type == AdaptationType.PROMPT_CONTEXT_ENRICHMENT:
            base_change.update({
                "change_type": "context_addition",
                "context_to_add": self._extract_missing_context(signal)
            })

        elif adaptation_type == AdaptationType.PROMPT_CHECKLIST_ADDITION:
            base_change.update({
                "change_type": "checklist_item",
                "checklist_items": self._extract_checklist_items(signal)
            })

        elif adaptation_type == AdaptationType.ROUTING_PROFILE_ADJUSTMENT:
            base_change.update({
                "change_type": "routing_weights",
                "adjustments": self._extract_routing_adjustments(signal)
            })

        elif adaptation_type in [AdaptationType.TOOL_PRIORITY_INCREASE, AdaptationType.TOOL_PRIORITY_DECREASE]:
            base_change.update({
                "change_type": "tool_priority",
                "tool_name": signal.get("metadata", {}).get("tool_name", "unknown"),
                "priority_delta": +1 if adaptation_type == AdaptationType.TOOL_PRIORITY_INCREASE else -1
            })

        elif adaptation_type == AdaptationType.TOOL_DISABLE:
            base_change.update({
                "change_type": "tool_availability",
                "tool_name": signal.get("metadata", {}).get("tool_name", "unknown"),
                "enabled": False
            })

        return base_change

    def _extract_prompt_modifications(self, signal: Dict[str, Any]) -> List[str]:
        """Extract prompt modification suggestions from signal."""
        metadata = signal.get("metadata", {})
        modifications = []

        # Low coherence → structure suggestions
        if metadata.get("avg_coherence", 100) < 60:
            modifications.append("Add numbered step structure to instructions")
            modifications.append("Clarify input/output specifications")

        # Unresolved questions → context additions
        if metadata.get("unresolved_question_count", 0) > 0:
            modifications.append("Expand context section with prerequisite information")

        return modifications

    def _extract_missing_context(self, signal: Dict[str, Any]) -> List[str]:
        """Extract missing context items from signal."""
        metadata = signal.get("metadata", {})
        context_items = []

        # Tool efficiency issues suggest missing context
        if metadata.get("avg_tool_efficiency", 100) < 50:
            context_items.append("API authentication requirements")
            context_items.append("Data source prerequisites")
            context_items.append("Tool usage examples")

        return context_items

    def _extract_checklist_items(self, signal: Dict[str, Any]) -> List[str]:
        """Extract checklist items from signal."""
        metadata = signal.get("metadata", {})
        items = []

        # Repeated questions → checklist
        if "theme" in metadata:
            items.append(f"Address {metadata['theme']} requirements explicitly")

        if metadata.get("question_count", 0) > 0:
            items.append("Verify all prerequisite information is provided")

        return items

    def _extract_routing_adjustments(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract routing adjustments from signal."""
        metadata = signal.get("metadata", {})
        adjustments = []

        scope_id = signal.get("scope_id", "")
        failure_rate = metadata.get("failure_rate", 0)

        if failure_rate > 0.3:
            adjustments.append({
                "agent": scope_id,
                "change": "decrease_weight",
                "reason": "High failure rate suggests misalignment",
                "suggested_alternative": "Review agent capabilities vs task requirements"
            })

        return adjustments

    def _generate_change_description(
        self,
        signal: Dict[str, Any],
        mapping: Dict[str, Any]
    ) -> str:
        """Generate human-readable change description."""
        scope_id = signal.get("scope_id", "unknown target")
        evidence_count = signal.get("evidence_count", 1)

        description = mapping["description"]
        return f"{description.capitalize()} for {scope_id} based on {evidence_count} observations."

    def _generate_evidence_summary(self, signal: Dict[str, Any]) -> str:
        """Generate evidence summary for the proposal."""
        signal_type = signal.get("signal_type", "")
        evidence_count = signal.get("evidence_count", 1)
        strength = signal.get("strength", "unknown")

        summary = f"Signal type: {signal_type}, "
        summary += f"Strength: {strength}, "
        summary += f"Evidence count: {evidence_count}"

        # Add signal-specific details
        metadata = signal.get("metadata", {})
        if metadata.get("avg_coherence"):
            summary += f", Avg coherence: {metadata['avg_coherence']:.1f}"
        if metadata.get("failure_rate"):
            summary += f", Failure rate: {metadata['failure_rate']:.1%}"

        return summary

    def _generate_rollback_plan(
        self,
        adaptation_type: AdaptationType,
        risk_tier: RiskTier
    ) -> Optional[str]:
        """Generate rollback plan based on adaptation type and risk."""
        if risk_tier == RiskTier.TIER_1_LOW:
            return "Revert to previous prompt version"

        if adaptation_type in [AdaptationType.PROMPT_REVISION, AdaptationType.PROMPT_STRUCTURAL_REWRITE]:
            return "Restore previous prompt version from version control"

        if adaptation_type in [AdaptationType.TOOL_PRIORITY_INCREASE, AdaptationType.TOOL_PRIORITY_DECREASE]:
            return "Reset tool priority to previous value"

        if adaptation_type == AdaptationType.TOOL_DISABLE:
            return "Re-enable tool and reset priority"

        if adaptation_type in [AdaptationType.ROUTING_PROFILE_ADJUSTMENT, AdaptationType.ROUTING_WEIGHT_TWEAK]:
            return "Restore previous routing weights"

        return "Review and revert to previous configuration"

    def _generate_expected_improvement(
        self,
        signal: Dict[str, Any],
        adaptation_type: AdaptationType
    ) -> Optional[str]:
        """Generate expected improvement description."""
        metadata = signal.get("metadata", {})

        if adaptation_type == AdaptationType.PROMPT_REVISION:
            if "avg_coherence" in metadata:
                current = metadata["avg_coherence"]
                target = min(current + 20, 100)
                return f"Coherence score: {current:.1f} → {target:.1f}"

        if "failure_rate" in metadata:
            current = metadata["failure_rate"]
            target = max(current - 0.2, 0)
            return f"Failure rate: {current:.1%} → {target:.1%}"

        return None

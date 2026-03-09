"""
Agent Teams - Decision Engine

Phase 5.2: Agent Teams as a governed execution primitive.

This module implements decision policies for team consensus,
including weighted consensus, validator gates, and dissent tracking.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .models import (
    TeamExecution,
    TeamMessage,
    DecisionPolicy,
    ValidatorStatus,
    DecisionOutcome,
    TeamRole,
    MessageType,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Decision Data Classes
# ============================================================================

class DecisionResult:
    """Result of team decision process."""

    def __init__(
        self,
        final_output: Dict[str, Any],
        confidence_score: float,
        decision_policy: str,
        total_votes: int = 0,
        approve_votes: int = 0,
        dissent_votes: int = 0,
        voters: List[str] = None,
        has_dissent: bool = False,
        dissenting_roles: List[str] = None,
        dissent_reasons: List[str] = None,
        validator_status: ValidatorStatus = ValidatorStatus.APPROVED,
        validator_notes: str = "",
        revision_count: int = 0,
        escalation_count: int = 0,
    ):
        self.final_output = final_output
        self.confidence_score = confidence_score
        self.decision_policy = decision_policy
        self.total_votes = total_votes
        self.approve_votes = approve_votes
        self.dissent_votes = dissent_votes
        self.voters = voters or []
        self.has_dissent = has_dissent
        self.dissenting_roles = dissenting_roles or []
        self.dissent_reasons = dissent_reasons or []
        self.validator_status = validator_status
        self.validator_notes = validator_notes
        self.revision_count = revision_count
        self.escalation_count = escalation_count


# ============================================================================
# Decision Engine
# ============================================================================

class DecisionEngine:
    """
    Implements decision policies for team consensus.

    Supported policies:
    - weighted_consensus: Weighted average of role confidences
    - unanimous: All roles must approve
    - majority: Simple majority approval
    - validator_gate: Validator can block output
    """

    def __init__(self, supabase):
        """
        Initialize the decision engine.

        Args:
            supabase: Supabase client
        """
        self.supabase = supabase

    async def make_decision(
        self,
        execution: TeamExecution,
        messages: List[TeamMessage],
        policy: DecisionPolicy,
    ) -> DecisionResult:
        """
        Make a team decision based on messages and policy.

        Args:
            execution: Team execution record
            messages: All collaboration messages
            policy: Decision policy to apply

        Returns:
            Decision result
        """
        # Extract role outputs and confidences
        role_confidences = self._extract_role_confidences(messages)
        role_outputs = self._extract_role_outputs(messages)

        # Check validator status
        validator_status, validator_notes = self._check_validator_status(messages)

        # Apply decision policy
        if policy == DecisionPolicy.WEIGHTED_CONSENSUS:
            return self._weighted_consensus(
                execution, role_confidences, role_outputs, validator_status, validator_notes
            )
        elif policy == DecisionPolicy.UNANIMOUS:
            return self._unanimous_decision(
                execution, role_confidences, role_outputs, validator_status, validator_notes
            )
        elif policy == DecisionPolicy.MAJORITY:
            return self._majority_decision(
                execution, role_confidences, role_outputs, validator_status, validator_notes
            )
        elif policy == DecisionPolicy.VALIDATOR_GATE:
            return self._validator_gate(
                execution, role_confidences, role_outputs, validator_status, validator_notes
            )
        else:
            # Default to weighted consensus
            return self._weighted_consensus(
                execution, role_confidences, role_outputs, validator_status, validator_notes
            )

    def _extract_role_confidences(self, messages: List[TeamMessage]) -> Dict[str, float]:
        """Extract confidence scores by role from messages."""
        confidences = {}
        for message in messages:
            if message.message_type in (MessageType.ROLE_TO_ROLE, MessageType.SYNTHESIS):
                if message.confidence > 0:
                    role = message.sender_role.value
                    # Use the latest (highest) confidence from each role
                    if role not in confidences or message.confidence > confidences[role]:
                        confidences[role] = message.confidence
        return confidences

    def _extract_role_outputs(self, messages: List[TeamMessage]) -> Dict[str, Dict[str, Any]]:
        """Extract outputs by role from messages."""
        outputs = {}
        for message in messages:
            if message.message_type == MessageType.ROLE_TO_ROLE:
                role = message.sender_role.value
                outputs[role] = message.content
        return outputs

    def _check_validator_status(self, messages: List[TeamMessage]) -> tuple[ValidatorStatus, str]:
        """Check validator status from messages."""
        for message in reversed(messages):  # Check latest first
            if message.message_type == MessageType.VALIDATION_BLOCK:
                return ValidatorStatus.BLOCKED, message.content.get("notes", "Validation failed")
            elif message.message_type == MessageType.VALIDATION_PASS:
                notes = message.content.get("notes", "Validation passed")
                return ValidatorStatus.APPROVED, notes
        return ValidatorStatus.PENDING, ""

    def _weighted_consensus(
        self,
        execution: TeamExecution,
        confidences: Dict[str, float],
        outputs: Dict[str, Dict[str, Any]],
        validator_status: ValidatorStatus,
        validator_notes: str,
    ) -> DecisionResult:
        """
        Calculate weighted consensus decision.

        Weights are defined in team member configuration.
        """
        # Get team member weights
        weights_result = self.supabase.table("agent_team_members").select("*").eq(
            "team_id", execution.team_id
        ).execute()

        weights = {m["role_name"]: m["confidence_weight"] for m in weights_result.data}

        # Calculate weighted confidence
        total_weight = 0.0
        weighted_sum = 0.0

        for role, confidence in confidences.items():
            weight = weights.get(role, 1.0)
            weighted_sum += confidence * weight
            total_weight += weight

        final_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Synthesize final output
        final_output = self._synthesize_outputs(outputs, confidences)

        # Check for dissent (roles below threshold)
        threshold = 0.7
        dissenting_roles = [
            role for role, conf in confidences.items()
            if conf < threshold
        ]

        # Apply validator gate if validator blocked
        if validator_status == ValidatorStatus.BLOCKED:
            final_output["validation_blocked"] = True
            final_output["validation_notes"] = validator_notes
            final_confidence = max(0.0, final_confidence - 0.2)

        return DecisionResult(
            final_output=final_output,
            confidence_score=final_confidence,
            decision_policy="weighted_consensus",
            total_votes=len(confidences),
            approve_votes=len(confidences) - len(dissenting_roles),
            dissent_votes=len(dissenting_roles),
            voters=list(confidences.keys()),
            has_dissent=len(dissenting_roles) > 0,
            dissenting_roles=dissenting_roles,
            validator_status=validator_status,
            validator_notes=validator_notes,
        )

    def _unanimous_decision(
        self,
        execution: TeamExecution,
        confidences: Dict[str, float],
        outputs: Dict[str, Dict[str, Any]],
        validator_status: ValidatorStatus,
        validator_notes: str,
    ) -> DecisionResult:
        """Require unanimous approval from all roles."""
        threshold = 0.8
        dissenting_roles = [
            role for role, conf in confidences.items()
            if conf < threshold
        ]

        if dissenting_roles:
            # Unanimous failed
            final_confidence = min(confidences.values()) if confidences else 0.0
            decision_status = ValidatorStatus.BLOCKED if validator_status == ValidatorStatus.BLOCKED else ValidatorStatus.ESCALATED
        else:
            final_confidence = sum(confidences.values()) / len(confidences) if confidences else 0.0
            decision_status = validator_status

        final_output = self._synthesize_outputs(outputs, confidences)

        return DecisionResult(
            final_output=final_output,
            confidence_score=final_confidence,
            decision_policy="unanimous",
            total_votes=len(confidences),
            approve_votes=len(confidences) - len(dissenting_roles),
            dissent_votes=len(dissenting_roles),
            voters=list(confidences.keys()),
            has_dissent=len(dissenting_roles) > 0,
            dissenting_roles=dissenting_roles,
            validator_status=decision_status,
            validator_notes=validator_notes,
            revision_count=1 if dissenting_roles else 0,
        )

    def _majority_decision(
        self,
        execution: TeamExecution,
        confidences: Dict[str, float],
        outputs: Dict[str, Dict[str, Any]],
        validator_status: ValidatorStatus,
        validator_notes: str,
    ) -> DecisionResult:
        """Require simple majority approval."""
        threshold = 0.5
        approve_roles = [role for role, conf in confidences.items() if conf >= threshold]
        dissent_roles = [role for role, conf in confidences.items() if conf < threshold]

        has_majority = len(approve_roles) > len(confidences) / 2

        if not has_majority:
            final_confidence = max(confidences.values()) if confidences else 0.0
        else:
            final_confidence = sum(confidences.values()) / len(confidences) if confidences else 0.0

        final_output = self._synthesize_outputs(outputs, confidences)

        return DecisionResult(
            final_output=final_output,
            confidence_score=final_confidence,
            decision_policy="majority",
            total_votes=len(confidences),
            approve_votes=len(approve_roles),
            dissent_votes=len(dissent_roles),
            voters=list(confidences.keys()),
            has_dissent=len(dissent_roles) > 0,
            dissenting_roles=dissent_roles,
            validator_status=validator_status if has_majority else ValidatorStatus.ESCALATED,
            validator_notes=validator_notes,
        )

    def _validator_gate(
        self,
        execution: TeamExecution,
        confidences: Dict[str, float],
        outputs: Dict[str, Dict[str, Any]],
        validator_status: ValidatorStatus,
        validator_notes: str,
    ) -> DecisionResult:
        """Validator has veto power over the decision."""
        final_confidence = sum(confidences.values()) / len(confidences) if confidences else 0.0
        final_output = self._synthesize_outputs(outputs, confidences)

        if validator_status == ValidatorStatus.BLOCKED:
            final_output["validation_blocked"] = True
            final_output["validation_notes"] = validator_notes
            final_confidence = 0.0

        return DecisionResult(
            final_output=final_output,
            confidence_score=final_confidence if validator_status != ValidatorStatus.BLOCKED else 0.0,
            decision_policy="validator_gate",
            total_votes=len(confidences),
            approve_votes=len(confidences),
            dissent_votes=0,
            voters=list(confidences.keys()),
            has_dissent=False,
            dissenting_roles=[],
            validator_status=validator_status,
            validator_notes=validator_notes,
        )

    def _synthesize_outputs(
        self,
        outputs: Dict[str, Dict[str, Any]],
        confidences: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Synthesize final output from role outputs.

        For MVP, combine outputs with lead taking precedence.
        """
        if not outputs:
            return {"text": "No outputs generated"}

        # Start with lead output as base
        lead_output = outputs.get("lead", {})
        synthesized = {
            "text": lead_output.get("text", ""),
            "contributions": {},
        }

        # Add contributions from other roles
        for role, output in outputs.items():
            if role != "lead" and output:
                synthesized["contributions"][role] = {
                    "text": output.get("text", ""),
                    "confidence": confidences.get(role, 0.0),
                }

                # Merge structured fields
                for key in ["steps", "recommendations", "findings", "issues"]:
                    if key in output and isinstance(output[key], list):
                        if key not in synthesized:
                            synthesized[key] = []
                        synthesized[key].extend(output[key])

        # Add overall confidence
        all_confidences = [c for c in confidences.values() if c > 0]
        if all_confidences:
            synthesized["confidence"] = sum(all_confidences) / len(all_confidences)

        return synthesized

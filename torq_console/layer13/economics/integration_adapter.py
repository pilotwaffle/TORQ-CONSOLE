"""
Layer 13 Integration Adapter

Consumes outputs from Layers 8-12 and converts them into
EconomicContext and ActionCandidate objects for evaluation.

This adapter bridges the existing TORQ layers with the new
economic intelligence layer.
"""

from typing import Any, Dict, List, Optional

from torq_console.layer13.economics.models import (
    ActionCandidate,
    EconomicContext,
    ResourceConstraint,
    ResourceCost,
    ResourceType,
    IntegrationInputs,
    Layer8MetaControlSignal,
    Layer9PolicyConstraint,
    Layer10PlanningGraph,
    Layer11ExecutionOutcome,
    Layer12FederatedInsight,
)


class Layer13IntegrationAdapter:
    """
    Adapter for converting Layer 8-12 outputs to Layer 13 inputs.

    This adapter:
    1. Collects outputs from Layers 8-12
    2. Converts them to EconomicContext
    3. Converts them to ActionCandidate[]
    4. Merges confidence from Layer 10 and Layer 11
    5. Applies policy constraints from Layer 9
    """

    def __init__(
        self,
        default_context: Optional[EconomicContext] = None,
    ):
        """
        Initialize the integration adapter.

        Args:
            default_context: Default economic context if no layer inputs provided
        """
        self.default_context = default_context or EconomicContext()

    async def collect_from_layers(
        self,
        layer8_output: Optional[Any] = None,
        layer9_output: Optional[Any] = None,
        layer10_output: Optional[Any] = None,
        layer11_output: Optional[Any] = None,
        layer12_output: Optional[Any] = None,
    ) -> IntegrationInputs:
        """
        Collect and normalize outputs from Layers 8-12.

        Args:
            layer8_output: Raw output from Layer 8 (Meta-Control)
            layer9_output: Raw output from Layer 9 (Policy Constraints)
            layer10_output: Raw output from Layer 10 (Planning/Verification)
            layer11_output: Raw output from Layer 11 (Execution/Learning)
            layer12_output: Raw output from Layer 12 (Federation)

        Returns:
            Normalized IntegrationInputs
        """
        inputs = IntegrationInputs()

        # Parse Layer 8: Meta-Control signals
        if layer8_output is not None:
            inputs.layer8 = self._parse_layer8(layer8_output)

        # Parse Layer 9: Policy constraints
        if layer9_output is not None:
            inputs.layer9 = self._parse_layer9(layer9_output)

        # Parse Layer 10: Confidence scores
        if layer10_output is not None:
            inputs.layer10 = self._parse_layer10(layer10_output)

        # Parse Layer 11: Success probabilities
        if layer11_output is not None:
            inputs.layer11 = self._parse_layer11(layer11_output)

        # Parse Layer 12: Federation consensus
        if layer12_output is not None:
            inputs.layer12 = self._parse_layer12(layer12_output)

        return inputs

    async def build_economic_context(
        self,
        inputs: Optional[IntegrationInputs] = None,
    ) -> EconomicContext:
        """
        Build EconomicContext from Layer 8-12 inputs.

        Merges budget constraints, risk tolerance, and policy
        settings from all layers.

        Args:
            inputs: Collected inputs from Layers 8-12

        Returns:
            EconomicContext for evaluation
        """
        if inputs is None:
            return self.default_context

        # Start with defaults
        budget = ResourceConstraint()

        # Apply Layer 9 resource limits
        if inputs.layer9:
            budget = inputs.get_merged_constraints()

        # Apply allowed/blocked domains from Layer 9
        allowed_domains = list(self.default_context.allowed_domains or [])
        blocked_domains = list(self.default_context.blocked_domains or [])

        if inputs.layer9:
            allowed_domains.extend(inputs.layer9.allowed_actions)
            blocked_domains.extend(inputs.layer9.blocked_actions)

        # Merge risk tolerance from Layer 11 if available
        risk_tolerance = self.default_context.risk_tolerance
        if inputs.layer11 and inputs.layer11.learned_preferences:
            # Update risk tolerance based on learned preferences
            learned_risk = inputs.layer11.learned_preferences.get("risk_tolerance")
            if learned_risk is not None:
                risk_tolerance = (risk_tolerance + learned_risk) / 2

        # Merge confidence floor from Layer 10
        confidence_floor = self.default_context.confidence_floor
        if inputs.layer10 and inputs.layer10.confidence_scores:
            # Could adjust confidence floor based on historical accuracy
            pass

        return EconomicContext(
            budget=budget,
            risk_tolerance=risk_tolerance,
            confidence_floor=confidence_floor,
            risk_ceiling=self.default_context.risk_ceiling,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    async def build_action_candidates(
        self,
        inputs: Optional[IntegrationInputs] = None,
        raw_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ActionCandidate]:
        """
        Build ActionCandidate list from Layer 8-12 inputs.

        Args:
            inputs: Collected inputs from Layers 8-12
            raw_candidates: Raw candidate data from Layer 8

        Returns:
            List of ActionCandidate objects
        """
        if raw_candidates is None:
            raw_candidates = []

        # Get merged confidence from Layer 10 and Layer 11
        merged_confidence = inputs.get_merged_confidence() if inputs else {}

        candidates = []

        for raw in raw_candidates:
            # Extract base fields
            action_id = raw.get("id", raw.get("action_id", ""))
            description = raw.get("description", "")
            domain = raw.get("domain", "general")

            # Extract economic dimensions
            estimated_value = raw.get("value", raw.get("estimated_value", 0.5))

            # Parse cost
            cost_data = raw.get("cost", raw.get("estimated_cost", {}))
            if isinstance(cost_data, dict):
                estimated_cost = ResourceCost(
                    compute_budget=cost_data.get("compute", 10.0),
                    api_call_budget=cost_data.get("api_calls", 0),
                    token_budget=cost_data.get("tokens", 0),
                    financial_cost=cost_data.get("financial", 0.0),
                )
            else:
                estimated_cost = ResourceCost(compute_budget=float(cost_data))

            # Extract confidence (from merged Layer 10 + Layer 11)
            confidence = merged_confidence.get(
                action_id,
                raw.get("confidence", 0.5)
            )

            # Extract risk
            risk = raw.get("risk", 0.2)

            # Extract timing
            urgency = raw.get("urgency", 0.5)
            time_to_realization = raw.get("time_to_realization", raw.get("time", 1.0))

            # Extract structure
            dependencies = raw.get("dependencies", raw.get("requires", []))

            # Extract strategic dimensions
            strategic_alignment = raw.get("strategic_alignment", 0.5)
            reversibility = raw.get("reversibility", 0.5)

            # Determine resource type
            resource_type_str = raw.get("resource_type", "compute")
            try:
                resource_type = ResourceType(resource_type_str)
            except ValueError:
                resource_type = ResourceType.COMPUTE

            candidate = ActionCandidate(
                id=action_id,
                description=description,
                domain=domain,
                estimated_value=estimated_value,
                estimated_cost=estimated_cost,
                confidence=confidence,
                risk=risk,
                urgency=urgency,
                time_to_realization=time_to_realization,
                dependencies=dependencies,
                strategic_alignment=strategic_alignment,
                reversibility=reversibility,
                resource_type=resource_type,
            )

            candidates.append(candidate)

        return candidates

    # ==========================================================================
    # Private Layer Parsers
    # ==========================================================================

    def _parse_layer8(self, output: Any) -> Layer8MetaControlSignal:
        """Parse Layer 8 meta-control output."""
        if isinstance(output, Layer8MetaControlSignal):
            return output

        if isinstance(output, dict):
            return Layer8MetaControlSignal(
                action_candidates=output.get("action_candidates", output.get("candidates", [])),
                control_signal=output.get("control_signal", {}),
            )

        return Layer8MetaControlSignal()

    def _parse_layer9(self, output: Any) -> Layer9PolicyConstraint:
        """Parse Layer 9 policy constraint output."""
        if isinstance(output, Layer9PolicyConstraint):
            return output

        if isinstance(output, dict):
            return Layer9PolicyConstraint(
                allowed_actions=output.get("allowed_actions", output.get("allowed", [])),
                blocked_actions=output.get("blocked_actions", output.get("blocked", [])),
                resource_limits=output.get("resource_limits", {}),
            )

        return Layer9PolicyConstraint()

    def _parse_layer10(self, output: Any) -> Layer10PlanningGraph:
        """Parse Layer 10 planning/verification output."""
        if isinstance(output, Layer10PlanningGraph):
            return output

        if isinstance(output, dict):
            return Layer10PlanningGraph(
                confidence_scores=output.get("confidence_scores", output.get("confidence", {})),
                verification_status=output.get("verification_status", {}),
            )

        return Layer10PlanningGraph()

    def _parse_layer11(self, output: Any) -> Layer11ExecutionOutcome:
        """Parse Layer 11 execution/learning output."""
        if isinstance(output, Layer11ExecutionOutcome):
            return output

        if isinstance(output, dict):
            return Layer11ExecutionOutcome(
                success_probabilities=output.get("success_probabilities", output.get("success", {})),
                learned_preferences=output.get("learned_preferences", {}),
            )

        return Layer11ExecutionOutcome()

    def _parse_layer12(self, output: Any) -> Layer12FederatedInsight:
        """Parse Layer 12 federation output."""
        if isinstance(output, Layer12FederatedInsight):
            return output

        if isinstance(output, dict):
            return Layer12FederatedInsight(
                consensus_scores=output.get("consensus_scores", output.get("consensus", {})),
                network_wide_agreement=output.get("network_wide_agreement", {}),
            )

        return Layer12FederatedInsight()


# =============================================================================
# Factory Function
# =============================================================================

def create_integration_adapter(
    default_context: Optional[EconomicContext] = None,
) -> Layer13IntegrationAdapter:
    """
    Factory function to create an integration adapter.

    Args:
        default_context: Default economic context

    Returns:
        Configured Layer13IntegrationAdapter instance
    """
    return Layer13IntegrationAdapter(default_context=default_context)

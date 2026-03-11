"""
Learning Signal Extraction Rules

Deterministic, heuristic-based rules for extracting learning signals.
These rules run first to identify explicit patterns before any LLM-assisted summarization.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from collections import Counter, defaultdict

from .models import (
    LearningSignalType,
    SignalStrength,
    SignalSource,
    LearningSignalCreate,
    ExtractionRule,
    SignalWeightCalculator,
    EntryImportance,
)


# ============================================================================
# Base Rule Definitions
# ============================================================================

class BaseExtractionRule:
    """Base class for extraction rules."""

    def __init__(self, rule_config: ExtractionRule):
        self.config = rule_config

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        """Extract signals from the provided data."""
        raise NotImplementedError

    def _calculate_strength(
        self,
        evidence_count: int,
        weight_sum: float,
        consistency_ratio: float = 1.0
    ) -> SignalStrength:
        """Calculate signal strength from evidence."""
        # Base strength from evidence count
        if evidence_count >= self.config.min_evidence_count * 3:
            base = SignalStrength.CONCLUSIVE
        elif evidence_count >= self.config.min_evidence_count * 2:
            base = SignalStrength.STRONG
        elif evidence_count >= self.config.min_evidence_count:
            base = SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK

        # Adjust by weight (average weight per evidence)
        avg_weight = weight_sum / max(evidence_count, 1)
        if avg_weight >= 1.3:
            return base  # Can't get stronger than CONCLUSIVE
        elif avg_weight >= 1.0:
            return base
        elif avg_weight >= 0.7:
            # Downgrade by one level
            strength_order = [SignalStrength.CONCLUSIVE, SignalStrength.STRONG,
                            SignalStrength.MODERATE, SignalStrength.WEAK]
            try:
                idx = strength_order.index(base)
                if idx < len(strength_order) - 1:
                    return strength_order[idx + 1]
            except ValueError:
                pass
        return SignalStrength.WEAK

    def _filter_by_importance(self, entries: List[Dict]) -> List[Dict]:
        """Filter entries by minimum importance."""
        importance_order = ["critical", "high", "medium", "low"]
        min_idx = importance_order.index(self.config.min_importance)

        filtered = []
        for entry in entries:
            imp = entry.get("importance", "medium")
            if imp in importance_order:
                imp_idx = importance_order.index(imp)
                if imp_idx <= min_idx:
                    filtered.append(entry)
        return filtered

    def _filter_by_source_type(self, entries: List[Dict]) -> List[Dict]:
        """Filter entries by allowed source types."""
        allowed = set(self.config.allowed_source_types)
        return [e for e in entries if e.get("source_type", "agent") in allowed]


# ============================================================================
# Prompt Improvement Rules
# ============================================================================

class PromptStructureClarityRule(BaseExtractionRule):
    """
    Detects prompt structure issues through repeated low coherence scores
    and high-importance unresolved questions in reasoning.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Group evaluations by agent/workflow
        evals_by_scope = defaultdict(list)
        for eval_data in evaluations:
            scope_id = eval_data.get("agent_id") or eval_data.get("workflow_id") or "unknown"
            evals_by_scope[scope_id].append(eval_data)

        # Check each scope for consistent low coherence
        for scope_id, scope_evals in evals_by_scope.items():
            if len(scope_evals) < self.config.min_evidence_count:
                continue

            # Count low coherence occurrences
            low_coherence_count = sum(
                1 for e in scope_evals
                if e.get("coherence_score", 100) < self.config.metric_thresholds.get("coherence", 60)
            )

            if low_coherence_count < self.config.min_evidence_count:
                continue

            # Check for supporting workspace evidence
            scope_entries = [
                e for e in workspace_entries
                if e.get("scope_id") == scope_id or e.get("agent_id") == scope_id
            ]
            high_importance_entries = self._filter_by_importance(scope_entries)
            unresolved_questions = [
                e for e in high_importance_entries
                if e.get("entry_type") == "question" and e.get("status") != "resolved"
            ]

            # Calculate weight
            weight_sum = 0.0
            for e in scope_evals:
                imp = e.get("importance", "medium")
                src = e.get("source_type", "agent")
                weight_sum += SignalWeightCalculator.calculate_weight(
                    imp, src, 1, 24  # Recent
                )

            strength = self._calculate_strength(low_coherence_count, weight_sum)

            signals.append(LearningSignalCreate(
                signal_type=LearningSignalType.PROMPT_STRUCTURE_CLARITY,
                strength=strength,
                source=SignalSource.EVALUATION_METRIC,
                scope_type="agent",
                scope_id=scope_id,
                evidence_count=low_coherence_count,
                supporting_execution_ids=[e.get("execution_id") for e in scope_evals if e.get("execution_id")],
                title=f"Repeated low coherence in {scope_id}",
                description=(
                    f"Agent {scope_id} shows consistent low coherence scores "
                    f"({low_coherence_count}/{len(scope_evals)} executions below threshold). "
                    f"Accompanied by {len(unresolved_questions)} high-importance unresolved questions."
                ),
                proposed_action="Review prompt structure for ambiguous instructions or missing context",
                metadata={
                    "avg_coherence": sum(e.get("coherence_score", 0) for e in scope_evals) / len(scope_evals),
                    "unresolved_question_count": len(unresolved_questions),
                    "threshold": self.config.metric_thresholds.get("coherence", 60)
                },
                salience="high" if low_coherence_count >= 5 else "medium"
            ))

        return signals


class PromptMissingContextRule(BaseExtractionRule):
    """
    Detects missing prompt context through repeated tool failures
    and requests for information that weren't anticipated.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Look for patterns: tool_use_efficiency low + specific questions about missing info
        entries_by_scope = defaultdict(list)
        for entry in workspace_entries:
            scope_id = entry.get("agent_id") or entry.get("workflow_id") or "unknown"
            entries_by_scope[scope_id].append(entry)

        for scope_id, entries in entries_by_scope.items():
            # Filter for tool-source entries
            tool_entries = [
                e for e in entries
                if e.get("source_type") == "tool"
            ]
            high_importance = self._filter_by_importance(tool_entries)

            # Look for missing information patterns
            missing_info_keywords = ["missing", "unavailable", "not found", "required", "needed"]
            missing_info_entries = [
                e for e in high_importance
                if any(kw in str(e.get("content", {})).lower() for kw in missing_info_keywords)
            ]

            if len(missing_info_entries) < self.config.min_evidence_count:
                continue

            # Correlate with evaluation metrics
            scope_evals = [
                e for e in evaluations
                if e.get("agent_id") == scope_id or e.get("workflow_id") == scope_id
            ]
            low_tool_efficiency = [
                e for e in scope_evals
                if e.get("tool_use_efficiency", 100) < self.config.metric_thresholds.get("tool_efficiency", 50)
            ]

            if not low_tool_efficiency:
                continue

            signals.append(LearningSignalCreate(
                signal_type=LearningSignalType.PROMPT_MISSING_CONTEXT,
                strength=SignalStrength.MODERATE,
                source=SignalSource.WORKSPACE_ENTRY,
                scope_type="agent",
                scope_id=scope_id,
                evidence_count=len(missing_info_entries),
                supporting_execution_ids=[e.get("execution_id") for e in missing_info_entries if e.get("execution_id")],
                title=f"Missing context patterns in {scope_id}",
                description=(
                    f"Agent {scope_id} repeatedly encounters missing information "
                    f"({len(missing_info_entries)} high-importance instances) "
                    f"correlated with low tool efficiency."
                ),
                proposed_action="Add context requirements to prompt (API keys, data sources, prerequisites)",
                metadata={
                    "missing_info_entries": len(missing_info_entries),
                    "avg_tool_efficiency": sum(e.get("tool_use_efficiency", 0) for e in scope_evals) / max(len(scope_evals), 1)
                },
                salience="medium"
            ))

        return signals


# ============================================================================
# Routing Adjustment Rules
# ============================================================================

class RoutingMisalignmentRule(BaseExtractionRule):
    """
    Detects when queries are consistently routed to the wrong agent
    based on execution outcomes and workspace contradictions.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Group executions by assigned agent
        executions_by_agent = defaultdict(list)
        for exec_data in executions:
            agent_id = exec_data.get("agent_id")
            if agent_id:
                executions_by_agent[agent_id].append(exec_data)

        for agent_id, agent_execs in executions_by_agent.items():
            if len(agent_execs) < self.config.min_evidence_count:
                continue

            # Count failures/poor outcomes
            failure_count = sum(
                1 for e in agent_execs
                if e.get("status") == "failed" or e.get("success") is False
            )

            if failure_count < self.config.min_evidence_count:
                continue

            # Check for contradiction patterns in workspace
            contradictions = [
                e for e in workspace_entries
                if e.get("entry_type") == "contradiction"
                and e.get("agent_id") == agent_id
            ]

            if not contradictions:
                continue

            signals.append(LearningSignalCreate(
                signal_type=LearningSignalType.ROUTING_MISALIGNMENT,
                strength=SignalStrength.STRONG if failure_count >= 5 else SignalStrength.MODERATE,
                source=SignalSource.EXECUTION_OUTCOME,
                scope_type="agent",
                scope_id=agent_id,
                evidence_count=failure_count,
                supporting_execution_ids=[e.get("id") for e in agent_execs if e.get("id")],
                title=f"Routing misalignment for {agent_id}",
                description=(
                    f"Agent {agent_id} fails {failure_count}/{len(agent_execs)} executions "
                    f"with {len(contradictions)} reasoning contradictions detected."
                ),
                proposed_action="Review routing criteria - queries may be better suited for a different agent",
                metadata={
                    "failure_rate": failure_count / len(agent_execs),
                    "contradiction_count": len(contradictions)
                },
                salience="high"
            ))

        return signals


# ============================================================================
# Tool Preference Rules
# ============================================================================

class ToolPreferenceEmergentRule(BaseExtractionRule):
    """
    Detects emergent tool preferences when specific tools
    consistently produce better outcomes.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Track tool usage by agent
        tool_usage_by_agent = defaultdict(lambda: defaultdict(list))

        for entry in workspace_entries:
            if entry.get("source_type") != "tool":
                continue

            agent_id = entry.get("agent_id") or entry.get("source_agent")
            tool_name = entry.get("content", {}).get("tool_name") or entry.get("content", {}).get("tool")

            if not agent_id or not tool_name:
                continue

            execution_id = entry.get("execution_id")
            if execution_id:
                tool_usage_by_agent[agent_id][tool_name].append(execution_id)

        # Find successful tool patterns
        for agent_id, tools in tool_usage_by_agent.items():
            for tool_name, exec_ids in tools.items():
                if len(exec_ids) < self.config.min_evidence_count:
                    continue

                # Check success rate for executions using this tool
                tool_execs = [e for e in executions if e.get("id") in exec_ids]
                if not tool_execs:
                    continue

                success_count = sum(1 for e in tool_execs if e.get("status") == "completed")
                success_rate = success_count / len(tool_execs)

                if success_rate >= self.config.metric_thresholds.get("success_rate", 0.8):
                    # Compare to agent's overall success rate
                    all_agent_execs = [e for e in executions if e.get("agent_id") == agent_id]
                    overall_success = sum(1 for e in all_agent_execs if e.get("status") == "completed") / max(len(all_agent_execs), 1)

                    if success_rate > overall_success + 0.1:  # At least 10% better
                        signals.append(LearningSignalCreate(
                            signal_type=LearningSignalType.TOOL_PREFERENCE_EMERGENT,
                            strength=SignalStrength.MODERATE,
                            source=SignalSource.CROSS_EXECUTION_PATTERN,
                            scope_type="agent",
                            scope_id=agent_id,
                            evidence_count=len(exec_ids),
                            supporting_execution_ids=exec_ids,
                            title=f"Successful tool preference: {tool_name}",
                            description=(
                                f"Agent {agent_id} has {success_rate:.1%} success rate with {tool_name} "
                                f"vs {overall_success:.1%} overall across {len(exec_ids)} executions."
                            ),
                            proposed_action=f"Prioritize {tool_name} in agent's tool selection",
                            metadata={
                                "tool_name": tool_name,
                                "tool_success_rate": success_rate,
                                "overall_success_rate": overall_success,
                                "improvement": success_rate - overall_success
                            },
                            salience="medium"
                        ))

        return signals


class ToolInefficiencyRule(BaseExtractionRule):
    """
    Detects when tools consistently cause problems
    (timeouts, errors, low-quality outputs).
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Track tool failures from workspace entries
        tool_failures = defaultdict(lambda: defaultdict(int))
        tool_entry_map = defaultdict(lambda: defaultdict(list))

        for entry in workspace_entries:
            if entry.get("source_type") != "tool":
                continue

            content = entry.get("content", {})
            if content.get("error") or content.get("failed") or content.get("timeout"):
                tool_name = content.get("tool_name") or content.get("tool")
                agent_id = entry.get("agent_id") or entry.get("source_agent")

                if tool_name and agent_id:
                    tool_failures[agent_id][tool_name] += 1
                    tool_entry_map[agent_id][tool_name].append(entry)

        for agent_id, tools in tool_failures.items():
            for tool_name, fail_count in tools.items():
                if fail_count < self.config.min_evidence_count:
                    continue

                entries = tool_entry_map[agent_id][tool_name]
                high_importance_failures = self._filter_by_importance(entries)

                signals.append(LearningSignalCreate(
                    signal_type=LearningSignalType.TOOL_INEFFICIENCY,
                    strength=SignalStrength.STRONG if len(high_importance_failures) >= fail_count / 2 else SignalStrength.MODERATE,
                    source=SignalSource.WORKSPACE_ENTRY,
                    scope_type="agent",
                    scope_id=agent_id,
                    evidence_count=fail_count,
                    supporting_execution_ids=[e.get("execution_id") for e in entries if e.get("execution_id")],
                    title=f"Tool inefficiency detected: {tool_name}",
                    description=(
                        f"Agent {agent_id} experiences {fail_count} failures with {tool_name}. "
                        f"{len(high_importance_failures)} are high-importance issues."
                    ),
                    proposed_action=f"Review {tool_name} configuration, consider alternative tools or error handling",
                    metadata={
                        "tool_name": tool_name,
                        "failure_count": fail_count,
                        "high_importance_failures": len(high_importance_failures)
                    },
                    salience="high"
                ))

        return signals


# ============================================================================
# Reasoning Pattern Rules
# ============================================================================

class RepeatedUnresolvedQuestionsRule(BaseExtractionRule):
    """
    Detects when the same questions remain unresolved across executions.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Group questions by their content/semantic similarity
        questions_by_scope = defaultdict(list)

        for entry in workspace_entries:
            if entry.get("entry_type") != "question":
                continue

            if entry.get("status") == "resolved":
                continue

            scope_id = entry.get("agent_id") or entry.get("workflow_id") or "unknown"
            questions_by_scope[scope_id].append(entry)

        for scope_id, questions in questions_by_scope.items():
            high_importance = self._filter_by_importance(questions)

            if len(high_importance) < self.config.min_evidence_count:
                continue

            # Group by question keywords (simple semantic clustering)
            question_groups = defaultdict(list)
            for q in high_importance:
                question_text = q.get("content", {}).get("question", "")
                # Simple keyword-based grouping
                keywords = set(question_text.lower().split())
                for keyword in keywords:
                    if len(keyword) > 3:  # Ignore short words
                        question_groups[keyword].append(q)

            # Find repeated themes
            for keyword, related_questions in question_groups.items():
                if len(related_questions) < self.config.min_evidence_count:
                    continue

                unique_executions = set(q.get("execution_id") for q in related_questions if q.get("execution_id"))

                signals.append(LearningSignalCreate(
                    signal_type=LearningSignalType.REPEATED_UNRESOLVED_QUESTIONS,
                    strength=SignalStrength.MODERATE,
                    source=SignalSource.WORKSPACE_ENTRY,
                    scope_type="agent",
                    scope_id=scope_id,
                    evidence_count=len(related_questions),
                    supporting_execution_ids=list(unique_executions),
                    title=f"Repeated unresolved questions in {scope_id}",
                    description=(
                        f"{len(related_questions)} high-importance questions around '{keyword}' "
                        f"remain unresolved across {len(unique_executions)} executions."
                    ),
                    proposed_action=f"Address '{keyword}' topic in agent prompt or system instructions",
                    metadata={
                        "theme": keyword,
                        "question_count": len(related_questions),
                        "execution_count": len(unique_executions)
                    },
                    salience="medium"
                ))

        return signals


class RepeatedContradictionRule(BaseExtractionRule):
    """
    Detects when similar contradictions appear repeatedly in reasoning.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Look for contradictions in syntheses
        contradictions_by_scope = defaultdict(list)

        for synth in syntheses:
            if synth.get("synthesis_type") != "contradictions":
                continue

            scope_id = synth.get("agent_id") or synth.get("workflow_id") or "unknown"
            contradictions_by_scope[scope_id].append(synth)

        for scope_id, synths in contradictions_by_scope.items():
            if len(synths) < self.config.min_evidence_count:
                continue

            # Extract contradiction themes from synthesis content
            all_contradictions = []
            for synth in synths:
                content = synth.get("content", {})
                contradictions = content.get("contradictions", [])
                all_contradictions.extend(contradictions)

            if len(all_contradictions) < self.config.min_evidence_count:
                continue

            # Group by themes
            contradiction_themes = defaultdict(int)
            for c in all_contradictions:
                if isinstance(c, dict):
                    theme = c.get("theme", c.get("category", "unknown"))
                else:
                    theme = str(c)[:50]
                contradiction_themes[theme] += 1

            # Find dominant themes
            for theme, count in contradiction_themes.items():
                if count < self.config.min_evidence_count:
                    continue

                signals.append(LearningSignalCreate(
                    signal_type=LearningSignalType.REPEATED_CONTRADICTION,
                    strength=SignalStrength.STRONG if count >= 5 else SignalStrength.MODERATE,
                    source=SignalSource.SYNTHESIS_OUTPUT,
                    scope_type="agent",
                    scope_id=scope_id,
                    evidence_count=count,
                    supporting_execution_ids=[s.get("execution_id") for s in synths if s.get("execution_id")],
                    title=f"Repeated contradiction pattern: {theme}",
                    description=(
                        f"Contradiction theme '{theme}' appears {count} times "
                        f"across {len(synths)} synthesis outputs."
                    ),
                    proposed_action=f"Review prompt and knowledge base for inconsistencies around '{theme}'",
                    metadata={
                        "theme": theme,
                        "synthesis_count": len(synths),
                        "total_contradictions": len(all_contradictions)
                    },
                    salience="high"
                ))

        return signals


class RiskPatternCriticalRule(BaseExtractionRule):
    """
    Detects critical risk patterns that appear in workspace reasoning.
    """

    def extract(
        self,
        evaluations: List[Dict[str, Any]],
        workspace_entries: List[Dict[str, Any]],
        syntheses: List[Dict[str, Any]],
        executions: List[Dict[str, Any]]
    ) -> List[LearningSignalCreate]:
        signals = []

        # Look for critical/high importance risk entries
        risk_entries = [
            e for e in workspace_entries
            if e.get("importance") in ["critical", "high"]
            and (
                "risk" in str(e.get("content", {})).lower()
                or "danger" in str(e.get("content", {})).lower()
                or "failure" in str(e.get("content", {})).lower()
                or e.get("entry_type") in ["risk", "warning"]
            )
        ]

        # Group by scope
        risks_by_scope = defaultdict(list)
        for entry in risk_entries:
            scope_id = entry.get("agent_id") or entry.get("workflow_id") or "unknown"
            risks_by_scope[scope_id].append(entry)

        for scope_id, risks in risks_by_scope.items():
            if len(risks) < self.config.min_evidence_count:
                continue

            # Correlate with evaluation risk scores
            scope_evals = [
                e for e in evaluations
                if e.get("agent_id") == scope_id or e.get("workflow_id") == scope_id
            ]
            high_risk_evals = [
                e for e in scope_evals
                if e.get("risk_score", 0) > self.config.metric_thresholds.get("risk", 70)
            ]

            if not high_risk_evals:
                continue

            critical_count = sum(1 for r in risks if r.get("importance") == "critical")

            signals.append(LearningSignalCreate(
                signal_type=LearningSignalType.RISK_PATTERN_CRITICAL,
                strength=SignalStrength.CONCLUSIVE if critical_count >= 2 else SignalStrength.STRONG,
                source=SignalSource.WORKSPACE_ENTRY,
                scope_type="agent",
                scope_id=scope_id,
                evidence_count=len(risks),
                supporting_execution_ids=[e.get("execution_id") for e in risks if e.get("execution_id")],
                title=f"Critical risk pattern in {scope_id}",
                description=(
                    f"{len(risks)} high/critical importance risks detected, "
                    f"{critical_count} are critical-level. "
                    f"Correlated with {len(high_risk_evals)} high-risk evaluations."
                ),
                proposed_action="Review risk mitigation strategies and update safety guidelines",
                metadata={
                    "risk_count": len(risks),
                    "critical_count": critical_count,
                    "avg_risk_score": sum(e.get("risk_score", 0) for e in scope_evals) / max(len(scope_evals), 1)
                },
                salience="critical"
            ))

        return signals


# ============================================================================
# Rule Registry
# ============================================================================

DEFAULT_EXTRACTION_RULES: list[type[BaseExtractionRule]] = [
    # Prompt improvement
    PromptStructureClarityRule,
    PromptMissingContextRule,

    # Routing adjustment
    RoutingMisalignmentRule,

    # Tool preference
    ToolPreferenceEmergentRule,
    ToolInefficiencyRule,

    # Reasoning pattern
    RepeatedUnresolvedQuestionsRule,
    RepeatedContradictionRule,
    RiskPatternCriticalRule,
]


def get_default_rule_configs() -> dict[LearningSignalType, ExtractionRule]:
    """Get default configuration for all extraction rules."""
    configs = {}

    # Prompt improvement rules
    configs[LearningSignalType.PROMPT_STRUCTURE_CLARITY] = ExtractionRule(
        signal_type=LearningSignalType.PROMPT_STRUCTURE_CLARITY,
        name="Prompt Structure Clarity",
        description="Detects unclear prompt structure through low coherence and unresolved questions",
        min_evidence_count=3,
        min_importance="medium",
        allowed_source_types=["agent", "tool", "system"],
        metric_thresholds={"coherence": 60, "reasoning_quality": 60}
    )

    configs[LearningSignalType.PROMPT_MISSING_CONTEXT] = ExtractionRule(
        signal_type=LearningSignalType.PROMPT_MISSING_CONTEXT,
        name="Missing Prompt Context",
        description="Detects missing context through tool failures and missing information patterns",
        min_evidence_count=2,
        min_importance="high",
        allowed_source_types=["tool", "system"],
        metric_thresholds={"tool_efficiency": 50}
    )

    # Routing adjustment rules
    configs[LearningSignalType.ROUTING_MISALIGNMENT] = ExtractionRule(
        signal_type=LearningSignalType.ROUTING_MISALIGNMENT,
        name="Routing Misalignment",
        description="Detects when queries are routed to the wrong agent",
        min_evidence_count=3,
        min_importance="medium",
        allowed_source_types=["agent", "system"],
        metric_thresholds={"success_rate": 0.5}
    )

    # Tool preference rules
    configs[LearningSignalType.TOOL_PREFERENCE_EMERGENT] = ExtractionRule(
        signal_type=LearningSignalType.TOOL_PREFERENCE_EMERGENT,
        name="Emergent Tool Preference",
        description="Detects tools that consistently produce better outcomes",
        min_evidence_count=4,
        min_importance="medium",
        allowed_source_types=["tool", "agent"],
        metric_thresholds={"success_rate": 0.8}
    )

    configs[LearningSignalType.TOOL_INEFFICIENCY] = ExtractionRule(
        signal_type=LearningSignalType.TOOL_INEFFICIENCY,
        name="Tool Inefficiency",
        description="Detects tools that consistently cause problems",
        min_evidence_count=3,
        min_importance="medium",
        allowed_source_types=["tool"],
        metric_thresholds={"failure_rate": 0.3}
    )

    # Reasoning pattern rules
    configs[LearningSignalType.REPEATED_UNRESOLVED_QUESTIONS] = ExtractionRule(
        signal_type=LearningSignalType.REPEATED_UNRESOLVED_QUESTIONS,
        name="Repeated Unresolved Questions",
        description="Detects when questions remain unresolved across executions",
        min_evidence_count=3,
        min_importance="high",
        allowed_source_types=["agent", "tool"],
        metric_thresholds={}
    )

    configs[LearningSignalType.REPEATED_CONTRADICTION] = ExtractionRule(
        signal_type=LearningSignalType.REPEATED_CONTRADICTION,
        name="Repeated Contradictions",
        description="Detects repeated contradiction patterns in reasoning",
        min_evidence_count=3,
        min_importance="medium",
        allowed_source_types=["agent", "synthesis"],
        metric_thresholds={}
    )

    configs[LearningSignalType.RISK_PATTERN_CRITICAL] = ExtractionRule(
        signal_type=LearningSignalType.RISK_PATTERN_CRITICAL,
        name="Critical Risk Pattern",
        description="Detects critical risk patterns in reasoning",
        min_evidence_count=2,
        min_importance="high",
        allowed_source_types=["agent", "tool", "system"],
        metric_thresholds={"risk": 70}
    )

    return configs

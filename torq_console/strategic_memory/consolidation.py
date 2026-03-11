"""
Memory Consolidation Engine

Converts patterns and insights into durable strategic memory candidates.

This is the gatekeeper between "interesting pattern" and "institutional memory."
Only patterns that demonstrate repeatability, validity, and broad applicability
should graduate to strategic memory status.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .models import (
    MemoryCandidate,
    MemoryType,
    MemoryScope,
    StrategicMemory,
    StrategicMemoryCreate,
    ConsolidationRule,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Default Consolidation Rules
# ============================================================================

DEFAULT_CONSOLIDATION_RULES = [
    # Playbook: High-success planning patterns
    ConsolidationRule(
        name="planning_playbook_extraction",
        description="Extract playbooks from successful planning workflow patterns",
        min_workspace_count=5,
        min_execution_count=20,
        min_success_rate=0.70,
        min_confidence=0.75,
        memory_type=MemoryType.PLAYBOOK,
        default_scope=MemoryScope.WORKFLOW_TYPE,
        default_durability=0.70,
        content_template={
            "guidance": "",
            "triggers": [],
            "steps": [],
            "expected_outcome": ""
        }
    ),

    # Warning: Recurring failure patterns
    ConsolidationRule(
        name="warning_pattern_extraction",
        description="Extract warnings from recurring failure or degradation patterns",
        min_workspace_count=3,
        min_execution_count=10,
        min_success_rate=0.0,  # Warnings from failures
        min_confidence=0.65,
        memory_type=MemoryType.WARNING,
        default_scope=MemoryScope.DOMAIN,
        default_durability=0.60,
        content_template={
            "risk_description": "",
            "severity": "medium",
            "mitigation": "",
            "anti_patterns": []
        }
    ),

    # Heuristic: Proven reasoning shortcuts
    ConsolidationRule(
        name="heuristic_extraction",
        description="Extract heuristics from validated routing and tool preference patterns",
        min_workspace_count=4,
        min_execution_count=15,
        min_success_rate=0.75,
        min_confidence=0.70,
        memory_type=MemoryType.HEURISTIC,
        default_scope=MemoryScope.DOMAIN,
        default_durability=0.65,
        content_template={
            "rule": "",
            "rationale": "",
            "exceptions": []
        }
    ),

    # Adaptation Lesson: Validated changes
    ConsolidationRule(
        name="adaptation_lesson_extraction",
        description="Extract lessons from experiments that successfully promoted",
        min_workspace_count=2,  # Can be narrower since validated by experiment
        min_execution_count=10,
        min_success_rate=0.80,  # High success rate from experiment
        min_confidence=0.80,
        memory_type=MemoryType.ADAPTATION_LESSON,
        default_scope=MemoryScope.WORKFLOW_TYPE,
        default_durability=0.75,
        content_template={
            "lesson": "",
            "adaptation_type": "",
            "impact_summary": {},
            "validation_status": "proven"
        }
    ),
]


# ============================================================================
# Consolidation Engine
# ============================================================================

class MemoryConsolidationEngine:
    """
    Converts cross-workspace patterns into strategic memory candidates.

    Responsibilities:
    - Identify patterns meeting consolidation thresholds
    - Score candidate confidence, durability, applicability
    - Generate memory content from pattern data
    - Propose memories for governance review
    """

    def __init__(self, supabase_client, rules: Optional[List[ConsolidationRule]] = None):
        self.supabase = supabase_client
        self.rules = rules or DEFAULT_CONSOLIDATION_RULES

    async def find_memory_candidates(
        self,
        days_back: int = 30
    ) -> List[MemoryCandidate]:
        """
        Find patterns that qualify as memory candidates.

        Returns candidates sorted by confidence score.
        """
        since = datetime.now() - timedelta(days=days_back)

        candidates = []

        # Check each consolidation rule
        for rule in self.rules:
            rule_candidates = await self._apply_consolidation_rule(rule, since)
            candidates.extend(rule_candidates)

        # Sort by composite score
        candidates.sort(
            key=lambda c: (
                c.confidence_score * 0.4 +
                c.durability_score * 0.3 +
                c.applicability_score * 0.3
            ),
            reverse=True
        )

        logger.info(f"Found {len(candidates)} memory candidates from {len(self.rules)} rules")
        return candidates

    async def consolidate_from_pattern(
        self,
        pattern_id: str,
        pattern_data: Dict[str, Any]
    ) -> Optional[MemoryCandidate]:
        """
        Create a memory candidate from a specific pattern.

        Used when a pattern is manually nominated for consolidation.
        """
        # Extract pattern metadata
        pattern_type = pattern_data.get("pattern_type", "")
        domain = pattern_data.get("domain", "")

        # Find matching rule
        matching_rule = self._find_rule_for_pattern(pattern_type, domain)
        if not matching_rule:
            logger.warning(f"No consolidation rule for pattern type: {pattern_type}")
            return None

        # Build candidate
        candidate = await self._build_candidate_from_pattern(
            matching_rule,
            pattern_id,
            pattern_data
        )

        return candidate

    async def propose_memory(
        self,
        candidate: MemoryCandidate
    ) -> StrategicMemoryCreate:
        """
        Convert a candidate into a memory create request.

        This is the final step before governance review.
        """
        # Calculate initial confidence from component scores
        initial_confidence = (
            candidate.confidence_score * 0.5 +
            candidate.durability_score * 0.3 +
            candidate.applicability_score * 0.2
        )

        # Calculate expiration based on durability
        # High durability = longer expiration
        base_days = 90
        durability_multiplier = 1 + (candidate.durability_score * 2)  # 1-3x
        expires_in_days = int(base_days * durability_multiplier)

        return StrategicMemoryCreate(
            memory_type=candidate.memory_type,
            title=candidate.title,
            domain=candidate.domain,
            scope=candidate.proposed_scope,
            scope_key=candidate.proposed_scope_key,
            memory_content=candidate.proposed_content,
            source_pattern_ids=candidate.source_patterns,
            source_insight_ids=candidate.source_insights,
            source_experiment_ids=candidate.source_experiments,
            initial_confidence=initial_confidence,
            initial_durability=candidate.durability_score,
            expires_in_days=expires_in_days
        )

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _apply_consolidation_rule(
        self,
        rule: ConsolidationRule,
        since: datetime
    ) -> List[MemoryCandidate]:
        """Apply a consolidation rule to find matching patterns."""
        candidates = []

        # Query for patterns matching the rule's criteria
        patterns = await self._query_eligible_patterns(rule, since)

        logger.info(f"Rule '{rule.name}' found {len(patterns)} eligible patterns")

        for pattern in patterns:
            # Check if pattern already has a memory
            existing_memory = await self._check_existing_memory(pattern["id"])
            if existing_memory:
                logger.debug(f"Pattern {pattern['id']} already has memory {existing_memory}")
                continue

            # Build candidate from pattern
            candidate = await self._build_candidate_from_pattern(rule, pattern["id"], pattern)
            if candidate:
                candidates.append(candidate)

        return candidates

    async def _query_eligible_patterns(
        self,
        rule: ConsolidationRule,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Query patterns that meet the consolidation threshold."""
        try:
            # Query from cross_workspace_patterns table (Phase 4G)
            result = self.supabase.table("cross_workspace_patterns").select("*").gte("created_at", since.isoformat()).execute()

            patterns = result.data or []

            # Filter by rule thresholds
            eligible = []
            for pattern in patterns:
                # Check workspace count
                workspace_count = pattern.get("workspace_count", 0)
                if workspace_count < rule.min_workspace_count:
                    continue

                # Check execution count
                execution_count = pattern.get("execution_count", 0)
                if execution_count < rule.min_execution_count:
                    continue

                # Check success rate if required
                if rule.min_success_rate > 0:
                    success_rate = pattern.get("success_rate", 0)
                    if success_rate < rule.min_success_rate:
                        continue

                eligible.append(pattern)

            return eligible

        except Exception as e:
            logger.error(f"Error querying eligible patterns: {e}")
            return []

    async def _check_existing_memory(self, pattern_id: str) -> Optional[str]:
        """Check if a pattern already has a strategic memory."""
        try:
            result = self.supabase.table("strategic_memories").select("id").contains("source_pattern_ids", [pattern_id]).execute()

            if result.data:
                return result.data[0]["id"]
            return None

        except Exception as e:
            logger.error(f"Error checking existing memory: {e}")
            return None

    async def _build_candidate_from_pattern(
        self,
        rule: ConsolidationRule,
        pattern_id: str,
        pattern_data: Dict[str, Any]
    ) -> Optional[MemoryCandidate]:
        """Build a memory candidate from pattern data and rule template."""
        try:
            # Extract pattern details
            pattern_type = pattern_data.get("pattern_type", "")
            domain = pattern_data.get("domain", pattern_data.get("category"))
            workflow_type = pattern_data.get("workflow_type")

            # Generate title from pattern
            title = self._generate_title(pattern_data, rule.memory_type)

            # Generate content using rule template
            proposed_content = self._generate_content(
                pattern_data,
                rule.content_template
            )

            # Determine scope
            proposed_scope = rule.default_scope
            proposed_scope_key = None

            if workflow_type and rule.default_scope == MemoryScope.WORKFLOW_TYPE:
                proposed_scope_key = workflow_type
            elif domain and rule.default_scope == MemoryScope.DOMAIN:
                proposed_scope_key = domain

            # Calculate scores
            confidence_score = self._calculate_confidence(pattern_data, rule)
            durability_score = self._calculate_durability(pattern_data, rule)
            applicability_score = self._calculate_applicability(pattern_data, rule)

            return MemoryCandidate(
                memory_type=rule.memory_type,
                title=title,
                proposed_content=proposed_content,
                proposed_scope=proposed_scope,
                proposed_scope_key=proposed_scope_key,
                domain=domain,
                confidence_score=confidence_score,
                durability_score=durability_score,
                applicability_score=applicability_score,
                source_patterns=[pattern_id],
                workspace_count=pattern_data.get("workspace_count", 0),
                execution_count=pattern_data.get("execution_count", 0),
                success_count=int(
                    pattern_data.get("execution_count", 0) *
                    pattern_data.get("success_rate", 0)
                )
            )

        except Exception as e:
            logger.error(f"Error building candidate from pattern: {e}")
            return None

    def _generate_title(self, pattern_data: Dict[str, Any], memory_type: MemoryType) -> str:
        """Generate a descriptive title for the memory."""
        pattern_type = pattern_data.get("pattern_type", "unknown")
        domain = pattern_data.get("domain", "")
        workflow_type = pattern_data.get("workflow_type", "")

        if memory_type == MemoryType.PLAYBOOK:
            base = f"{workflow_type or domain} Playbook" if workflow_type or domain else "Workflow Playbook"
            if pattern_type == "planning_structure":
                return f"Planning Structure {base}"
            return base

        elif memory_type == MemoryType.WARNING:
            if pattern_type == "coherence_actionability_tradeoff":
                return "Prompt Verbosity vs Actionability Trade-off"
            return f"{domain.title()} Warning" if domain else "System Warning"

        elif memory_type == MemoryType.HEURISTIC:
            if pattern_type == "tool_preference":
                tool = pattern_data.get("preferred_tool", "unknown")
                return f"Prefer {tool} for {domain or 'specified'} Tasks"
            return f"{domain.title()} Heuristic" if domain else "Reasoning Heuristic"

        elif memory_type == MemoryType.ADAPTATION_LESSON:
            adaptation_type = pattern_data.get("adaptation_type", "change")
            return f"Validated {adaptation_type.title()} Lesson"

        return "Strategic Memory"

    def _generate_content(
        self,
        pattern_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate memory content from pattern data and template."""
        content = template.copy()

        # Fill in template fields from pattern data
        if "guidance" in template and "description" in pattern_data:
            content["guidance"] = pattern_data["description"]

        if "risk_description" in template:
            content["risk_description"] = pattern_data.get("risk_description", "")

        if "rule" in template:
            content["rule"] = pattern_data.get("rule", pattern_data.get("description", ""))

        if "lesson" in template:
            content["lesson"] = pattern_data.get("lesson", pattern_data.get("description", ""))

        # Add triggers from pattern
        if "triggers" in content:
            content["triggers"] = pattern_data.get("triggers", [])

        # Add workflow types
        if "workflow_types" in content:
            content["workflow_types"] = [pattern_data.get("workflow_type")] if pattern_data.get("workflow_type") else []

        # Add impact summary if available
        if "impact_summary" in content and "impact" in pattern_data:
            content["impact_summary"] = pattern_data["impact"]

        return content

    def _calculate_confidence(self, pattern_data: Dict[str, Any], rule: ConsolidationRule) -> float:
        """Calculate confidence score for the candidate."""
        score = 0.0

        # Base score from rule minimum
        score = rule.min_confidence

        # Boost from workspace count (more workspaces = more confidence)
        workspace_count = pattern_data.get("workspace_count", 0)
        if workspace_count > rule.min_workspace_count:
            boost = min((workspace_count - rule.min_workspace_count) * 0.05, 0.15)
            score += boost

        # Boost from execution count
        execution_count = pattern_data.get("execution_count", 0)
        if execution_count > rule.min_execution_count * 2:
            boost = min(0.10, 0.05)
            score += boost

        # Boost from success rate
        success_rate = pattern_data.get("success_rate", 0)
        if success_rate > rule.min_success_rate:
            score += (success_rate - rule.min_success_rate) * 0.2

        return min(score, 1.0)

    def _calculate_durability(self, pattern_data: Dict[str, Any], rule: ConsolidationRule) -> float:
        """Calculate durability score for the candidate."""
        score = rule.default_durability

        # Higher durability for cross-domain patterns
        if not pattern_data.get("domain"):
            score += 0.15

        # Higher durability for long-observed patterns
        created_at = pattern_data.get("created_at")
        if created_at:
            age_days = (datetime.now() - datetime.fromisoformat(created_at)).days
            if age_days > 30:
                score += 0.10

        # Lower durability for volatile patterns
        variance = pattern_data.get("variance", 0)
        if variance > 0.2:
            score -= 0.15

        return max(0.0, min(score, 1.0))

    def _calculate_applicability(self, pattern_data: Dict[str, Any], rule: ConsolidationRule) -> float:
        """Calculate applicability score (how broadly applicable)."""
        score = 0.5  # Base applicability

        # Broad domain = higher applicability
        if not pattern_data.get("domain"):
            score += 0.25

        # Multiple workflow types = higher applicability
        workflow_types = pattern_data.get("workflow_types", [])
        if len(workflow_types) > 1:
            score += 0.15

        # Global scope = highest applicability
        scope = pattern_data.get("scope", "")
        if scope == "global":
            score += 0.20

        return min(score, 1.0)

    def _find_rule_for_pattern(self, pattern_type: str, domain: str) -> Optional[ConsolidationRule]:
        """Find the appropriate consolidation rule for a pattern."""
        for rule in self.rules:
            if rule.memory_type == MemoryType.WARNING:
                if "failure" in pattern_type or "risk" in pattern_type or "warning" in pattern_type:
                    return rule
            elif rule.memory_type == MemoryType.HEURISTIC:
                if "routing" in pattern_type or "tool" in pattern_type:
                    return rule
            elif rule.memory_type == MemoryType.ADAPTATION_LESSON:
                if "adaptation" in pattern_type or "experiment" in pattern_type:
                    return rule
            elif rule.memory_type == MemoryType.PLAYBOOK:
                if "planning" in pattern_type or "workflow" in pattern_type:
                    return rule

        return None

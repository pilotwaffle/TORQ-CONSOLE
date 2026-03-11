"""
Phase 4G Milestone 2: Pattern Extraction & Aggregation Pipeline

This module provides the pipeline for extracting pattern candidates from
actual platform history (artifacts, memory, insights) and aggregating
them into governed pattern objects.

Key Components:
- PatternCandidateExtractor: Scans sources for pattern evidence
- PatternAggregationEngine: Groups evidence into candidates
- PatternScoringService: Scores candidates on multiple dimensions
- PatternPersistenceService: Persists candidates with lineage
- PatternRejectionLogger: Logs why candidates were rejected

Layer Architecture:
- Artifact = Raw execution output (Phase 5.3)
- Memory = Validated carry-forward knowledge (Phase 4H.1)
- Insight = Curated reusable intelligence (Insight Publishing M1-M4)
- Pattern = Recurring, cross-execution structure (This Phase - 4G)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import from pattern_models
from .pattern_models import (
    PatternType,
    PatternLifecycleState,
    PatternSourceType,
    PatternCreate,
    PatternUpdate,
    Pattern,
    PatternSourceReference,
    PatternQualityMetrics,
    PatternObservation,
    AggregationEligibilityRule,
    PatternLineageRequirement,
    AggregationCriteria,
)

# Import from aggregation_rules
from .aggregation_rules import (
    PatternTypeEligibility,
    DEFAULT_ELIGIBILITY_RULES,
    DEFAULT_QUALITY_THRESHOLDS,
    LIFECYCLE_TRANSITIONS,
    AggregationEligibilityChecker,
    PatternLifecycleValidator,
    check_pattern_eligibility,
    validate_pattern_transition,
)


# ============================================================================
# Extraction Source Models
# ============================================================================

class ExtractionSource(BaseModel):
    """A source to scan for pattern evidence."""
    source_type: PatternSourceType
    source_id: str
    source_data: Dict[str, Any]
    extracted_at: datetime = Field(default_factory=datetime.now)
    execution_id: Optional[str] = None
    team_id: Optional[UUID] = None
    mission_id: Optional[str] = None


class PatternEvidence(BaseModel):
    """
    A single piece of evidence contributing to a pattern candidate.

    Evidence is extracted from artifacts, memory, insights, or execution traces.
    """
    id: UUID = Field(default_factory=uuid4)

    # What was observed
    pattern_type: PatternType
    observed_structure: Dict[str, Any]

    # Where it came from
    source_type: PatternSourceType
    source_id: str
    execution_id: Optional[str] = None

    # Context
    domain: Optional[str] = None
    scope: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Confidence in this evidence
    extraction_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Timestamps
    observed_at: datetime = Field(default_factory=datetime.now)
    extracted_at: datetime = Field(default_factory=datetime.now)

    # Extraction metadata
    extraction_method: str = "unknown"
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)


class RejectionReason(str, Enum):
    """Reasons why a pattern candidate was rejected."""

    INSUFFICIENT_RECURRENCE = "insufficient_recurrence"
    LOW_CONFIDENCE = "low_confidence"
    POOR_SOURCE_DIVERSITY = "poor_source_diversity"
    STALE_EVIDENCE = "stale_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    NARROW_SCOPE = "narrow_scope"
    LOW_STABILITY = "low_stability"
    INSUFFICIENT_OBSERVATIONS = "insufficient_observations"


class PatternRejectionRecord(BaseModel):
    """Record of a rejected pattern candidate."""
    id: UUID = Field(default_factory=uuid4)
    pattern_type: PatternType
    rejection_reason: RejectionReason
    description: str

    # Evidence that led to rejection
    evidence_count: int
    sources_consulted: List[PatternSourceType]

    # Scores at time of rejection
    recurrence_score: float
    confidence_score: float
    stability_score: float

    # When rejected
    rejected_at: datetime = Field(default_factory=datetime.now)
    rejected_by: str = "extraction_pipeline"


# ============================================================================
# Pattern Candidate Models
# ============================================================================

class PatternCandidate(BaseModel):
    """
    A pattern candidate before aggregation and validation.

    Candidates accumulate evidence before being promoted to full patterns.
    """
    id: UUID = Field(default_factory=uuid4)

    # Pattern identification
    pattern_type: PatternType
    name: str
    description: str

    # Domain/scope
    domain: Optional[str] = None
    scope: Optional[str] = None

    # Accumulated evidence
    evidence: List[PatternEvidence] = Field(default_factory=list)

    # Aggregated scores
    recurrence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    stability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    temporal_consistency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Quality metrics
    quality: Optional[PatternQualityMetrics] = None

    # Source lineage
    source_references: List[PatternSourceReference] = Field(default_factory=list)

    # Structure and characteristics
    structure: Dict[str, Any] = Field(default_factory=dict)
    characteristics: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Status
    lifecycle_state: PatternLifecycleState = PatternLifecycleState.CANDIDATE

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    extracted_by: str = "pattern_extractor"


# ============================================================================
# Pattern Candidate Extractor
# ============================================================================

class PatternCandidateExtractor:
    """
    Extracts pattern candidates from platform sources.

    Scans:
    - Workspace artifacts
    - Validated memory records
    - Published insights
    - Execution traces / audit trails
    """

    def __init__(
        self,
        min_confidence: float = 0.3,
        max_evidence_age_days: int = 90
    ):
        """Initialize the extractor."""
        self.min_confidence = min_confidence
        self.max_evidence_age_days = max_evidence_age_days

    def extract_from_artifacts(
        self,
        artifacts: List[Dict[str, Any]]
    ) -> List[PatternEvidence]:
        """Extract pattern evidence from workspace artifacts."""
        evidence = []

        for artifact in artifacts:
            # Skip artifacts below confidence threshold
            artifact_confidence = artifact.get("confidence", 0.5)
            if artifact_confidence < self.min_confidence:
                continue

            # Check age
            artifact_date = artifact.get("created_at")
            if artifact_date:
                age = (datetime.now() - artifact_date).days
                if age > self.max_evidence_age_days:
                    continue

            # Detect pattern type based on artifact type and content
            pattern_type = self._detect_pattern_type_from_artifact(artifact)
            if pattern_type:
                ev = PatternEvidence(
                    pattern_type=pattern_type,
                    observed_structure=self._extract_structure_from_artifact(artifact),
                    source_type=PatternSourceType.ARTIFACT,
                    source_id=artifact.get("id", ""),
                    execution_id=artifact.get("execution_id"),
                    domain=artifact.get("domain"),
                    scope=artifact.get("scope"),
                    extraction_confidence=artifact_confidence,
                    observed_at=artifact_date or datetime.now(),
                    extraction_method="artifact_scan",
                    extraction_metadata={"artifact_type": artifact.get("artifact_type")}
                )
                evidence.append(ev)

        logger.info(f"Extracted {len(evidence)} evidence from {len(artifacts)} artifacts")
        return evidence

    def extract_from_memory(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[PatternEvidence]:
        """Extract pattern evidence from validated memory records."""
        evidence = []

        for memory in memories:
            # Only validated memories contribute to patterns
            if memory.get("lifecycle_state") != "validated":
                continue

            memory_confidence = memory.get("quality", {}).get("confidence_score", 0.5)
            if memory_confidence < self.min_confidence:
                continue

            # Detect pattern type from memory type
            pattern_type = self._detect_pattern_type_from_memory(memory)
            if pattern_type:
                ev = PatternEvidence(
                    pattern_type=pattern_type,
                    observed_structure=self._extract_structure_from_memory(memory),
                    source_type=PatternSourceType.MEMORY,
                    source_id=memory.get("id", ""),
                    execution_id=memory.get("execution_id"),
                    domain=memory.get("domain"),
                    scope=memory.get("scope"),
                    extraction_confidence=memory_confidence,
                    observed_at=memory.get("created_at", datetime.now()),
                    extraction_method="memory_scan",
                    extraction_metadata={"memory_type": memory.get("memory_type")}
                )
                evidence.append(ev)

        logger.info(f"Extracted {len(evidence)} evidence from {len(memories)} memories")
        return evidence

    def extract_from_insights(
        self,
        insights: List[Dict[str, Any]]
    ) -> List[PatternEvidence]:
        """Extract pattern evidence from published insights."""
        evidence = []

        for insight in insights:
            # Only published insights contribute
            if insight.get("lifecycle_state") != "published":
                continue

            insight_confidence = insight.get("quality", {}).get("confidence_score", 0.5)
            if insight_confidence < self.min_confidence:
                continue

            pattern_type = self._detect_pattern_type_from_insight(insight)
            if pattern_type:
                ev = PatternEvidence(
                    pattern_type=pattern_type,
                    observed_structure=self._extract_structure_from_insight(insight),
                    source_type=PatternSourceType.INSIGHT,
                    source_id=insight.get("id", ""),
                    execution_id=insight.get("execution_id"),
                    domain=insight.get("domain"),
                    scope=insight.get("scope"),
                    extraction_confidence=insight_confidence,
                    observed_at=insight.get("published_at", datetime.now()),
                    extraction_method="insight_scan",
                    extraction_metadata={"insight_type": insight.get("insight_type")}
                )
                evidence.append(ev)

        logger.info(f"Extracted {len(evidence)} evidence from {len(insights)} insights")
        return evidence

    def extract_from_execution_traces(
        self,
        traces: List[Dict[str, Any]]
    ) -> List[PatternEvidence]:
        """Extract pattern evidence from execution traces."""
        evidence = []

        for trace in traces:
            trace_confidence = trace.get("confidence", 0.5)
            if trace_confidence < self.min_confidence:
                continue

            pattern_type = self._detect_pattern_type_from_trace(trace)
            if pattern_type:
                ev = PatternEvidence(
                    pattern_type=pattern_type,
                    observed_structure=self._extract_structure_from_trace(trace),
                    source_type=PatternSourceType.EXECUTION_TRACE,
                    source_id=trace.get("id", ""),
                    execution_id=trace.get("execution_id"),
                    extraction_confidence=trace_confidence,
                    observed_at=trace.get("timestamp", datetime.now()),
                    extraction_method="trace_scan",
                    extraction_metadata={"trace_type": trace.get("trace_type")}
                )
                evidence.append(ev)

        logger.info(f"Extracted {len(evidence)} evidence from {len(traces)} traces")
        return evidence

    def _detect_pattern_type_from_artifact(self, artifact: Dict[str, Any]) -> Optional[PatternType]:
        """Detect pattern type from artifact characteristics."""
        artifact_type = artifact.get("artifact_type", "").lower()
        content = artifact.get("content", {}).get("summary", "").lower() if artifact.get("content") else ""

        # Failure patterns
        if "error" in content or "failure" in content or "exception" in content:
            return PatternType.FAILURE_PATTERN

        # Execution patterns
        if artifact_type in ["code_execution", "api_call", "tool_execution"]:
            return PatternType.EXECUTION_PATTERN

        # Retrieval patterns
        if artifact_type in ["file_read", "database_query", "knowledge_query"]:
            return PatternType.RETRIEVAL_PATTERN

        # Decision patterns
        if "decision" in content or "choice" in content or "selected" in content:
            return PatternType.DECISION_PATTERN

        # Default to execution pattern
        return PatternType.EXECUTION_PATTERN

    def _detect_pattern_type_from_memory(self, memory: Dict[str, Any]) -> Optional[PatternType]:
        """Detect pattern type from memory characteristics."""
        memory_type = memory.get("memory_type", "").lower()

        if "warning" in memory_type:
            return PatternType.RISK_PATTERN
        elif "playbook" in memory_type:
            return PatternType.EXECUTION_PATTERN
        elif "heuristic" in memory_type:
            return PatternType.DECISION_PATTERN
        elif "failure" in memory_type or "recovery" in memory_type:
            return PatternType.RECOVERY_PATTERN

        return PatternType.EXECUTION_PATTERN

    def _detect_pattern_type_from_insight(self, insight: Dict[str, Any]) -> Optional[PatternType]:
        """Detect pattern type from insight characteristics."""
        insight_type = insight.get("insight_type", "").lower()
        summary = insight.get("summary", "").lower()

        if "warning" in insight_type or "risk" in summary:
            return PatternType.RISK_PATTERN
        elif "heuristic" in insight_type or "rule" in summary:
            return PatternType.DECISION_PATTERN
        elif "workflow" in insight_type or "process" in summary:
            return PatternType.EXECUTION_PATTERN
        elif "recovery" in summary or "mitigation" in summary:
            return PatternType.RECOVERY_PATTERN

        return PatternType.EXECUTION_PATTERN

    def _detect_pattern_type_from_trace(self, trace: Dict[str, Any]) -> Optional[PatternType]:
        """Detect pattern type from execution trace."""
        trace_type = trace.get("trace_type", "").lower()

        if "error" in trace_type or "exception" in trace_type:
            return PatternType.FAILURE_PATTERN
        elif "recovery" in trace_type:
            return PatternType.RECOVERY_PATTERN
        elif "collaboration" in trace_type or "handoff" in trace_type:
            return PatternType.COLLABORATION_PATTERN
        elif "decision" in trace_type:
            return PatternType.DECISION_PATTERN

        return PatternType.EXECUTION_PATTERN

    def _extract_structure_from_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern structure from artifact."""
        return {
            "type": "artifact_structure",
            "artifact_type": artifact.get("artifact_type"),
            "summary": artifact.get("content", {}).get("summary", "")[:200] if artifact.get("content") else "",
            "outcome": artifact.get("outcome"),
        }

    def _extract_structure_from_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern structure from memory."""
        return {
            "type": "memory_structure",
            "memory_type": memory.get("memory_type"),
            "summary": memory.get("summary", "")[:200],
            "applicability": memory.get("applicability"),
        }

    def _extract_structure_from_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern structure from insight."""
        return {
            "type": "insight_structure",
            "insight_type": insight.get("insight_type"),
            "summary": insight.get("summary", "")[:200],
            "applicability": insight.get("applicability"),
        }

    def _extract_structure_from_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern structure from trace."""
        return {
            "type": "trace_structure",
            "trace_type": trace.get("trace_type"),
            "steps": trace.get("steps", [])[:5],
            "outcome": trace.get("outcome"),
        }


# ============================================================================
# Pattern Aggregation Engine
# ============================================================================

class PatternAggregationEngine:
    """
    Groups evidence into pattern candidates.

    Aggregation rules:
    - Repeated occurrence (same/similar structure)
    - Shared context (domain, scope)
    - Shared failure mode
    - Shared retrieval behavior
    - Repeated decision structure
    - Repeated collaboration flow
    """

    def __init__(
        self,
        similarity_threshold: float = 0.6,
        min_evidence_per_candidate: int = 2
    ):
        """Initialize the aggregation engine."""
        self.similarity_threshold = similarity_threshold
        self.min_evidence_per_candidate = min_evidence_per_candidate

    def aggregate(
        self,
        evidence: List[PatternEvidence]
    ) -> Tuple[List[PatternCandidate], List[PatternRejectionRecord]]:
        """
        Aggregate evidence into pattern candidates.

        Returns:
            Tuple of (candidates, rejection_records)
        """
        # Group evidence by pattern type
        evidence_by_type: Dict[PatternType, List[PatternEvidence]] = defaultdict(list)
        for ev in evidence:
            evidence_by_type[ev.pattern_type].append(ev)

        candidates = []
        rejections = []

        # For each pattern type, aggregate evidence into candidates
        for pattern_type, type_evidence in evidence_by_type.items():
            type_candidates, type_rejections = self._aggregate_by_type(
                pattern_type,
                type_evidence
            )
            candidates.extend(type_candidates)
            rejections.extend(type_rejections)

        logger.info(
            f"Aggregated {len(evidence)} evidence into "
            f"{len(candidates)} candidates, {len(rejections)} rejected"
        )

        return candidates, rejections

    def _aggregate_by_type(
        self,
        pattern_type: PatternType,
        evidence: List[PatternEvidence]
    ) -> Tuple[List[PatternCandidate], List[PatternRejectionRecord]]:
        """Aggregate evidence of a single type."""
        candidates = []
        rejections = []
        used_evidence: Set[UUID] = set()

        # Group evidence by similarity
        groups = self._group_evidence_by_similarity(evidence)

        for group_evidence in groups:
            if len(group_evidence) < self.min_evidence_per_candidate:
                # Reject: insufficient recurrence
                rejections.append(self._create_rejection_record(
                    pattern_type,
                    group_evidence,
                    RejectionReason.INSUFFICIENT_RECURRENCE
                ))
                continue

            # Create candidate from grouped evidence
            candidate = self._create_candidate_from_evidence(pattern_type, group_evidence)

            # Check eligibility rules
            eligibility_results = check_pattern_eligibility(
                pattern_type,
                [self._evidence_to_observation(ev) for ev in group_evidence]
            )

            if not eligibility_results["is_eligible"]:
                # Determine rejection reason
                reason = self._determine_rejection_reason(eligibility_results)
                rejections.append(self._create_rejection_record_from_results(
                    pattern_type,
                    group_evidence,
                    eligibility_results,
                    reason
                ))
                continue

            candidates.append(candidate)
            used_evidence.update(ev.id for ev in group_evidence)

        # Reject ungrouped evidence
        for ev in evidence:
            if ev.id not in used_evidence:
                rejections.append(self._create_rejection_record(
                    pattern_type,
                    [ev],
                    RejectionReason.NARROW_SCOPE
                ))

        return candidates, rejections

    def _group_evidence_by_similarity(
        self,
        evidence: List[PatternEvidence]
    ) -> List[List[PatternEvidence]]:
        """Group evidence by similarity."""
        groups = []
        ungrouped = list(evidence)

        while ungrouped:
            # Start a new group with the first ungrouped evidence
            current_group = [ungrouped.pop(0)]

            # Find similar evidence
            i = 0
            while i < len(ungrouped):
                ev = ungrouped[i]
                if self._is_similar_to_group(ev, current_group):
                    current_group.append(ev)
                    ungrouped.pop(i)
                else:
                    i += 1

            if current_group:
                groups.append(current_group)

        return groups

    def _is_similar_to_group(
        self,
        evidence: PatternEvidence,
        group: List[PatternEvidence]
    ) -> bool:
        """Check if evidence is similar to evidence in a group."""
        for group_ev in group:
            # Same pattern type is required
            if evidence.pattern_type != group_ev.pattern_type:
                continue

            # Same pattern type is enough for grouping
            # (domain/scope differences don't prevent grouping)
            return True

        return False

    def _structure_similarity(
        self,
        struct1: Dict[str, Any],
        struct2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two structures."""
        if not struct1 or not struct2:
            return 0.0

        # Extract base type (e.g., "artifact_structure" -> "structure")
        type1 = struct1.get("type", "")
        type2 = struct2.get("type", "")

        # Both end in "_structure" - consider them similar
        if type1.endswith("_structure") and type2.endswith("_structure"):
            type_match = 0.8  # High similarity for same pattern category
        elif type1 == type2:
            type_match = 1.0
        else:
            type_match = 0.0

        keys1 = set(struct1.keys()) - {"type", "summary"}
        keys2 = set(struct2.keys()) - {"type", "summary"}

        if not keys1 or not keys2:
            return type_match * 0.5

        overlap = len(keys1 & keys2)
        total = len(keys1 | keys2)

        key_similarity = overlap / total if total > 0 else 0.0

        return (type_match * 0.6 + key_similarity * 0.4)

    def _create_candidate_from_evidence(
        self,
        pattern_type: PatternType,
        evidence: List[PatternEvidence]
    ) -> PatternCandidate:
        """Create a pattern candidate from grouped evidence."""
        # Aggregate structure
        merged_structure = self._merge_structures([ev.observed_structure for ev in evidence])

        # Determine name and description
        name = self._generate_candidate_name(pattern_type, evidence)
        description = self._generate_candidate_description(evidence)

        # Extract domain and scope
        domain = self._most_common([ev.domain for ev in evidence if ev.domain])
        scope = self._most_common([ev.scope for ev in evidence if ev.scope])

        # Create candidate
        candidate = PatternCandidate(
            pattern_type=pattern_type,
            name=name,
            description=description,
            domain=domain,
            scope=scope,
            evidence=evidence,
            structure=merged_structure,
            tags=self._extract_tags(evidence),
        )

        # Create source references
        candidate.source_references = [
            PatternSourceReference(
                source_type=ev.source_type,
                source_id=ev.source_id,
                observed_at=ev.observed_at,
                extraction_method=ev.extraction_method
            )
            for ev in evidence
        ]

        return candidate

    def _merge_structures(self, structures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple structures into one."""
        if not structures:
            return {}

        # Start with the first structure
        merged = structures[0].copy()

        # Add keys from other structures
        for struct in structures[1:]:
            for key, value in struct.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    # Merge lists
                    merged[key] = list(set(merged[key] + value))
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    # Recursively merge dicts
                    merged[key] = self._merge_structures([merged[key], value])

        return merged

    def _generate_candidate_name(
        self,
        pattern_type: PatternType,
        evidence: List[PatternEvidence]
    ) -> str:
        """Generate a name for the candidate."""
        domain = self._most_common([ev.domain for ev in evidence if ev.domain])
        scope = self._most_common([ev.scope for ev in evidence if ev.scope])

        parts = [
            domain.capitalize() if domain else "",
            scope.capitalize() if scope else "",
            pattern_type.value.replace("_", " ").title()
        ]

        return " ".join(filter(None, parts))

    def _generate_candidate_description(self, evidence: List[PatternEvidence]) -> str:
        """Generate a description for the candidate."""
        sources = set(ev.source_type.value for ev in evidence)
        executions = len(set(ev.execution_id for ev in evidence if ev.execution_id))

        return (
            f"Pattern detected across {len(evidence)} observations "
            f"from {len(sources)} source types and {executions} executions."
        )

    def _extract_tags(self, evidence: List[PatternEvidence]) -> List[str]:
        """Extract tags from evidence."""
        tags = set()
        for ev in evidence:
            tags.update(ev.tags)
            if ev.domain:
                tags.add(ev.domain)
            if ev.scope:
                tags.add(ev.scope)
        return list(tags)

    def _most_common(self, items: List[str]) -> Optional[str]:
        """Find the most common item."""
        if not items:
            return None
        from collections import Counter
        return Counter(items).most_common(1)[0][0]

    def _evidence_to_observation(self, evidence: PatternEvidence) -> PatternObservation:
        """Convert evidence to observation format."""
        return PatternObservation(
            pattern_type=evidence.pattern_type,
            observed_structure=evidence.observed_structure,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            execution_id=evidence.execution_id,
            observed_at=evidence.observed_at,
            detection_method=evidence.extraction_method,
            observation_confidence=evidence.extraction_confidence  # Map extraction_confidence to observation_confidence
        )

    def _create_rejection_record(
        self,
        pattern_type: PatternType,
        evidence: List[PatternEvidence],
        reason: RejectionReason
    ) -> PatternRejectionRecord:
        """Create a rejection record."""
        sources = set(ev.source_type for ev in evidence)

        return PatternRejectionRecord(
            pattern_type=pattern_type,
            rejection_reason=reason,
            description=f"Rejected due to {reason.value}",
            evidence_count=len(evidence),
            sources_consulted=list(sources),
            recurrence_score=len(evidence) / 10.0,  # Normalized estimate
            confidence_score=sum(ev.extraction_confidence for ev in evidence) / len(evidence) if evidence else 0.0,
            stability_score=0.5,  # Placeholder
        )

    def _create_rejection_record_from_results(
        self,
        pattern_type: PatternType,
        evidence: List[PatternEvidence],
        results: Dict[str, Any],
        reason: RejectionReason
    ) -> PatternRejectionRecord:
        """Create a rejection record from eligibility results."""
        scores = results.get("scores", {})
        sources = set(ev.source_type for ev in evidence)

        return PatternRejectionRecord(
            pattern_type=pattern_type,
            rejection_reason=reason,
            description=f"Rejected: {'; '.join(results.get('failed_criteria', []))}",
            evidence_count=len(evidence),
            sources_consulted=list(sources),
            recurrence_score=scores.get("observation_count", 0) / 10.0,
            confidence_score=scores.get("avg_confidence", 0.0),
            stability_score=scores.get("avg_confidence", 0.0),
        )

    def _determine_rejection_reason(self, results: Dict[str, Any]) -> RejectionReason:
        """Determine rejection reason from eligibility results."""
        failed = results.get("failed_criteria", [])

        if "Insufficient observations" in " ".join(failed):
            return RejectionReason.INSUFFICIENT_OBSERVATIONS
        if "Insufficient confidence" in " ".join(failed):
            return RejectionReason.LOW_CONFIDENCE
        if "source diversity" in " ".join(failed):
            return RejectionReason.POOR_SOURCE_DIVERSITY

        return RejectionReason.INSUFFICIENT_RECURRENCE


# ============================================================================
# Pattern Scoring Service
# ============================================================================

class PatternScoringService:
    """
    Scores pattern candidates on multiple dimensions.

    Scores:
    - Recurrence score: How often does this occur?
    - Confidence score: How confident are we?
    - Source diversity score: How many source types?
    - Temporal consistency score: Is this consistent over time?
    - Relevance score: How relevant is this pattern?
    - Stability score: How stable is the pattern?
    """

    def score_candidate(self, candidate: PatternCandidate) -> PatternCandidate:
        """Score a pattern candidate on all dimensions."""
        # Extract evidence data
        evidence = candidate.evidence
        if not evidence:
            return candidate

        # Recurrence score: based on observation count
        candidate.recurrence_score = self._score_recurrence(evidence)

        # Confidence score: average extraction confidence
        candidate.confidence_score = self._score_confidence(evidence)

        # Source diversity score: variety of source types
        candidate.source_diversity_score = self._score_source_diversity(evidence)

        # Temporal consistency score: distribution over time
        candidate.temporal_consistency_score = self._score_temporal_consistency(evidence)

        # Relevance score: based on domain/scope specificity
        candidate.relevance_score = self._score_relevance(candidate)

        # Stability score: consistency of structure
        candidate.stability_score = self._score_stability(evidence)

        # Create quality metrics
        candidate.quality = self._create_quality_metrics(candidate)

        # Update timestamp
        candidate.updated_at = datetime.now()

        return candidate

    def _score_recurrence(self, evidence: List[PatternEvidence]) -> float:
        """Score recurrence based on observation count."""
        count = len(evidence)
        # Logarithmic scaling: more observations = diminishing returns
        import math
        return min(1.0, math.log10(count + 1) / math.log10(20))

    def _score_confidence(self, evidence: List[PatternEvidence]) -> float:
        """Score confidence based on average extraction confidence."""
        if not evidence:
            return 0.0
        return sum(ev.extraction_confidence for ev in evidence) / len(evidence)

    def _score_source_diversity(self, evidence: List[PatternEvidence]) -> float:
        """Score source diversity."""
        source_types = set(ev.source_type for ev in evidence)
        # Max diversity is all 7 source types
        return len(source_types) / 7.0

    def _score_temporal_consistency(self, evidence: List[PatternEvidence]) -> float:
        """Score temporal consistency."""
        if len(evidence) < 2:
            return 0.0

        times = sorted(ev.observed_at for ev in evidence)
        if not times:
            return 0.0

        # Calculate time span
        span = (times[-1] - times[0]).days
        if span < 7:
            return 0.3  # Too recent
        elif span < 30:
            return 0.7  # Good recent consistency
        else:
            return 1.0  # Long-term consistency

    def _score_relevance(self, candidate: PatternCandidate) -> float:
        """Score relevance based on domain/scope specificity."""
        score = 0.0

        if candidate.domain:
            score += 0.3
        if candidate.scope:
            score += 0.3
        if candidate.tags:
            score += 0.2

        # Evidence count contributes
        score += min(0.2, len(candidate.evidence) / 20)

        return min(1.0, score)

    def _score_stability(self, evidence: List[PatternEvidence]) -> float:
        """Score stability based on structure consistency."""
        if len(evidence) < 2:
            return 0.5

        # Calculate average pairwise similarity
        similarities = []
        for i in range(len(evidence)):
            for j in range(i + 1, len(evidence)):
                sim = self._structure_similarity(
                    evidence[i].observed_structure,
                    evidence[j].observed_structure
                )
                similarities.append(sim)

        if not similarities:
            return 0.5

        return sum(similarities) / len(similarities)

    def _structure_similarity(
        self,
        struct1: Dict[str, Any],
        struct2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two structures."""
        if not struct1 or not struct2:
            return 0.0

        # Extract base type (e.g., "artifact_structure" -> "structure")
        type1 = struct1.get("type", "")
        type2 = struct2.get("type", "")

        # Both end in "_structure" - consider them similar
        if type1.endswith("_structure") and type2.endswith("_structure"):
            type_match = 0.8  # High similarity for same pattern category
        elif type1 == type2:
            type_match = 1.0
        else:
            type_match = 0.0

        keys1 = set(struct1.keys()) - {"type", "summary"}
        keys2 = set(struct2.keys()) - {"type", "summary"}

        if not keys1 or not keys2:
            return type_match * 0.5

        overlap = len(keys1 & keys2)
        total = len(keys1 | keys2)

        key_similarity = overlap / total if total > 0 else 0.0

        return (type_match * 0.6 + key_similarity * 0.4)

    def _create_quality_metrics(self, candidate: PatternCandidate) -> PatternQualityMetrics:
        """Create quality metrics from scores."""
        evidence = candidate.evidence
        executions = max(1, len(set(ev.execution_id for ev in evidence if ev.execution_id)))
        sources = max(1, len(set(ev.source_type for ev in evidence)))

        times = [ev.observed_at for ev in evidence]
        first_observed = min(times) if times else datetime.now()
        last_observed = max(times) if times else datetime.now()

        return PatternQualityMetrics(
            confidence_score=candidate.confidence_score,
            stability_score=candidate.stability_score,
            consistency_score=candidate.temporal_consistency_score,
            observation_count=len(evidence),
            unique_execution_count=executions,
            distinct_source_count=sources,
            first_observed_at=first_observed,
            last_observed_at=last_observed,
            observation_span_days=(last_observed - first_observed).days if times else 0,
        )


# ============================================================================
# Pattern Persistence Service
# ============================================================================

class PatternPersistenceService:
    """
    Persists pattern candidates with lineage.

    Storage:
    - In-memory registry (for this milestone)
    - Future: Database persistence
    """

    def __init__(self):
        """Initialize the persistence service."""
        self._patterns: Dict[UUID, Pattern] = {}
        self._rejections: List[PatternRejectionRecord] = []

    def persist_candidate(
        self,
        candidate: PatternCandidate,
        promote_to: PatternLifecycleState = PatternLifecycleState.CANDIDATE
    ) -> Pattern:
        """Persist a pattern candidate."""
        # Create Pattern from candidate
        pattern = Pattern(
            pattern_type=candidate.pattern_type,
            name=candidate.name,
            description=candidate.description,
            domain=candidate.domain,
            scope=candidate.scope,
            structure=candidate.structure,
            characteristics=candidate.characteristics,
            tags=candidate.tags,
            source_references=candidate.source_references,
            quality=candidate.quality or PatternQualityMetrics(
                confidence_score=candidate.confidence_score,
                stability_score=candidate.stability_score,
                consistency_score=candidate.temporal_consistency_score,
                observation_count=max(1, len(candidate.evidence)),
                unique_execution_count=max(1, len(set(ev.execution_id for ev in candidate.evidence if ev.execution_id))),
                distinct_source_count=max(1, len(set(ev.source_type for ev in candidate.evidence))),
                first_observed_at=min((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
                last_observed_at=max((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
            ),
            lifecycle_state=promote_to,
            created_by=candidate.extracted_by,
        )

        # Store pattern
        self._patterns[pattern.id] = pattern

        logger.info(
            f"Persisted pattern {pattern.id}: {pattern.name} "
            f"({pattern.lifecycle_state.value})"
        )

        return pattern

    def persist_rejection(self, rejection: PatternRejectionRecord) -> None:
        """Persist a rejection record."""
        self._rejections.append(rejection)
        logger.info(
            f"Logged rejection: {rejection.pattern_type.value} - {rejection.rejection_reason.value}"
        )

    def get_pattern(self, pattern_id: UUID) -> Optional[Pattern]:
        """Get a persisted pattern."""
        return self._patterns.get(pattern_id)

    def list_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        lifecycle_state: Optional[PatternLifecycleState] = None
    ) -> List[Pattern]:
        """List persisted patterns."""
        patterns = list(self._patterns.values())

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        if lifecycle_state:
            patterns = [p for p in patterns if p.lifecycle_state == lifecycle_state]

        return patterns

    def list_rejections(
        self,
        pattern_type: Optional[PatternType] = None,
        reason: Optional[RejectionReason] = None
    ) -> List[PatternRejectionRecord]:
        """List rejection records."""
        rejections = self._rejections

        if pattern_type:
            rejections = [r for r in rejections if r.pattern_type == pattern_type]

        if reason:
            rejections = [r for r in rejections if r.rejection_reason == reason]

        return rejections

    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        by_type = defaultdict(int)
        by_state = defaultdict(int)

        for pattern in self._patterns.values():
            by_type[pattern.pattern_type.value] += 1
            by_state[pattern.lifecycle_state.value] += 1

        by_rejection_reason = defaultdict(int)
        for rejection in self._rejections:
            by_rejection_reason[rejection.rejection_reason.value] += 1

        return {
            "total_patterns": len(self._patterns),
            "total_rejections": len(self._rejections),
            "patterns_by_type": dict(by_type),
            "patterns_by_state": dict(by_state),
            "rejections_by_reason": dict(by_rejection_reason),
        }


# ============================================================================
# Main Pipeline Orchestration
# ============================================================================

class PatternExtractionPipeline:
    """
    Main pipeline for pattern extraction and aggregation.

    Flow:
    1. Extract evidence from sources
    2. Aggregate evidence into candidates
    3. Score candidates
    4. Persist candidates and rejections
    """

    def __init__(
        self,
        extractor: Optional[PatternCandidateExtractor] = None,
        aggregator: Optional[PatternAggregationEngine] = None,
        scorer: Optional[PatternScoringService] = None,
        persistence: Optional[PatternPersistenceService] = None
    ):
        """Initialize the pipeline."""
        self.extractor = extractor or PatternCandidateExtractor()
        self.aggregator = aggregator or PatternAggregationEngine()
        self.scorer = scorer or PatternScoringService()
        self.persistence = persistence or PatternPersistenceService()

    def run(
        self,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        insights: Optional[List[Dict[str, Any]]] = None,
        traces: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run the full extraction pipeline.

        Returns:
            Pipeline results with candidates and rejections
        """
        results = {
            "evidence_extracted": 0,
            "candidates_created": 0,
            "patterns_persisted": 0,
            "rejections_logged": 0,
            "candidate_ids": [],
            "pattern_ids": [],
        }

        # Step 1: Extract evidence
        evidence = []

        if artifacts:
            evidence.extend(self.extractor.extract_from_artifacts(artifacts))
        if memories:
            evidence.extend(self.extractor.extract_from_memory(memories))
        if insights:
            evidence.extend(self.extractor.extract_from_insights(insights))
        if traces:
            evidence.extend(self.extractor.extract_from_execution_traces(traces))

        results["evidence_extracted"] = len(evidence)

        if not evidence:
            logger.warning("No evidence extracted from sources")
            return results

        # Step 2: Aggregate into candidates
        candidates, rejections = self.aggregator.aggregate(evidence)
        results["candidates_created"] = len(candidates)
        results["rejections_logged"] = len(rejections)

        # Step 3: Score candidates
        scored_candidates = [self.scorer.score_candidate(c) for c in candidates]

        # Step 4: Persist candidates and rejections
        for candidate in scored_candidates:
            pattern = self.persistence.persist_candidate(candidate)
            results["pattern_ids"].append(str(pattern.id))
            results["patterns_persisted"] += 1

        for rejection in rejections:
            self.persistence.persist_rejection(rejection)

        logger.info(
            f"Pipeline complete: {results['evidence_extracted']} evidence → "
            f"{results['candidates_created']} candidates → "
            f"{results['patterns_persisted']} patterns, "
            f"{results['rejections_logged']} rejections"
        )

        return results


# ============================================================================
# Convenience Functions
# ============================================================================

def run_pattern_extraction(
    artifacts: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    traces: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Run pattern extraction with default configuration."""
    pipeline = PatternExtractionPipeline()
    return pipeline.run(artifacts, memories, insights, traces)


def extract_and_aggregate(
    evidence: List[PatternEvidence]
) -> Tuple[List[PatternCandidate], List[PatternRejectionRecord]]:
    """Extract and aggregate evidence into candidates."""
    engine = PatternAggregationEngine()
    return engine.aggregate(evidence)

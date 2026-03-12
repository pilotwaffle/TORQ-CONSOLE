"""
TORQ Readiness Checker - Evidence Collector

Milestone 2: Evidence collection from TORQ subsystems.

Provides interfaces and implementations for collecting readiness evidence
from execution history, artifacts, memory, insights, patterns, and audits.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Evidence Collection Interface
# ============================================================================

class CollectorResult(BaseModel):
    """
    Result from an evidence collector.

    Contains the collected evidence data along with metadata
    about the collection process.
    """
    # Identification
    collector_name: str
    dimension: str  # PolicyDimension value
    candidate_id: UUID

    # Evidence data
    data: Dict[str, Any] = Field(default_factory=dict)

    # Scoring inputs (normalized 0.0 - 1.0)
    raw_values: Dict[str, float] = Field(default_factory=dict)
    normalized_scores: Dict[str, float] = Field(default_factory=dict)

    # Metadata
    collected_at: datetime = Field(default_factory=datetime.now)
    collection_duration_ms: int = 0

    # Data quality
    has_sufficient_data: bool = True
    data_freshness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    sample_size: int = 0  # Number of data points collected

    # Issues
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Source tracking
    source_system: Optional[str] = None
    source_queries: List[str] = Field(default_factory=list)


class CollectorError(Exception):
    """Exception raised when evidence collection fails."""
    pass


class EvidenceCollector(ABC):
    """
    Abstract base class for evidence collectors.

    Each collector is responsible for gathering evidence from a specific
    TORQ subsystem and normalizing it for readiness scoring.
    """

    def __init__(self, source_system: str):
        """
        Initialize the evidence collector.

        Args:
            source_system: Name of the TORQ subsystem this collector queries
        """
        self.source_system = source_system

    @abstractmethod
    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """
        Collect evidence for a readiness candidate.

        Args:
            candidate_id: ID of the candidate to evaluate
            context: Additional context for collection

        Returns:
            CollectorResult with collected evidence

        Raises:
            CollectorError: If collection fails
        """
        pass

    def _create_result(
        self,
        candidate_id: UUID,
        data: Dict[str, Any],
        raw_values: Dict[str, float],
        normalized_scores: Dict[str, float],
        sample_size: int = 0,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> CollectorResult:
        """Helper to create a CollectorResult."""
        return CollectorResult(
            collector_name=self.__class__.__name__,
            dimension=self.__class__.__name__.replace("Collector", "").replace("Evidence", ""),
            candidate_id=candidate_id,
            data=data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=sample_size,
            has_sufficient_data=sample_size > 0,
            errors=errors or [],
            warnings=warnings or [],
            source_system=self.source_system,
        )


# ============================================================================
# Dimension-Specific Collectors
# ============================================================================

class ExecutionStabilityCollector(EvidenceCollector):
    """
    Collects evidence about execution stability from 5.2.

    Evaluates:
    - Success rate
    - Failure rate
    - Runtime variance
    - Retry rate
    - Execution frequency
    """

    def __init__(self):
        super().__init__("execution_5.2")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """
        Collect execution stability evidence.

        Args:
            candidate_id: ID of the candidate
            context: Should contain candidate_type and candidate_key

        Returns:
            CollectorResult with execution stability evidence
        """
        

        # Extract context
        candidate_type = context.get("candidate_type")
        candidate_key = context.get("candidate_key")

        # In a real implementation, this would query 5.2 execution history
        # For now, we'll create a mock result structure

        # Mock data - would be replaced with actual queries
        execution_data = {
            "total_executions": 100,
            "successful_executions": 92,
            "failed_executions": 8,
            "retries": 12,
            "avg_runtime_ms": 450,
            "runtime_stddev_ms": 120,
            "last_execution_at": datetime.now().isoformat(),
            "first_execution_at": (datetime.now() - timedelta(days=30)).isoformat(),
        }

        # Compute raw values
        success_rate = execution_data["successful_executions"] / execution_data["total_executions"]
        failure_rate = execution_data["failed_executions"] / execution_data["total_executions"]
        retry_rate = execution_data["retries"] / execution_data["total_executions"]
        runtime_cv = execution_data["runtime_stddev_ms"] / execution_data["avg_runtime_ms"]

        # Normalize to 0.0 - 1.0 (higher is better)
        raw_values = {
            "success_rate": success_rate,
            "failure_rate": 1.0 - failure_rate,  # Invert so higher is better
            "retry_rate": 1.0 - retry_rate,  # Invert
            "runtime_stability": 1.0 - min(runtime_cv, 1.0),  # Lower CV is better
            "execution_frequency": min(execution_data["total_executions"] / 100, 1.0),
        }

        # Overall normalized score
        normalized_scores = {
            "execution_stability": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=execution_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=execution_data["total_executions"],
        )


class ArtifactCompletenessCollector(EvidenceCollector):
    """
    Collects evidence about artifact completeness from 5.3.

    Evaluates:
    - Artifact count
    - Required fields present
    - Traceability coverage
    - Missing artifact rate
    """

    def __init__(self):
        super().__init__("artifacts_5.3")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect artifact completeness evidence."""
        

        # Mock artifact data
        artifact_data = {
            "total_artifacts": 45,
            "complete_artifacts": 40,
            "incomplete_artifacts": 5,
            "missing_required_fields": 3,
            "total_required_fields": 150,
            "artifacts_with_traceability": 38,
            "last_artifact_at": datetime.now().isoformat(),
        }

        # Compute raw values
        completeness_rate = artifact_data["complete_artifacts"] / artifact_data["total_artifacts"]
        field_coverage = 1.0 - (artifact_data["missing_required_fields"] / artifact_data["total_required_fields"])
        traceability_coverage = artifact_data["artifacts_with_traceability"] / artifact_data["total_artifacts"]

        raw_values = {
            "completeness_rate": completeness_rate,
            "field_coverage": field_coverage,
            "traceability_coverage": traceability_coverage,
            "artifact_density": min(artifact_data["total_artifacts"] / 50, 1.0),
        }

        normalized_scores = {
            "artifact_completeness": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=artifact_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=artifact_data["total_artifacts"],
        )


class MemoryConfidenceCollector(EvidenceCollector):
    """
    Collects evidence about memory confidence from 4H.1.

    Evaluates:
    - Governed memory count
    - Memory quality scores
    - Stale memory ratio
    - Memory freshness
    """

    def __init__(self):
        super().__init__("memory_4H.1")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect memory confidence evidence."""
        

        # Mock memory data
        memory_data = {
            "governed_memory_count": 25,
            "validated_memory_count": 22,
            "stale_memory_count": 3,
            "avg_confidence_score": 0.82,
            "avg_validation_score": 0.78,
            "last_validated_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "oldest_memory_age_days": 45,
            "total_memories": 30,
        }

        # Compute raw values
        governance_rate = memory_data["governed_memory_count"] / memory_data["total_memories"]
        validation_rate = memory_data["validated_memory_count"] / memory_data["governed_memory_count"]
        freshness_score = 1.0 - min(memory_data["oldest_memory_age_days"] / 90, 1.0)
        stale_ratio = 1.0 - (memory_data["stale_memory_count"] / memory_data["governed_memory_count"])

        raw_values = {
            "governance_rate": governance_rate,
            "validation_rate": validation_rate,
            "freshness": freshness_score,
            "stale_ratio": stale_ratio,
            "quality": memory_data["avg_confidence_score"],
        }

        normalized_scores = {
            "memory_confidence": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=memory_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=memory_data["governed_memory_count"],
        )


class InsightQualityCollector(EvidenceCollector):
    """
    Collects evidence about insight quality from Insight Publishing.

    Evaluates:
    - Approved insight count
    - Insight suppression rate
    - Stale insight exposure
    - Insight quality scores
    """

    def __init__(self):
        super().__init__("insights_publishing")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect insight quality evidence."""
        

        # Mock insight data
        insight_data = {
            "approved_insight_count": 18,
            "total_insights": 25,
            "suppressed_insights": 7,
            "stale_insights": 2,
            "avg_quality_score": 0.86,
            "avg_confidence_score": 0.82,
            "last_published_at": datetime.now().isoformat(),
        }

        # Compute raw values
        approval_rate = insight_data["approved_insight_count"] / insight_data["total_insights"]
        suppression_rate = insight_data["suppressed_insights"] / insight_data["total_insights"]
        stale_rate = insight_data["stale_insights"] / insight_data["approved_insight_count"]

        raw_values = {
            "approval_rate": approval_rate,
            "suppression_rate": 1.0 - suppression_rate,  # Lower suppression is better
            "stale_exposure": 1.0 - stale_rate,
            "quality": insight_data["avg_quality_score"],
        }

        normalized_scores = {
            "insight_quality": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=insight_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=insight_data["approved_insight_count"],
        )


class PatternConfidenceCollector(EvidenceCollector):
    """
    Collects evidence about pattern confidence from 4G Pattern Aggregation.

    Evaluates:
    - Validated pattern count
    - Pattern confidence scores
    - Source diversity
    - Active pattern count
    """

    def __init__(self):
        super().__init__("patterns_4G")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect pattern confidence evidence."""
        

        # Mock pattern data
        pattern_data = {
            "validated_pattern_count": 8,
            "active_pattern_count": 6,
            "total_patterns": 12,
            "avg_confidence_score": 0.78,
            "source_diversity_score": 0.72,
            "avg_observation_count": 25,
            "last_validated_at": (datetime.now() - timedelta(days=5)).isoformat(),
        }

        # Compute raw values
        validation_rate = pattern_data["validated_pattern_count"] / pattern_data["total_patterns"]
        activation_rate = pattern_data["active_pattern_count"] / pattern_data["validated_pattern_count"]
        diversity = pattern_data["source_diversity_score"]
        observation_score = min(pattern_data["avg_observation_count"] / 50, 1.0)

        raw_values = {
            "validation_rate": validation_rate,
            "activation_rate": activation_rate,
            "diversity": diversity,
            "observation_score": observation_score,
            "confidence": pattern_data["avg_confidence_score"],
        }

        normalized_scores = {
            "pattern_confidence": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=pattern_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=pattern_data["validated_pattern_count"],
        )


class AuditCoverageCollector(EvidenceCollector):
    """
    Collects evidence about audit coverage.

    Evaluates:
    - Audit log completeness
    - Retrieval audit coverage
    - Publication audit integrity
    - Governance event logging
    """

    def __init__(self):
        super().__init__("audit_system")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect audit coverage evidence."""
        

        # Mock audit data
        audit_data = {
            "total_retrievals": 150,
            "audited_retrievals": 142,
            "total_publications": 45,
            "audited_publications": 45,
            "governance_events_last_30d": 12,
            "audit_log_completeness": 0.95,
            "last_audit_at": datetime.now().isoformat(),
        }

        # Compute raw values
        retrieval_coverage = audit_data["audited_retrievals"] / audit_data["total_retrievals"]
        publication_coverage = audit_data["audited_publications"] / audit_data["total_publications"]
        log_completeness = audit_data["audit_log_completeness"]
        governance_activity = min(audit_data["governance_events_last_30d"] / 20, 1.0)

        raw_values = {
            "retrieval_coverage": retrieval_coverage,
            "publication_coverage": publication_coverage,
            "log_completeness": log_completeness,
            "governance_activity": governance_activity,
        }

        normalized_scores = {
            "audit_coverage": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=audit_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=audit_data["total_retrievals"] + audit_data["total_publications"],
        )


class PolicyComplianceCollector(EvidenceCollector):
    """
    Collects evidence about policy compliance.

    Evaluates:
    - Blocked types count
    - Unsafe transitions
    - Disabled capabilities
    - Policy violations
    """

    def __init__(self):
        super().__init__("policy_engine")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect policy compliance evidence."""
        

        # Mock policy data
        policy_data = {
            "total_policy_checks": 80,
            "passed_checks": 76,
            "blocked_types": 1,
            "unsafe_transitions_blocked": 3,
            "disabled_capabilities": 2,
            "policy_violations": 4,
            "last_policy_check_at": datetime.now().isoformat(),
        }

        # Compute raw values
        pass_rate = policy_data["passed_checks"] / policy_data["total_policy_checks"]
        violation_rate = policy_data["policy_violations"] / policy_data["total_policy_checks"]
        blocked_types_ratio = 1.0 - min(policy_data["blocked_types"] / 10, 1.0)  # Fewer blocked is better
        transition_safety = 1.0 - min(policy_data["unsafe_transitions_blocked"] / 20, 1.0)

        raw_values = {
            "pass_rate": pass_rate,
            "violation_rate": 1.0 - violation_rate,  # Invert
            "blocked_types": blocked_types_ratio,
            "transition_safety": transition_safety,
        }

        normalized_scores = {
            "policy_compliance": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=policy_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=policy_data["total_policy_checks"],
        )


class OperationalConsistencyCollector(EvidenceCollector):
    """
    Collects evidence about operational consistency.

    Evaluates:
    - Concurrency behavior
    - Deterministic ranking
    - Recent regression status
    - System stability
    """

    def __init__(self):
        super().__init__("operations_monitor")

    async def collect(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> CollectorResult:
        """Collect operational consistency evidence."""
        

        # Mock operational data
        operational_data = {
            "concurrent_operations": 25,
            "concurrent_errors": 1,
            "ranking_consistency_checks": 50,
            "ranking_consistent": 48,
            "recent_regressions": 0,
            "system_uptime_pct": 99.5,
            "last_regression_at": None,
        }

        # Compute raw values
        concurrency_success = 1.0 - (operational_data["concurrent_errors"] / operational_data["concurrent_operations"])
        ranking_consistency = operational_data["ranking_consistent"] / operational_data["ranking_consistency_checks"]
        regression_free = 1.0 if operational_data["recent_regressions"] == 0 else 0.5
        uptime_score = operational_data["system_uptime_pct"] / 100

        raw_values = {
            "concurrency": concurrency_success,
            "ranking": ranking_consistency,
            "regression_free": regression_free,
            "uptime": uptime_score,
        }

        normalized_scores = {
            "operational_consistency": sum(raw_values.values()) / len(raw_values),
        }


        return self._create_result(
            candidate_id=candidate_id,
            data=operational_data,
            raw_values=raw_values,
            normalized_scores=normalized_scores,
            sample_size=operational_data["concurrent_operations"] + operational_data["ranking_consistency_checks"],
        )


# ============================================================================
# Evidence Collection Orchestrator
# ============================================================================

class EvidenceCollectionOrchestrator:
    """
    Orchestrates evidence collection from all TORQ subsystems.

    Runs all dimension collectors and aggregates their results
    into a unified evidence summary.
    """

    def __init__(self):
        """Initialize the orchestrator with all dimension collectors."""
        self.collectors = {
            "execution_stability": ExecutionStabilityCollector(),
            "artifact_completeness": ArtifactCompletenessCollector(),
            "memory_confidence": MemoryConfidenceCollector(),
            "insight_quality": InsightQualityCollector(),
            "pattern_confidence": PatternConfidenceCollector(),
            "audit_coverage": AuditCoverageCollector(),
            "policy_compliance": PolicyComplianceCollector(),
            "operational_consistency": OperationalConsistencyCollector(),
        }

    async def collect_all(
        self,
        candidate_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, CollectorResult]:
        """
        Collect evidence from all dimensions.

        Args:
            candidate_id: ID of the candidate to evaluate
            context: Additional context for collection

        Returns:
            Dictionary mapping dimension names to CollectorResults
        """
        results = {}

        for dimension_name, collector in self.collectors.items():
            try:
                result = await collector.collect(candidate_id, context)
                results[dimension_name] = result
            except Exception as e:
                logger.error(f"Collector {dimension_name} failed: {e}")
                # Create error result
                results[dimension_name] = CollectorResult(
                    collector_name=collector.__class__.__name__,
                    dimension=dimension_name,
                    candidate_id=candidate_id,
                    has_sufficient_data=False,
                    errors=[str(e)],
                    source_system=collector.source_system,
                )

        return results

    def get_collector(self, dimension_name: str) -> Optional[EvidenceCollector]:
        """Get a specific collector by dimension name."""
        return self.collectors.get(dimension_name)


# Global orchestrator instance
_orchestrator: Optional[EvidenceCollectionOrchestrator] = None


def get_evidence_orchestrator() -> EvidenceCollectionOrchestrator:
    """Get the global evidence orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EvidenceCollectionOrchestrator()
    return _orchestrator


async def collect_all_evidence(
    candidate_id: UUID,
    context: Dict[str, Any]
) -> Dict[str, CollectorResult]:
    """
    Collect evidence from all dimensions.

    Convenience function that uses the global orchestrator.

    Args:
        candidate_id: ID of the candidate to evaluate
        context: Additional context for collection

    Returns:
        Dictionary mapping dimension names to CollectorResults
    """
    orchestrator = get_evidence_orchestrator()
    return await orchestrator.collect_all(candidate_id, context)

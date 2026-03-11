"""
Insight Candidate Extractor - Phase Insight Publishing Milestone 2

Extracts insight candidates from validated strategic memory.

This module bridges the Memory layer → Insight layer:
- Reads validated strategic memories
- Applies insight-specific extraction rules
- Creates insight candidates with proper provenance
- Only extracts where allowed by publishing rules
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..strategic_memory.models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
)

from .models import (
    InsightType,
    InsightScope,
    InsightLifecycleState,
    InsightSourceType,
    InsightCreate,
    SourceReference,
    QualityMetrics,
    InsightTemplates,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Memory Type → Insight Type Mapping
# ============================================================================

MEMORY_TO_INSIGHT_TYPE_MAP: Dict[MemoryType, InsightType] = {
    MemoryType.HEURISTIC: InsightType.BEST_PRACTICE,
    MemoryType.PLAYBOOK: InsightType.REUSABLE_PLAYBOOK,
    MemoryType.WARNING: InsightType.RISK_PATTERN,
    MemoryType.ASSUMPTION: InsightType.STRATEGIC_INSIGHT,
    MemoryType.ADAPTATION_LESSON: InsightType.EXECUTION_LESSON,
}


# ============================================================================
# Extraction Rules
# ============================================================================

class ExtractionRule(BaseModel):
    """
    Rule for extracting insights from memory.
    """
    name: str
    description: str

    # Source memory requirements
    memory_types: List[MemoryType]
    min_confidence: float = 0.70
    min_durability: float = 0.60
    required_status: MemoryStatus = MemoryStatus.ACTIVE

    # Target insight type
    insight_type: InsightType
    default_scope: InsightScope = InsightScope.WORKFLOW_TYPE

    # Content transformation
    content_mapping: Dict[str, str] = Field(default_factory=dict)


# Default extraction rules
DEFAULT_EXTRACTION_RULES: List[ExtractionRule] = [
    ExtractionRule(
        name="playbook_to_reusable_playbook",
        description="Extract reusable playbooks from validated playbook memories",
        memory_types=[MemoryType.PLAYBOOK],
        min_confidence=0.75,
        min_durability=0.70,
        required_status=MemoryStatus.ACTIVE,
        insight_type=InsightType.REUSABLE_PLAYBOOK,
        default_scope=InsightScope.WORKFLOW_TYPE,
        content_mapping={
            "guidance": "guidance",
            "triggers": "triggers",
            "steps": "steps",
            "expected_outcome": "expected_outcome",
        }
    ),

    ExtractionRule(
        name="warning_to_risk_pattern",
        description="Extract risk patterns from validated warning memories",
        memory_types=[MemoryType.WARNING],
        min_confidence=0.70,
        min_durability=0.65,
        required_status=MemoryStatus.ACTIVE,
        insight_type=InsightType.RISK_PATTERN,
        default_scope=InsightScope.DOMAIN,
        content_mapping={
            "risk_description": "risk_description",
            "mitigation": "mitigation",
            "anti_patterns": "indicators",
        }
    ),

    ExtractionRule(
        name="heuristic_to_best_practice",
        description="Extract best practices from validated heuristic memories",
        memory_types=[MemoryType.HEURISTIC],
        min_confidence=0.70,
        min_durability=0.65,
        required_status=MemoryStatus.ACTIVE,
        insight_type=InsightType.BEST_PRACTICE,
        default_scope=InsightScope.WORKFLOW_TYPE,
        content_mapping={
            "rule": "practice",
            "rationale": "rationale",
            "exceptions": "exceptions",
        }
    ),

    ExtractionRule(
        name="adaptation_lesson_to_execution_lesson",
        description="Extract execution lessons from validated adaptation lessons",
        memory_types=[MemoryType.ADAPTATION_LESSON],
        min_confidence=0.70,
        min_durability=0.60,
        required_status=MemoryStatus.ACTIVE,
        insight_type=InsightType.EXECUTION_LESSON,
        default_scope=InsightScope.WORKFLOW_TYPE,
        content_mapping={
            "lesson": "lesson",
            "adaptation_type": "context",
        }
    ),

    ExtractionRule(
        name="assumption_to_strategic_insight",
        description="Extract strategic insights from validated assumption memories",
        memory_types=[MemoryType.ASSUMPTION],
        min_confidence=0.75,
        min_durability=0.70,
        required_status=MemoryStatus.ACTIVE,
        insight_type=InsightType.STRATEGIC_INSIGHT,
        default_scope=InsightScope.GLOBAL,
        content_mapping={
            "assumption": "observation",
        }
    ),
]


# ============================================================================
# Extraction Result
# ============================================================================

class ExtractionResult(BaseModel):
    """
    Result of insight candidate extraction.
    """
    success: bool
    candidate: Optional[InsightCreate] = None
    source_memory_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Candidate Extractor
# ============================================================================

class InsightCandidateExtractor:
    """
    Extracts insight candidates from validated strategic memory.

    Only extracts memories that meet quality thresholds and
    maps memory content to insight-specific structure.
    """

    def __init__(
        self,
        extraction_rules: Optional[List[ExtractionRule]] = None,
    ):
        """
        Initialize the extractor.

        Args:
            extraction_rules: Custom extraction rules (uses defaults if None)
        """
        self.extraction_rules = extraction_rules or DEFAULT_EXTRACTION_RULES

    def extract_from_memory(
        self,
        memory: StrategicMemory
    ) -> ExtractionResult:
        """
        Extract an insight candidate from a single memory.

        Args:
            memory: The strategic memory to extract from

        Returns:
            ExtractionResult with candidate or rejection reason
        """
        # Check if memory meets basic requirements
        if not self._is_eligible_memory(memory):
            return ExtractionResult(
                success=False,
                source_memory_id=memory.id,
                rejection_reason=self._get_ineligibility_reason(memory)
            )

        # Find applicable extraction rule
        rule = self._find_applicable_rule(memory)
        if not rule:
            return ExtractionResult(
                success=False,
                source_memory_id=memory.id,
                rejection_reason=f"No extraction rule for memory type: {memory.memory_type.value}"
            )

        # Transform memory content to insight content
        insight_content = self._transform_content(
            memory.memory_content,
            rule.content_mapping
        )

        # Map memory scope to insight scope
        insight_scope = self._map_scope(memory.scope)

        # Create source reference
        source_ref = SourceReference(
            source_type=InsightSourceType.MEMORY,
            source_id=memory.id,
            contribution_weight=1.0,
            extraction_method="memory_to_insight_extraction",
            referenced_at=datetime.now(),
            evidence_snippet=memory.title
        )

        # Build quality metrics from memory
        quality = QualityMetrics(
            confidence_score=memory.confidence,
            validation_score=memory.effectiveness_score or memory.confidence,
            applicability_score=memory.durability_score,
            source_count=len(memory.source_pattern_ids) + len(memory.source_insight_ids),
            execution_count=memory.usage_count,
            success_rate=memory.effectiveness_score,
            last_validated_at=memory.last_validated_at,
            evidence_cutoff_at=memory.created_at,
        )

        # Create insight candidate
        candidate = InsightCreate(
            insight_type=rule.insight_type,
            title=f"Insight: {memory.title}",
            summary=memory.memory_content.get("description", memory.title)[:500],
            scope=insight_scope,
            scope_key=memory.scope_key,
            content=insight_content,
            domain=memory.domain,
            tags=self._extract_tags(memory),
            source_references=[source_ref],
            quality=quality,
            initial_state=InsightLifecycleState.CANDIDATE,
        )

        return ExtractionResult(
            success=True,
            candidate=candidate,
            source_memory_id=memory.id,
        )

    def extract_from_memories(
        self,
        memories: List[StrategicMemory]
    ) -> List[ExtractionResult]:
        """
        Extract insight candidates from multiple memories.

        Args:
            memories: List of strategic memories to extract from

        Returns:
            List of extraction results
        """
        results = []
        for memory in memories:
            result = self.extract_from_memory(memory)
            results.append(result)

        # Log summary
        extracted = sum(1 for r in results if r.success)
        rejected = len(results) - extracted
        logger.info(
            f"Extraction complete: {extracted} candidates, {rejected} rejected "
            f"from {len(memories)} memories"
        )

        return results

    def _is_eligible_memory(self, memory: StrategicMemory) -> bool:
        """Check if memory is eligible for insight extraction."""
        # Must be active
        if memory.status != MemoryStatus.ACTIVE:
            return False

        # Must not be superseded
        if memory.supplanted_by_memory_id:
            return False

        # Must not be expired
        if memory.expires_at and memory.expires_at < datetime.now():
            return False

        # Must meet minimum confidence
        if memory.confidence < 0.65:
            return False

        # Must have content
        if not memory.memory_content:
            return False

        return True

    def _get_ineligibility_reason(self, memory: StrategicMemory) -> str:
        """Get the reason why a memory is not eligible."""
        if memory.status != MemoryStatus.ACTIVE:
            return f"Memory status is {memory.status.value}, not ACTIVE"

        if memory.supplanted_by_memory_id:
            return "Memory has been superseded"

        if memory.expires_at and memory.expires_at < datetime.now():
            return "Memory has expired"

        if memory.confidence < 0.65:
            return f"Memory confidence {memory.confidence} below threshold 0.65"

        if not memory.memory_content:
            return "Memory has no content"

        return "Memory does not meet eligibility criteria"

    def _find_applicable_rule(
        self,
        memory: StrategicMemory
    ) -> Optional[ExtractionRule]:
        """Find the extraction rule that applies to this memory."""
        for rule in self.extraction_rules:
            if memory.memory_type in rule.memory_types:
                # Check quality thresholds
                if memory.confidence < rule.min_confidence:
                    continue
                if memory.durability_score < rule.min_durability:
                    continue
                if memory.status != rule.required_status:
                    continue

                return rule

        return None

    def _transform_content(
        self,
        memory_content: Dict[str, Any],
        content_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Transform memory content to insight content structure."""
        insight_content = {}

        for insight_key, memory_key in content_mapping.items():
            if memory_key in memory_content:
                insight_content[insight_key] = memory_content[memory_key]

        # Preserve any additional fields not in mapping
        for key, value in memory_content.items():
            if key not in content_mapping.values() and key not in insight_content:
                insight_content[key] = value

        return insight_content

    def _map_scope(self, memory_scope: MemoryScope) -> InsightScope:
        """Map memory scope to insight scope."""
        scope_map = {
            MemoryScope.GLOBAL: InsightScope.GLOBAL,
            MemoryScope.WORKFLOW_TYPE: InsightScope.WORKFLOW_TYPE,
            MemoryScope.AGENT_TYPE: InsightScope.AGENT_TYPE,
            MemoryScope.DOMAIN: InsightScope.DOMAIN,
            MemoryScope.TENANT: InsightScope.DOMAIN,  # Map tenant to domain
        }
        return scope_map.get(memory_scope, InsightScope.WORKFLOW_TYPE)

    def _extract_tags(self, memory: StrategicMemory) -> List[str]:
        """Extract tags from memory for insight categorization."""
        tags = []

        # Add memory type as tag
        tags.append(memory.memory_type.value)

        # Add domain if present
        if memory.domain:
            tags.append(memory.domain)

        # Add scope if specific
        if memory.scope_key:
            tags.append(memory.scope_key)

        # Extract from content
        if memory.memory_content:
            # Look for common tag fields
            for tag_field in ["tags", "keywords", "categories"]:
                if tag_field in memory.memory_content:
                    field_value = memory.memory_content[tag_field]
                    if isinstance(field_value, list):
                        tags.extend(field_value)
                    elif isinstance(field_value, str):
                        tags.append(field_value)

        # Dedupe and return
        return list(set(tags))


# ============================================================================
# Batch Extraction
# ============================================================================

def extract_insight_candidates(
    memories: List[StrategicMemory],
    extraction_rules: Optional[List[ExtractionRule]] = None
) -> List[InsightCreate]:
    """
    Batch extract insight candidates from memories.

    Returns only successful candidates (not rejected ones).

    Args:
        memories: List of strategic memories
        extraction_rules: Optional custom extraction rules

    Returns:
        List of insight candidates ready for publication validation
    """
    extractor = InsightCandidateExtractor(extraction_rules)
    results = extractor.extract_from_memories(memories)

    # Filter to only successful extractions
    candidates = [
        result.candidate
        for result in results
        if result.success and result.candidate
    ]

    logger.info(
        f"Batch extraction: {len(candidates)} candidates from {len(memories)} memories "
        f"({len(results) - len(candidates)} rejected)"
    )

    return candidates


def get_extraction_summary(
    results: List[ExtractionResult]
) -> Dict[str, Any]:
    """
    Get summary statistics for extraction results.

    Args:
        results: List of extraction results

    Returns:
        Summary dict with counts and reasons
    """
    total = len(results)
    extracted = sum(1 for r in results if r.success)
    rejected = total - extracted

    # Group rejections by reason
    rejection_reasons: Dict[str, int] = {}
    for result in results:
        if not result.success and result.rejection_reason:
            reason = result.rejection_reason
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    # Group by insight type
    insight_type_counts: Dict[str, int] = {}
    for result in results:
        if result.success and result.candidate:
            itype = result.candidate.insight_type.value
            insight_type_counts[itype] = insight_type_counts.get(itype, 0) + 1

    return {
        "total_memories": total,
        "candidates_extracted": extracted,
        "rejected": rejected,
        "extraction_rate": extracted / total if total > 0 else 0,
        "rejection_reasons": rejection_reasons,
        "insight_type_counts": insight_type_counts,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def get_default_extractor() -> InsightCandidateExtractor:
    """Get the default insight candidate extractor."""
    return InsightCandidateExtractor(DEFAULT_EXTRACTION_RULES)


def is_memory_extractable(memory: StrategicMemory) -> bool:
    """
    Quick check if a memory is eligible for insight extraction.

    Args:
        memory: The strategic memory to check

    Returns:
        True if memory can be extracted
    """
    extractor = get_default_extractor()
    return extractor._is_eligible_memory(memory)

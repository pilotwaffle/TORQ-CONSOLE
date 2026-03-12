"""
TORQ Layer 8 - Insight Evolution Engine

L8-M1: Enables insights to evolve through supersession.

The InsightEvolutionEngine manages insight lifecycle, tracks
lineage, and handles supersession of old insights by improved ones.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from ..autonomous_models import (
    InsightEvolution,
    InsightLineage,
    InsightSupersession,
    InsightLifecycleStage,
)


# ============================================================================
# Insight Update Proposal
# ============================================================================

class InsightUpdateProposal(BaseModel):
    """A proposed update to an insight."""
    insight_id: str
    proposed_content: str
    improvement_reason: str
    confidence_delta: float  # Expected change in confidence
    supporting_evidence: List[str] = Field(default_factory=list)


# ============================================================================
# Insight Evolution Engine
# ============================================================================

class InsightEvolutionEngine:
    """
    Manages insight evolution and supersession.

    Tracks insight lifecycle, manages lineage, and handles
    the transition of insights through stages.
    """

    def __init__(self):
        """Initialize the insight evolution engine."""
        # Insight evolutions
        self._evolutions: Dict[str, InsightEvolution] = {}

        # Lineage tracking
        self._lineages: Dict[str, InsightLineage] = {}

        # Supersession records
        self._supersessions: List[InsightSupersession] = []

        # Stage tracking
        self._insights_by_stage: Dict[InsightLifecycleStage, List[str]] = (
            defaultdict(list)
        )

        # Validation tracking
        self._validation_history: Dict[str, List[datetime]] = defaultdict(list)
        self._reinforcement_history: Dict[str, int] = defaultdict(int)
        self._contradiction_history: Dict[str, int] = defaultdict(int)

    async def register_insight(
        self,
        insight_id: str,
        initial_confidence: float,
        source: str = "unknown",
        parent_insight_id: Optional[str] = None,
    ) -> InsightEvolution:
        """
        Register a new insight for evolution tracking.

        Args:
            insight_id: ID of the insight
            initial_confidence: Initial confidence score
            source: Source of the insight
            parent_insight_id: Optional parent insight ID

        Returns:
            InsightEvolution record
        """
        # Create lineage
        lineage = InsightLineage(
            insight_id=insight_id,
            parent_insight_id=parent_insight_id,
            evolution_count=0,
            creation_source=source,
        )
        self._lineages[insight_id] = lineage

        # Track parent
        if parent_insight_id:
            parent_lineage = self._lineages.get(parent_insight_id)
            if parent_lineage:
                parent_lineage.child_insight_ids.append(insight_id)

        # Create evolution record
        evolution = InsightEvolution(
            insight_id=insight_id,
            current_stage=InsightLifecycleStage.PUBLISHED,
            lineage=lineage,
            initial_confidence=initial_confidence,
            current_confidence=initial_confidence,
            confidence_history=[initial_confidence],
            created_at=datetime.now(),
        )

        self._evolutions[insight_id] = evolution
        self._insights_by_stage[InsightLifecycleStage.PUBLISHED].append(insight_id)

        logger.info(
            f"[InsightEvolution] Registered insight {insight_id}: "
            f"confidence={initial_confidence:.2f}, source={source}"
        )

        return evolution

    async def validate_insight(
        self,
        insight_id: str,
        validated: bool,
        validation_evidence: Optional[List[str]] = None,
    ) -> InsightEvolution:
        """
        Record a validation of an insight.

        Args:
            insight_id: ID of the insight
            validated: Whether validation was successful
            validation_evidence: Optional evidence for validation

        Returns:
            Updated InsightEvolution
        """
        evolution = self._evolutions.get(insight_id)
        if not evolution:
            raise ValueError(f"Insight not found: {insight_id}")

        evolution.validation_count += 1
        evolution.last_validated_at = datetime.now()

        # Track validation
        self._validation_history[insight_id].append(datetime.now())

        if validated:
            evolution.current_stage = InsightLifecycleStage.VALIDATED
            self._reinforcement_history[insight_id] += 1

            # Boost confidence slightly
            confidence_boost = 0.05
            evolution.current_confidence = min(1.0, evolution.current_confidence + confidence_boost)
        else:
            self._contradiction_history[insight_id] += 1

            # Reduce confidence
            confidence_penalty = 0.1
            evolution.current_confidence = max(0.0, evolution.current_confidence - confidence_penalty)

        evolution.confidence_history.append(evolution.current_confidence)

        # Update stage
        self._update_stage(evolution)

        logger.info(
            f"[InsightEvolution] Validated {insight_id}: "
            f"validated={validated}, new_confidence={evolution.current_confidence:.2f}"
        )

        return evolution

    async def reinforce_insight(
        self,
        insight_id: str,
        evidence: List[str],
    ) -> InsightEvolution:
        """
        Reinforce an insight with new supporting evidence.

        Args:
            insight_id: ID of the insight
            evidence: Supporting evidence

        Returns:
            Updated InsightEvolution
        """
        evolution = self._evolutions.get(insight_id)
        if not evolution:
            raise ValueError(f"Insight not found: {insight_id}")

        evolution.reinforcement_count += 1
        evolution.last_evolved_at = datetime.now()

        # Move to reinforced stage
        evolution.current_stage = InsightLifecycleStage.REINFORCED

        # Boost confidence
        confidence_boost = 0.03
        evolution.current_confidence = min(1.0, evolution.current_confidence + confidence_boost)
        evolution.confidence_history.append(evolution.current_confidence)

        self._update_stage(evolution)

        logger.info(
            f"[InsightEvolution] Reinforced {insight_id}: "
            f"reinforcements={evolution.reinforcement_count}, "
            f"confidence={evolution.current_confidence:.2f}"
        )

        return evolution

    async def supersede_insight(
        self,
        old_insight_id: str,
        new_insight_id: str,
        supersession_reason: str,
        improvement_description: str,
        new_confidence: float,
        validated_by: Optional[str] = None,
    ) -> InsightSupersession:
        """
        Supersede an old insight with a new improved version.

        Args:
            old_insight_id: ID of the insight being superseded
            new_insight_id: ID of the new insight
            supersession_reason: Reason for supersession
            improvement_description: Description of the improvement
            new_confidence: Confidence of the new insight
            validated_by: Optional validator

        Returns:
            InsightSupersession record
        """
        old_evolution = self._evolutions.get(old_insight_id)
        if not old_evolution:
            raise ValueError(f"Old insight not found: {old_insight_id}")

        # Calculate confidence gain
        old_confidence = old_evolution.current_confidence
        confidence_gain = new_confidence - old_confidence

        # Create supersession record
        supersession = InsightSupersession(
            old_insight_id=old_insight_id,
            new_insight_id=new_insight_id,
            supersession_reason=supersession_reason,
            improvement_description=improvement_description,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            confidence_gain=confidence_gain,
            validated_by=validated_by,
        )

        self._supersessions.append(supersession)

        # Update old insight
        old_evolution.current_stage = InsightLifecycleStage.SUPERSEDED
        old_evolution.superseded_by = new_insight_id
        old_evolution.superseded_at = datetime.now()

        # Update lineage
        old_lineage = self._lineages.get(old_insight_id)
        if old_lineage:
            old_lineage.child_insight_ids.append(new_insight_id)

        # Create or update new insight lineage
        new_lineage = InsightLineage(
            insight_id=new_insight_id,
            parent_insight_id=old_insight_id,
            evolution_count=old_lineage.evolution_count + 1 if old_lineage else 1,
            creation_source="supersession",
        )
        self._lineages[new_insight_id] = new_lineage

        # Create evolution for new insight
        new_evolution = InsightEvolution(
            insight_id=new_insight_id,
            current_stage=InsightLifecycleStage.PUBLISHED,
            lineage=new_lineage,
            initial_confidence=new_confidence,
            current_confidence=new_confidence,
            confidence_history=[new_confidence],
            created_at=datetime.now(),
        )
        self._evolutions[new_insight_id] = new_evolution

        logger.info(
            f"[InsightEvolution] Superseded {old_insight_id} with {new_insight_id}: "
            f"confidence_gain={confidence_gain:+.2f}"
        )

        return supersession

    async def merge_insights(
        self,
        insight_ids: List[str],
        merged_insight_id: str,
        merge_reason: str,
    ) -> InsightEvolution:
        """
        Merge multiple insights into a single combined insight.

        Args:
            insight_ids: IDs of insights to merge
            merged_insight_id: ID of the new merged insight
            merge_reason: Reason for the merge

        Returns:
            InsightEvolution for the merged insight
        """
        # Get all evolutions
        evolutions = [self._evolutions.get(i) for i in insight_ids]
        if None in evolutions:
            raise ValueError("One or more insights not found")

        # Calculate merged confidence (average)
        avg_confidence = sum(e.current_confidence for e in evolutions) / len(evolutions)

        # Create lineage for merged insight
        lineage = InsightLineage(
            insight_id=merged_insight_id,
            parent_insight_id=None,  # Merged from multiple
            evolution_count=1,
            creation_source="merge",
            merged_from=insight_ids,
        )
        self._lineages[merged_insight_id] = lineage

        # Update source insights
        for insight_id in insight_ids:
            source_lineage = self._lineages.get(insight_id)
            if source_lineage:
                # Mark as merged into new insight
                source_lineage.child_insight_ids.append(merged_insight_id)

        # Create evolution for merged insight
        evolution = InsightEvolution(
            insight_id=merged_insight_id,
            current_stage=InsightLifecycleStage.PUBLISHED,
            lineage=lineage,
            initial_confidence=avg_confidence,
            current_confidence=avg_confidence,
            confidence_history=[avg_confidence],
            created_at=datetime.now(),
        )
        self._evolutions[merged_insight_id] = evolution

        logger.info(
            f"[InsightEvolution] Merged {len(insight_ids)} insights into {merged_insight_id}: "
            f"confidence={avg_confidence:.2f}"
        )

        return evolution

    async def archive_insight(
        self,
        insight_id: str,
        reason: str,
    ) -> InsightEvolution:
        """
        Archive an insight that is no longer relevant.

        Args:
            insight_id: ID of the insight to archive
            reason: Reason for archiving

        Returns:
            Updated InsightEvolution
        """
        evolution = self._evolutions.get(insight_id)
        if not evolution:
            raise ValueError(f"Insight not found: {insight_id}")

        evolution.current_stage = InsightLifecycleStage.ARCHIVED

        logger.info(
            f"[InsightEvolution] Archived {insight_id}: {reason}"
        )

        return evolution

    def _update_stage(self, evolution: InsightEvolution):
        """Update the insight's stage based on its state."""
        # Remove from old stage
        for stage, insights in self._insights_by_stage.items():
            if evolution.insight_id in insights:
                insights.remove(evolution.insight_id)

        # Add to new stage
        self._insights_by_stage[evolution.current_stage].append(evolution.insight_id)

    async def get_evolution(
        self,
        insight_id: str,
    ) -> Optional[InsightEvolution]:
        """Get evolution record for an insight."""
        return self._evolutions.get(insight_id)

    async def get_lineage(
        self,
        insight_id: str,
    ) -> Optional[InsightLineage]:
        """Get lineage record for an insight."""
        return self._lineages.get(insight_id)

    async def get_insights_by_stage(
        self,
        stage: InsightLifecycleStage,
        limit: int = 100,
    ) -> List[InsightEvolution]:
        """Get all insights at a specific lifecycle stage."""
        insight_ids = self._insights_by_stage.get(stage, [])
        evolutions = [
            self._evolutions[i]
            for i in insight_ids[:limit]
            if i in self._evolutions
        ]
        return evolutions

    async def get_supersessions(
        self,
        insight_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[InsightSupersession]:
        """
        Get supersession records.

        Args:
            insight_id: Optional filter for old or new insight ID
            limit: Maximum results

        Returns:
            List of supersessions
        """
        supersessions = self._supersessions

        if insight_id:
            supersessions = [
                s for s in supersessions
                if s.old_insight_id == insight_id or s.new_insight_id == insight_id
            ]

        # Sort by time (newest first)
        supersessions = sorted(
            supersessions,
            key=lambda s: s.superseded_at,
            reverse=True,
        )

        return supersessions[:limit]

    async def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of insight evolution statistics."""
        return {
            "total_insights": len(self._evolutions),
            "by_stage": {
                stage.value: len(ids)
                for stage, ids in self._insights_by_stage.items()
            },
            "total_supersessions": len(self._supersessions),
            "avg_evolution_depth": sum(
                l.evolution_count
                for l in self._lineages.values()
            ) / max(len(self._lineages), 1),
            "avg_confidence": (
                sum(e.current_confidence for e in self._evolutions.values()) /
                max(len(self._evolutions), 1)
            ),
        }


# Global insight evolution engine instance
_engine: Optional[InsightEvolutionEngine] = None


def get_insight_evolution_engine() -> InsightEvolutionEngine:
    """Get the global insight evolution engine instance."""
    global _engine
    if _engine is None:
        _engine = InsightEvolutionEngine()
    return _engine

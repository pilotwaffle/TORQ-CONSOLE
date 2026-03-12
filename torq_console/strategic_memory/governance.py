"""
Memory Governance & Expiration Layer

Prevents strategic memory from becoming fossilized or dangerous.

Strategic memory can be harmful if it hardens outdated assumptions or
biases. Every memory must be validated, reviewable, and expirable.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from .models import (
    StrategicMemory,
    MemoryStatus,
    MemoryType,
    MemoryScope,
    MemoryValidation,
    MemorySupersedence,
    MemoryChallenge,
    GovernanceMetrics,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Governance State Machine
# ============================================================================

class GovernanceTransition(str, Enum):
    """Valid status transitions for governance."""
    CANDIDATE_TO_ACTIVE = "candidate_to_active"
    ACTIVE_TO_DEPRECATED = "active_to_deprecated"
    ACTIVE_TO_SUPPLANTED = "active_to_supplanted"
    DEPRECATED_TO_ARCHIVED = "deprecated_to_archived"
    ACTIVE_TO_ARCHIVED = "active_to_archived"

    # Revalidation paths
    ACTIVE_TO_ACTIVE = "active_revalidated"
    DEPRECATED_TO_ACTIVE = "deprecated_reinstated"


VALID_TRANSITIONS = {
    MemoryStatus.CANDIDATE: [MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED],
    MemoryStatus.ACTIVE: [MemoryStatus.DEPRECATED, MemoryStatus.SUPPLANTED, MemoryStatus.ARCHIVED],
    MemoryStatus.DEPRECATED: [MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED],
    MemoryStatus.SUPPLANTED: [MemoryStatus.ARCHIVED],
    MemoryStatus.ARCHIVED: []
}


# ============================================================================
# Governance Engine
# ============================================================================

class MemoryGovernanceEngine:
    """
    Manages the lifecycle of strategic memories.

    Responsibilities:
    - Validate candidate memories before activation
    - Revalidate active memories periodically
    - Expire stale or outdated memories
    - Handle supersession when newer memories replace old ones
    - Process challenges to memories based on new evidence
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    # ========================================================================
    # Approval & Activation
    # ========================================================================

    async def approve_candidate(
        self,
        memory_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> StrategicMemory:
        """
        Approve a candidate memory for activation.

        This is the primary governance action - graduating a pattern
        from "interesting" to "institutional knowledge."
        """
        # Get current memory
        memory = await self._get_memory(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        if memory.status != MemoryStatus.CANDIDATE:
            raise ValueError(f"Only candidate memories can be approved. Current status: {memory.status}")

        # Transition to active
        update_data = {
            "status": MemoryStatus.ACTIVE.value,
            "reviewed_at": datetime.now().isoformat(),
            "last_validated_at": datetime.now().isoformat()
        }

        # Set expiration if not set
        if not memory.expires_at:
            base_days = 90
            durability_multiplier = 1 + (memory.durability_score * 2)
            expires_in_days = int(base_days * durability_multiplier)
            update_data["expires_at"] = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

        result = self.supabase.table("strategic_memories").update(update_data).eq("id", memory_id).execute()

        logger.info(f"Approved candidate memory {memory_id} by {reviewer}")

        return StrategicMemory(**result.data[0]) if result.data else memory

    async def reject_candidate(
        self,
        memory_id: str,
        reviewer: str,
        reason: str
    ) -> bool:
        """Reject a candidate memory."""
        memory = await self._get_memory(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        if memory.status != MemoryStatus.CANDIDATE:
            raise ValueError(f"Only candidate memories can be rejected. Current status: {memory.status}")

        # Archive rejected candidates
        result = self.supabase.table("strategic_memories").update({
            "status": MemoryStatus.ARCHIVED.value,
            "reviewed_at": datetime.now().isoformat()
        }).eq("id", memory_id).execute()

        logger.info(f"Rejected candidate memory {memory_id}: {reason}")

        return True

    # ========================================================================
    # Revalidation
    # ========================================================================

    async def revalidate_memory(
        self,
        memory_id: str,
        validation: MemoryValidation
    ) -> StrategicMemory:
        """
        Revalidate an active memory with new evidence.

        Can adjust confidence and durability based on ongoing performance.
        """
        memory = await self._get_memory(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        update_data = {
            "last_validated_at": validation.validated_at.isoformat()
        }

        # Adjust scores if provided
        if validation.confidence_adjustment is not None:
            new_confidence = max(0.0, min(1.0, validation.confidence_adjustment))
            update_data["confidence"] = new_confidence

        if validation.durability_adjustment is not None:
            new_durability = max(0.0, min(1.0, validation.durability_adjustment))
            update_data["durability_score"] = new_durability

        # Deprecate if validation failed
        if not validation.is_valid:
            update_data["status"] = MemoryStatus.DEPRECATED.value

        result = self.supabase.table("strategic_memories").update(update_data).eq("id", memory_id).execute()

        logger.info(f"Revalidated memory {memory_id}: valid={validation.is_valid}")

        return StrategicMemory(**result.data[0]) if result.data else memory

    async def revalidate_due_memories(self) -> List[StrategicMemory]:
        """
        Revalidate all memories due for revalidation.

        Memories should be revalidated periodically based on their durability:
        - High durability: Every 90 days
        - Medium durability: Every 60 days
        - Low durability: Every 30 days
        """
        since = datetime.now() - timedelta(days=30)

        # Get memories not validated recently
        result = self.supabase.table("strategic_memories").select("*").eq("status", MemoryStatus.ACTIVE.value).lt("last_validated_at", since.isoformat()).execute()

        memories = [StrategicMemory(**m) for m in result.data] if result.data else []

        revalidated = []
        for memory in memories:
            # Auto-revalidate with current scores (system validator)
            validation = MemoryValidation(
                memory_id=memory.id,
                is_valid=True,
                validator="system_auto",
                notes=f"Automatic revalidation after {memory.durability_score:.0f} durability period"
            )
            updated = await self.revalidate_memory(memory.id, validation)
            revalidated.append(updated)

        logger.info(f"Auto-revalidated {len(revalidated)} memories")

        return revalidated

    # ========================================================================
    # Expiration
    # ========================================================================

    async def expire_stale_memories(self) -> List[StrategicMemory]:
        """
        Expire memories that have passed their expiration date.

        Deprecated memories are archived rather than deleted for audit trail.
        """
        now = datetime.now().isoformat()

        # Find expired active memories
        result = self.supabase.table("strategic_memories").select("*").eq("status", MemoryStatus.ACTIVE.value).lt("expires_at", now).execute()

        expired = []
        for memory_data in result.data:
            memory = StrategicMemory(**memory_data)

            # Deprecate expired memory
            updated = await self.deprecate_memory(
                memory.id,
                "system",
                "Expired per governance policy"
            )
            expired.append(updated)

        logger.info(f"Expired {len(expired)} memories")

        return expired

    async def deprecate_memory(
        self,
        memory_id: str,
        deprecator: str,
        reason: str
    ) -> StrategicMemory:
        """
        Deprecate a memory (mark as outdated but keep for reference).

        Unlike archival, deprecated memories remain visible as reference.
        """
        result = self.supabase.table("strategic_memories").update({
            "status": MemoryStatus.DEPRECATED.value
        }).eq("id", memory_id).execute()

        logger.info(f"Deprecated memory {memory_id} by {deprecator}: {reason}")

        return StrategicMemory(**result.data[0]) if result.data else await self._get_memory(memory_id)

    async def archive_memory(self, memory_id: str) -> StrategicMemory:
        """
        Archive a memory (remove from active use, keep for audit).

        Archived memories are not returned in searches but remain in database.
        """
        result = self.supabase.table("strategic_memories").update({
            "status": MemoryStatus.ARCHIVED.value
        }).eq("id", memory_id).execute()

        logger.info(f"Archived memory {memory_id}")

        return StrategicMemory(**result.data[0]) if result.data else await self._get_memory(memory_id)

    # ========================================================================
    # Supersession
    # ========================================================================

    async def supersede_memory(
        self,
        old_memory_id: str,
        new_memory_id: str,
        reason: str
    ) -> MemorySupersedence:
        """
        Mark an old memory as replaced by a new one.

        Creates a lineage chain showing memory evolution.
        """
        # Update old memory
        await self.deprecate_memory(old_memory_id, "system", f"Superseded by {new_memory_id}")

        # Link memories
        self.supabase.table("strategic_memories").update({
            "supplanted_by_memory_id": new_memory_id
        }).eq("id", old_memory_id).execute()

        self.supabase.table("strategic_memories").update({
            "supplanted_by_memory_id": old_memory_id  # Reference back
        }).eq("id", new_memory_id).execute()

        # Record supersession
        record = MemorySupersedence(
            old_memory_id=old_memory_id,
            new_memory_id=new_memory_id,
            reason=reason
        )

        self.supabase.table("memory_supersessions").insert({
            "old_memory_id": old_memory_id,
            "new_memory_id": new_memory_id,
            "reason": reason,
            "superseded_at": record.superseded_at.isoformat()
        }).execute()

        logger.info(f"Superseded memory {old_memory_id} with {new_memory_id}")

        return record

    # ========================================================================
    # Challenges
    # ========================================================================

    async def challenge_memory(
        self,
        challenge: MemoryChallenge
    ) -> bool:
        """
        Challenge a memory based on new contradicting evidence.

        Challenges can trigger automatic deprecation or human review.
        """
        # Record the challenge
        self.supabase.table("memory_challenges").insert({
            "memory_id": challenge.memory_id,
            "challenging_pattern_id": challenge.challenging_pattern_id,
            "challenge_description": challenge.challenge_description,
            "evidence_summary": challenge.evidence_summary,
            "challenged_at": challenge.challenged_at.isoformat()
        }).execute()

        # Get challenge count for this memory
        result = self.supabase.table("memory_challenges").select("*").eq("memory_id", challenge.memory_id).execute()

        challenge_count = len(result.data) if result.data else 0

        # Auto-deprecate if multiple challenges
        if challenge_count >= 3:
            await self.deprecate_memory(
                challenge.memory_id,
                "system",
                f"Auto-deprecated after {challenge_count} challenges"
            )
            logger.warning(f"Auto-deprecated memory {challenge.memory_id} after multiple challenges")
            return True

        # Lower confidence on single challenge
        memory = await self._get_memory(challenge.memory_id)
        if memory:
            new_confidence = max(0.3, memory.confidence - 0.15)
            await self.revalidate_memory(
                challenge.memory_id,
                MemoryValidation(
                    memory_id=challenge.memory_id,
                    is_valid=True,
                    confidence_adjustment=new_confidence,
                    validator="system_challenge",
                    notes="Confidence reduced due to challenge"
                )
            )

        return True

    # ========================================================================
    # Governance Metrics
    # ========================================================================

    async def get_governance_metrics(self) -> GovernanceMetrics:
        """Get metrics about strategic memory governance health."""
        # Count by status
        def count_by_status(status: MemoryStatus) -> int:
            result = self.supabase.table("strategic_memories").select("id", count="exact").eq("status", status.value).execute()
            return result.count if hasattr(result, 'count') else len(result.data) if result.data else 0

        total = count_by_status(MemoryStatus.ACTIVE) + count_by_status(MemoryStatus.CANDIDATE)
        active = count_by_status(MemoryStatus.ACTIVE)
        candidates = count_by_status(MemoryStatus.CANDIDATE)
        deprecated = count_by_status(MemoryStatus.DEPRECATED)

        # Expiring soon
        soon = datetime.now() + timedelta(days=7)
        expiring_result = self.supabase.table("strategic_memories").select("id").eq("status", MemoryStatus.ACTIVE.value).lt("expires_at", soon.isoformat()).execute()
        expiring_soon = len(expiring_result.data) if expiring_result.data else 0

        # Expired but still active
        now = datetime.now().isoformat()
        expired_active_result = self.supabase.table("strategic_memories").select("id").eq("status", MemoryStatus.ACTIVE.value).lt("expires_at", now).execute()
        expired_but_active = len(expired_active_result.data) if expired_active_result.data else 0

        # Low confidence active
        low_conf_result = self.supabase.table("strategic_memories").select("id").eq("status", MemoryStatus.ACTIVE.value).lt("confidence", 0.5).execute()
        low_confidence_active = len(low_conf_result.data) if low_conf_result.data else 0

        # Never validated (no last_validated_at)
        never_validated_result = self.supabase.table("strategic_memories").select("id", "created_at").eq("status", MemoryStatus.ACTIVE.value).is_("last_validated_at", None).execute()
        never_validated = len(never_validated_result.data) if never_validated_result.data else 0

        # Average age
        age_result = self.supabase.table("strategic_memories").select("created_at").eq("status", MemoryStatus.ACTIVE.value).execute()
        if age_result.data:
            ages = []
            for m in age_result.data:
                created = datetime.fromisoformat(m["created_at"])
                age_days = (datetime.now() - created).days
                ages.append(age_days)
            avg_age = sum(ages) / len(ages) if ages else 0
        else:
            avg_age = 0.0

        return GovernanceMetrics(
            total_memories=total,
            active_memories=active,
            candidate_memories=candidates,
            deprecated_memories=deprecated,
            expiring_soon=expiring_soon,
            expired_but_active=expired_but_active,
            low_confidence_active=low_confidence_active,
            never_validated=never_validated,
            average_memory_age_days=round(avg_age, 1)
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_memory(self, memory_id: str) -> Optional[StrategicMemory]:
        """Get a memory by ID."""
        result = self.supabase.table("strategic_memories").select("*").eq("id", memory_id).execute()

        if result.data:
            return StrategicMemory(**result.data[0])
        return None

    async def can_transition(
        self,
        memory_id: str,
        new_status: MemoryStatus
    ) -> bool:
        """Check if a status transition is valid."""
        memory = await self._get_memory(memory_id)
        if not memory:
            return False

        valid_targets = VALID_TRANSITIONS.get(memory.status, [])
        return new_status in valid_targets


# ============================================================================
# Memory Lineage Tracker
# ============================================================================

class MemoryLineageTracker:
    """
    Tracks the evolution and relationships between memories.

    Useful for understanding:
    - Which memories replaced which (supersession chain)
    - Which memories derived from which patterns (source lineage)
    - Which memories are related (common source patterns)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def get_lineage(self, memory_id: str) -> Dict[str, Any]:
        """Get the full lineage of a memory."""
        memory = await self._get_memory(memory_id)
        if not memory:
            return {}

        lineage = {
            "memory": {
                "id": memory.id,
                "title": memory.title,
                "type": memory.memory_type,
                "status": memory.status
            },
            "sources": {
                "patterns": memory.source_pattern_ids,
                "insights": memory.source_insight_ids,
                "experiments": memory.source_experiment_ids
            },
            "supersedes": None,
            "supplanted_by": None,
            "related": []
        }

        # Supersedes
        if memory.supplanted_by_memory_id:
            old_memory = await self._get_memory(memory.supplanted_by_memory_id)
            if old_memory:
                lineage["supersedes"] = {
                    "id": old_memory.id,
                    "title": old_memory.title,
                    "status": old_memory.status
                }

        # Supplanted by
        result = self.supabase.table("strategic_memories").select("*").eq("supplanted_by_memory_id", memory_id).execute()
        if result.data:
            newer = StrategicMemory(**result.data[0])
            lineage["supplanted_by"] = {
                "id": newer.id,
                "title": newer.title,
                "status": newer.status
            }

        # Related memories (share source patterns)
        if memory.source_pattern_ids:
            related_result = self.supabase.table("strategic_memories").select("*").contains("source_pattern_ids", memory.source_pattern_ids).neq("id", memory_id).execute()
            lineage["related"] = [
                {"id": m["id"], "title": m["title"], "type": m["memory_type"]}
                for m in related_result.data[:5]
            ] if related_result.data else []

        return lineage

    async def _get_memory(self, memory_id: str) -> Optional[StrategicMemory]:
        """Get a memory by ID."""
        result = self.supabase.table("strategic_memories").select("*").eq("id", memory_id).execute()

        if result.data:
            return StrategicMemory(**result.data[0])
        return None

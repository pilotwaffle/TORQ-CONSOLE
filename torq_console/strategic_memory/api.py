"""
Strategic Memory API

Administrative and runtime endpoints for strategic memory management.

Provides:
- Memory creation, review, and approval workflow
- Memory search and retrieval for agent injection
- Governance operations (deprecate, supersede, challenge)
- Metrics and analytics for memory health
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .models import (
    StrategicMemory,
    StrategicMemoryCreate,
    StrategicMemoryUpdate,
    MemoryType,
    MemoryScope,
    MemoryStatus,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryInjectionContext,
    MemoryInjection,
    GovernanceMetrics,
    MemoryValidation,
    MemorySupersedence,
    MemoryChallenge,
)
from .consolidation import MemoryConsolidationEngine, MemoryCandidate
from .retrieval import MemoryRetrievalEngine, MemoryInjector
from .governance import MemoryGovernanceEngine, MemoryLineageTracker


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategic-memory", tags=["strategic-memory"])


# ============================================================================
# Dependencies
# ============================================================================

def get_supabase():
    """Get Supabase client."""
    from ..dependencies import get_supabase_client
    return get_supabase_client()


def get_consolidation_engine(supabase=Depends(get_supabase)) -> MemoryConsolidationEngine:
    """Get consolidation engine instance."""
    return MemoryConsolidationEngine(supabase)


def get_retrieval_engine(supabase=Depends(get_supabase)) -> MemoryRetrievalEngine:
    """Get retrieval engine instance."""
    return MemoryRetrievalEngine(supabase)


def get_governance_engine(supabase=Depends(get_supabase)) -> MemoryGovernanceEngine:
    """Get governance engine instance."""
    return MemoryGovernanceEngine(supabase)


def get_lineage_tracker(supabase=Depends(get_supabase)) -> MemoryLineageTracker:
    """Get lineage tracker instance."""
    return MemoryLineageTracker(supabase)


# ============================================================================
# Memory Creation & Consolidation
# ============================================================================

@router.post("/consolidate")
async def consolidate_candidates(
    days_back: int = Query(30, ge=1, le=90),
    engine: MemoryConsolidationEngine = Depends(get_consolidation_engine)
):
    """
    Find and propose memory candidates from cross-workspace patterns.

    Runs consolidation rules to identify patterns that qualify for
    strategic memory status.
    """
    candidates = await engine.find_memory_candidates(days_back=days_back)

    return {
        "candidates_found": len(candidates),
        "period_days": days_back,
        "candidates": [
            {
                "memory_type": c.memory_type,
                "title": c.title,
                "domain": c.domain,
                "confidence": c.confidence_score,
                "durability": c.durability_score,
                "workspace_count": c.workspace_count,
                "execution_count": c.execution_count
            }
            for c in candidates
        ]
    }


@router.post("/propose")
async def propose_memory(
    candidate: MemoryCandidate,
    engine: MemoryConsolidationEngine = Depends(get_consolidation_engine),
    supabase=Depends(get_supabase)
):
    """
    Propose a memory candidate for governance review.

    Converts a candidate into a formal memory create request.
    """
    proposal = await engine.propose_memory(candidate)

    # Insert as candidate
    result = supabase.table("strategic_memories").insert({
        "memory_type": proposal.memory_type.value,
        "title": proposal.title,
        "domain": proposal.domain,
        "scope": proposal.scope.value,
        "scope_key": proposal.scope_key,
        "memory_content": proposal.memory_content,
        "source_pattern_ids": proposal.source_pattern_ids,
        "source_insight_ids": proposal.source_insight_ids,
        "source_experiment_ids": proposal.source_experiment_ids,
        "confidence": proposal.initial_confidence,
        "durability_score": proposal.initial_durability,
        "status": "candidate",
        "expires_at": (datetime.now() + timedelta(days=proposal.expires_in_days)).isoformat()
    }).execute()

    return {
        "success": True,
        "memory_id": result.data[0]["id"] if result.data else None,
        "status": "candidate",
        "message": "Memory proposed and pending review"
    }


@router.post("/create")
async def create_memory(
    memory: StrategicMemoryCreate,
    supabase=Depends(get_supabase)
):
    """Create a new strategic memory (bypasses consolidation)."""
    expires_at = None
    if memory.expires_in_days:
        expires_at = (datetime.now() + timedelta(days=memory.expires_in_days)).isoformat()

    result = supabase.table("strategic_memories").insert({
        "memory_type": memory.memory_type.value,
        "title": memory.title,
        "domain": memory.domain,
        "scope": memory.scope.value,
        "scope_key": memory.scope_key,
        "memory_content": memory.memory_content,
        "source_pattern_ids": memory.source_pattern_ids,
        "source_insight_ids": memory.source_insight_ids,
        "source_experiment_ids": memory.source_experiment_ids,
        "confidence": memory.initial_confidence,
        "durability_score": memory.initial_durability,
        "status": "candidate",
        "expires_at": expires_at
    }).execute()

    return {
        "success": True,
        "memory_id": result.data[0]["id"] if result.data else None
    }


# ============================================================================
# Memory Listing & Retrieval
# ============================================================================

@router.get("/")
async def list_memories(
    status: Optional[MemoryStatus] = Query(None),
    memory_type: Optional[MemoryType] = Query(None),
    scope: Optional[MemoryScope] = Query(None),
    domain: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    supabase=Depends(get_supabase)
):
    """List strategic memories with optional filters."""
    query = supabase.table("strategic_memories").select("*")

    if status:
        query = query.eq("status", status.value)
    if memory_type:
        query = query.eq("memory_type", memory_type.value)
    if scope:
        query = query.eq("scope", scope.value)
    if domain:
        query = query.eq("domain", domain)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "memories": result.data if result.data else [],
        "count": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    supabase=Depends(get_supabase)
):
    """Get a specific memory by ID."""
    result = supabase.table("strategic_memories").select("*").eq("id", memory_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Memory not found")

    return result.data[0]


@router.get("/{memory_id}/lineage")
async def get_memory_lineage(
    memory_id: str,
    tracker: MemoryLineageTracker = Depends(get_lineage_tracker)
):
    """Get the lineage and relationships of a memory."""
    lineage = await tracker.get_lineage(memory_id)

    if not lineage:
        raise HTTPException(status_code=404, detail="Memory not found")

    return lineage


# ============================================================================
# Memory Governance Actions
# ============================================================================

@router.post("/{memory_id}/approve")
async def approve_memory(
    memory_id: str,
    reviewer: str = Query(...),
    notes: Optional[str] = None,
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Approve a candidate memory for activation."""
    try:
        memory = await governance.approve_candidate(memory_id, reviewer, notes)
        return {
            "success": True,
            "memory_id": memory.id,
            "status": memory.status,
            "message": "Memory approved and activated"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{memory_id}/reject")
async def reject_memory(
    memory_id: str,
    reviewer: str = Query(...),
    reason: str = Query(...),
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Reject a candidate memory."""
    try:
        await governance.reject_candidate(memory_id, reviewer, reason)
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory rejected and archived"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{memory_id}/deprecate")
async def deprecate_memory(
    memory_id: str,
    deprecator: str = Query(...),
    reason: str = Query(...),
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Deprecate an active memory."""
    memory = await governance.deprecate_memory(memory_id, deprecator, reason)
    return {
        "success": True,
        "memory_id": memory.id,
        "status": memory.status
    }


@router.post("/{memory_id}/revalidate")
async def revalidate_memory(
    memory_id: str,
    validation: MemoryValidation,
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Revalidate a memory with new evidence."""
    memory = await governance.revalidate_memory(memory_id, validation)
    return {
        "success": True,
        "memory_id": memory.id,
        "confidence": memory.confidence,
        "status": memory.status
    }


@router.post("/{memory_id}/challenge")
async def challenge_memory(
    memory_id: str,
    challenge: MemoryChallenge,
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Challenge a memory with contradicting evidence."""
    challenge.memory_id = memory_id
    success = await governance.challenge_memory(challenge)

    return {
        "success": success,
        "memory_id": memory_id,
        "message": "Challenge recorded"
    }


@router.post("/supersede")
async def supersede_memory(
    old_memory_id: str,
    new_memory_id: str,
    reason: str = Query(...),
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Mark an old memory as replaced by a new one."""
    record = await governance.supersede_memory(old_memory_id, new_memory_id, reason)

    return {
        "success": True,
        "old_memory_id": old_memory_id,
        "new_memory_id": new_memory_id,
        "superseded_at": record.superseded_at.isoformat()
    }


# ============================================================================
# Runtime Search & Injection
# ============================================================================

@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    retrieval: MemoryRetrievalEngine = Depends(get_retrieval_engine)
):
    """
    Search for strategic memories.

    Returns memories ranked by relevance to the search context.
    """
    results = await retrieval.search(request)

    return {
        "results": [
            {
                "memory": {
                    "id": r.memory.id,
                    "type": r.memory.memory_type,
                    "title": r.memory.title,
                    "domain": r.memory.domain,
                    "scope": r.memory.scope,
                    "confidence": r.memory.confidence,
                    "durability": r.memory.durability_score
                },
                "relevance_score": r.relevance_score,
                "match_reason": r.match_reason
            }
            for r in results
        ],
        "count": len(results)
    }


@router.post("/inject")
async def get_injection(
    context: MemoryInjectionContext,
    retrieval: MemoryRetrievalEngine = Depends(get_retrieval_engine)
):
    """
    Get memories to inject into agent context.

    This is the primary endpoint for runtime memory injection.
    """
    injection = await retrieval.get_injection(context)

    return {
        "heuristics": [
            {"id": h.id, "title": h.title, "content": h.memory_content}
            for h in injection.heuristics
        ],
        "playbooks": [
            {"id": p.id, "title": p.title, "content": p.memory_content}
            for p in injection.playbooks
        ],
        "warnings": [
            {"id": w.id, "title": w.title, "content": w.memory_content}
            for w in injection.warnings
        ],
        "assumptions": [
            {"id": a.id, "title": a.title, "content": a.memory_content}
            for a in injection.assumptions
        ],
        "adaptation_lessons": [
            {"id": l.id, "title": l.title, "content": l.memory_content}
            for l in injection.adaptation_lessons
        ],
        "total_count": injection.total_count,
        "context_text": injection.get_context_text()
    }


@router.get("/playbooks")
async def get_playbooks(
    workflow_type: Optional[str] = None,
    domain: Optional[str] = None,
    max_results: int = Query(5, ge=1, le=20),
    retrieval: MemoryRetrievalEngine = Depends(get_retrieval_engine)
):
    """Get active playbooks for a workflow type or domain."""
    playbooks = await retrieval.get_playbooks(workflow_type, domain, max_results)

    return {
        "playbooks": [
            {
                "id": p.id,
                "title": p.title,
                "domain": p.domain,
                "scope": p.scope,
                "scope_key": p.scope_key,
                "confidence": p.confidence,
                "guidance": p.memory_content.get("guidance", ""),
                "triggers": p.memory_content.get("triggers", [])
            }
            for p in playbooks
        ],
        "count": len(playbooks)
    }


@router.get("/warnings")
async def get_warnings(
    workflow_type: Optional[str] = None,
    domain: Optional[str] = None,
    max_results: int = Query(5, ge=1, le=20),
    retrieval: MemoryRetrievalEngine = Depends(get_retrieval_engine)
):
    """Get active warnings for a workflow type or domain."""
    warnings = await retrieval.get_warnings(workflow_type, domain, max_results)

    return {
        "warnings": [
            {
                "id": w.id,
                "title": w.title,
                "domain": w.domain,
                "severity": w.memory_content.get("severity", "unknown"),
                "risk_description": w.memory_content.get("risk_description", ""),
                "mitigation": w.memory_content.get("mitigation", "")
            }
            for w in warnings
        ],
        "count": len(warnings)
    }


@router.get("/heuristics")
async def get_heuristics(
    domain: Optional[str] = None,
    agent_type: Optional[str] = None,
    max_results: int = Query(5, ge=1, le=20),
    retrieval: MemoryRetrievalEngine = Depends(get_retrieval_engine)
):
    """Get active heuristics for a domain or agent type."""
    heuristics = await retrieval.get_heuristics(domain, agent_type, max_results)

    return {
        "heuristics": [
            {
                "id": h.id,
                "title": h.title,
                "domain": h.domain,
                "rule": h.memory_content.get("rule", ""),
                "rationale": h.memory_content.get("rationale", ""),
                "confidence": h.confidence
            }
            for h in heuristics
        ],
        "count": len(heuristics)
    }


# ============================================================================
# Metrics & Analytics
# ============================================================================

@router.get("/metrics/governance")
async def get_governance_metrics(
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Get governance metrics about strategic memory health."""
    return await governance.get_governance_metrics()


@router.get("/metrics/effectiveness")
async def get_effectiveness_metrics(
    supabase=Depends(get_supabase)
):
    """Get effectiveness summary for active memories."""
    result = supabase.table("memory_effectiveness_summary").select("*").execute()

    return {
        "memories": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }


@router.get("/metrics/usage")
async def get_usage_metrics(
    days_back: int = Query(30, ge=1, le=90),
    supabase=Depends(get_supabase)
):
    """Get memory usage statistics over a period."""
    since = datetime.now() - timedelta(days=days_back)

    result = supabase.table("memory_usage").select("*").gte("used_at", since.isoformat()).execute()

    usage_by_type = {}
    for usage in result.data if result.data else []:
        # Get memory type from strategic_memories
        memory_result = supabase.table("strategic_memories").select("memory_type").eq("id", usage["memory_id"]).execute()
        if memory_result.data:
            mem_type = memory_result.data[0]["memory_type"]
            usage_by_type[mem_type] = usage_by_type.get(mem_type, 0) + 1

    return {
        "period_days": days_back,
        "total_usage": len(result.data) if result.data else 0,
        "usage_by_type": usage_by_type,
        "helpful_ratio": sum(1 for u in result.data if u.get("was_helpful") == True) / max(len(result.data), 1) if result.data else 0
    }


# ============================================================================
# Maintenance Operations
# ============================================================================

@router.post("/maintenance/revalidate")
async def run_revalidation(
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Run automatic revalidation of due memories."""
    revalidated = await governance.revalidate_due_memories()

    return {
        "success": True,
        "revalidated_count": len(revalidated),
        "memories": [{"id": m.id, "confidence": m.confidence} for m in revalidated]
    }


@router.post("/maintenance/expire")
async def run_expiration(
    governance: MemoryGovernanceEngine = Depends(get_governance_engine)
):
    """Expire stale memories past their expiration date."""
    expired = await governance.expire_stale_memories()

    return {
        "success": True,
        "expired_count": len(expired),
        "memories": [{"id": m.id, "title": m.title} for m in expired]
    }


# ============================================================================
# Admin Views
# ============================================================================

@router.get("/admin/candidates")
async def get_candidates(supabase=Depends(get_supabase)):
    """Get candidate memories awaiting review."""
    result = supabase.table("candidate_memories").select("*").execute()

    return {
        "candidates": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }


@router.get("/admin/needs-attention")
async def get_needs_attention(supabase=Depends(get_supabase)):
    """Get memories requiring governance attention."""
    result = supabase.table("memories_needing_attention").select("*").execute()

    return {
        "memories": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }

"""
Memory Retrieval & Injection Layer

Searches, ranks, and injects strategic memories into agent reasoning context.

This is what makes strategic memory operational - it ensures agents begin
new tasks with institutional knowledge, not just local context.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from .models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryInjectionContext,
    MemoryInjection,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Relevance Scoring
# ============================================================================

class RelevanceSignal(str, Enum):
    """Types of relevance signals for memory matching."""
    EXACT_WORKFLOW_MATCH = "exact_workflow_match"
    DOMAIN_MATCH = "domain_match"
    AGENT_TYPE_MATCH = "agent_type_match"
    KEYWORD_MATCH = "keyword_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    GLOBAL_RELEVANCE = "global_relevance"


# ============================================================================
# Retrieval Engine
# ============================================================================

class MemoryRetrievalEngine:
    """
    Searches and ranks strategic memories for injection into agent context.

    Responsibilities:
    - Search memories by workflow type, domain, agent type
    - Rank by relevance, confidence, durability
    - Inject top memories into agent context
    - Track memory usage for effectiveness analytics
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def search(
        self,
        request: MemorySearchRequest
    ) -> List[MemorySearchResult]:
        """
        Search for strategic memories matching the criteria.

        Returns results ranked by relevance score.
        """
        # Build query
        query = self.supabase.table("strategic_memories").select("*")

        # Filter by status
        if not request.include_deprecated:
            query = query.eq("status", MemoryStatus.ACTIVE.value)
        else:
            query = query.in_("status", [
                MemoryStatus.ACTIVE.value,
                MemoryStatus.DEPRECATED.value
            ])

        # Filter by memory types
        if request.memory_types:
            type_values = [t.value if isinstance(t, str) else t.value for t in request.memory_types]
            query = query.in_("memory_type", type_values)

        # Filter by scope
        if request.scope:
            query = query.eq("scope", request.scope.value)

        # Filter by minimum confidence
        query = query.gte("confidence", request.min_confidence)

        # Execute query
        try:
            result = query.execute()
            memories = result.data or []
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

        # Filter out expired
        valid_memories = []
        now = datetime.now().isoformat()
        for m in memories:
            expires_at = m.get("expires_at")
            if expires_at and expires_at < now:
                continue
            valid_memories.append(m)

        # Score and rank
        results = []
        for memory_data in valid_memories[:request.max_results * 3]:  # Get more, then rank
            memory = StrategicMemory(**memory_data)
            relevance = self._score_relevance(memory, request)
            if relevance > 0.1:  # Minimum relevance threshold
                results.append(MemorySearchResult(
                    memory=memory,
                    relevance_score=relevance,
                    match_reason=self._explain_match(memory, request)
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Return top results
        return results[:request.max_results]

    async def get_injection(
        self,
        context: MemoryInjectionContext
    ) -> MemoryInjection:
        """
        Get memories to inject into agent context.

        This is the primary method for runtime memory injection.
        """
        injection = MemoryInjection()

        # Build search request from context
        search_request = MemorySearchRequest(
            workflow_type=context.workflow_type,
            domain=context.domain,
            agent_type=context.agent_type,
            query=context.task_description,
            max_results=context.max_memories,
            min_confidence=context.min_confidence
        )

        # Search all memory types
        results = await self.search(search_request)

        # Categorize by memory type
        for result in results:
            memory = result.memory
            inclusion = False

            if context.include_warnings and memory.memory_type == MemoryType.WARNING:
                injection.warnings.append(memory)
                inclusion = True
            elif context.include_playbooks and memory.memory_type == MemoryType.PLAYBOOK:
                injection.playbooks.append(memory)
                inclusion = True
            elif context.include_heuristics and memory.memory_type == MemoryType.HEURISTIC:
                injection.heuristics.append(memory)
                inclusion = True
            elif memory.memory_type == MemoryType.ASSUMPTION:
                injection.assumptions.append(memory)
                inclusion = True
            elif memory.memory_type == MemoryType.ADAPTATION_LESSON:
                injection.adaptation_lessons.append(memory)
                inclusion = True

            # Track usage
            if inclusion:
                await self._track_usage(memory.id, context.execution_id)

        injection.total_count = (
            len(injection.warnings) +
            len(injection.playbooks) +
            len(injection.heuristics) +
            len(injection.assumptions) +
            len(injection.adaptation_lessons)
        )

        return injection

    async def get_playbooks(
        self,
        workflow_type: Optional[str] = None,
        domain: Optional[str] = None,
        max_results: int = 5
    ) -> List[StrategicMemory]:
        """Get active playbooks for a workflow type or domain."""
        request = MemorySearchRequest(
            workflow_type=workflow_type,
            domain=domain,
            memory_types=[MemoryType.PLAYBOOK],
            max_results=max_results
        )
        results = await self.search(request)
        return [r.memory for r in results]

    async def get_warnings(
        self,
        workflow_type: Optional[str] = None,
        domain: Optional[str] = None,
        max_results: int = 5
    ) -> List[StrategicMemory]:
        """Get active warnings for a workflow type or domain."""
        request = MemorySearchRequest(
            workflow_type=workflow_type,
            domain=domain,
            memory_types=[MemoryType.WARNING],
            max_results=max_results
        )
        results = await self.search(request)
        return [r.memory for r in results]

    async def get_heuristics(
        self,
        domain: Optional[str] = None,
        agent_type: Optional[str] = None,
        max_results: int = 5
    ) -> List[StrategicMemory]:
        """Get active heuristics for a domain or agent type."""
        request = MemorySearchRequest(
            domain=domain,
            agent_type=agent_type,
            memory_types=[MemoryType.HEURISTIC],
            max_results=max_results
        )
        results = await self.search(request)
        return [r.memory for r in results]

    async def get_memory_by_id(self, memory_id: str) -> Optional[StrategicMemory]:
        """Get a specific memory by ID."""
        try:
            result = self.supabase.table("strategic_memories").select("*").eq("id", memory_id).execute()

            if result.data:
                return StrategicMemory(**result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None

    async def get_memories_by_status(
        self,
        status: MemoryStatus,
        limit: int = 50
    ) -> List[StrategicMemory]:
        """Get memories by status (for governance UI)."""
        try:
            result = self.supabase.table("strategic_memories").select("*").eq("status", status.value).limit(limit).execute()

            return [StrategicMemory(**m) for m in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error getting memories by status: {e}")
            return []

    # ========================================================================
    # Relevance Scoring
    # ========================================================================

    def _score_relevance(
        self,
        memory: StrategicMemory,
        request: MemorySearchRequest
    ) -> float:
        """Calculate relevance score for a memory given the search context."""
        score = 0.0

        # Base score from confidence
        score += memory.confidence * 0.2

        # Durability boost (more durable = more broadly applicable)
        score += memory.durability_score * 0.1

        # Scope matching
        if memory.scope == MemoryScope.GLOBAL:
            score += 0.3  # Global memories are broadly relevant
        elif memory.scope == MemoryScope.WORKFLOW_TYPE and request.workflow_type:
            if memory.scope_key == request.workflow_type:
                score += 0.5  # Exact workflow match
        elif memory.scope == MemoryScope.DOMAIN and request.domain:
            if memory.scope_key == request.domain:
                score += 0.4  # Domain match
        elif memory.scope == MemoryScope.AGENT_TYPE and request.agent_type:
            if memory.scope_key == request.agent_type:
                score += 0.4  # Agent type match

        # Keyword matching in title
        if request.query:
            query_lower = request.query.lower()
            title_lower = memory.title.lower()
            if query_lower in title_lower:
                score += 0.2

        # Domain matching
        if memory.domain and request.domain:
            if memory.domain.lower() == request.domain.lower():
                score += 0.15

        # Effectiveness boost (if tracked)
        if memory.effectiveness_score:
            score += memory.effectiveness_score * 0.1

        # Recent usage boost (memories used successfully recently)
        if memory.last_used_at:
            days_since_use = (datetime.now() - memory.last_used_at).days
            if days_since_use < 30:
                score += 0.05 * (1 - days_since_use / 30)

        return min(score, 1.0)

    def _explain_match(
        self,
        memory: StrategicMemory,
        request: MemorySearchRequest
    ) -> str:
        """Generate a human-readable explanation of why a memory matched."""
        reasons = []

        # Scope-based matching
        if memory.scope == MemoryScope.GLOBAL:
            reasons.append("global relevance")
        elif memory.scope == MemoryScope.WORKFLOW_TYPE and request.workflow_type:
            if memory.scope_key == request.workflow_type:
                reasons.append(f"exact workflow type match: {request.workflow_type}")
        elif memory.scope == MemoryScope.DOMAIN and request.domain:
            if memory.scope_key == request.domain:
                reasons.append(f"domain match: {request.domain}")

        # Domain matching
        if memory.domain and request.domain:
            if memory.domain.lower() == request.domain.lower():
                reasons.append(f"domain alignment: {memory.domain}")

        # Keyword matching
        if request.query and request.query.lower() in memory.title.lower():
            reasons.append("keyword match in title")

        # High confidence
        if memory.confidence > 0.8:
            reasons.append("high confidence")

        # High durability
        if memory.durability_score > 0.7:
            reasons.append("proven durability")

        return ", ".join(reasons) if reasons else "general relevance"

    async def _track_usage(self, memory_id: str, execution_id: Optional[str]):
        """Track memory usage for effectiveness analytics."""
        try:
            # Update usage count and last_used_at
            self.supabase.table("strategic_memories").update({
                "usage_count": self.supabase.table("strategic_memories").select("usage_count").eq("id", memory_id) + 1,
                "last_used_at": datetime.now().isoformat()
            }).eq("id", memory_id).execute()

            # Log usage to memory_usage table if tracking execution context
            if execution_id:
                self.supabase.table("memory_usage").insert({
                    "memory_id": memory_id,
                    "execution_id": execution_id,
                    "used_at": datetime.now().isoformat()
                }).execute()

        except Exception as e:
            logger.error(f"Error tracking memory usage: {e}")


# ============================================================================
# Context Injection Helper
# ============================================================================

class MemoryInjector:
    """
    Helper for injecting strategic memory into agent execution context.

    Provides methods for formatting memories into various context formats.
    """

    def __init__(self, retrieval_engine: MemoryRetrievalEngine):
        self.retrieval = retrieval_engine

    async def inject_into_system_prompt(
        self,
        context: MemoryInjectionContext,
        base_prompt: str
    ) -> str:
        """Inject memories into a system prompt."""
        injection = await self.retrieval.get_injection(context)

        if injection.total_count == 0:
            return base_prompt

        memory_context = injection.get_context_text()

        # Insert after system prompt header
        lines = base_prompt.split("\n")
        insert_idx = 0

        # Find end of initial header section
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                insert_idx = i
                break

        # Insert memory context
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, "## INSTITUTIONAL KNOWLEDGE")
        lines.insert(insert_idx + 2, memory_context)
        lines.insert(insert_idx + 3, "")

        return "\n".join(lines)

    async def inject_into_reasoning_trace(
        self,
        context: MemoryInjectionContext
    ) -> Dict[str, Any]:
        """Inject memories into a reasoning trace as structured metadata."""
        injection = await self.retrieval.get_injection(context)

        return {
            "strategic_memory_injection": {
                "injected_at": datetime.now().isoformat(),
                "context": {
                    "workflow_type": context.workflow_type,
                    "domain": context.domain,
                    "agent_type": context.agent_type
                },
                "memories": {
                    "warnings": [
                        {"id": m.id, "title": m.title, "severity": m.memory_content.get("severity", "unknown")}
                        for m in injection.warnings
                    ],
                    "heuristics": [
                        {"id": m.id, "title": m.title, "rule": m.memory_content.get("rule", "")}
                        for m in injection.heuristics
                    ],
                    "playbooks": [
                        {"id": m.id, "title": m.title, "steps_count": len(m.memory_content.get("steps", []))}
                        for m in injection.playbooks
                    ]
                },
                "total_injected": injection.total_count
            }
        }

    async def get_quick_warnings(
        self,
        workflow_type: str
    ) -> List[str]:
        """Get quick warning messages for a workflow type."""
        warnings = await self.retrieval.get_warnings(workflow_type=workflow_type)
        return [
            f"⚠️ {w.title}: {w.memory_content.get('risk_description', '')}"
            for w in warnings
        ]

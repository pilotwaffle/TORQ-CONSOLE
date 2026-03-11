"""
Strategic Memory Scoping Rules

Prevent institutional doctrine from overwhelming local context.

Scope hierarchy: tenant > workflow_type > domain > agent_type > global

Higher-scoped memories (tenant) override lower-scoped memories (global).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .models import (
    StrategicMemory,
    MemoryScope,
    MemoryType,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Scope Configuration
# ============================================================================

class ScopePrecedence(str, Enum):
    """Scope precedence levels (lower number = higher precedence)."""
    TENANT = 1
    WORKFLOW_TYPE = 2
    DOMAIN = 3
    AGENT_TYPE = 4
    GLOBAL = 5


# Per-scope memory limits (prevent context overload)
SCOPE_LIMITS = {
    MemoryScope.TENANT: 10,        # Most specific, allow more
    MemoryScope.WORKFLOW_TYPE: 5,
    MemoryScope.DOMAIN: 5,
    MemoryScope.AGENT_TYPE: 3,
    MemoryScope.GLOBAL: 3,         # Least specific, allow fewer
}

# Recommended mix for balanced injection
RECOMMENDED_MIX = {
    "workflow_scoped": 2,
    "domain_scoped": 1,
    "global_heuristic": 1,
    "playbook": 1,
}


# ============================================================================
# Scoping Rules
# ============================================================================

@dataclass
class ScopeConfig:
    """Configuration for memory scoping."""
    enable_tenant_scoping: bool = True
    enable_workflow_scoping: bool = True
    enable_domain_scoping: bool = True
    enable_agent_scoping: bool = True
    enable_global_scoping: bool = True

    # Override defaults
    scope_limits: Dict[MemoryScope, int] = field(default_factory=dict)
    precedence_order: List[MemoryScope] = field(default_factory=lambda: [
        MemoryScope.TENANT,
        MemoryScope.WORKFLOW_TYPE,
        MemoryScope.DOMAIN,
        MemoryScope.AGENT_TYPE,
        MemoryScope.GLOBAL,
    ])

    def get_limit(self, scope: MemoryScope) -> int:
        """Get memory limit for a scope."""
        return self.scope_limits.get(scope, SCOPE_LIMITS.get(scope, 5))

    def get_precedence(self, scope: MemoryScope) -> int:
        """Get precedence level for a scope (lower = higher priority)."""
        try:
            return self.precedence_order.index(scope) + 1
        except ValueError:
            return 10  # Unknown scopes get lowest priority


# ============================================================================
# Scoped Retrieval
# ============================================================================

class ScopedMemoryRetriever:
    """
    Retrieve memories with proper scope precedence and limits.

    Ensures:
    - Higher-scoped memories override lower-scoped ones
    - Per-scope limits prevent context overload
    - No duplicate topics across scopes
    """

    def __init__(self, supabase_client, config: Optional[ScopeConfig] = None):
        self.supabase = supabase_client
        self.config = config or ScopeConfig()

    async def retrieve_with_scoping(
        self,
        tenant_id: Optional[str],
        workflow_type: Optional[str],
        domain: Optional[str],
        agent_type: Optional[str],
        max_total: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        min_confidence: float = 0.5
    ) -> List[StrategicMemory]:
        """
        Retrieve memories with proper scope precedence.

        Returns deduplicated memories ordered by scope precedence.
        """
        all_memories = []

        # Fetch memories by scope in precedence order
        # Start with global (baseline), then layer on more specific scopes
        for scope in reversed(self.config.precedence_order):  # Global first
            if not self._is_scope_enabled(scope):
                continue

            memories = await self._fetch_by_scope(
                scope,
                tenant_id,
                workflow_type,
                domain,
                agent_type,
                memory_types,
                min_confidence
            )

            # Apply per-scope limit
            limit = self.config.get_limit(scope)
            memories = memories[:limit]

            all_memories.extend(memories)

        # Apply supersedence (higher scopes override lower scopes)
        deduped = self._apply_supersedence(all_memories)

        # Apply total limit and return
        return deduped[:max_total]

    async def retrieve_by_precedence(
        self,
        tenant_id: Optional[str],
        workflow_type: Optional[str],
        domain: Optional[str],
        agent_type: Optional[str],
        max_total: int = 5
    ) -> Dict[str, List[StrategicMemory]]:
        """
        Retrieve memories grouped by scope precedence.

        Returns dict with scope names as keys for debugging/analysis.
        """
        result = {}

        for scope in reversed(self.config.precedence_order):
            if not self._is_scope_enabled(scope):
                continue

            memories = await self._fetch_by_scope(
                scope,
                tenant_id,
                workflow_type,
                domain,
                agent_type,
                None,  # All types
                0.5   # Default confidence
            )

            result[scope.value] = memories[:self.config.get_limit(scope)]

        return result

    async def get_recommended_mix(
        self,
        workflow_type: Optional[str],
        domain: Optional[str],
        min_confidence: float = 0.5
    ) -> List[StrategicMemory]:
        """
        Get a balanced mix of memories by scope and type.

        Returns:
        - 2 workflow-scoped memories
        - 1 domain-scoped memory
        - 1 global heuristic
        - 1 playbook (any scope)
        """
        memories = []

        # Workflow-scoped (up to 2)
        if workflow_type:
            workflow_memories = await self._fetch_by_scope(
                MemoryScope.WORKFLOW_TYPE,
                None, workflow_type, None, None,
                [MemoryType.HEURISTIC, MemoryType.PLAYBOOK],
                min_confidence
            )
            memories.extend(workflow_memories[:2])

        # Domain-scoped (up to 1)
        if domain:
            domain_memories = await self._fetch_by_scope(
                MemoryScope.DOMAIN,
                None, None, domain, None,
                [MemoryType.HEURISTIC, MemoryType.WARNING],
                min_confidence
            )
            memories.extend(domain_memories[:1])

        # Global heuristic (1)
        global_heuristics = await self._fetch_by_scope(
            MemoryScope.GLOBAL,
            None, None, None, None,
            [MemoryType.HEURISTIC],
            min_confidence
        )
        memories.extend(global_heuristics[:1])

        # Any playbook (1, higher precedence)
        playbook_memories = await self._fetch_by_scope(
            MemoryScope.WORKFLOW_TYPE,
            None, workflow_type, None, None,
            [MemoryType.PLAYBOOK],
            min_confidence
        )
        if not playbook_memories:
            playbook_memories = await self._fetch_by_scope(
                MemoryScope.DOMAIN,
                None, None, domain, None,
                [MemoryType.PLAYBOOK],
                min_confidence
            )
        memories.extend(playbook_memories[:1])

        # Apply supersedence and limit
        deduped = self._apply_supersedence(memories)

        return deduped[:5]

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _fetch_by_scope(
        self,
        scope: MemoryScope,
        tenant_id: Optional[str],
        workflow_type: Optional[str],
        domain: Optional[str],
        agent_type: Optional[str],
        memory_types: Optional[List[MemoryType]],
        min_confidence: float
    ) -> List[StrategicMemory]:
        """Fetch memories for a specific scope."""
        try:
            query = self.supabase.table("strategic_memories").select("*")

            # Filter by status
            query = query.eq("status", "active")

            # Filter by scope
            query = query.eq("scope", scope.value)

            # Filter by scope_key
            scope_key = self._get_scope_key(scope, tenant_id, workflow_type, domain, agent_type)
            if scope_key:
                query = query.eq("scope_key", scope_key)

            # Filter by memory types
            if memory_types:
                type_values = [t.value if isinstance(t, str) else t.value for t in memory_types]
                query = query.in_("memory_type", type_values)

            # Filter by confidence
            query = query.gte("confidence", min_confidence)

            # Filter out expired
            query = query.or_("expires_at.is.null,expires_at.gt.now()")

            # Order by effectiveness if available, then confidence
            query = query.order("effectiveness_score", desc=True, nulls_last=True)
            query = query.order("confidence", desc=True)

            result = query.execute()

            return [StrategicMemory(**m) for m in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error fetching memories for scope {scope}: {e}")
            return []

    def _get_scope_key(
        self,
        scope: MemoryScope,
        tenant_id: Optional[str],
        workflow_type: Optional[str],
        domain: Optional[str],
        agent_type: Optional[str]
    ) -> Optional[str]:
        """Get the scope_key for a given scope type."""
        if scope == MemoryScope.TENANT:
            return tenant_id
        elif scope == MemoryScope.WORKFLOW_TYPE:
            return workflow_type
        elif scope == MemoryScope.DOMAIN:
            return domain
        elif scope == MemoryScope.AGENT_TYPE:
            return agent_type
        elif scope == MemoryScope.GLOBAL:
            return None  # Global memories don't have a scope_key
        return None

    def _is_scope_enabled(self, scope: MemoryScope) -> bool:
        """Check if a scope is enabled in config."""
        if scope == MemoryScope.TENANT:
            return self.config.enable_tenant_scoping
        elif scope == MemoryScope.WORKFLOW_TYPE:
            return self.config.enable_workflow_scoping
        elif scope == MemoryScope.DOMAIN:
            return self.config.enable_domain_scoping
        elif scope == MemoryScope.AGENT_TYPE:
            return self.config.enable_agent_scoping
        elif scope == MemoryScope.GLOBAL:
            return self.config.enable_global_scoping
        return False

    def _apply_supersedence(
        self,
        memories: List[StrategicMemory]
    ) -> List[StrategicMemory]:
        """
        Apply supersedence rules to remove conflicting memories.

        A memory supersedes another if:
        - Same memory_type
        - Similar topic (title/content similarity)
        - Higher scope precedence (lower precedence number)
        - Newer created_at (if same scope)
        - Higher confidence (if same scope and age)
        """
        if not memories:
            return []

        # Sort by scope precedence, then confidence, then recency
        sorted_memories = sorted(
            memories,
            key=lambda m: (
                self.config.get_precedence(m.scope),
                -m.confidence,
                -m.created_at.timestamp()
            )
        )

        kept = []
        kept_topics: Set[str] = set()

        for memory in sorted_memories:
            # Extract topic from title
            topic = self._extract_topic(memory.title, memory.memory_type)

            # Check if this topic already exists in kept memories
            if topic in kept_topics:
                # This memory is superseded by a higher-precedence one
                continue

            # Also check for conflicts with kept memories
            has_conflict = False
            for kept_memory in kept:
                if self._are_conflicting(memory, kept_memory):
                    # Higher precedence memory already kept
                    has_conflict = True
                    break

            if not has_conflict:
                kept.append(memory)
                kept_topics.add(topic)

        return kept

    def _extract_topic(self, title: str, memory_type: MemoryType) -> str:
        """
        Extract a topic key from memory title for deduplication.

        Simplified: use first few meaningful words.
        """
        # Remove common prefixes
        prefixes = ["the", "a", "an", "strategic", "memory", ""]
        words = title.lower().split()

        # Filter out common words
        meaningful = [w for w in words if w not in prefixes and len(w) > 2]

        # Return first 2-3 meaningful words as topic
        return "_".join(meaningful[:3])

    def _are_conflicting(
        self,
        memory1: StrategicMemory,
        memory2: StrategicMemory
    ) -> bool:
        """
        Check if two memories conflict (same topic, different guidance).

        Memories conflict if:
        - Same memory_type
        - Similar topics
        - Different scope_key (would apply to different contexts)
        """
        if memory1.memory_type != memory2.memory_type:
            return False

        # If different scope keys, they apply to different contexts
        if memory1.scope_key and memory2.scope_key:
            if memory1.scope_key != memory2.scope_key:
                return False

        # Check topic similarity
        topic1 = self._extract_topic(memory1.title, memory1.memory_type)
        topic2 = self._extract_topic(memory2.title, memory2.memory_type)

        # Exact match = conflict
        if topic1 == topic2:
            return True

        # Partial match (one is substring of other)
        if topic1 in topic2 or topic2 in topic1:
            return True

        return False


# ============================================================================
# Scope Configuration Management
# ============================================================================

class ScopeConfigManager:
    """
    Manage scope configuration for strategic memory retrieval.

    Stores and retrieves scope rules from database.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def get_config(self) -> ScopeConfig:
        """Get current scope configuration."""
        # Fetch from database or use defaults
        try:
            result = self.supabase.table("memory_scope_rules").select("*").order("precedence", ascending=True).execute()

            if result.data:
                return self._config_from_db(result.data)
            else:
                # Insert defaults
                await self._initialize_defaults()
                return ScopeConfig()

        except Exception as e:
            logger.error(f"Error fetching scope config: {e}")
            return ScopeConfig()

    async def update_limits(
        self,
        scope_limits: Dict[str, int]
    ):
        """Update per-scope memory limits."""
        for scope_str, limit in scope_limits.items():
            try:
                scope = MemoryScope(scope_str)
                self.supabase.table("memory_scope_rules").update({
                    "max_memories": limit
                ).eq("scope", scope.value).execute()
            except ValueError:
                logger.warning(f"Invalid scope: {scope_str}")

    async def _initialize_defaults(self):
        """Initialize default scope rules in database."""
        defaults = [
            {"scope": "tenant", "precedence": 1, "max_memories": 10, "enabled": True},
            {"scope": "workflow_type", "precedence": 2, "max_memories": 5, "enabled": True},
            {"scope": "domain", "precedence": 3, "max_memories": 5, "enabled": True},
            {"scope": "agent_type", "precedence": 4, "max_memories": 3, "enabled": True},
            {"scope": "global", "precedence": 5, "max_memories": 3, "enabled": True},
        ]

        for rule in defaults:
            self.supabase.table("memory_scope_rules").insert(rule).execute()

    def _config_from_db(self, rules: List[Dict[str, Any]]) -> ScopeConfig:
        """Build ScopeConfig from database rules."""
        enabled = {
            "tenant": False,
            "workflow_type": False,
            "domain": False,
            "agent_type": False,
            "global": False,
        }
        limits = {}
        precedence_order = []

        for rule in rules:
            scope_str = rule["scope"]
            enabled[scope_str] = rule.get("enabled", True)

            if rule.get("max_memories"):
                try:
                    scope = MemoryScope(scope_str)
                    limits[scope] = rule["max_memories"]
                except ValueError:
                    pass

            if rule.get("enabled", True):
                try:
                    precedence_order.append(MemoryScope(scope_str))
                except ValueError:
                    pass

        return ScopeConfig(
            enable_tenant_scoping=enabled.get("tenant", True),
            enable_workflow_scoping=enabled.get("workflow_type", True),
            enable_domain_scoping=enabled.get("domain", True),
            enable_agent_scoping=enabled.get("agent_type", True),
            enable_global_scoping=enabled.get("global", True),
            scope_limits=limits,
            precedence_order=precedence_order if precedence_order else None
        )

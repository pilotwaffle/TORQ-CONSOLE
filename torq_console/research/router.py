"""
Conservative Research Router

Decides when web research is needed. Implements a "local-first" approach
to avoid unnecessary browsing and control costs.
"""

import re
import logging
from typing import List, Optional, Set
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Time-related signals that indicate need for fresh data
TIME_CUES = [
    r"\btoday\b",
    r"\bthis week\b",
    r"\bthis month\b",
    r"\bthis year\b",
    r"\blatest\b",
    r"\brecent\b",
    r"\bcurrent\b",
    r"\bnow\b",
    r"\bnew\b",
    r"\bbreaking\b",
    r"\bjust\b.{0,20}\b(happened|released|announced)",
    r"\d{4}\s*(forecast|prediction|outlook|projection)",
    r"\b(price|rate|index|market).{0,50}\btoday\b",
]

# Volatility domains where information becomes stale quickly
VOLATILITY_DOMAINS = [
    "markets", "trading", "stocks", "bonds", "crypto", "bitcoin", "eth", "defi",
    "sports", "scores", "games", "match", "tournament", "league",
    "politics", "election", "vote", "congress", "parliament",
    "laws", "regulations", "legal", "court", "ruling", "bill",
    "security", "vulnerability", "breach", "exploit", "cve",
    "company", "ceo", "executive", "leadership", "founded",
    "weather", "forecast", "temperature",
]

# Signals user explicitly wants verification
EXPLICIT_RESEARCH_SIGNALS = [
    r"\bverify\b",
    r"\bcheck\b",
    r"\bconfirm\b",
    r"\bsources?\b",
    r"\blink\b",
    r"\breferences?\b",
    r"\bevidence\b",
    r"\bprove\b",
    r"\baccording to\b",
    r"\bsearch\b",
]

# Questions that are conceptual and don't need research
CONCEPTUAL_PATTERNS = [
    r"^what is\s+[a-z]{2,20}\s*\?$",  # "What is X?" (single concept)
    r"^define\s+",  # "Define X"
    r"^explain\s+(the concept of\s+)?[a-z]{2,20}\s*\?$",
    r"\b(meaning|definition|concept)\s+of\s+[a-z]{2,20}\b",
]

# Simple factual patterns that should be in local knowledge
LOCAL_KNOWLEDGE_PATTERNS = [
    r"\b(capital of|largest city in|population of)\s+[a-z]+\s*\?$",
    r"\b(president of|prime minister of)\s+[a-z]+\b",
    r"^\d+\s*\+\s*\d+\s*=",  # Math
]


class ResearchRouter:
    """
    Decides whether a query requires web research.

    Implements a conservative "local-first" approach:
    - Prefer cached/local knowledge when possible
    - Only browse when signals indicate fresh data is needed
    - Log the decision for auditability
    """

    def __init__(
        self,
        enable_cache: bool = True,
        cache_freshness_threshold_hours: int = 1,
    ):
        self.enable_cache = enable_cache
        self.cache_freshness_threshold_hours = cache_freshness_threshold_hours

    def should_research(
        self,
        query: str,
        user_context: Optional[dict] = None,
    ) -> tuple[bool, List[str]]:
        """
        Decide if research is needed for this query.

        Returns:
            (should_research, list of signals that triggered the decision)
        """
        query_lower = query.lower().strip()
        signals = []

        # Check for explicit research request (highest priority)
        if self._has_explicit_research_signal(query_lower):
            signals.append("explicit_research_request")

        # Check for time cues indicating need for current data
        time_cue = self._detect_time_cue(query_lower)
        if time_cue:
            signals.append(f"time_cue: {time_cue}")

        # Check for volatility domains
        volatility = self._detect_volatility_domain(query_lower)
        if volatility:
            signals.append(f"volatility_domain: {volatility}")

        # Check for unknown entities (proper nouns not in local memory)
        # This would be implemented with an embedding lookup in production
        # unknown_entities = self._detect_unknown_entities(query)

        # Check if this is a conceptual question (should NOT research)
        if self._is_conceptual(query):
            signals.append("conceptual_question")
            # For conceptual questions, prefer local knowledge
            # Only research if explicitly requested
            if "explicit_research_request" in signals:
                return True, signals
            return False, signals

        # Check if this is simple factual knowledge
        if self._is_local_knowledge(query):
            signals.append("local_knowledge")
            if "explicit_research_request" in signals:
                return True, signals
            return False, signals

        # If any signal indicates need for fresh data
        if signals and not self._is_conceptual(query) and not self._is_local_knowledge(query):
            return True, signals

        # Default: no research for simple queries
        return False, signals

    def _has_explicit_research_signal(self, query: str) -> bool:
        """Check if user explicitly asked for research/verification."""
        for pattern in EXPLICIT_RESEARCH_SIGNALS:
            if re.search(pattern, query):
                return True
        return False

    def _detect_time_cue(self, query: str) -> Optional[str]:
        """Detect time-related words indicating need for current data."""
        for pattern in TIME_CUES:
            if re.search(pattern, query):
                return pattern.replace(r"\b", "").replace(r"\s+", " ")
        return None

    def _detect_volatility_domain(self, query: str) -> Optional[str]:
        """Detect domains where information becomes stale quickly."""
        for domain in VOLATILITY_DOMAINS:
            if domain in query:
                return domain
        return None

    def _is_conceptual(self, query: str) -> bool:
        """Check if this is a conceptual/definition question."""
        for pattern in CONCEPTUAL_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def _is_local_knowledge(self, query: str) -> bool:
        """Check if this is simple factual knowledge that should be local."""
        for pattern in LOCAL_KNOWLEDGE_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def get_research_params(
        self,
        query: str,
        signals: List[str],
    ) -> dict:
        """
        Determine research parameters based on query type and signals.

        Returns parameters optimized for the type of research needed.
        """
        params = {
            "top_k": 5,
            "search_depth": "basic",
            "recency_days": None,
        }

        # Time-sensitive queries get recent results
        if any("time_cue" in s for s in signals):
            params["recency_days"] = 7  # Last week

        # Volatility domains need very recent data
        if any("volatility_domain" in s for s in signals):
            params["recency_days"] = 3  # Last 3 days
            params["top_k"] = 10  # More sources

        # Explicit research might need deeper search
        if "explicit_research_request" in signals:
            params["search_depth"] = "advanced"
            params["top_k"] = 10

        # Financial queries need recent + more sources
        if any(word in query.lower() for word in ["price", "stock", "crypto", "market"]):
            params["recency_days"] = 1  # Last day
            params["top_k"] = 10

        return params

    def log_decision(
        self,
        query: str,
        should_research: bool,
        signals: List[str],
        params: Optional[dict] = None,
    ) -> dict:
        """
        Create a structured log of the routing decision.

        Returns a dict suitable for telemetry logging.
        """
        return {
            "router_decision": "research" if should_research else "local",
            "query": query,
            "signals": signals,
            "params": params or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def create_research_router(**kwargs) -> ResearchRouter:
    """Factory function to create a configured ResearchRouter."""
    return ResearchRouter(**kwargs)


# Singleton instance
_default_router: Optional[ResearchRouter] = None


def get_research_router() -> ResearchRouter:
    """Get the default research router instance."""
    global _default_router
    if _default_router is None:
        _default_router = ResearchRouter()
    return _default_router

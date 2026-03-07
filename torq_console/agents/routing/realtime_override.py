"""
Real-Time Routing Override Module

Provides deterministic pre-routing for queries that require web search
and real-time data retrieval. This runs BEFORE any agent selection or
LLM-based routing decisions.

Key principle: HARD-ROUTE, not soft-suggest. When a query matches these
patterns, we force RESEARCH mode and web search tools, bypassing normal
agent routing that might otherwise choose a fast conversational path.

Acceptance Tests (must work WITHOUT "search" keyword):
1. "What is Bitcoin price today?"
2. "What's the current S&P 500?"
3. "Latest AI news"
4. "What happened with Nvidia this week?"
5. "Who is the current CEO of OpenAI?"
6. "What's the current 10-year Treasury yield?"

From __future__ import annotations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RoutingOverride:
    """
    Represents a routing override decision.

    When force_research=True, the orchestrator MUST:
    - Set mode to RESEARCH
    - Force web search tool availability
    - Route to an agent with web search capabilities
    - NOT fall back to generic chat without search

    Attributes:
        force_research: Whether to force RESEARCH mode
        reason: Human-readable reason for the override
        mode: The execution mode to force (typically "RESEARCH")
        force_tools: List of tools that must be available
        matched_terms: List of terms that triggered this override
    """
    force_research: bool = False
    reason: Optional[str] = None
    mode: Optional[str] = None
    force_tools: List[str] = field(default_factory=list)
    matched_terms: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Truthiness check - True if this override is active."""
        return self.force_research


# ============================================================================
# Term Sets for Pattern Matching
# ============================================================================

FINANCE_TERMS = {
    # Crypto
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "blockchain", "defi", "nft", "altcoin", "coin", "token",
    "solana", "cardano", "dogecoin", "ripple", "xrp", "polkadot",

    # Stocks & Markets
    "stock", "stocks", "share", "shares", "equity", "equities",
    "market", "markets", "market cap", "index", "indices",
    "sp500", "s&p", "s&p 500", "nasdaq", "dow", "dow jones", "djia",
    "russell", "ftse", "dax", "nikkei", "hang seng",

    # Bonds & Yields
    "treasury", "treasuries", "bond", "bonds", "bond yield",
    "yield", "yields", "interest rate", "rates", "fed funds",
    "10-year", "2-year", "30-year", "ytm", "coupon",

    # Investment Vehicles
    "etf", "etfs", "mutual fund", "hedge fund", "reit",
    "option", "options", "future", "futures", "derivative",

    # Trading
    "trading", "trade", "portfolio", "dividend", "earnings",
    "ipo", "valuation", "price target", "analyst", "rating"
}

REALTIME_TERMS = {
    # Temporal - current moment
    "current", "currently", "right now",
    "today", "today's", "todays",

    # Recent past
    "latest", "recent", "recently", "just now",
    "this week", "this month", "this year",
    "past week", "past month", "past year",

    # Live/Active
    "live", "ongoing", "happening now",
    "breaking", "just in", "just announced",

    # Status seeking
    "what is", "what's", "whats", "how is", "how's",
    "status", "state of", "condition of"
}

NEWS_TERMS = {
    # News sources
    "news", "headline", "headlines", "press", "media",
    "article", "report", "breaking news", "breaking",

    # Events
    "announcement", "announced", "update", "updates",
    "release", "released", "happened", "occurring",
    "developments", "development", "story", "coverage",

    # Information seeking
    "what happened", "what's happening", "whats happening",
    "what's going on", "whats going on", "latest on",
    "reporting", "reported", "coverage"
}

LOOKUP_TERMS = {
    # Value/Price queries
    "price", "pricing", "quote", "value", "valued", "worth",
    "cost", "rate", "costing", "priced at",

    # Scoring/Ranking
    "score", "scores", "ranking", "ranked", "rating", "rated",
    "position", "standing", "tier", "grade",

    # People/Roles
    "who is", "who's", "whos", "who are", "ceo", "cto", "cfo",
    "president", "chairman", "founder", "director", "lead",
    "head of", "leader", "leadership", "management",

    # Schedules/Events
    "schedule", "scheduled", "timing", "when is", "date",
    "calendar", "upcoming", "next", "deadline",

    # Current state
    "weather", "temperature", "condition", "version",
    "current version", "latest version", "status of"
}


# ============================================================================
# Pattern Matching Helpers
# ============================================================================

def _hits(text: str, terms: set[str]) -> list[str]:
    """
    Find which terms from a set appear in the text.

    Args:
        text: The search text (lowercased)
        terms: Set of terms to search for

    Returns:
        List of matched terms in order of appearance in text
    """
    found = []
    for term in terms:
        if term in text:
            found.append(term)
    return found


def _has_realtime_finance_intent(text: str, finance_hits: list[str], realtime_hits: list[str]) -> bool:
    """
    Determine if query has real-time finance intent.

    Pattern: finance/crypto terms + temporal/lookup indicators

    Examples:
    - "What is Bitcoin price today?" → True (bitcoin + price + today)
    - "Current S&P 500" → True (s&p 500 + current)
    - "What is a blockchain?" → False (definition, not realtime)
    - "Bitcoin mining explained" → False (educational, not realtime)
    """
    if not finance_hits:
        return False

    # Definition patterns - these are educational, not real-time value queries
    # "What is a X", "Explain X", "How does X work"
    definition_patterns = {
        "what is a ", "what's a ", "whats a ",
        "explain ", "explained ", "explaining ",
        "how does ", "how do ",
        "define ", "definition ",
        "meaning of ", "what does ",
        "how to ", "tutorial ", "guide ",
    }

    # Check if this is a definition/educational query
    text_lower = text.lower()
    for pattern in definition_patterns:
        if pattern in text_lower:
            return False  # Educational, not real-time

    # Finance term + explicit temporal indicator
    if realtime_hits:
        return True

    # Finance term + lookup/value term (implying current state)
    # But only if the lookup is about price/value/rate
    value_lookups = {"price", "pricing", "value", "worth", "cost", "rate", "yield",
                     "quote", "trading at", "level", "index", "standing"}
    for lookup in value_lookups:
        if lookup in text_lower:
            return True

    return False


def _has_news_intent(text: str, news_hits: list[str], realtime_hits: list[str]) -> bool:
    """
    Determine if query has current news intent.

    Pattern: news terms + temporal indicators

    Examples:
    - "Latest AI news" → True (news + latest)
    - "What happened with Nvidia" → True (happened)
    - "News archives from 2020" → False (historical, not current)
    """
    if not news_hits:
        return False

    # News + temporal = current news seeking
    if realtime_hits:
        return True

    # "What happened" pattern implies seeking recent info
    if "what happened" in text or "what's happening" in text:
        return True

    return False


def _has_lookup_intent(text: str, lookup_hits: list[str], realtime_hits: list[str]) -> bool:
    """
    Determine if query has current lookup intent.

    Pattern: role/status/people terms + temporal indicators

    Examples:
    - "Who is the current CEO" → True (who is + current + ceo)
    - "Current weather" → True (current + weather)
    - "How to become a CEO" → False (instructional, not lookup)
    """
    if not lookup_hits:
        return False

    # Temporal + lookup role/people = current status lookup
    if realtime_hits:
        return True

    # "Who is/Who's" + role/person = current person lookup
    # This handles "Who is the CEO of OpenAI?"
    who_is_pattern = {"who is", "who's", "whos", "who are"}
    if any(pattern in text for pattern in who_is_pattern):
        # Also check it's not "how to" (instructional)
        if "how to" not in text and "how do" not in text:
            return True

    return False


# ============================================================================
# Main Detection Function
# ============================================================================

def detect_routing_override(message: str) -> RoutingOverride:
    """
    Detect if a message requires real-time routing override.

    This is a DETERMINISTIC pre-router that runs BEFORE:
    - Agent selection/routing
    - LLM-based intent classification
    - Mode selection

    When an override is detected, the orchestrator MUST:
    1. Force mode to RESEARCH
    2. Route to agent with web search
    3. Ensure web search tools are available
    4. Not fall back to generic chat

    Args:
        message: The user's query/message

    Returns:
        RoutingOverride with force_research=True if override needed

    Examples that trigger override:
        "What is Bitcoin price today?"
        "Current S&P 500 level"
        "Latest AI news"
        "What happened with Nvidia this week?"
        "Who is the CEO of OpenAI?"
        "What's the 10-year Treasury yield?"
    """
    text = (message or "").strip().lower()

    if not text or len(text) < 3:
        return RoutingOverride()

    # Find all matching terms
    finance_hits = _hits(text, FINANCE_TERMS)
    realtime_hits = _hits(text, REALTIME_TERMS)
    news_hits = _hits(text, NEWS_TERMS)
    lookup_hits = _hits(text, LOOKUP_TERMS)

    # Pattern 1: Real-time finance / crypto queries
    # "What is Bitcoin price today?", "Current S&P 500"
    if _has_realtime_finance_intent(text, finance_hits, realtime_hits):
        logger.info(
            f"Routing override: realtime_finance - "
            f"finance={finance_hits}, realtime={realtime_hits}"
        )
        return RoutingOverride(
            force_research=True,
            reason="realtime_finance",
            mode="RESEARCH",
            force_tools=["web_search"],
            matched_terms=finance_hits + realtime_hits + lookup_hits,
        )

    # Pattern 2: Current / latest news queries
    # "Latest AI news", "What happened with Nvidia"
    if _has_news_intent(text, news_hits, realtime_hits):
        logger.info(
            f"Routing override: current_news - "
            f"news={news_hits}, realtime={realtime_hits}"
        )
        return RoutingOverride(
            force_research=True,
            reason="current_news",
            mode="RESEARCH",
            force_tools=["web_search"],
            matched_terms=news_hits + realtime_hits,
        )

    # Pattern 3: Current office-holder / role / status lookups
    # "Who is the current CEO", "Current weather"
    if _has_lookup_intent(text, lookup_hits, realtime_hits):
        logger.info(
            f"Routing override: current_lookup - "
            f"lookup={lookup_hits}, realtime={realtime_hits}"
        )
        return RoutingOverride(
            force_research=True,
            reason="current_lookup",
            mode="RESEARCH",
            force_tools=["web_search"],
            matched_terms=lookup_hits + realtime_hits,
        )

    # Pattern 4: AI-specific latest queries
    # "Latest AI", "AI news", "What's new in AI"
    # NOTE: Use word boundary matching to avoid "ai" matching in "blockchain"
    import re
    ai_keywords = {"ai", "artificial intelligence", "machine learning", "llm", "gpt", "claude"}
    ai_hits = []
    for kw in ai_keywords:
        # Match whole words only with word boundaries
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text):
            ai_hits.append(kw)
    if ai_hits and (realtime_hits or news_hits):
        logger.info(
            f"Routing override: latest_ai - "
            f"ai={ai_hits}, realtime={realtime_hits}, news={news_hits}"
        )
        return RoutingOverride(
            force_research=True,
            reason="latest_ai",
            mode="RESEARCH",
            force_tools=["web_search"],
            matched_terms=ai_hits + realtime_hits + news_hits,
        )

    # No override - let normal routing proceed
    return RoutingOverride()


# ============================================================================
# Testing Helpers
# ============================================================================

def _test_override(messages: list[str]) -> dict[str, RoutingOverride]:
    """
    Test helper to check routing decisions for a list of messages.

    Args:
        messages: List of test messages

    Returns:
        Dict mapping message to its RoutingOverride result
    """
    results = {}
    for msg in messages:
        results[msg] = detect_routing_override(msg)
    return results


if __name__ == "__main__":
    # Simple test runner
    import sys

    # Ensure UTF-8 output for Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    test_messages = [
        "What is Bitcoin price today?",
        "Current S&P 500",
        "Latest AI news",
        "What happened with Nvidia this week?",
        "Who is the CEO of OpenAI?",
        "What's the 10-year Treasury yield?",
        "Hello, how are you?",
        "Explain recursion in Python",
        "Write a function to sort arrays",
    ]

    print("Routing Override Test Results:")
    print("=" * 60)
    for msg in test_messages:
        override = detect_routing_override(msg)
        status = "[OVERRIDE]" if override.force_research else "[normal]  "
        print(f"{status}: {msg}")
        if override.force_research:
            print(f"         -> reason={override.reason}, terms={override.matched_terms}")

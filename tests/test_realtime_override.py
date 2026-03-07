"""
Unit tests for realtime routing override module.

Tests the deterministic pre-router that forces RESEARCH mode
for real-time queries (finance, news, lookups).

Acceptance Tests - these queries MUST trigger override:
1. "What is Bitcoin price today?"
2. "What's the current S&P 500?"
3. "Latest AI news"
4. "What happened with Nvidia this week?"
5. "Who is the current CEO of OpenAI?"
6. "What's the current 10-year Treasury yield?"
"""

import pytest
from torq_console.agents.routing.realtime_override import (
    detect_routing_override,
    RoutingOverride,
    FINANCE_TERMS,
    REALTIME_TERMS,
    NEWS_TERMS,
    LOOKUP_TERMS,
)


class TestRoutingOverride:
    """Test routing override detection."""

    # ========================================================================
    # Acceptance Tests - MUST PASS
    # ========================================================================

    def test_acceptance_bitcoin_price_today(self):
        """Acceptance test 1: Bitcoin price today forces research."""
        override = detect_routing_override("What is Bitcoin price today?")
        assert override.force_research is True
        assert override.reason == "realtime_finance"
        assert "bitcoin" in str(override.matched_terms).lower()
        assert "today" in str(override.matched_terms).lower()
        assert "web_search" in override.force_tools

    def test_acceptance_current_sp500(self):
        """Acceptance test 2: Current S&P 500 forces research."""
        override = detect_routing_override("What's the current S&P 500?")
        assert override.force_research is True
        assert override.reason == "realtime_finance"
        assert any("s&p" in str(t).lower() for t in override.matched_terms)
        assert "web_search" in override.force_tools

    def test_acceptance_latest_ai_news(self):
        """Acceptance test 3: Latest AI news forces research."""
        override = detect_routing_override("Latest AI news")
        assert override.force_research is True
        assert override.reason in ("current_news", "latest_ai")
        assert "news" in str(override.matched_terms).lower()
        assert "web_search" in override.force_tools

    def test_acceptance_nvidia_this_week(self):
        """Acceptance test 4: What happened with Nvidia this week."""
        override = detect_routing_override("What happened with Nvidia this week?")
        assert override.force_research is True
        assert override.reason == "current_news"
        assert "web_search" in override.force_tools

    def test_acceptance_ceo_openai(self):
        """Acceptance test 5: Who is the CEO of OpenAI."""
        override = detect_routing_override("Who is the CEO of OpenAI?")
        assert override.force_research is True
        assert override.reason == "current_lookup"
        assert "ceo" in str(override.matched_terms).lower()
        assert "web_search" in override.force_tools

    def test_acceptance_treasury_yield(self):
        """Acceptance test 6: Current 10-year Treasury yield."""
        override = detect_routing_override("What's the current 10-year Treasury yield?")
        assert override.force_research is True
        assert override.reason == "realtime_finance"
        assert "treasury" in str(override.matched_terms).lower()
        assert "yield" in str(override.matched_terms).lower()
        assert "web_search" in override.force_tools

    # ========================================================================
    # Real-time Finance/Crypto Tests
    # ========================================================================

    def test_bitcoin_price(self):
        """Bitcoin price query forces research."""
        override = detect_routing_override("What is the price of Bitcoin?")
        assert override.force_research is True
        assert override.reason == "realtime_finance"

    def test_ethereum_current_price(self):
        """Ethereum current price query forces research."""
        override = detect_routing_override("Current Ethereum price")
        assert override.force_research is True
        assert override.reason == "realtime_finance"

    def test_stock_market_today(self):
        """Stock market today query forces research."""
        override = detect_routing_override("How is the stock market today?")
        assert override.force_research is True
        assert override.reason == "realtime_finance"

    def test_crypto_trading(self):
        """Crypto trading without realtime indicators does NOT force research."""
        override = detect_routing_override("How does cryptocurrency trading work?")
        # Should NOT override - this is educational, not real-time
        assert override.force_research is False

    # ========================================================================
    # News Tests
    # ========================================================================

    def test_latest_news(self):
        """Latest news query forces research."""
        override = detect_routing_override("What's the latest news?")
        assert override.force_research is True
        assert override.reason == "current_news"

    def test_breaking_news(self):
        """Breaking news query forces research."""
        override = detect_routing_override("Any breaking news?")
        assert override.force_research is True
        assert override.reason == "current_news"

    def test_tech_news_this_week(self):
        """Tech news this week forces research."""
        override = detect_routing_override("What are the tech news stories this week?")
        assert override.force_research is True
        assert override.reason == "current_news"

    # ========================================================================
    # Lookup Tests
    # ========================================================================

    def test_current_weather(self):
        """Current weather query forces research."""
        override = detect_routing_override("What's the current weather?")
        assert override.force_research is True
        assert override.reason == "current_lookup"

    def test_who_is_president(self):
        """Who is president query forces research."""
        override = detect_routing_override("Who is the president of the United States?")
        assert override.force_research is True
        assert override.reason == "current_lookup"

    def test_current_version(self):
        """Current version query forces research."""
        override = detect_routing_override("What's the current version of Python?")
        assert override.force_research is True
        assert override.reason == "current_lookup"

    # ========================================================================
    # Negative Tests - Should NOT Override
    # ========================================================================

    def test_smalltalk_no_override(self):
        """Smalltalk does NOT force research."""
        override = detect_routing_override("Hello, how are you?")
        assert override.force_research is False

    def test_code_help_no_override(self):
        """Code help does NOT force research."""
        override = detect_routing_override("Explain recursion in Python")
        assert override.force_research is False

    def test_how_to_no_override(self):
        """How-to questions do NOT force research (instructional)."""
        override = detect_routing_override("How do I become a CEO?")
        assert override.force_research is False

    def test_definition_no_override(self):
        """Definition questions do NOT force research."""
        override = detect_routing_override("What is a blockchain?")
        assert override.force_research is False

    def test_historical_no_override(self):
        """Historical questions do NOT force research."""
        override = detect_routing_override("What was the stock market in 2020?")
        assert override.force_research is False

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_message(self):
        """Empty message does NOT override."""
        override = detect_routing_override("")
        assert override.force_research is False

    def test_short_message(self):
        """Very short message does NOT override."""
        override = detect_routing_override("Hi")
        assert override.force_research is False

    def test_case_insensitive(self):
        """Detection is case-insensitive."""
        override1 = detect_routing_override("BITCOIN PRICE TODAY")
        override2 = detect_routing_override("bitcoin price today")
        override3 = detect_routing_override("Bitcoin Price Today")
        assert all(o.force_research for o in [override1, override2, override3])

    def test_truthiness(self):
        """RoutingOverride is truthy when force_research=True."""
        override_active = detect_routing_override("Bitcoin price today")
        override_inactive = detect_routing_override("Hello")

        assert bool(override_active) is True
        assert bool(override_inactive) is False


class TestTermSets:
    """Test that term sets contain expected terms."""

    def test_finance_terms(self):
        """Finance terms include expected crypto and stock terms."""
        assert "bitcoin" in FINANCE_TERMS
        assert "ethereum" in FINANCE_TERMS
        assert "stock" in FINANCE_TERMS
        assert "treasury" in FINANCE_TERMS
        assert "yield" in FINANCE_TERMS

    def test_realtime_terms(self):
        """Realtime terms include temporal indicators."""
        assert "current" in REALTIME_TERMS
        assert "today" in REALTIME_TERMS
        assert "latest" in REALTIME_TERMS
        assert "recent" in REALTIME_TERMS

    def test_news_terms(self):
        """News terms include news-related keywords."""
        assert "news" in NEWS_TERMS
        assert "headline" in NEWS_TERMS
        assert "breaking" in NEWS_TERMS or "breaking news" in NEWS_TERMS

    def test_lookup_terms(self):
        """Lookup terms include role and status keywords."""
        assert "ceo" in LOOKUP_TERMS
        assert "price" in LOOKUP_TERMS
        assert "who is" in LOOKUP_TERMS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

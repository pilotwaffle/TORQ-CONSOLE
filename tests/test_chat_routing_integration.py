"""
Integration tests for chat API routing.

Tests that routing override works end-to-end through the
UnifiedOrchestrator and appears correctly in API responses.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from torq_console.agents.railway_orchestration_v2 import (
    UnifiedOrchestrator,
    UnifiedChatRequest,
    ExecutionMode,
)
from torq_console.agents.routing.realtime_override import detect_routing_override


class TestChatRoutingIntegration:
    """Test that routing override integrates with the chat API."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator with mocked dependencies."""
        with patch('torq_console.agents.railway_orchestration_v2.SUPABASE_AVAILABLE', False):
            orchestrator = UnifiedOrchestrator(session_store=None)
            return orchestrator

    @pytest.mark.asyncio
    async def test_bitcoin_price_routing_in_response(self, orchestrator):
        """Bitcoin price query should show routing override in response."""
        # Mock the _execute_single to avoid actual agent call
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "Bitcoin is currently $X",
        })

        request = UnifiedChatRequest(
            message="What is Bitcoin price today?",
            session_id="test-session"
        )

        response = await orchestrator.chat(request)

        # Verify routing override is reflected in response
        assert response.routing is not None
        assert response.routing.get("override_active") is True
        assert response.routing.get("override_reason") == "realtime_finance"
        assert "bitcoin" in str(response.routing.get("override_matched_terms", [])).lower()

        # Verify mode was forced to RESEARCH
        assert response.mode_used == ExecutionMode.RESEARCH

    @pytest.mark.asyncio
    async def test_latest_news_routing_in_response(self, orchestrator):
        """Latest news query should show routing override in response."""
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "Here are the latest news...",
        })

        request = UnifiedChatRequest(
            message="Latest AI news",
            session_id="test-session"
        )

        response = await orchestrator.chat(request)

        assert response.routing.get("override_active") is True
        assert response.routing.get("override_reason") in ("current_news", "latest_ai")
        assert response.mode_used == ExecutionMode.RESEARCH

    @pytest.mark.asyncio
    async def test_normal_chat_no_routing_override(self, orchestrator):
        """Normal chat should NOT show routing override."""
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "Hello! How can I help you?",
        })

        request = UnifiedChatRequest(
            message="Hello, how are you?",
            session_id="test-session"
        )

        response = await orchestrator.chat(request)

        # Should NOT have routing override
        assert response.routing.get("override_active") is False
        # Mode should be SINGLE (not RESEARCH)
        assert response.mode_used == ExecutionMode.SINGLE

    @pytest.mark.asyncio
    async def test_explicit_agent_with_routing_override(self, orchestrator):
        """Explicit agent selection still respects routing override for mode."""
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "Current S&P 500 is X",
        })

        request = UnifiedChatRequest(
            message="What's the current S&P 500?",
            session_id="test-session",
            agent_id="torq_prince_flowers"  # Explicit agent
        )

        response = await orchestrator.chat(request)

        # Routing override should still be active
        assert response.routing.get("override_active") is True
        assert response.mode_used == ExecutionMode.RESEARCH
        # But agent_id_used should be the explicit one
        assert response.agent_id_used == "torq_prince_flowers"

    @pytest.mark.asyncio
    async def test_routing_metadata_preserved(self, orchestrator):
        """Routing metadata should include all override information."""
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "The CEO is X",
        })

        request = UnifiedChatRequest(
            message="Who is the current CEO of OpenAI?",
            session_id="test-session"
        )

        response = await orchestrator.chat(request)

        # Check all expected metadata fields
        assert response.metadata is not None
        assert response.metadata.get("routing_override") is True
        assert response.metadata.get("task_id") is not None

        # Check routing details
        routing = response.routing
        assert routing.get("override_active") is True
        assert routing.get("override_reason") == "current_lookup"
        assert "ceo" in str(routing.get("override_matched_terms", [])).lower()
        assert routing.get("reasoning") == "Routing override: current_lookup"

    @pytest.mark.asyncio
    async def test_web_search_tool_in_forced_tools(self, orchestrator):
        """Routing override should include web_search in forced tools."""
        orchestrator._execute_single = AsyncMock(return_value={
            "response": "Treasury yield is X%",
        })

        request = UnifiedChatRequest(
            message="What's the current 10-year Treasury yield?",
            session_id="test-session"
        )

        response = await orchestrator.chat(request)

        # The routing override context should have been passed
        # The mock may have been called multiple times while finding the right agent
        assert orchestrator._execute_single.call_count >= 1

        # Get the last call (the actual execution)
        call_args_list = orchestrator._execute_single.call_args_list
        last_call_args = call_args_list[-1]
        context = last_call_args[0][2]  # Third argument is the enhanced_context

        assert context.get("routing_override") is not None
        assert "web_search" in context["routing_override"].get("force_tools", [])


class TestRoutingOverrideDetector:
    """Direct tests of the routing override detector."""

    def test_all_acceptance_tests_trigger_override(self):
        """All 6 acceptance test queries should trigger override."""
        acceptance_queries = [
            "What is Bitcoin price today?",
            "What's the current S&P 500?",
            "Latest AI news",
            "What happened with Nvidia this week?",
            "Who is the current CEO of OpenAI?",
            "What's the current 10-year Treasury yield?",
        ]

        for query in acceptance_queries:
            override = detect_routing_override(query)
            assert override.force_research is True, f"Query should trigger override: {query}"
            assert "web_search" in override.force_tools, f"Query should force web_search: {query}"

    def test_normal_queries_do_not_trigger_override(self):
        """Normal conversational queries should NOT trigger override."""
        normal_queries = [
            "Hello, how are you?",
            "Explain recursion in Python",
            "Write a function to sort arrays",
            "What is a blockchain?",  # Definition, not current value
            "How do I become a CEO?",  # How-to, not current lookup
        ]

        for query in normal_queries:
            override = detect_routing_override(query)
            assert override.force_research is False, f"Query should NOT trigger override: {query}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

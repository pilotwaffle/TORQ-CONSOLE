"""
Test Suite for Prince Flowers Enhanced Integration

Validates the enhanced query routing and workflow execution
with comprehensive test cases covering search vs code generation.
"""

import asyncio
import pytest
from torq_console.agents.prince_flowers_enhanced_integration import (
    create_prince_flowers_enhanced,
    EnhancedAgentResult
)

class TestPrinceFlowersEnhancedIntegration:
    """Comprehensive test suite for enhanced Prince Flowers integration."""

    @pytest.fixture
    async def agent(self):
        """Create enhanced agent instance."""
        return create_prince_flowers_enhanced(llm_provider=None)

    @pytest.mark.asyncio
    async def test_explicit_code_request_routing(self):
        """Test that explicit code requests route to CODE_GENERATION."""
        agent = create_prince_flowers_enhanced()

        test_queries = [
            "write code for user authentication",
            "generate code using Perplexity API",
            "create code for search application",
            "implement code for database connection",
            "write a script to process data"
        ]

        for query in test_queries:
            routing = await agent.route_query(query)
            assert routing['intent'] == 'CODE_GENERATION', \
                f"Query '{query}' should route to CODE_GENERATION, got {routing['intent']}"
            assert routing['confidence'] >= 0.9, \
                f"Explicit code request should have high confidence, got {routing['confidence']}"

    @pytest.mark.asyncio
    async def test_search_query_routing(self):
        """Test that search queries route to WEB_SEARCH."""
        agent = create_prince_flowers_enhanced()

        test_queries = [
            "search prince celebration 2026",
            "find information about AI",
            "lookup recent developments",
            "research quantum computing",
            "what is machine learning"
        ]

        for query in test_queries:
            routing = await agent.route_query(query)
            assert routing['intent'] == 'WEB_SEARCH', \
                f"Query '{query}' should route to WEB_SEARCH, got {routing['intent']}"
            assert routing['confidence'] >= 0.7, \
                f"Search query should have good confidence, got {routing['confidence']}"

    @pytest.mark.asyncio
    async def test_tool_based_search_routing(self):
        """Test that tool-based search patterns route to WEB_SEARCH, NOT CODE_GENERATION."""
        agent = create_prince_flowers_enhanced()

        test_queries = [
            "use perplexity to search prince celebration 2026",
            "use google to find recent news",
            "with duckduckgo search AI developments",
            "via bing lookup historical events",
            "through google research quantum physics"
        ]

        for query in test_queries:
            routing = await agent.route_query(query)
            assert routing['intent'] == 'WEB_SEARCH', \
                f"Query '{query}' should route to WEB_SEARCH (not code gen), got {routing['intent']}"
            assert routing['confidence'] >= 0.85, \
                f"Tool-based search should have high confidence, got {routing['confidence']}"
            assert 'Tool-based search pattern' in routing['reasoning'], \
                f"Should detect tool-based search pattern in reasoning"

    @pytest.mark.asyncio
    async def test_research_query_routing(self):
        """Test that research queries route appropriately."""
        agent = create_prince_flowers_enhanced()

        test_queries = [
            "tell me about quantum computing",
            "information about machine learning",
            "how to implement neural networks",
            "where is the best documentation",
            "when did AI development start"
        ]

        for query in test_queries:
            routing = await agent.route_query(query)
            assert routing['intent'] in ['WEB_SEARCH', 'RESEARCH'], \
                f"Query '{query}' should route to search/research, got {routing['intent']}"

    @pytest.mark.asyncio
    async def test_edge_case_code_with_search_mention(self):
        """Test edge case: code request mentioning search."""
        agent = create_prince_flowers_enhanced()

        # These should be CODE_GENERATION because they start with explicit code request
        code_queries = [
            "write code to search a database",
            "generate code for search functionality",
            "create code for find operation"
        ]

        for query in code_queries:
            routing = await agent.route_query(query)
            assert routing['intent'] == 'CODE_GENERATION', \
                f"Query '{query}' starts with code request, should be CODE_GENERATION, got {routing['intent']}"

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that routing follows correct priority order."""
        agent = create_prince_flowers_enhanced()

        # Priority 1: Explicit code request (highest)
        routing1 = await agent.route_query("write code to search something")
        assert routing1['intent'] == 'CODE_GENERATION'
        assert routing1['confidence'] >= 0.9

        # Priority 2: Tool-based search
        routing2 = await agent.route_query("use perplexity to search prince celebration")
        assert routing2['intent'] == 'WEB_SEARCH'
        assert routing2['confidence'] >= 0.85

        # Priority 3: General search
        routing3 = await agent.route_query("search for information")
        assert routing3['intent'] == 'WEB_SEARCH'
        assert routing3['confidence'] >= 0.7

        # Priority 4: Default research
        routing4 = await agent.route_query("tell me something interesting")
        assert routing4['intent'] in ['RESEARCH', 'WEB_SEARCH']

    @pytest.mark.asyncio
    async def test_enhanced_status(self):
        """Test enhanced status reporting."""
        agent = create_prince_flowers_enhanced()

        status = agent.get_enhanced_status()

        assert 'agent_name' in status
        assert status['agent_name'] == 'Prince Flowers Enhanced'
        assert 'planning' in status
        assert 'tools' in status
        assert 'memory' in status
        assert 'learning' in status

        assert status['tools']['total_tools'] > 20
        assert status['planning']['strategies_available'] >= 10

    @pytest.mark.asyncio
    async def test_full_workflow_web_search(self):
        """Test complete web search workflow execution."""
        agent = create_prince_flowers_enhanced()

        query = "search for latest AI developments"
        result = await agent.process_query_enhanced(query)

        assert isinstance(result, EnhancedAgentResult)
        assert result.workflow_type in ['WEB_SEARCH', 'RESEARCH']
        assert result.execution_time > 0
        assert len(result.tools_used) > 0

    @pytest.mark.asyncio
    async def test_learning_experience_storage(self):
        """Test that routing experiences are stored for learning."""
        agent = create_prince_flowers_enhanced()

        # Execute a query
        query = "search prince celebration 2026"
        await agent.process_query_enhanced(query)

        # Verify experience was stored
        assert len(agent.learning['experience_buffer']) > 0
        assert len(agent.learning['query_routing_patterns']) > 0

        # Verify WEB_SEARCH pattern was recorded
        assert 'WEB_SEARCH' in agent.learning['query_routing_patterns']

def run_manual_tests():
    """Run manual tests for quick validation."""
    print("="*80)
    print("Prince Flowers Enhanced Integration - Manual Test Suite")
    print("="*80)

    async def run_tests():
        agent = create_prince_flowers_enhanced()

        print("\n1. Testing Query Routing...")
        print("-"*80)

        test_cases = [
            ("search prince celebration 2026", "WEB_SEARCH"),
            ("use perplexity to search AI", "WEB_SEARCH"),
            ("write code for authentication", "CODE_GENERATION"),
            ("generate code using Perplexity API", "CODE_GENERATION"),
            ("find information about quantum computing", "WEB_SEARCH"),
            ("research machine learning trends", "WEB_SEARCH"),
        ]

        for query, expected_intent in test_cases:
            routing = await agent.route_query(query)
            status = "✓ PASS" if routing['intent'] == expected_intent else "✗ FAIL"
            print(f"{status} | Query: '{query[:50]}'")
            print(f"       | Expected: {expected_intent}, Got: {routing['intent']}")
            print(f"       | Confidence: {routing['confidence']:.2f}")
            print(f"       | Reasoning: {routing['reasoning']}")
            print()

        print("\n2. Testing Enhanced Status...")
        print("-"*80)
        status = agent.get_enhanced_status()
        print(f"Agent: {status['agent_name']}")
        print(f"Total Tools: {status['tools']['total_tools']}")
        print(f"Planning Strategies: {status['planning']['strategies_available']}")
        print(f"Interactions: {status['total_interactions']}")
        print(f"Success Rate: {status['success_rate']:.2%}")

        print("\n3. Testing Full Workflow...")
        print("-"*80)
        result = await agent.process_query_enhanced("search for AI news")
        print(f"Success: {result.success}")
        print(f"Workflow Type: {result.workflow_type}")
        print(f"Tools Used: {result.tools_used}")
        print(f"Execution Time: {result.execution_time:.3f}s")
        print(f"Confidence: {result.confidence:.2f}")

        print("\n" + "="*80)
        print("Test Suite Complete!")
        print("="*80)

    asyncio.run(run_tests())

if __name__ == "__main__":
    print("Running manual test suite...")
    run_manual_tests()

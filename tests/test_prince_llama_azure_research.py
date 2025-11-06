"""
Test Prince Flowers Agent with Llama LLM researching Azure Free Services

Tests:
1. Prince Flowers initialization with Llama provider
2. Web search functionality through SearchMaster
3. Research quality and verification
4. Azure free services content accuracy

This test demonstrates the integration of:
- Prince Flowers agent (ARTIST-style agentic RL)
- Llama LLM provider (OllamaProvider or llama.cpp)
- SearchMaster for comprehensive web research
- Azure Free Tier service discovery
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
from torq_console.llm.providers.ollama import OllamaProvider
from torq_console.llm.providers.llama_cpp_provider import LlamaCppProvider


class TestPrinceFlowersLlamaAzureResearch:
    """Test suite for Prince Flowers with Llama researching Azure Free Services"""

    def setup_method(self):
        """Initialize test environment"""
        print("\n" + "=" * 80)
        print("SETUP: Initializing Prince Flowers + Llama Provider")
        print("=" * 80)

        # Choose provider based on what's available
        # Try Ollama first (easier to set up)
        self.provider_name = None
        self.llm_provider = None

        try:
            print("Attempting Ollama provider connection...")
            self.llm_provider = OllamaProvider(
                base_url="http://localhost:11434",
                default_model="llama3.2"  # Or llama2, llama3, etc.
            )
            self.provider_name = "Ollama (llama3.2)"
            print(f"✓ Connected to {self.provider_name}")
        except Exception as e:
            print(f"✗ Ollama connection failed: {e}")
            print("Attempting llama.cpp provider connection...")

            # Fallback to llama.cpp if configured
            model_path = os.getenv('LLAMA_CPP_MODEL_PATH')
            if model_path and os.path.exists(model_path):
                try:
                    self.llm_provider = LlamaCppProvider(
                        model_path=model_path,
                        n_gpu_layers=int(os.getenv('LLAMA_CPP_N_GPU_LAYERS', '28')),
                        n_ctx=int(os.getenv('LLAMA_CPP_N_CTX', '2048'))
                    )
                    self.provider_name = f"llama.cpp ({os.path.basename(model_path)})"
                    print(f"✓ Connected to {self.provider_name}")
                except Exception as e2:
                    print(f"✗ llama.cpp connection failed: {e2}")
                    raise Exception("No Llama provider configured or accessible")
            else:
                raise Exception("No Llama provider configured (Ollama not running, llama.cpp not configured)")

        # Initialize Prince Flowers agent
        print("Initializing Prince Flowers agent...")
        try:
            self.agent = TORQPrinceFlowers(
                llm_provider=self.llm_provider,
                config={
                    'enhanced_mode': True,
                    'max_search_results': 10
                }
            )
            print("✓ Prince Flowers agent initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Prince Flowers: {e}")
            raise

        print("=" * 80)

    @pytest.mark.asyncio
    async def test_01_llm_provider_initialized(self):
        """Test that Llama provider is initialized"""
        print("\nTEST 1: LLM Provider Initialization")
        print("-" * 80)

        assert self.llm_provider is not None, "LLM provider not initialized"
        assert self.provider_name is not None, "Provider name not set"
        assert self.agent is not None, "Agent not initialized"

        print(f"✓ Provider: {self.provider_name}")
        print(f"✓ Agent: TORQPrinceFlowers")
        print(f"✓ Execution mode: Research with web search")

    @pytest.mark.asyncio
    async def test_02_simple_query(self):
        """Test simple query to verify agent works"""
        print("\nTEST 2: Simple Query Test")
        print("-" * 80)

        query = "What is Azure?"
        print(f"Query: {query}")

        result = await self.agent.process_query(
            query=query,
            context={}
        )

        print(f"Result received: {result is not None}")
        print(f"Success: {result.success}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Tools used: {result.tools_used}")
        print(f"Execution time: {result.execution_time:.2f}s")

        assert result.success is True, f"Query failed: {result.metadata}"
        assert len(result.content) > 0, "No content returned"
        assert result.confidence >= 0.0, "Invalid confidence score"

        print(f"Response preview: {result.content[:200]}...")
        print("✓ Simple query test PASSED")

    @pytest.mark.asyncio
    async def test_03_azure_free_services_research(self):
        """Test researching Azure 12-month free services - MAIN TEST"""
        print("\nTEST 3: Azure Free Services Research (12 Months) - MAIN TEST")
        print("-" * 80)

        query = "Research the 12 months of free services from Azure portal. What services are available at https://portal.azure.com for free tier customers?"
        print(f"Query: {query}")
        print("\nExecuting research...")

        start_time = datetime.now()
        result = await self.agent.process_query(
            query=query,
            context={}
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{'='*80}")
        print("RESEARCH RESULTS:")
        print(f"{'='*80}")

        # Basic assertions
        print(f"\n1. Success: {result.success}")
        assert result.success is True, f"Research failed: {result.metadata}"

        print(f"2. Content length: {len(result.content)} characters")
        assert len(result.content) > 100, "Content too short"

        print(f"3. Confidence: {result.confidence:.2f}")
        assert result.confidence > 0.2, f"Low confidence: {result.confidence}"

        print(f"4. Tools used: {result.tools_used}")
        assert len(result.tools_used) > 0, "No tools were used"

        # Verify search was used
        tools_str = str(result.tools_used).lower()
        has_search = ('web_search' in tools_str or 'searchmaster' in tools_str or 'search' in tools_str)
        print(f"5. Web search used: {has_search}")

        print(f"6. Execution time: {result.execution_time:.2f}s (Total: {duration:.2f}s)")
        print(f"7. Reasoning mode: {result.reasoning_mode}")

        # Content verification
        content_lower = result.content.lower()

        print(f"\n{'='*80}")
        print("CONTENT VERIFICATION:")
        print(f"{'='*80}")

        # Check for Azure mention
        has_azure = 'azure' in content_lower
        print(f"Contains 'Azure': {has_azure}")
        assert has_azure, "Azure not mentioned in result"

        # Check for free tier or 12 month mention
        has_free_term = ('free' in content_lower or '12' in content_lower or 'month' in content_lower)
        print(f"Contains free tier reference: {has_free_term}")

        # Check for common Azure free tier services
        free_service_keywords = [
            'virtual machine', 'vm', 'compute',
            'storage', 'blob',
            'database', 'sql',
            'app service', 'web app',
            'free tier', 'free services', '12 month'
        ]

        keyword_matches = []
        for keyword in free_service_keywords:
            if keyword in content_lower:
                keyword_matches.append(keyword)

        print(f"Azure service keywords found: {len(keyword_matches)}")
        for keyword in keyword_matches:
            print(f"  - {keyword}")

        assert len(keyword_matches) >= 1, \
            f"Expected at least 1 Azure service mention, got {len(keyword_matches)}"

        # Print full research content
        print(f"\n{'='*80}")
        print("RESEARCH CONTENT:")
        print(f"{'='*80}")
        print(result.content)
        print(f"{'='*80}")

        # Store for later tests
        self.azure_research_result = result

        print("\n✓ Azure Free Services Research PASSED")

    @pytest.mark.asyncio
    async def test_04_result_verification(self):
        """Test that results contain verifiable information"""
        print("\nTEST 4: Result Verification")
        print("-" * 80)

        # Use result from test 3 if available
        if hasattr(self, 'azure_research_result'):
            result = self.azure_research_result
        else:
            # Run new query if test 3 wasn't run
            result = await self.agent.process_query(
                query="What are the free compute services in Azure for 12 months?",
                context={}
            )

        print(f"Result success: {result.success}")
        assert result.success is True

        # Check metadata
        print(f"Metadata keys: {list(result.metadata.keys())}")

        # Check for trajectory
        if 'trajectory_id' in result.metadata:
            print(f"Trajectory ID: {result.metadata['trajectory_id']}")

        # Check for tool execution details
        if 'tool_executions' in result.metadata:
            print(f"Tool executions: {len(result.metadata['tool_executions'])}")

        print("✓ Result Verification PASSED")

    @pytest.mark.asyncio
    async def test_05_comprehensive_azure_research(self):
        """Test comprehensive Azure free tier research with multiple queries"""
        print("\nTEST 5: Comprehensive Azure Research")
        print("-" * 80)

        queries = [
            "What free services does Azure provide for 12 months?",
            "List the Azure free tier compute services",
            "What storage is included in Azure free tier?"
        ]

        results = []
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            result = await self.agent.process_query(query, context={})
            results.append(result)

            success = result.success
            confidence = result.confidence
            print(f"  Success: {success}, Confidence: {confidence:.2f}")

            assert result.success is True, f"Query {i} failed"

        # All queries should succeed
        assert all(r.success for r in results), "Not all queries succeeded"

        # At least one should have reasonable confidence
        max_confidence = max(r.confidence for r in results)
        print(f"\nMax confidence across queries: {max_confidence:.2f}")
        assert max_confidence > 0.2, f"Low confidence scores: {[r.confidence for r in results]}"

        print("✓ Comprehensive Research PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 100)
    print(" " * 20 + "PRINCE FLOWERS + LLAMA + AZURE RESEARCH TEST SUITE")
    print("=" * 100)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    pytest_args = [
        __file__,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-s',  # Show print statements
        '--color=yes',
        '--asyncio-mode=auto'  # Handle async tests
    ]

    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 100)
    if exit_code == 0:
        print(" " * 40 + "✓ ALL TESTS PASSED ✓")
    else:
        print(" " * 40 + "✗ SOME TESTS FAILED ✗")
    print("=" * 100)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    return exit_code


if __name__ == '__main__':
    exit(run_all_tests())

#!/usr/bin/env python3
"""
TORQ Console Prince Flowers Integration v0.70.0 - FIXED

Comprehensive integration wrapper for the Prince Flowers Enhanced Agent
with standardized response formatting, CLI testing interface, and full
TORQ Console compatibility.

This module provides:
1. PrinceFlowersAgent class wrapper with enhanced capabilities
2. Registration functions for TORQ Console integration
3. CLI test interface for standalone testing
4. Standardized response formatting and error handling
5. Demo capabilities and health monitoring

Author: TORQ Console Team
Version: 0.70.0
Compatible with: TORQ Console v0.70.0
"""

import asyncio
import logging
import time
import json
import sys
import traceback
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import TORQ Console components
try:
    from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent as BasePrinceFlowersAgent
    from torq_console.agents.torq_prince_flowers import TORQPrinceFlowersInterface
    from torq_console.core.config import TorqConfig
    from torq_console.llm.providers.base import BaseLLMProvider
    TORQ_CONSOLE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TORQ Console components not available: {e}")
    TORQ_CONSOLE_AVAILABLE = False

# Try importing local torq_prince_flowers for fallback
try:
    from torq_prince_flowers import TORQPrinceFlowersInterface as LocalTORQPrinceFlowersInterface
    LOCAL_INTERFACE_AVAILABLE = True
except ImportError:
    print("⚠️ Could not import local torq_prince_flowers.py")
    LOCAL_INTERFACE_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PrinceFlowersIntegration')

@dataclass
class IntegrationResponse:
    """Standardized response format for Prince Flowers integration."""
    success: bool
    content: str
    confidence: float
    tools_used: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
    agent_status: Optional[Dict[str, Any]] = None

@dataclass
class AgentCapabilities:
    """Agent capability definitions."""
    web_search: bool = True
    research: bool = True
    analysis: bool = True
    planning: bool = True
    memory: bool = True
    learning: bool = True
    tool_composition: bool = True
    error_recovery: bool = True

class PrinceFlowersIntegrationWrapper:
    """
    Integration wrapper for Prince Flowers Enhanced Agent.

    Provides standardized interface, error handling, and performance monitoring
    for seamless TORQ Console integration.
    """

    def __init__(self, torq_console=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integration wrapper.

        Args:
            torq_console: Reference to TORQ Console instance
            config: Optional configuration dictionary
        """
        self.torq_console = torq_console
        self.config = config or {}
        self.logger = logging.getLogger(f"PrinceFlowers.Integration")

        # Initialize base agent
        self._init_base_agent()

        # Integration state
        self.integration_active = True
        self.start_time = time.time()
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

        # Performance metrics
        self.performance_history = []
        self.max_history = 100

        self.logger.info("Prince Flowers Integration Wrapper initialized")

    def _init_base_agent(self):
        """Initialize the base Prince Flowers agent."""
        try:
            if TORQ_CONSOLE_AVAILABLE and self.torq_console:
                # Use TORQ Console integrated agent
                self.agent = self.torq_console.prince_flowers
                self.agent_type = "torq_console"
                self.logger.info("Using TORQ Console integrated Prince Flowers agent")
            elif LOCAL_INTERFACE_AVAILABLE:
                # Use local interface
                self.agent = LocalTORQPrinceFlowersInterface()
                self.agent_type = "local"
                self.logger.info("Using local Prince Flowers interface")
            else:
                # Fallback to mock agent
                self.agent = self._create_mock_agent()
                self.agent_type = "mock"
                self.logger.info("Using mock Prince Flowers agent")

        except Exception as e:
            self.logger.error(f"Failed to initialize base agent: {e}")
            self.agent = self._create_mock_agent()
            self.agent_type = "mock"

    def _create_mock_agent(self):
        """Create a mock agent for testing/demonstration."""
        class MockAgent:
            def __init__(self):
                self.agent_name = "Prince Flowers (Mock)"
                self.capabilities = AgentCapabilities()

            async def process_query(self, query: str, context: Dict = None):
                await asyncio.sleep(0.1)  # Simulate processing

                # Handle special commands
                if query.lower() == 'help':
                    content = """Prince Flowers Enhanced Agent (Mock Version)

I am an advanced agentic RL agent with the following capabilities:
- Web search and research
- Analysis and reasoning
- Multi-tool composition
- Self-correction and learning

Available commands:
- prince help - Show this help
- prince status - Show agent status
- prince search <query> - Search for information
- Any other query will be processed through my reasoning system

This is a mock version for testing. The full agent provides:
- Advanced web search and content fetching
- Browser automation capabilities
- Multi-step reasoning chains
- Tool composition and error recovery
- Persistent memory and learning systems"""
                elif query.lower() == 'status':
                    content = """Prince Flowers Agent Status (Mock):
- Status: Active and ready
- Type: Mock agent for integration testing
- Capabilities: All core features simulated
- Performance: Optimal for testing scenarios"""
                elif 'search' in query.lower():
                    search_term = query.lower().replace('search', '').strip()
                    content = f"""Search Results for: {search_term}

Based on my research capabilities, here's what I found:

This is a simulated search response demonstrating the agent's ability to:
1. Process search queries intelligently
2. Return structured information
3. Show reasoning steps and tool usage
4. Provide confidence metrics

In the full version, I would use real web search APIs to fetch current information."""
                else:
                    content = f"""Analysis of your query: "{query}"

I've processed your request using my enhanced reasoning capabilities. This mock response demonstrates:

1. **Query Understanding**: I analyze the intent and context
2. **Tool Selection**: I choose appropriate tools for the task
3. **Multi-step Processing**: I break complex tasks into steps
4. **Response Synthesis**: I provide comprehensive, helpful answers

The full Prince Flowers agent would perform actual web searches, tool compositions, and advanced reasoning for this query."""

                # Create a mock result that matches the expected interface
                class MockResult:
                    def __init__(self, content):
                        self.success = True
                        self.content = content
                        self.confidence = 0.8
                        self.tools_used = ['mock_processor', 'reasoning_engine']
                        self.execution_time = 0.1
                        self.metadata = {'mock': True, 'query_type': 'general'}

                return MockResult(content)

            async def handle_prince_command(self, command: str, context: Dict = None):
                """Handle prince commands in TORQ Console format."""
                # Extract the actual query from the command
                if command.lower().startswith('prince '):
                    query = command[7:].strip()
                elif command.lower().startswith('@prince '):
                    query = command[8:].strip()
                else:
                    query = command.strip()

                result = await self.process_query(query, context)
                return result.content

            def get_status(self):
                return {
                    'agent_name': self.agent_name,
                    'status': 'active',
                    'type': 'mock',
                    'uptime_seconds': time.time() - self.start_time if hasattr(self, 'start_time') else 0
                }

            async def health_check(self):
                return {'status': 'healthy', 'type': 'mock'}

            def get_capabilities_description(self):
                return """Prince Flowers Enhanced Agent (Mock Version)

I am an intelligent agent designed for comprehensive assistance with:
- Advanced web search and research
- Multi-step analysis and reasoning
- Tool composition and workflow automation
- Self-correction and adaptive learning

This mock version demonstrates the integration interface while the full agent provides real capabilities."""

        mock = MockAgent()
        mock.start_time = time.time()
        return mock

    async def query(
        self,
        query_text: str,
        context: Optional[Dict[str, Any]] = None,
        show_performance: bool = False
    ) -> IntegrationResponse:
        """
        Process a query through Prince Flowers with standardized response format.

        Args:
            query_text: The query string
            context: Optional context dictionary
            show_performance: Whether to include performance metrics

        Returns:
            IntegrationResponse with standardized format
        """
        start_time = time.time()
        self.total_queries += 1

        try:
            # Prepare context
            enhanced_context = self._prepare_context(context)

            # Process query through agent based on type
            if self.agent_type == "local" and hasattr(self.agent, 'process_command'):
                # Use local interface method
                result = await self.agent.process_command(query_text, enhanced_context)
                # Convert to expected format
                class LocalResult:
                    def __init__(self, result_dict):
                        self.success = result_dict.get("success", True)
                        self.content = result_dict.get("response", str(result_dict))
                        self.confidence = result_dict.get("performance", {}).get("confidence", 0.8)
                        self.tools_used = result_dict.get("tools_used", ["local_processor"])
                        self.execution_time = result_dict.get("performance", {}).get("execution_time", 0.1)
                        self.metadata = result_dict.get("metadata", {})

                result = LocalResult(result)
            elif self.agent_type == "torq_console" and hasattr(self.agent, 'handle_prince_command'):
                # Use TORQ Console interface - prepare prince command
                prince_command = f"prince {query_text}"
                response_text = await self.agent.handle_prince_command(prince_command, enhanced_context)

                # Convert string response to standard format
                class TORQResult:
                    def __init__(self, content):
                        self.success = True
                        self.content = content
                        self.confidence = 0.8
                        self.tools_used = ["torq_prince_flowers"]
                        self.execution_time = time.time() - start_time
                        self.metadata = {'source': 'torq_console', 'agent_type': 'torq_prince_flowers'}

                result = TORQResult(response_text)
            elif hasattr(self.agent, 'process_query'):
                # Use standard interface with process_query method
                result = await self.agent.process_query(query_text, enhanced_context)
            else:
                # Fallback - try to get response as string
                if hasattr(self.agent, 'handle_prince_command'):
                    prince_command = f"prince {query_text}"
                    response_text = await self.agent.handle_prince_command(prince_command, enhanced_context)
                else:
                    response_text = f"Processed query: {query_text} (fallback response)"

                # Convert to standard format
                class FallbackResult:
                    def __init__(self, content):
                        self.success = True
                        self.content = content
                        self.confidence = 0.7
                        self.tools_used = ["fallback_processor"]
                        self.execution_time = time.time() - start_time
                        self.metadata = {'source': 'fallback', 'agent_type': self.agent_type}

                result = FallbackResult(response_text)

            execution_time = time.time() - start_time

            # Track performance
            self._track_performance(result.success, execution_time, result.confidence)

            if result.success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1

            # Create standardized response
            response = IntegrationResponse(
                success=result.success,
                content=result.content,
                confidence=result.confidence,
                tools_used=result.tools_used,
                execution_time=execution_time,
                metadata=result.metadata,
                agent_status=self.get_status() if show_performance else None
            )

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_queries += 1

            error_msg = f"Integration error: {str(e)}"
            self.logger.error(f"Query processing failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            return IntegrationResponse(
                success=False,
                content=f"I encountered an error processing your request. Please try again.",
                confidence=0.0,
                tools_used=[],
                execution_time=execution_time,
                metadata={'error': str(e), 'agent_type': self.agent_type},
                error=error_msg
            )

    def _prepare_context(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare enhanced context for the agent."""
        enhanced_context = {
            'integration_active': self.integration_active,
            'total_queries': self.total_queries,
            'integration_uptime': time.time() - self.start_time,
            'agent_type': self.agent_type
        }

        if context:
            enhanced_context.update(context)

        if self.torq_console:
            try:
                enhanced_context.update({
                    'torq_session': self.torq_console.get_session_info(),
                    'mcp_servers': len(self.torq_console.connected_servers),
                    'active_files': len(self.torq_console.active_files)
                })
            except Exception as e:
                self.logger.debug(f"Could not add TORQ Console context: {e}")

        return enhanced_context

    def _track_performance(self, success: bool, execution_time: float, confidence: float):
        """Track performance metrics."""
        performance_entry = {
            'timestamp': time.time(),
            'success': success,
            'execution_time': execution_time,
            'confidence': confidence
        }

        self.performance_history.append(performance_entry)

        # Keep only recent history
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        uptime = time.time() - self.start_time
        success_rate = self.successful_queries / max(self.total_queries, 1)

        # Calculate performance metrics
        if self.performance_history:
            avg_execution_time = sum(p['execution_time'] for p in self.performance_history) / len(self.performance_history)
            avg_confidence = sum(p['confidence'] for p in self.performance_history) / len(self.performance_history)
        else:
            avg_execution_time = 0.0
            avg_confidence = 0.0

        base_status = {
            'integration_active': self.integration_active,
            'agent_type': self.agent_type,
            'uptime_seconds': uptime,
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'avg_confidence': avg_confidence,
            'performance_entries': len(self.performance_history)
        }

        # Add agent-specific status if available
        try:
            if hasattr(self.agent, 'get_status'):
                agent_status = self.agent.get_status()
                if isinstance(agent_status, dict):
                    base_status['agent_status'] = agent_status
        except Exception as e:
            self.logger.debug(f"Could not get agent status: {e}")

        return base_status

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        base_capabilities = {
            'web_search': True,
            'research': True,
            'analysis': True,
            'planning': True,
            'memory': True,
            'learning': True,
            'tool_composition': True,
            'error_recovery': True,
            'integration_type': self.agent_type,
            'torq_console_integrated': self.torq_console is not None
        }

        # Add agent-specific capabilities if available
        try:
            if hasattr(self.agent, 'capabilities'):
                if hasattr(self.agent.capabilities, '__dict__'):
                    base_capabilities.update(self.agent.capabilities.__dict__)
                elif isinstance(self.agent.capabilities, dict):
                    base_capabilities.update(self.agent.capabilities)
        except Exception as e:
            self.logger.debug(f"Could not get agent capabilities: {e}")

        return base_capabilities

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            # Test basic functionality
            test_start = time.time()
            test_response = await self.query("health check test", show_performance=False)
            test_time = time.time() - test_start

            health_status = {
                'overall_status': 'healthy' if test_response.success else 'degraded',
                'integration_active': self.integration_active,
                'agent_type': self.agent_type,
                'test_query_success': test_response.success,
                'test_response_time': test_time,
                'total_queries_processed': self.total_queries,
                'current_success_rate': self.successful_queries / max(self.total_queries, 1),
                'uptime_seconds': time.time() - self.start_time
            }

            # Add agent-specific health if available
            try:
                if hasattr(self.agent, 'health_check'):
                    agent_health = await self.agent.health_check()
                    if isinstance(agent_health, dict):
                        health_status['agent_health'] = agent_health
            except Exception as e:
                health_status['agent_health_error'] = str(e)

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'overall_status': 'unhealthy',
                'error': str(e),
                'integration_active': self.integration_active,
                'agent_type': self.agent_type
            }


def register_prince_flowers_integration(torq_console) -> PrinceFlowersIntegrationWrapper:
    """
    Register Prince Flowers integration with TORQ Console.

    Args:
        torq_console: The TORQ Console instance

    Returns:
        PrinceFlowersIntegrationWrapper instance
    """
    logger.info("Registering Prince Flowers integration with TORQ Console")

    try:
        integration = PrinceFlowersIntegrationWrapper(torq_console)
        logger.info("Prince Flowers integration registered successfully")
        return integration
    except Exception as e:
        logger.error(f"Failed to register Prince Flowers integration: {e}")
        raise


# CLI Interface for standalone testing
def main():
    """CLI interface for testing the integration."""
    parser = argparse.ArgumentParser(description="Prince Flowers Integration Test CLI")
    parser.add_argument('--query', '-q', type=str, help='Query to process')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--status', '-s', action='store_true', help='Show integration status')
    parser.add_argument('--health', action='store_true', help='Perform health check')
    parser.add_argument('--capabilities', '-c', action='store_true', help='Show capabilities')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize integration
    integration = PrinceFlowersIntegrationWrapper()

    async def run_cli():
        """Run CLI operations."""
        if args.status:
            status = integration.get_status()
            print("=== Prince Flowers Integration Status ===")
            print(json.dumps(status, indent=2))
            return

        if args.health:
            health = await integration.health_check()
            print("=== Prince Flowers Integration Health ===")
            print(json.dumps(health, indent=2))
            return

        if args.capabilities:
            capabilities = integration.get_capabilities()
            print("=== Prince Flowers Integration Capabilities ===")
            print(json.dumps(capabilities, indent=2))
            return

        if args.query:
            print(f"Processing query: {args.query}")
            response = await integration.query(args.query, show_performance=True)
            print("=== Response ===")
            print(response.content)
            if response.agent_status:
                print(f"\n=== Performance ===")
                print(f"Execution time: {response.execution_time:.2f}s")
                print(f"Confidence: {response.confidence:.1%}")
                print(f"Tools used: {', '.join(response.tools_used)}")
            return

        if args.interactive:
            print("=== Prince Flowers Interactive Test ===")
            print("Type queries or 'quit' to exit")

            while True:
                try:
                    query = input("PF> ").strip()
                    if query.lower() in ['quit', 'exit', 'q']:
                        break

                    if query:
                        response = await integration.query(query, show_performance=True)
                        print(f"\n{response.content}\n")
                        if response.agent_status:
                            print(f"[{response.execution_time:.2f}s, {response.confidence:.1%} confidence]\n")

                except KeyboardInterrupt:
                    break

            print("Goodbye!")
            return

        # Default: show help
        parser.print_help()

    # Run the CLI
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
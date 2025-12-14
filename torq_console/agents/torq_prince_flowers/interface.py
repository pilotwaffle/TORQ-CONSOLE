"""
TORQ Prince Flowers Interface for TORQ Console integration.

This module provides the interface class that integrates the Prince Flowers
agent with TORQ Console's command system and user interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .core.agent import TORQPrinceFlowers


class TORQPrinceFlowersInterface:
    """Interface for TORQ Prince Flowers agent integration with TORQ Console."""

    def __init__(self, console_instance):
        """Initialize the interface with a TORQ Console instance."""
        self.console_instance = console_instance
        self.agent = None
        self.logger = logging.getLogger("TORQPrinceFlowersInterface")

        # Initialize agent
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the Prince Flowers agent."""
        try:
            # Get LLM provider from console instance
            llm_provider = getattr(self.console_instance, 'llm_provider', None)

            # Create agent instance
            self.agent = TORQPrinceFlowers(llm_provider=llm_provider)
            self.logger.info("TORQ Prince Flowers agent initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize TORQ Prince Flowers agent: {e}")
            self.agent = None

    async def handle_prince_command(self, command: str, context: Dict[str, Any] = None) -> str:
        """
        Handle a Prince Flowers command.

        Args:
            command: The command to handle
            context: Additional context for the command

        Returns:
            Response string from the agent
        """
        if not self.agent:
            return "TORQ Prince Flowers agent is not available. Please check the configuration."

        try:
            # Parse command type
            if command.startswith("prince "):
                # Remove "prince " prefix
                query = command[7:].strip()
            else:
                query = command.strip()

            # Handle special commands
            if query.lower() in ["help", "status", "health", "capabilities"]:
                return await self._handle_special_command(query.lower())
            else:
                return await self._handle_query(query, context or {})

        except Exception as e:
            self.logger.error(f"Error handling Prince Flowers command: {e}")
            return f"Error processing command: {str(e)}"

    async def _handle_query(self, query: str, context: Dict[str, Any]) -> str:
        """Handle a regular query."""
        if not self.agent:
            return "Agent not available"

        try:
            result = await self.agent.process_query(query, context)
            return result.response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"

    async def _handle_special_command(self, command: str) -> str:
        """Handle special commands like help, status, health, capabilities."""
        if not self.agent:
            return "Agent not available"

        try:
            if command == "help":
                return self._handle_help_command()
            elif command == "status":
                return await self._handle_status_command()
            elif command == "health":
                return await self._handle_health_command()
            elif command == "capabilities":
                return self._handle_capabilities_command()
            else:
                return f"Unknown special command: {command}"

        except Exception as e:
            self.logger.error(f"Error handling special command '{command}': {e}")
            return f"Error handling command: {str(e)}"

    def _handle_help_command(self) -> str:
        """Return help information for Prince Flowers commands."""
        help_text = """
## TORQ Prince Flowers Enhanced - Help

### Available Commands:

**Direct Query:**
- Simply type your question or request
- Example: "How do I implement JWT authentication in Python?"

**Research Mode:**
- `prince search [query]` - Perform comprehensive web search
- Example: "prince search latest trends in AI development"

**Analysis Mode:**
- `prince analyze [topic]` - Deep analysis of a topic
- Example: "prince analyze microservices vs monolithic architecture"

**System Commands:**
- `prince help` - Show this help message
- `prince status` - Show agent status and statistics
- `prince health` - Perform health check
- `prince capabilities` - List all available capabilities

### Capabilities:
🔍 Advanced web search and research
🤖 Intelligent reasoning and analysis
🛠️ Dynamic tool composition
📊 Performance learning and optimization
🔒 Security-first approach
💾 Intelligent memory management
🎯 Meta-planning and strategy
🔄 Self-correction and adaptation

For more detailed information, use `prince capabilities`.
        """
        return help_text.strip()

    async def _handle_status_command(self) -> str:
        """Return current agent status."""
        try:
            status = self.agent.get_agent_status()

            status_text = f"""
## TORQ Prince Flowers Enhanced - Status

**Agent Information:**
- ID: {status['agent_id']}
- Name: {status['agent_name']}
- Version: {status['version']}
- Uptime: {status['uptime_seconds']:.1f} seconds

**Performance Statistics:**
- Total Queries: {status['total_queries']}
- Successful Responses: {status['successful_responses']}
- Success Rate: {status['success_rate']:.1%}
- Trajectories Tracked: {status['trajectory_count']}

**System Status:**
- Memory Usage: {status.get('memory_usage', 'N/A')}
- Available Tools: {len(status.get('available_tools', []))}
- Learning Engine: Active
            """.strip()

            return status_text

        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return f"Error retrieving status: {str(e)}"

    async def _handle_health_command(self) -> str:
        """Perform and return health check results."""
        try:
            health = await self.agent.health_check()

            if health.get('healthy', False):
                health_text = f"""
## TORQ Prince Flowers Enhanced - Health Check ✅

**Overall Health:** {health['overall_health_score']:.1%}

**Component Status:**
"""
                for component, status in health['components'].items():
                    icon = "✅" if status.get('healthy', False) else "❌"
                    health_text += f"\n- {component}: {icon}"

                if 'performance' in health:
                    perf = health['performance']
                    health_text += f"""

**Performance Metrics:**
- CPU Usage: {perf.get('cpu_usage', 'N/A')}%
- Memory Usage: {perf.get('memory_usage', 'N/A')}MB
- Response Time: {perf.get('avg_response_time', 'N/A')}s
                """

                return health_text.strip()
            else:
                return f"""
## TORQ Prince Flowers Enhanced - Health Check ❌

**Status:** Unhealthy
**Error:** {health.get('error', 'Unknown error')}
**Timestamp:** {health.get('timestamp', 'N/A')}
                """.strip()

        except Exception as e:
            self.logger.error(f"Error performing health check: {e}")
            return f"Error during health check: {str(e)}"

    def _handle_capabilities_command(self) -> str:
        """Return detailed capabilities description."""
        try:
            capabilities = self.agent.get_capabilities_description()

            capabilities_text = f"""
## TORQ Prince Flowers Enhanced - Capabilities

{capabilities}

### Tool Ecosystem:
The agent has access to a comprehensive tool ecosystem including:
- Advanced web search with multi-source capability
- Image generation (DALL-E 3)
- Social media posting (Twitter, LinkedIn)
- Landing page generation
- File operations with security controls
- Code generation for multiple languages
- N8N workflow automation
- Browser automation
- Terminal command execution
- MCP client integration

### Reasoning Modes:
1. **Research Mode:** Comprehensive information gathering and synthesis
2. **Analysis Mode:** Deep technical analysis and recommendations
3. **Composition Mode:** Complex task orchestration with tool chaining
4. **Direct Mode:** Quick responses for simple queries
5. **Meta-Planning Mode:** Strategic planning and adaptive execution

### Learning Features:
- Continuous learning from experience
- User feedback integration
- Performance optimization through experience replay
- Adaptive strategy selection
- Failure analysis and self-correction

### Security Features:
- Comprehensive input validation
- Security-focused code generation
- Safe tool execution with approval workflows
- Error handling with detailed logging
- Fallback mechanisms for robustness

For usage examples, use `prince help`.
            """.strip()

            return capabilities_text

        except Exception as e:
            self.logger.error(f"Error getting capabilities: {e}")
            return f"Error retrieving capabilities: {str(e)}"
"""
TORQ Console Marvin Agent Command Interface
Implements /torq-agent commands for Marvin-powered AI agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional

from .marvin_query_router import MarvinQueryRouter, AgentCapability
from .marvin_prince_flowers import MarvinPrinceFlowers
from .marvin_orchestrator import MarvinAgentOrchestrator, OrchestrationMode, get_orchestrator
from .marvin_workflow_agents import WorkflowType, get_workflow_agent
from .marvin_memory import MarvinAgentMemory, InteractionType, get_agent_memory


class MarvinAgentCommands:
    """Command interface for TORQ Console Marvin Agent integration"""

    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger("TORQ.Marvin.Commands")
        self.model = model or "anthropic/claude-3-5-sonnet-20241022"

        # Initialize components
        self.orchestrator = get_orchestrator(model=self.model)
        self.memory = get_agent_memory()

        self.logger.info("Initialized Marvin Agent Commands")

    async def handle_torq_agent_command(self, subcommand: str, args: List[str]) -> str:
        """Handle /torq-agent subcommands"""
        try:
            if subcommand == "query":
                return await self._handle_query(args)
            elif subcommand == "chat":
                return await self._handle_chat(args)
            elif subcommand == "code":
                return await self._handle_code_generation(args)
            elif subcommand == "debug":
                return await self._handle_debugging(args)
            elif subcommand == "docs":
                return await self._handle_documentation(args)
            elif subcommand == "test":
                return await self._handle_testing(args)
            elif subcommand == "arch":
                return await self._handle_architecture(args)
            elif subcommand == "orchestrate":
                return await self._handle_orchestration(args)
            elif subcommand == "memory":
                return await self._handle_memory(args)
            elif subcommand == "metrics":
                return await self._handle_metrics(args)
            elif subcommand == "status":
                return await self._handle_status(args)
            else:
                return self._help()
        except Exception as e:
            self.logger.error(f"Command error: {e}", exc_info=True)
            return f"ERROR Failed to execute command: {e}"

    async def _handle_query(self, args: List[str]) -> str:
        """Handle intelligent query routing"""
        if not args:
            return """Usage: /torq-agent query <your question or task>

Example:
  /torq-agent query "How do I implement JWT authentication in Python?"
  /torq-agent query "Debug this function that's causing memory leaks"
  /torq-agent query "Generate tests for my API endpoints"
"""

        query = " ".join(args)

        result = await self.orchestrator.process_query(
            query,
            mode=OrchestrationMode.SINGLE_AGENT
        )

        # Record interaction
        self.memory.record_interaction(
            user_input=query,
            agent_response=str(result.primary_response),
            agent_name=result.routing_decision.primary_agent if result.routing_decision else "unknown",
            interaction_type=InteractionType.QUERY,
            success=result.success
        )

        if not result.success:
            return f"FAIL {result.primary_response}"

        output = f"""PASS Query processed

Agent Used: {result.routing_decision.primary_agent if result.routing_decision else 'N/A'}
Confidence: {result.routing_decision.confidence:.2f if result.routing_decision else 0.0}

Response:
{result.primary_response}
"""

        if result.routing_decision and result.routing_decision.reasoning:
            output += f"""
Routing Reasoning:
  {result.routing_decision.reasoning}
"""

        return output

    async def _handle_chat(self, args: List[str]) -> str:
        """Handle conversational agent interaction"""
        if not args:
            return """Usage: /torq-agent chat <message>

Have a conversation with Prince Flowers, the enhanced conversational agent.

Example:
  /torq-agent chat "What's the best way to structure a FastAPI project?"
  /torq-agent chat "Can you help me understand async/await in Python?"
"""

        message = " ".join(args)

        prince_flowers = self.orchestrator.get_agent('prince_flowers')
        response = await prince_flowers.chat(message)

        # Record interaction
        self.memory.record_interaction(
            user_input=message,
            agent_response=response,
            agent_name="prince_flowers",
            interaction_type=InteractionType.GENERAL_CHAT,
            success=True
        )

        return f"""PASS Chat Response

{response}
"""

    async def _handle_code_generation(self, args: List[str]) -> str:
        """Handle code generation requests"""
        if len(args) < 1:
            return """Usage: /torq-agent code <requirements> [--language=<lang>]

Generate code based on requirements.

Options:
  --language=<lang>  Programming language (default: python)

Example:
  /torq-agent code "Create a function to validate email addresses" --language=python
  /torq-agent code "Implement a binary search tree with insert and search methods"
"""

        # Parse arguments
        language = "python"
        requirements_parts = []

        for arg in args:
            if arg.startswith("--language="):
                language = arg[11:]
            else:
                requirements_parts.append(arg)

        requirements = " ".join(requirements_parts)

        # Get code generation agent
        code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION, self.model)
        if not code_agent:
            return "ERROR: Code generation agent not available. Ensure Marvin is properly installed and configured."

        result = await code_agent.generate_code(requirements, language)

        # Record interaction
        self.memory.record_interaction(
            user_input=requirements,
            agent_response=str(result.output) if result.success else "Failed",
            agent_name="code_generation_agent",
            interaction_type=InteractionType.CODE_GENERATION,
            success=result.success
        )

        if not result.success:
            return f"""FAIL Code generation failed

Error: {result.metadata.get('error', 'Unknown error')}

Recommendations:
{self._format_list(result.recommendations)}
"""

        return f"""PASS Code Generated

Language: {language}

{result.output}

Recommendations:
{self._format_list(result.recommendations)}
"""

    async def _handle_debugging(self, args: List[str]) -> str:
        """Handle debugging assistance"""
        if len(args) < 2:
            return """Usage: /torq-agent debug "<code>" "<error_message>" [--language=<lang>]

Debug problematic code.

Options:
  --language=<lang>  Programming language (default: python)

Example:
  /torq-agent debug "def calc(x): return x/0" "ZeroDivisionError" --language=python
"""

        # Parse arguments
        language = "python"
        code = args[0]
        error_message = args[1]

        for arg in args[2:]:
            if arg.startswith("--language="):
                language = arg[11:]

        # Get debugging agent
        debug_agent = get_workflow_agent(WorkflowType.DEBUGGING, self.model)
        if not debug_agent:
            return "ERROR: Debugging agent not available. Ensure Marvin is properly installed and configured."

        result = await debug_agent.debug_issue(code, error_message, language)

        # Record interaction
        self.memory.record_interaction(
            user_input=f"Debug: {error_message}",
            agent_response=str(result.output) if result.success else "Failed",
            agent_name="debugging_agent",
            interaction_type=InteractionType.DEBUG,
            success=result.success
        )

        if not result.success:
            return f"""FAIL Debugging failed

Error: {result.metadata.get('error', 'Unknown error')}

Recommendations:
{self._format_list(result.recommendations)}
"""

        return f"""PASS Debugging Analysis

Language: {language}

{result.output}

Recommendations:
{self._format_list(result.recommendations)}
"""

    async def _handle_documentation(self, args: List[str]) -> str:
        """Handle documentation generation"""
        if len(args) < 1:
            return """Usage: /torq-agent docs "<code>" [--type=<doc_type>] [--language=<lang>]

Generate documentation for code.

Options:
  --type=<doc_type>  Documentation type (api, guide, reference) (default: api)
  --language=<lang>  Programming language (default: python)

Example:
  /torq-agent docs "def add(a, b): return a + b" --type=api --language=python
"""

        # Parse arguments
        language = "python"
        doc_type = "api"
        code = args[0]

        for arg in args[1:]:
            if arg.startswith("--language="):
                language = arg[11:]
            elif arg.startswith("--type="):
                doc_type = arg[7:]

        # Get documentation agent
        doc_agent = get_workflow_agent(WorkflowType.DOCUMENTATION, self.model)
        if not doc_agent:
            return "ERROR: Documentation agent not available. Ensure Marvin is properly installed and configured."

        result = await doc_agent.generate_documentation(code, doc_type, language)

        # Record interaction
        self.memory.record_interaction(
            user_input=f"Document: {code[:100]}",
            agent_response=str(result.output) if result.success else "Failed",
            agent_name="documentation_agent",
            interaction_type=InteractionType.DOCUMENTATION,
            success=result.success
        )

        if not result.success:
            return f"""FAIL Documentation generation failed

Error: {result.metadata.get('error', 'Unknown error')}

Recommendations:
{self._format_list(result.recommendations)}
"""

        return f"""PASS Documentation Generated

Type: {doc_type}
Language: {language}

{result.output}

Recommendations:
{self._format_list(result.recommendations)}
"""

    async def _handle_testing(self, args: List[str]) -> str:
        """Handle test generation"""
        if len(args) < 1:
            return """Usage: /torq-agent test "<code>" [--framework=<framework>] [--language=<lang>]

Generate tests for code.

Options:
  --framework=<framework>  Test framework (pytest, unittest, etc.) (default: pytest)
  --language=<lang>        Programming language (default: python)

Example:
  /torq-agent test "def add(a, b): return a + b" --framework=pytest
"""

        # Parse arguments
        language = "python"
        framework = "pytest"
        code = args[0]

        for arg in args[1:]:
            if arg.startswith("--language="):
                language = arg[11:]
            elif arg.startswith("--framework="):
                framework = arg[12:]

        # Get testing agent
        test_agent = get_workflow_agent(WorkflowType.TESTING, self.model)
        if not test_agent:
            return "ERROR: Testing agent not available. Ensure Marvin is properly installed and configured."

        result = await test_agent.generate_tests(code, framework, language)

        if not result.success:
            return f"""FAIL Test generation failed

Error: {result.metadata.get('error', 'Unknown error')}

Recommendations:
{self._format_list(result.recommendations)}
"""

        return f"""PASS Tests Generated

Framework: {framework}
Language: {language}

{result.output}

Recommendations:
{self._format_list(result.recommendations)}
"""

    async def _handle_architecture(self, args: List[str]) -> str:
        """Handle architecture design"""
        if len(args) < 1:
            return """Usage: /torq-agent arch "<requirements>" [--type=<system_type>]

Design software architecture.

Options:
  --type=<system_type>  System type (web_application, microservice, etc.) (default: web_application)

Example:
  /torq-agent arch "E-commerce platform with user management and payment processing" --type=web_application
"""

        # Parse arguments
        system_type = "web_application"
        requirements_parts = []

        for arg in args:
            if arg.startswith("--type="):
                system_type = arg[7:]
            else:
                requirements_parts.append(arg)

        requirements = " ".join(requirements_parts)

        # Get architecture agent
        arch_agent = get_workflow_agent(WorkflowType.ARCHITECTURE, self.model)
        if not arch_agent:
            return "ERROR: Architecture agent not available. Ensure Marvin is properly installed and configured."

        result = await arch_agent.design_architecture(requirements, system_type)

        if not result.success:
            return f"""FAIL Architecture design failed

Error: {result.metadata.get('error', 'Unknown error')}

Recommendations:
{self._format_list(result.recommendations)}
"""

        return f"""PASS Architecture Design

System Type: {system_type}

{result.output}

Recommendations:
{self._format_list(result.recommendations)}
"""

    async def _handle_orchestration(self, args: List[str]) -> str:
        """Handle multi-agent orchestration"""
        if len(args) < 1:
            return """Usage: /torq-agent orchestrate "<task>" [--mode=<mode>]

Coordinate multiple agents for complex tasks.

Options:
  --mode=<mode>  Orchestration mode (single_agent, multi_agent, pipeline, parallel) (default: multi_agent)

Example:
  /torq-agent orchestrate "Build authentication system with tests and documentation" --mode=multi_agent
"""

        # Parse arguments
        mode = OrchestrationMode.MULTI_AGENT
        task_parts = []

        for arg in args:
            if arg.startswith("--mode="):
                mode_str = arg[7:]
                mode = OrchestrationMode(mode_str)
            else:
                task_parts.append(arg)

        task = " ".join(task_parts)

        result = await self.orchestrator.process_query(task, mode=mode)

        if not result.success:
            return f"""FAIL Orchestration failed

Error: {result.metadata.get('error', 'Unknown error')}
"""

        output = f"""PASS Multi-Agent Orchestration Complete

Mode: {result.mode.value}
Agents Used: {', '.join(result.agent_responses.keys())}

Primary Response:
{result.primary_response}
"""

        if result.routing_decision:
            output += f"""
Routing Decision:
  Primary Agent: {result.routing_decision.primary_agent}
  Confidence: {result.routing_decision.confidence:.2f}
  Reasoning: {result.routing_decision.reasoning}
"""

        return output

    async def _handle_memory(self, args: List[str]) -> str:
        """Handle agent memory operations"""
        if not args:
            return """Usage: /torq-agent memory <action> [options]

Actions:
  snapshot              Show memory snapshot
  history [agent]       Show interaction history
  preferences           Show user preferences
  set <key> <value>     Set user preference
  clear [days]          Clear old interactions

Example:
  /torq-agent memory snapshot
  /torq-agent memory history prince_flowers
  /torq-agent memory set code_style "google"
  /torq-agent memory clear 30
"""

        action = args[0]

        if action == "snapshot":
            snapshot = self.memory.get_memory_snapshot()
            return f"""PASS Memory Snapshot

Total Interactions: {snapshot.total_interactions}
Success Rate: {snapshot.success_rate:.1%}
Average Feedback: {snapshot.average_feedback:.2f}

Interactions by Type:
{self._format_dict(snapshot.interactions_by_type)}

Learned Patterns: {len(snapshot.learned_patterns)}
{self._format_list(snapshot.learned_patterns[:10])}

Last Updated: {snapshot.last_updated}
"""

        elif action == "history":
            agent_name = args[1] if len(args) > 1 else None
            limit = 10

            history = self.memory.get_interaction_history(
                agent_name=agent_name,
                limit=limit
            )

            if not history:
                return "No interaction history found"

            output = f"PASS Interaction History ({len(history)} recent):\n"
            for interaction in history:
                output += f"""
[{interaction.timestamp[:19]}] {interaction.agent_name}
  Type: {interaction.interaction_type.value}
  Success: {'Yes' if interaction.success else 'No'}
  Input: {interaction.user_input[:100]}...
  Response: {interaction.agent_response[:100]}...
"""
            return output

        elif action == "preferences":
            prefs = self.memory.user_preferences
            if not prefs:
                return "No user preferences set"

            return f"""PASS User Preferences

{self._format_dict(prefs)}
"""

        elif action == "set":
            if len(args) < 3:
                return "Usage: /torq-agent memory set <key> <value>"

            key = args[1]
            value = " ".join(args[2:])
            self.memory.update_preference(key, value)

            return f"PASS Preference updated: {key} = {value}"

        elif action == "clear":
            days = int(args[1]) if len(args) > 1 else 30
            self.memory.clear_old_interactions(days)
            return f"PASS Cleared interactions older than {days} days"

        else:
            return "Unknown memory action. Use '/torq-agent memory' for help"

    async def _handle_metrics(self, args: List[str]) -> str:
        """Show comprehensive metrics"""
        metrics = self.orchestrator.get_comprehensive_metrics()

        return f"""PASS Marvin Agent Metrics

Orchestrator:
  Total Requests: {metrics['orchestrator']['total_requests']}
  Single Agent: {metrics['orchestrator']['single_agent_requests']}
  Multi Agent: {metrics['orchestrator']['multi_agent_requests']}
  Success Rate: {metrics['orchestrator']['success_rate']:.1%}

Router:
  Total Routes: {metrics['router']['total_routes']}
  Successful Routes: {metrics['router']['successful_routes']}
  Average Confidence: {metrics['router']['average_confidence']:.2f}

Prince Flowers:
  Conversations: {metrics['prince_flowers']['total_chats']}
  Task Requests: {metrics['prince_flowers']['task_requests']}
  Code Assistance: {metrics['prince_flowers']['code_assistance_requests']}

Memory:
  Total Interactions: {self.memory.get_memory_snapshot().total_interactions}
  Success Rate: {self.memory.get_memory_snapshot().success_rate:.1%}
"""

    async def _handle_status(self, args: List[str]) -> str:
        """Show agent system status"""
        memory_snapshot = self.memory.get_memory_snapshot()

        return f"""PASS Marvin Agent System Status

Model: {self.model}
Status: Active

Components:
  • Query Router: Active
  • Prince Flowers Agent: Active
  • Code Generation Agent: Active
  • Debugging Agent: Active
  • Documentation Agent: Active
  • Testing Agent: Active
  • Architecture Agent: Active
  • Agent Orchestrator: Active
  • Agent Memory: Active ({memory_snapshot.total_interactions} interactions)

Capabilities:
  • General Chat
  • Code Generation
  • Code Review
  • Debugging
  • Documentation
  • Testing
  • Architecture Design
  • Specification Analysis
  • Multi-Agent Orchestration

Recent Activity:
  Last {len(self.memory.interactions[-5:])} interactions recorded
  Average success rate: {memory_snapshot.success_rate:.1%}
"""

    def _format_list(self, items: List[str]) -> str:
        """Format list with bullet points"""
        return "\n".join(f"  • {item}" for item in items)

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary as key-value pairs"""
        return "\n".join(
            f"  • {key}: {value:.2f}" if isinstance(value, float) else f"  • {key}: {value}"
            for key, value in data.items()
        )

    def _help(self) -> str:
        """Main help text"""
        return """TORQ Console Marvin Agent System - AI-Powered Intelligent Agents

Commands:
  /torq-agent query <question>         - Intelligent query routing
  /torq-agent chat <message>           - Chat with Prince Flowers agent
  /torq-agent code <requirements>      - Generate code
  /torq-agent debug <code> <error>     - Debug assistance
  /torq-agent docs <code>              - Generate documentation
  /torq-agent test <code>              - Generate tests
  /torq-agent arch <requirements>      - Design architecture
  /torq-agent orchestrate <task>       - Multi-agent coordination
  /torq-agent memory <action>          - Manage agent memory
  /torq-agent metrics                  - Show performance metrics
  /torq-agent status                   - Show system status

Features:
  • Intelligent query routing to specialized agents
  • Multi-agent orchestration for complex tasks
  • Persistent memory and learning from interactions
  • Real-time code generation, debugging, and testing
  • Architecture design and documentation generation
  • Contextual awareness across conversations

Example Workflow:
  1. /torq-agent query "How do I implement authentication?"
  2. /torq-agent code "JWT authentication with refresh tokens" --language=python
  3. /torq-agent test "<generated_code>" --framework=pytest
  4. /torq-agent docs "<generated_code>" --type=api

Use '/torq-agent <command>' without arguments for detailed help on specific commands.

For Python API usage, see: examples/marvin_integration_examples.py
For quick start guide, see: examples/QUICKSTART.md
"""


# Convenience function to create commands instance
def create_marvin_commands(model: Optional[str] = None) -> MarvinAgentCommands:
    """Create a Marvin Agent Commands instance."""
    return MarvinAgentCommands(model=model)

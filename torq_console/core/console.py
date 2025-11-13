"""
TORQ CONSOLE Main Console Class.

The core console that orchestrates all TORQ CONSOLE functionality,
integrating MCP servers, AI models, Git operations, and Claude Code compatibility.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import sys
import os

from rich.console import Console
from rich.panel import Panel

from .config import TorqConfig
from .logger import setup_logger
from .context_manager import ContextManager
from .chat_manager import ChatManager
from ..mcp.client import MCPClient
from ..mcp.claude_code_bridge import ClaudeCodeBridge
from ..mcp.enhanced_integration import EnhancedMCPIntegration
from ..ui.inline_editor import InlineEditor
from ..ui.command_palette import CommandPalette
from ..utils.git_manager import GitManager
from ..utils.ai_integration import AIIntegration
from ..utils.file_monitor import FileMonitor
from ..llm.manager import LLMManager
from ..llm.providers.websearch import WebSearchProvider
from ..swarm.orchestrator import SwarmOrchestrator
from ..swarm.orchestrator_advanced import AdvancedSwarmOrchestrator
from ..agents.torq_prince_flowers import TORQPrinceFlowersInterface
from ..spec_kit.spec_engine import SpecKitEngine
from ..spec_kit.spec_commands import SpecKitCommands

# Import enhanced integration wrapper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from torq_integration import register_prince_flowers_integration, PrinceFlowersIntegrationWrapper
    ENHANCED_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced integration not available: {e}")
    ENHANCED_INTEGRATION_AVAILABLE = False


class TorqConsole:
    """
    Main TORQ CONSOLE class that provides enhanced AI pair programming
    with MCP integration and Claude Code compatibility.
    """

    def __init__(
        self,
        config: TorqConfig,
        repo_path: Path = None,
        model: str = "claude-3-5-sonnet-20241022",
        diff_tool: str = "delta",
        voice_enabled: bool = False,
        ideation_mode: bool = False,
        planning_mode: bool = False
    ):
        self.config = config
        self.repo_path = repo_path or Path.cwd()
        self.model = model
        self.diff_tool = diff_tool
        self.voice_enabled = voice_enabled
        self.ideation_mode = ideation_mode
        self.planning_mode = planning_mode

        # Initialize components
        self.console = Console()
        self.logger = setup_logger("torq_console")
        self.context_manager = ContextManager(config, self.repo_path)
        self.chat_manager = ChatManager(config, self.context_manager)
        self.git_manager = GitManager(self.repo_path)
        self.ai_integration = AIIntegration(model=model, config=config)
        self.file_monitor = FileMonitor(self.repo_path)

        # Initialize LLM infrastructure
        self.llm_manager = LLMManager(config)
        self.web_search_provider = WebSearchProvider()

        # Initialize advanced swarm orchestrator with enhanced features
        self.swarm_orchestrator = AdvancedSwarmOrchestrator(
            llm_manager=self.llm_manager,
            web_search_provider=self.web_search_provider,
            memory_storage_path=None  # Will use default: ~/.torq_console/swarm_memory
        )

        # Initialize Prince Flowers Enhanced Agent
        self.prince_flowers = TORQPrinceFlowersInterface(self)

        # Initialize enhanced integration wrapper if available
        if ENHANCED_INTEGRATION_AVAILABLE:
            try:
                self.prince_flowers_integration = register_prince_flowers_integration(self)
                self.logger.info("Enhanced Prince Flowers integration registered successfully")
            except Exception as e:
                self.logger.error(f"Failed to register enhanced integration: {e}")
                self.prince_flowers_integration = None
        else:
            self.prince_flowers_integration = None

        # Initialize UI components
        self.inline_editor = InlineEditor(config, self.context_manager)
        self.command_palette = CommandPalette(
            config, self.context_manager, self.chat_manager, self.inline_editor
        )
        # Add console reference for MCP commands
        self.command_palette._console = self

        # MCP components - Enhanced integration
        self.mcp_client = MCPClient()
        self.claude_code_bridge = ClaudeCodeBridge(self.mcp_client)
        self.enhanced_mcp = EnhancedMCPIntegration()
        self.connected_servers: Dict[str, Any] = {}

        # Spec-Kit Integration - Phase 1: Intelligent Spec-Driven Foundation
        self.spec_engine = SpecKitEngine(
            workspace_path=str(self.repo_path),
            enhanced_rl_system=getattr(self, 'enhanced_rl_system', None)
        )
        self.spec_commands = SpecKitCommands(self.spec_engine)

        # State
        self.current_session: Optional[Dict[str, Any]] = None
        self.active_files: List[Path] = []
        self.current_context_id: Optional[str] = None

        self.logger.info(f"TORQ CONSOLE v0.70.0 initialized at {self.repo_path}")
        integration_status = "with Enhanced Integration" if self.prince_flowers_integration else "with Standard Integration"
        self.logger.info(f"All components loaded: ContextManager, ChatManager, InlineEditor, CommandPalette, Prince Flowers Agent {integration_status}")

    async def initialize_async(self):
        """Async initialization for components that need it"""
        try:
            # Initialize enhanced MCP integration
            await self.enhanced_mcp.initialize()
            self.logger.info("Enhanced MCP integration initialized successfully")

            # Initialize Spec-Kit Engine
            await self.spec_engine.initialize()
            self.logger.info("Spec-Kit Engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced MCP integration: {e}")

    async def connect_mcp(self, endpoint: str) -> bool:
        """Connect to an MCP server endpoint using enhanced integration."""
        try:
            print(f"Connecting to {endpoint}...")

            # Try enhanced MCP integration first
            enhanced_success = await self.enhanced_mcp.connect_legacy_endpoint(endpoint)

            # Also maintain legacy client for backward compatibility
            legacy_success = await self.mcp_client.connect(endpoint)

            if enhanced_success or legacy_success:
                if legacy_success:
                    server_info = await self.mcp_client.get_server_info()
                    self.connected_servers[endpoint] = server_info

                    # Initialize Claude Code bridge
                    await self.claude_code_bridge.initialize_for_server(endpoint)

                print(f"OK - MCP server connected: {endpoint}")

                # Show integration status
                mcp_info = self.enhanced_mcp.get_integration_info()
                print(f"Enhanced MCP: {mcp_info['active_enhanced_connections']} connections, Legacy: {mcp_info['legacy_connections']} connections")

                # Show available tools from both systems
                if legacy_success:
                    tools = await self.mcp_client.list_tools()
                    if tools:
                        print(f"Legacy tools: {', '.join([t['name'] for t in tools])}")

                return True
            else:
                print(f"Failed to connect to {endpoint}")
                return False

        except Exception as e:
            self.logger.error(f"MCP connection error: {e}")
            print(f"Error: {e}")
            return False

    async def handle_mcp_command(self, command: str) -> str:
        """Handle MCP commands using enhanced integration"""
        try:
            # Parse MCP command: "/mcp <subcommand> <args>"
            parts = command.split()
            if len(parts) < 2:
                return await self.enhanced_mcp.handle_mcp_command("help", [])

            mcp_command = parts[1]  # Remove "/mcp" prefix
            mcp_args = parts[2:] if len(parts) > 2 else []

            return await self.enhanced_mcp.handle_mcp_command(mcp_command, mcp_args)

        except Exception as e:
            self.logger.error(f"MCP command error: {e}")
            return f"Error executing MCP command: {e}"

    async def handle_spec_kit_command(self, command: str) -> str:
        """Handle Spec-Kit commands using integrated Spec-Kit Engine"""
        try:
            # Parse Spec-Kit command: "/torq-spec <subcommand> <args>"
            parts = command.split()
            if len(parts) < 2:
                return self.spec_commands._help()

            spec_command = parts[1]  # Remove "/torq-spec" prefix
            spec_args = parts[2:] if len(parts) > 2 else []

            return await self.spec_commands.handle_torq_spec_command(spec_command, spec_args)

        except Exception as e:
            self.logger.error(f"Spec-Kit command error: {e}")
            return f"Error executing Spec-Kit command: {e}"

    async def process_command(self, command: str) -> str:
        """
        Process a command that might be for Prince Flowers or general console.

        Args:
            command: The command string

        Returns:
            Response string
        """
        command = command.strip()

        # Check for MCP commands
        if command.lower().startswith('/mcp '):
            return await self.handle_mcp_command(command)

        # Check for Spec-Kit commands
        if command.lower().startswith('/torq-spec '):
            return await self.handle_spec_kit_command(command)

        # Check for Prince Flowers commands
        if command.lower().startswith('prince ') or command.lower().startswith('@prince '):
            return await self.handle_prince_command(command)

        # Handle other TORQ Console commands
        return await self.handle_general_command(command)

    async def handle_prince_command(self, command: str) -> str:
        """
        Handle Prince Flowers commands with enhanced integration support.

        Args:
            command: Prince Flowers command string

        Returns:
            Response from Prince Flowers agent
        """
        try:
            # Prepare context for Prince Flowers
            context = {
                'console_session': self.get_session_info(),
                'mcp_servers': len(self.connected_servers),
                'active_files': [str(f) for f in self.active_files],
                'current_context_id': self.current_context_id,
                'repo_path': str(self.repo_path),
                'show_performance': self.config.get('show_agent_performance', False) if hasattr(self.config, 'get') else False
            }

            # Remove @prince prefix if present
            if command.lower().startswith('@prince '):
                command = 'prince ' + command[8:]

            # Use enhanced integration if available
            if self.prince_flowers_integration:
                # Extract query from command
                if command.lower().startswith('prince '):
                    query = command[7:].strip()
                else:
                    query = command.strip()

                # Handle special integration commands
                if query.lower() == 'integration-status':
                    status = self.prince_flowers_integration.get_status()
                    response = f"Prince Flowers Integration Status:\n{json.dumps(status, indent=2)}"
                elif query.lower() == 'integration-health':
                    health = await self.prince_flowers_integration.health_check()
                    response = f"Prince Flowers Integration Health:\n{json.dumps(health, indent=2)}"
                elif query.lower() == 'integration-capabilities':
                    capabilities = self.prince_flowers_integration.get_capabilities()
                    response = f"Prince Flowers Integration Capabilities:\n{json.dumps(capabilities, indent=2)}"
                else:
                    # Use integration wrapper for processing
                    show_performance = context.get('show_performance', False)
                    integration_response = await self.prince_flowers_integration.query(query, context, show_performance)

                    # Format response
                    if integration_response.success:
                        response = integration_response.content
                        if show_performance and integration_response.agent_status:
                            response += f"\n\n[Performance: {integration_response.execution_time:.2f}s, Confidence: {integration_response.confidence:.1%}]"
                    else:
                        response = integration_response.content
            else:
                # Fallback to standard interface
                response = await self.prince_flowers.handle_prince_command(command, context)

            # Display with nice formatting
            self.console.print(Panel(
                response,
                title="🤖 Prince Flowers Enhanced",
                border_style="cyan"
            ))

            return response

        except Exception as e:
            error_msg = f"Prince Flowers agent error: {e}"
            self.logger.error(error_msg)
            self.console.print(Panel(
                error_msg,
                title="❌ Prince Flowers Error",
                border_style="red"
            ))
            return error_msg

    async def handle_general_command(self, command: str) -> str:
        """
        Handle general TORQ Console commands.

        Args:
            command: General command string

        Returns:
            Response string
        """
        parts = command.split()
        if not parts:
            return "No command provided"

        cmd = parts[0].lower()

        # Route to existing handlers
        if cmd == 'status':
            status = await self.git_manager.get_status()
            return f"Repository status: {status}"
        elif cmd == 'session':
            info = self.get_session_info()
            return f"Session info: {info}"
        elif cmd == 'diff':
            diff = await self.get_visual_diff()
            return diff
        elif cmd in ['help', '?']:
            return self.get_help_text()
        else:
            # Try to handle as a query or edit command
            return await self.handle_query_or_edit(command)

    async def handle_query_or_edit(self, command: str) -> str:
        """
        Handle queries or edit commands.

        Routes conversational queries to Prince Flowers by default.
        Only routes to edit handler for explicit code commands.

        Args:
            command: The command/query string

        Returns:
            Response string
        """
        try:
            command_lower = command.lower()

            # Check if it's an explicit code/edit command
            code_commands = ['build', 'create', 'implement', 'write', 'add', 'fix',
                           'update', 'modify', 'refactor', 'generate code', 'write code']
            is_code_command = any(cmd in command_lower for cmd in code_commands)

            # Check if it's a web search query
            search_terms = ['search', 'find', 'look up', 'get', 'show me']
            is_search_query = any(term in command_lower for term in search_terms)

            # Route decision:
            # 1. Explicit search queries → search handler
            # 2. Explicit code commands → edit handler
            # 3. Everything else (conversational) → Prince Flowers

            if is_search_query:
                return await self._handle_search_query(command)
            elif is_code_command:
                success = await self.edit_files(message=command)
                return f"Edit {'succeeded' if success else 'failed'}"
            else:
                # Route conversational queries to Prince Flowers
                return await self.handle_prince_command(f"prince {command}")

        except Exception as e:
            self.logger.error(f"Error handling query/edit: {e}")
            return f"Error processing command: {e}"

    def get_help_text(self) -> str:
        """Get help text for TORQ Console commands."""
        integration_status = "Enhanced" if self.prince_flowers_integration else "Standard"
        return f"""
🚀 **TORQ CONSOLE Commands**

**General Commands:**
- `status` - Show repository status
- `session` - Show current session info
- `diff` - Show visual diff
- `help` - Show this help

**Prince Flowers Enhanced Agent ({integration_status}):**
- `prince <query>` - Query the enhanced agentic RL agent
- `prince search <topic>` - Search for information
- `prince status` - Show agent performance metrics
- `prince health` - Check agent health
- `prince help` - Show Prince Flowers help
- `@prince <query>` - Alternative command format

**Enhanced Integration Commands:**
- `prince integration-status` - Show integration status
- `prince integration-health` - Check integration health
- `prince integration-capabilities` - Show integration features

**Edit Commands:**
- Any other text will be treated as an edit request

**Examples:**
- `prince search latest AI developments`
- `prince analyze machine learning trends`
- `@prince what is agentic reinforcement learning`
- `prince integration-status`
- `edit this file to add logging`

Type 'prince help' for detailed agent capabilities.
"""

    async def edit_files(
        self,
        message: Optional[str] = None,
        files: Optional[List[str]] = None,
        auto_commit: bool = False,
        context_type: str = "mixed"
    ) -> bool:
        """Edit files with AI assistance, enhanced context management, and MCP integration."""
        try:
            # Start new session
            await self.start_session()

            # Parse context from message using ContextManager
            context_results = {}
            if message:
                context_results = await self.context_manager.parse_and_retrieve(message, context_type)

                # Extract context ID for tracking
                if context_results and self.context_manager.active_contexts:
                    self.current_context_id = list(self.context_manager.active_contexts.keys())[-1]

            # Detect files if not specified, using context information
            if not files:
                files = await self.detect_relevant_files(message, context_results)

            # Ensure we have files to work with
            if not files:
                self.logger.warning("No relevant files detected for edit operation")
                # For web search queries without @-symbols, create a fallback
                if message and not any(symbol in message for symbol in ['@', '#', ':']):
                    # This is likely a search query - handle gracefully
                    return await self._handle_search_query(message)

            self.active_files = [Path(f) for f in files] if files else []

            # Get MCP context if in ideation mode
            mcp_context = {}
            if self.ideation_mode and self.connected_servers:
                mcp_context = await self.gather_mcp_context(message)

            # Prepare enhanced edit context with ContextManager results
            edit_context = {
                "message": message,
                "files": files,
                "repo_status": await self.git_manager.get_status(),
                "mcp_context": mcp_context,
                "context_results": context_results,
                "context_id": self.current_context_id,
                "session_id": self.current_session["id"]
            }

            # Use Claude Code bridge for enhanced editing
            success = await self.claude_code_bridge.perform_edit(edit_context)

            if success and auto_commit:
                await self.git_manager.auto_commit(f"TORQ: {message}")

            return success

        except Exception as e:
            self.logger.error(f"Edit error: {e}")
            print(f"Error during edit: {e}")
            return False

    async def start_session(self) -> Dict[str, Any]:
        """Start a new TORQ CONSOLE session."""
        import uuid
        from datetime import datetime

        session = {
            "id": str(uuid.uuid4())[:8],
            "started_at": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "model": self.model,
            "connected_servers": list(self.connected_servers.keys()),
            "files_tracked": [],
            "integration_type": "Enhanced" if self.prince_flowers_integration else "Standard"
        }

        self.current_session = session
        self.logger.info(f"Started session {session['id']}")

        # Show session info
        print(f"=== TORQ CONSOLE Session ===")
        print(f"Session: {session['id']}")
        print(f"Repository: {self.repo_path.name}")
        print(f"Model: {self.model}")
        print(f"MCP Servers: {len(self.connected_servers)}")
        print(f"Integration: {session['integration_type']}")
        print("="*30)

        return session

    async def detect_relevant_files(self, message: Optional[str], context_results: Dict[str, Any] = None) -> List[str]:
        """Detect relevant files using enhanced context management, AI, and Git status."""
        candidate_files = set()

        # Extract files from context results
        if context_results:
            for context_type, matches in context_results.items():
                for match in matches:
                    if match.file_path:
                        candidate_files.add(str(match.file_path))

        # Get Git status
        git_status = await self.git_manager.get_status()
        candidate_files.update(git_status.get("modified", []))
        candidate_files.update(git_status.get("untracked", []))

        # Get recent files
        recent_files = await self.git_manager.get_recent_files(limit=10)
        candidate_files.update(recent_files)

        # If we have MCP context, use it
        if self.connected_servers:
            mcp_context_files = await self.get_context_files(message)
            candidate_files.update(mcp_context_files)

        # Use AI to filter most relevant if we have a message
        if message and candidate_files:
            relevant_files = await self.ai_integration.select_relevant_files(
                message, list(candidate_files)
            )
            return relevant_files[:10]  # Increased limit for better context

        return list(candidate_files)[:10]

    async def gather_mcp_context(self, message: Optional[str]) -> Dict[str, Any]:
        """Gather relevant context from connected MCP servers."""
        context = {}

        if not message:
            return context

        try:
            # Gather context from each connected server
            for endpoint, server_info in self.connected_servers.items():
                server_context = await self.claude_code_bridge.gather_context(
                    endpoint, message
                )
                if server_context:
                    context[endpoint] = server_context

            self.logger.debug(f"Gathered MCP context: {len(context)} servers")

        except Exception as e:
            self.logger.error(f"Error gathering MCP context: {e}")

        return context

    async def get_context_files(self, message: Optional[str]) -> List[str]:
        """Get context files from MCP servers."""
        context_files = []

        if not message or not self.connected_servers:
            return context_files

        try:
            # Use MCP to find relevant files
            for endpoint in self.connected_servers:
                files = await self.claude_code_bridge.find_relevant_files(
                    endpoint, message, str(self.repo_path)
                )
                context_files.extend(files)

        except Exception as e:
            self.logger.error(f"Error getting context files: {e}")

        return context_files

    async def generate_plan(self, message: str) -> Dict[str, Any]:
        """Generate a multi-file prototyping plan using MCP context."""
        try:
            # Gather comprehensive context
            repo_structure = await self.git_manager.get_repo_structure()
            mcp_context = await self.gather_mcp_context(message)

            # Generate plan using AI with MCP context
            plan = await self.ai_integration.generate_plan(
                message=message,
                repo_structure=repo_structure,
                mcp_context=mcp_context
            )

            # Save plan to session
            if self.current_session:
                self.current_session["last_plan"] = plan

            return plan

        except Exception as e:
            self.logger.error(f"Error generating plan: {e}")
            return {"error": str(e)}

    async def get_visual_diff(self, tool: str = None) -> str:
        """Get enhanced visual diff using specified tool."""
        tool = tool or self.diff_tool
        return await self.git_manager.get_visual_diff(tool=tool)

    async def shutdown(self):
        """Cleanup and shutdown TORQ CONSOLE."""
        try:
            # Shutdown UI components
            await self.command_palette.shutdown()
            await self.inline_editor.cleanup()
            await self.chat_manager.shutdown()

            # Shutdown core components
            await self.context_manager.shutdown()

            # Disconnect MCP servers
            for endpoint in list(self.connected_servers.keys()):
                await self.mcp_client.disconnect(endpoint)

            # Stop file monitoring
            await self.file_monitor.stop()

            # Shutdown LLM manager
            if hasattr(self, 'llm_manager'):
                await self.llm_manager.shutdown()

            # Save session if active
            if self.current_session:
                await self.save_session()

            self.logger.info("TORQ CONSOLE v0.70.0 shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    # Context Management Methods

    async def parse_context(self, text: str, context_type: str = "mixed") -> Dict[str, Any]:
        """Parse and retrieve context using ContextManager."""
        try:
            context_results = await self.context_manager.parse_and_retrieve(text, context_type)

            if context_results:
                self.current_context_id = list(self.context_manager.active_contexts.keys())[-1]

                # Display context summary
                total_matches = sum(len(matches) for matches in context_results.values())
                print(f"✓ Context parsed: {total_matches} matches across {len(context_results)} categories")

                for category, matches in context_results.items():
                    if matches:
                        print(f"  - {category}: {len(matches)} matches")

            return context_results

        except Exception as e:
            self.logger.error(f"Error parsing context: {e}")
            return {}

    async def switch_context(self, context_id: str) -> bool:
        """Switch to a different active context."""
        try:
            context = await self.context_manager.get_active_context(context_id)
            if context:
                self.current_context_id = context_id
                print(f"✓ Switched to context: {context_id}")
                return True
            else:
                print(f"✗ Context not found: {context_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error switching context: {e}")
            return False

    async def list_contexts(self) -> Dict[str, Any]:
        """List all active contexts."""
        try:
            contexts = {}
            for context_id, context_data in self.context_manager.active_contexts.items():
                total_matches = sum(len(matches) for matches in context_data.values())
                contexts[context_id] = {
                    'categories': list(context_data.keys()),
                    'total_matches': total_matches,
                    'is_current': context_id == self.current_context_id
                }

            return contexts

        except Exception as e:
            self.logger.error(f"Error listing contexts: {e}")
            return {}

    async def search_ai_news(self, query: str = "latest AI news") -> str:
        """Search for AI news using the swarm system."""
        try:
            self.logger.info(f"AI news search requested: {query}")
            print(f"🤖 Searching for AI news: '{query}'")

            result = await self.swarm_orchestrator.search_ai_news(query)

            if result:
                self.console.print(Panel(result, title="🤖 AI News", border_style="cyan"))
                return result
            else:
                print("❌ No AI news results found")
                return "No results found"

        except Exception as e:
            self.logger.error(f"AI news search error: {e}")
            print(f"❌ AI news search failed: {e}")
            return f"Search failed: {e}"

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of the swarm intelligence system."""
        try:
            if hasattr(self, 'swarm_orchestrator'):
                return await self.swarm_orchestrator.get_swarm_status()
            else:
                return {"status": "swarm_not_initialized"}
        except Exception as e:
            self.logger.error(f"Error getting swarm status: {e}")
            return {"status": "error", "error": str(e)}

    async def health_check_swarm(self) -> Dict[str, Any]:
        """Perform health check on the swarm system."""
        try:
            if hasattr(self, 'swarm_orchestrator'):
                return await self.swarm_orchestrator.health_check()
            else:
                return {"status": "swarm_not_initialized"}
        except Exception as e:
            self.logger.error(f"Error checking swarm health: {e}")
            return {"status": "error", "error": str(e)}

    async def clear_context(self, context_id: str = None) -> bool:
        """Clear specific context or all contexts."""
        try:
            await self.context_manager.clear_context(context_id)

            if context_id:
                if self.current_context_id == context_id:
                    self.current_context_id = None
                print(f"✓ Cleared context: {context_id}")
            else:
                self.current_context_id = None
                print("✓ Cleared all contexts")

            return True

        except Exception as e:
            self.logger.error(f"Error clearing context: {e}")
            return False

    async def export_context(self, context_id: str = None, format: str = "json") -> Optional[str]:
        """Export context data."""
        try:
            target_id = context_id or self.current_context_id
            if not target_id:
                print("✗ No context to export")
                return None

            exported_data = await self.context_manager.export_context(target_id, format)
            if exported_data:
                print(f"✓ Exported context {target_id} as {format}")
                return exported_data
            else:
                print(f"✗ Failed to export context {target_id}")
                return None

        except Exception as e:
            self.logger.error(f"Error exporting context: {e}")
            return None

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get comprehensive context summary."""
        try:
            # Get ContextManager summary
            cm_summary = await self.context_manager.get_context_summary()

            # Add console-specific information
            summary = {
                **cm_summary,
                'current_context_id': self.current_context_id,
                'session_id': self.current_session['id'] if self.current_session else None,
                'active_files_count': len(self.active_files),
                'connected_mcp_servers': len(self.connected_servers),
                'integration_type': 'Enhanced' if self.prince_flowers_integration else 'Standard'
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting context summary: {e}")
            return {}

    async def get_supported_context_patterns(self) -> Dict[str, List[str]]:
        """Get supported @-symbol patterns."""
        return self.context_manager.get_supported_patterns()

    async def save_session(self):
        """Save current session to disk."""
        if not self.current_session:
            return

        try:
            session_dir = self.config.config_dir / "sessions"
            session_dir.mkdir(exist_ok=True)

            session_file = session_dir / f"{self.current_session['id']}.json"
            session_file.write_text(json.dumps(self.current_session, indent=2))

            self.logger.debug(f"Session saved: {session_file}")

        except Exception as e:
            self.logger.error(f"Error saving session: {e}")

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information with context details."""
        if not self.current_session:
            return {}

        return {
            **self.current_session,
            "active_files": [str(f) for f in self.active_files],
            "current_context_id": self.current_context_id,
            "active_contexts_count": len(self.context_manager.active_contexts),
            "git_status": asyncio.create_task(self.git_manager.get_status()),
            "connected_servers_count": len(self.connected_servers),
            "integration_enhanced": self.prince_flowers_integration is not None
        }

    async def _handle_search_query(self, query: str) -> bool:
        """Handle search queries using the swarm intelligence system."""
        try:
            self.logger.info(f"Handling search query with swarm: {query}")

            print(f"🔍 Searching for: '{query}'")
            print("Using swarm intelligence system...")

            # Determine query type for appropriate routing
            query_lower = query.lower()
            if any(term in query_lower for term in ['ai news', 'artificial intelligence news', 'ai developments']):
                result = await self.swarm_orchestrator.search_ai_news(query)
            elif any(term in query_lower for term in ['latest', 'recent', 'current', 'today']):
                result = await self.swarm_orchestrator.search_recent_developments(query)
            else:
                result = await self.swarm_orchestrator.general_search(query)

            # Display the result
            if result:
                self.console.print(Panel(result, title="Search Results", border_style="blue"))
                return True
            else:
                print("❌ Search completed but no results found")
                return False

        except Exception as e:
            self.logger.error(f"Error handling search query: {e}")
            print(f"❌ Search failed: {e}")
            return False

    async def _auto_connect_mcp(self):
        """Auto-connect to local MCP servers."""
        local_endpoints = [
            "http://localhost:3100",  # Hybrid MCP server
            "http://localhost:3101",  # N8N proxy
            "http://localhost:3102"   # Local machine proxy
        ]

        self.logger.info("Auto-connecting to local MCP servers...")

        for endpoint in local_endpoints:
            try:
                success = await self.connect_mcp(endpoint)
                if success:
                    self.logger.info(f"Auto-connected to {endpoint}")
                else:
                    self.logger.debug(f"Could not connect to {endpoint} (may not be running)")
            except Exception as e:
                self.logger.debug(f"Auto-connect failed for {endpoint}: {e}")

        if self.connected_servers:
            print(f"OK - Auto-connected to {len(self.connected_servers)} MCP servers")
        else:
            print("No MCP servers connected. Run E:\\start_hybrid_mcp.bat first")
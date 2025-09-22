"""
Core TORQ CONSOLE implementation.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import TorqConfig
from ..mcp.client import MCPClient
from ..mcp.manager import MCPManager
from ..ui.shell import InteractiveShell
from ..ui.web import WebUI
from ..utils.git import GitManager
from ..utils.ai import AIManager


logger = logging.getLogger(__name__)


class TorqConsole:
    """Main TORQ CONSOLE class."""
    
    def __init__(
        self,
        config: TorqConfig,
        interactive: bool = False,
        mcp_endpoint: Optional[str] = None,
        voice_enabled: bool = False,
        ideate_mode: bool = False,
        plan_mode: bool = False,
        files: Optional[List[Path]] = None,
    ):
        self.config = config
        self.interactive = interactive
        self.mcp_endpoint = mcp_endpoint
        self.voice_enabled = voice_enabled
        self.ideate_mode = ideate_mode
        self.plan_mode = plan_mode
        self.files = files or []
        
        self.console = Console()
        self.mcp_manager = MCPManager(config)
        self.git_manager = GitManager(config.project_root)
        self.ai_manager = AIManager(config)
        
        # UI components
        self.shell: Optional[InteractiveShell] = None
        self.web_ui: Optional[WebUI] = None
        
        logger.info("TORQ Console initialized")
    
    async def run(self) -> None:
        """Main entry point."""
        try:
            await self._initialize()
            
            if self.interactive:
                await self._run_interactive()
            else:
                await self._run_batch()
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _initialize(self) -> None:
        """Initialize all components."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            
            # Initialize MCP connections
            init_task = progress.add_task("Initializing MCP connections...", total=None)
            await self.mcp_manager.initialize()
            
            if self.mcp_endpoint:
                await self.mcp_manager.connect_endpoint(self.mcp_endpoint)
            
            progress.update(init_task, description="MCP connections ready")
            
            # Initialize AI models
            ai_task = progress.add_task("Loading AI models...", total=None)
            await self.ai_manager.initialize()
            progress.update(ai_task, description="AI models ready")
            
            # Initialize Git
            git_task = progress.add_task("Scanning repository...", total=None)
            await self.git_manager.initialize()
            progress.update(git_task, description="Repository scanned")
            
            # Initialize UI components
            if self.interactive:
                ui_task = progress.add_task("Setting up interactive shell...", total=None)
                self.shell = InteractiveShell(
                    console=self,
                    voice_enabled=self.voice_enabled,
                )
                progress.update(ui_task, description="Interactive shell ready")
            
            if self.config.ui.enable_web_ui:
                web_task = progress.add_task("Starting web UI...", total=None)
                self.web_ui = WebUI(self.config)
                await self.web_ui.start()
                progress.update(web_task, description="Web UI started")
        
        # Display status
        self._display_status()
    
    async def _run_interactive(self) -> None:
        """Run in interactive mode."""
        if not self.shell:
            raise RuntimeError("Interactive shell not initialized")
        
        self.console.print("[green]Starting interactive mode...[/green]")
        await self.shell.run()
    
    async def _run_batch(self) -> None:
        """Run in batch mode."""
        self.console.print("[green]Running in batch mode...[/green]")
        
        if self.files:
            await self._process_files()
        elif self.ideate_mode:
            await self._run_ideate_mode()
        elif self.plan_mode:
            await self._run_plan_mode()
        else:
            self.console.print("[yellow]No files specified and no mode selected[/yellow]")
            self.console.print("Use --interactive for interactive mode or specify files to process")
    
    async def _process_files(self) -> None:
        """Process specified files."""
        self.console.print(f"[cyan]Processing {len(self.files)} files...[/cyan]")
        
        for file_path in self.files:
            if file_path.exists():
                self.console.print(f"Processing: {file_path}")
                # TODO: Implement file processing logic
            else:
                self.console.print(f"[red]File not found: {file_path}[/red]")
    
    async def _run_ideate_mode(self) -> None:
        """Run ideation mode."""
        self.console.print("[cyan]Starting ideation mode...[/cyan]")
        # TODO: Implement ideation mode
    
    async def _run_plan_mode(self) -> None:
        """Run planning mode."""
        self.console.print("[cyan]Starting planning mode...[/cyan]")
        # TODO: Implement planning mode
    
    def _display_status(self) -> None:
        """Display current status."""
        table = Table(title="TORQ CONSOLE Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        # MCP Status
        mcp_status = "Connected" if self.mcp_manager.is_connected() else "Disconnected"
        mcp_details = f"{len(self.mcp_manager.get_active_endpoints())} endpoints"
        table.add_row("MCP", mcp_status, mcp_details)
        
        # AI Status
        ai_status = "Ready" if self.ai_manager.is_ready() else "Not Ready"
        ai_details = f"Model: {self.config.default_model}"
        table.add_row("AI", ai_status, ai_details)
        
        # Git Status
        git_status = "Ready" if self.git_manager.is_repo() else "No Repository"
        git_details = f"Branch: {self.git_manager.current_branch()}" if self.git_manager.is_repo() else ""
        table.add_row("Git", git_status, git_details)
        
        # Voice Status
        voice_status = "Enabled" if self.voice_enabled else "Disabled"
        table.add_row("Voice", voice_status, "")
        
        # Web UI Status
        if self.web_ui:
            web_status = "Running"
            web_details = f"Port: {self.config.ui.web_ui_port}"
        else:
            web_status = "Disabled"
            web_details = ""
        table.add_row("Web UI", web_status, web_details)
        
        self.console.print(table)
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up...")
        
        if self.web_ui:
            await self.web_ui.stop()
        
        await self.mcp_manager.shutdown()
        
        logger.info("Cleanup complete")
    
    # Public API methods
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command and return results."""
        logger.info(f"Executing command: {command}")
        
        # TODO: Implement command parsing and execution
        return {"status": "success", "result": f"Executed: {command}"}
    
    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools."""
        return await self.mcp_manager.get_available_tools()
    
    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP tool."""
        return await self.mcp_manager.call_tool(tool_name, **kwargs)
    
    def get_project_files(self) -> List[Path]:
        """Get list of project files."""
        return self.git_manager.get_tracked_files()
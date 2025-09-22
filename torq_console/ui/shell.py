"""
Interactive shell for TORQ CONSOLE.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import message_dialog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


logger = logging.getLogger(__name__)


class InteractiveShell:
    """Interactive shell for TORQ CONSOLE."""
    
    def __init__(self, console: "TorqConsole", voice_enabled: bool = False):
        self.torq_console = console
        self.voice_enabled = voice_enabled
        self.rich_console = Console()
        
        # Setup prompt session
        self.history = InMemoryHistory()
        self.completions = self._build_completions()
        self.session = PromptSession(
            history=self.history,
            completer=WordCompleter(self.completions),
            key_bindings=self._build_key_bindings(),
        )
        
        self.running = False
        
    def _build_completions(self) -> List[str]:
        """Build command completions."""
        base_commands = [
            "help", "exit", "quit", "clear",
            "status", "config", "tools", "endpoints",
            "mcp", "git", "ai", "files", "ideate", "plan",
        ]
        return base_commands
    
    def _build_key_bindings(self) -> KeyBindings:
        """Build key bindings for the shell."""
        kb = KeyBindings()
        
        @kb.add('c-c')
        def _(event):
            """Exit on Ctrl+C."""
            event.app.exit()
        
        @kb.add('c-d')
        def _(event):
            """Exit on Ctrl+D."""
            event.app.exit()
        
        return kb
    
    async def run(self) -> None:
        """Run the interactive shell."""
        self.running = True
        
        self._display_welcome()
        self._display_help()
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = await self._get_input()
                    
                    if not user_input.strip():
                        continue
                    
                    # Process command
                    await self._process_command(user_input.strip())
                    
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self.rich_console.print(f"[red]Error: {e}[/red]")
                    logger.exception("Error in interactive shell")
        
        finally:
            self.running = False
            self._display_goodbye()
    
    async def _get_input(self) -> str:
        """Get input from user with prompt."""
        prompt_text = "torq> "
        
        # Run prompt in thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.session.prompt(prompt_text)
        )
    
    async def _process_command(self, command: str) -> None:
        """Process a user command."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Built-in commands
        if cmd in ['exit', 'quit']:
            self.running = False
            return
        elif cmd == 'help':
            self._display_help()
            return
        elif cmd == 'clear':
            self.rich_console.clear()
            return
        elif cmd == 'status':
            await self._show_status()
            return
        elif cmd == 'tools':
            await self._show_tools()
            return
        elif cmd == 'endpoints':
            await self._show_endpoints()
            return
        elif cmd == 'config':
            await self._show_config()
            return
        elif cmd == 'mcp':
            await self._handle_mcp_command(args)
            return
        elif cmd == 'git':
            await self._handle_git_command(args)
            return
        elif cmd == 'ai':
            await self._handle_ai_command(args)
            return
        elif cmd == 'files':
            await self._show_files()
            return
        elif cmd == 'ideate':
            await self._start_ideate_mode()
            return
        elif cmd == 'plan':
            await self._start_plan_mode()
            return
        
        # Try to execute as general command
        try:
            result = await self.torq_console.execute_command(command)
            self._display_result(result)
        except Exception as e:
            self.rich_console.print(f"[red]Unknown command: {cmd}[/red]")
            self.rich_console.print("Type 'help' for available commands")
    
    def _display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="dim")
        welcome_text.append("TORQ CONSOLE", style="bold cyan")
        welcome_text.append(" v0.60.0", style="dim")
        welcome_text.append("\nInteractive AI pair programmer with MCP integration", style="dim")
        
        panel = Panel(welcome_text, border_style="cyan", title="Welcome")
        self.rich_console.print(panel)
    
    def _display_help(self) -> None:
        """Display help message."""
        help_text = """Available commands:

[bold cyan]General:[/bold cyan]
  help                 Show this help message
  status               Show system status
  config               Show configuration
  clear                Clear the screen
  exit, quit           Exit TORQ CONSOLE

[bold cyan]MCP:[/bold cyan]
  tools                List available MCP tools
  endpoints            Show MCP endpoint status
  mcp <command>        Execute MCP commands

[bold cyan]Development:[/bold cyan]
  git <command>        Git operations
  ai <command>         AI model operations
  files                List project files
  ideate               Start ideation mode
  plan                 Start planning mode

[bold cyan]Shortcuts:[/bold cyan]
  Ctrl+C, Ctrl+D       Exit
"""
        
        self.rich_console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def _display_goodbye(self) -> None:
        """Display goodbye message."""
        self.rich_console.print("\n[yellow]Thank you for using TORQ CONSOLE![/yellow]")
    
    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display command result."""
        if result.get("status") == "success":
            self.rich_console.print(f"[green]✓[/green] {result.get('result', 'Success')}")
        else:
            self.rich_console.print(f"[red]✗[/red] {result.get('error', 'Failed')}")
    
    async def _show_status(self) -> None:
        """Show system status."""
        self.torq_console._display_status()
    
    async def _show_tools(self) -> None:
        """Show available MCP tools."""
        try:
            tools = await self.torq_console.get_mcp_tools()
            if tools:
                self.rich_console.print(f"[cyan]Available MCP Tools ({len(tools)}):[/cyan]")
                for tool in tools:
                    self.rich_console.print(f"  • {tool['name']} - {tool['description']}")
            else:
                self.rich_console.print("[yellow]No MCP tools available[/yellow]")
        except Exception as e:
            self.rich_console.print(f"[red]Error loading tools: {e}[/red]")
    
    async def _show_endpoints(self) -> None:
        """Show MCP endpoint status."""
        status = self.torq_console.mcp_manager.get_endpoint_status()
        if status:
            self.rich_console.print("[cyan]MCP Endpoints:[/cyan]")
            for name, info in status.items():
                status_icon = "🟢" if info["connected"] else "🔴"
                self.rich_console.print(f"  {status_icon} {name} - {info['tools_count']} tools")
        else:
            self.rich_console.print("[yellow]No MCP endpoints configured[/yellow]")
    
    async def _show_config(self) -> None:
        """Show configuration."""
        config = self.torq_console.config
        self.rich_console.print("[cyan]Configuration:[/cyan]")
        self.rich_console.print(f"  Project Root: {config.project_root}")
        self.rich_console.print(f"  Cache Dir: {config.cache_dir}")
        self.rich_console.print(f"  Default Model: {config.default_model}")
        self.rich_console.print(f"  Voice Enabled: {self.voice_enabled}")
        self.rich_console.print(f"  Telemetry: {config.telemetry_enabled}")
    
    async def _show_files(self) -> None:
        """Show project files."""
        files = self.torq_console.get_project_files()
        if files:
            self.rich_console.print(f"[cyan]Project Files ({len(files)}):[/cyan]")
            for file_path in files[:20]:  # Show first 20
                self.rich_console.print(f"  • {file_path}")
            if len(files) > 20:
                self.rich_console.print(f"  ... and {len(files) - 20} more")
        else:
            self.rich_console.print("[yellow]No project files found[/yellow]")
    
    async def _handle_mcp_command(self, args: List[str]) -> None:
        """Handle MCP-specific commands."""
        if not args:
            self.rich_console.print("[yellow]Usage: mcp <command> [args...][/yellow]")
            return
        
        subcmd = args[0]
        if subcmd == "connect":
            if len(args) < 2:
                self.rich_console.print("[yellow]Usage: mcp connect <endpoint_url>[/yellow]")
                return
            # TODO: Implement MCP connect
            self.rich_console.print(f"[green]Connecting to {args[1]}...[/green]")
        else:
            self.rich_console.print(f"[red]Unknown MCP command: {subcmd}[/red]")
    
    async def _handle_git_command(self, args: List[str]) -> None:
        """Handle Git-specific commands."""
        if not args:
            self.rich_console.print("[yellow]Usage: git <command> [args...][/yellow]")
            return
        
        # TODO: Implement git commands
        self.rich_console.print(f"[green]Git command: {' '.join(args)}[/green]")
    
    async def _handle_ai_command(self, args: List[str]) -> None:
        """Handle AI-specific commands."""
        if not args:
            self.rich_console.print("[yellow]Usage: ai <command> [args...][/yellow]")
            return
        
        # TODO: Implement AI commands
        self.rich_console.print(f"[green]AI command: {' '.join(args)}[/green]")
    
    async def _start_ideate_mode(self) -> None:
        """Start ideation mode."""
        self.rich_console.print("[cyan]Starting ideation mode...[/cyan]")
        # TODO: Implement ideation mode
    
    async def _start_plan_mode(self) -> None:
        """Start planning mode."""
        self.rich_console.print("[cyan]Starting planning mode...[/cyan]")
        # TODO: Implement planning mode
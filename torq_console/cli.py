"""
CLI entry point for TORQ CONSOLE.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .core.console import TorqConsole
from .core.config import TorqConfig
from .core.logger import setup_logging


console = Console()


@click.command()
@click.version_option(version="0.60.0", prog_name="TORQ CONSOLE")
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Start interactive shell with guided prompts",
)
@click.option(
    "--mcp-connect",
    help="MCP endpoint URL for discovery and secure auth",
)
@click.option(
    "--voice-shortcuts",
    is_flag=True,
    help="Enable voice command support via Whisper + TTS",
)
@click.option(
    "--ideate",
    is_flag=True,
    help="Enable web/DB-powered ideation through MCP",
)
@click.option(
    "--plan",
    is_flag=True,
    help="Enable planning mode through MCP",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@click.argument("files", nargs=-1, type=click.Path(path_type=Path))
def main(
    interactive: bool,
    mcp_connect: Optional[str],
    voice_shortcuts: bool,
    ideate: bool,
    plan: bool,
    config: Optional[Path],
    verbose: bool,
    debug: bool,
    files: List[Path],
) -> None:
    """
    TORQ CONSOLE - Enhanced AI pair programmer with MCP integration.
    
    An evolution of Aider that combines CLI speed with Model Context Protocol
    for agentic workflows, polished UX, and intuitive ideation.
    """
    # Setup logging
    setup_logging(verbose=verbose, debug=debug)
    
    # Display welcome banner
    welcome_text = Text()
    welcome_text.append("TORQ CONSOLE", style="bold cyan")
    welcome_text.append(" v0.60.0\n", style="dim")
    welcome_text.append("Enhanced AI pair programmer with MCP integration", style="dim")
    
    console.print(Panel(welcome_text, border_style="cyan"))
    
    try:
        # Load configuration
        torq_config = TorqConfig.load(config)
        
        # Initialize TORQ Console
        torq = TorqConsole(
            config=torq_config,
            interactive=interactive,
            mcp_endpoint=mcp_connect,
            voice_enabled=voice_shortcuts,
            ideate_mode=ideate,
            plan_mode=plan,
            files=list(files),
        )
        
        # Run the console
        asyncio.run(torq.run())
        
    except KeyboardInterrupt:
        console.print("\n[yellow]TORQ CONSOLE interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
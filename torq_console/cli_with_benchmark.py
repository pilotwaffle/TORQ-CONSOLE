"""
TORQ CONSOLE Command Line Interface with Benchmarking Integration.

Enhanced CLI that bridges Aider functionality with Claude Code capabilities
through MCP integration, polished UX, and comprehensive performance benchmarking.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List

import click
import rich.console
from rich.panel import Panel
from rich.text import Text

from .core.console import TorqConsole
from .core.config import TorqConfig
from .ui.shell import InteractiveShell
from .ui.web import WebUI
from .utils.git_manager import GitManager
from .mcp.client import MCPClient


console = rich.console.Console()


def show_banner():
    """Display TORQ CONSOLE banner."""
    banner = Text("TORQ CONSOLE", style="bold cyan")
    subtitle = Text("Enhanced AI pair programmer with MCP + Claude Code integration",
                    style="dim")
    version = Text("v0.80.0", style="bold green")  # Updated version with benchmarking

    panel_content = f"{banner}\n{subtitle}\n{version}"
    panel = Panel(panel_content, border_style="cyan", padding=(1, 2))
    console.print(panel)


@click.group(invoke_without_command=True)
@click.option('--interactive', '-i', is_flag=True,
              help='Launch interactive shell with guided prompts')
@click.option('--web', '-w', is_flag=True,
              help='Launch web UI interface')
@click.option('--voice', '-v', is_flag=True,
              help='Enable voice command shortcuts')
@click.option('--mcp-connect', multiple=True,
              help='Connect to MCP server endpoints')
@click.option('--ideate', is_flag=True,
              help='Enable ideation mode with MCP context')
@click.option('--plan', is_flag=True,
              help='Generate multi-file prototyping plans')
@click.option('--diff-tool', default='delta',
              help='Visual diff tool (delta, git, bat)')
@click.option('--model', '-m', default='claude-3-5-sonnet-20241022',
              help='AI model to use')
@click.option('--config', '-c', type=click.Path(),
              help='Configuration file path')
@click.option('--repo-path', type=click.Path(exists=True),
              help='Repository path (default: current directory)')
@click.pass_context
def main(ctx, interactive, web, voice, mcp_connect, ideate, plan,
         diff_tool, model, config, repo_path):
    """
    TORQ CONSOLE - Enhanced AI pair programmer.

    Combines Aider's CLI speed with Cursor's polish, enhanced with
    MCP integration for agentic workflows, Claude Code compatibility,
    and comprehensive performance benchmarking.
    """
    if ctx.invoked_subcommand is None:
        show_banner()

        # Load configuration
        config_path = Path(config) if config else None
        torq_config = TorqConfig.load(config_path)

        # Initialize console
        console_instance = TorqConsole(
            config=torq_config,
            repo_path=Path(repo_path) if repo_path else Path.cwd(),
            model=model,
            diff_tool=diff_tool,
            voice_enabled=voice,
            ideation_mode=ideate,
            planning_mode=plan
        )

        # Initialize async components
        asyncio.run(console_instance.initialize_async())

        # Connect MCP servers
        for endpoint in mcp_connect:
            asyncio.run(console_instance.connect_mcp(endpoint))

        # Launch appropriate interface
        if web:
            asyncio.run(launch_web_ui(console_instance))
        elif interactive:
            asyncio.run(launch_interactive_shell(console_instance))
        else:
            # Default: show usage and start interactive
            click.echo("Starting interactive mode...")
            asyncio.run(launch_interactive_shell(console_instance))


@main.command()
@click.argument('message', required=False)
@click.option('--files', '-f', multiple=True,
              help='Files to edit')
@click.option('--auto-commit', is_flag=True,
              help='Auto-commit changes')
def edit(message, files, auto_commit):
    """Edit files with AI assistance."""
    console.print(f"[cyan]Editing files:[/cyan] {', '.join(files) if files else 'auto-detected'}")

    config = TorqConfig.load()
    console_instance = TorqConsole(config=config)

    asyncio.run(console_instance.edit_files(
        message=message,
        files=list(files) if files else None,
        auto_commit=auto_commit
    ))


@main.command()
@click.option('--endpoint', '-e', required=True,
              help='MCP server endpoint (stdio://path or http://url)')
@click.option('--test', is_flag=True,
              help='Test connection without saving')
def mcp(endpoint, test):
    """Manage MCP server connections."""
    console.print(f"[cyan]Connecting to MCP server:[/cyan] {endpoint}")

    client = MCPClient()
    result = asyncio.run(client.connect(endpoint))

    if result:
        console.print("[green]OK[/green] MCP connection successful")
        if not test:
            config = TorqConfig.load()
            config.add_mcp_endpoint(endpoint)
            config.save()
            console.print("[green]OK[/green] MCP endpoint saved to config")
    else:
        console.print("[red]Failed[/red] MCP connection failed")
        sys.exit(1)


@main.command()
@click.option('--output', '-o', type=click.Path(),
              help='Output file for diff')
@click.option('--tool', default='delta',
              help='Diff tool to use')
def diff(output, tool):
    """Generate enhanced visual diffs."""
    git_manager = GitManager(Path.cwd())

    console.print(f"[cyan]Generating diff with {tool}...[/cyan]")
    diff_result = asyncio.run(git_manager.get_visual_diff(tool=tool))

    if output:
        Path(output).write_text(diff_result)
        console.print(f"[green]OK[/green] Diff saved to {output}")
    else:
        console.print(diff_result)


@main.command()
@click.option('--port', '-p', default=8080,
              help='Web UI port')
@click.option('--host', default='localhost',
              help='Web UI host')
def serve(port, host):
    """Launch web UI server."""
    console.print(f"[cyan]Starting web UI at http://{host}:{port}[/cyan]")

    config = TorqConfig.load()
    console_instance = TorqConsole(config=config)

    asyncio.run(launch_web_ui(console_instance, host=host, port=port))


@main.command()
def config_init():
    """Initialize TORQ CONSOLE configuration."""
    config_path = TorqConfig.get_default_path()

    if config_path.exists():
        if not click.confirm(f"Config file exists at {config_path}. Overwrite?"):
            return

    config = TorqConfig.create_default()
    config.save()

    console.print(f"[green]OK[/green] Configuration initialized at {config_path}")
    console.print("\nEdit the config file to customize:")
    console.print(f"  {config_path}")


@main.command(name='eval')
@click.option('--set', 'set_name', required=True,
              help='Evaluation set to run (e.g., v1.0)')
@click.option('--seed', default=42, type=int,
              help='Random seed for deterministic behavior')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for JSON results')
@click.option('--no-baseline', is_flag=True,
              help='Skip baseline comparison')
def eval_command(set_name, seed, output, no_baseline):
    """
    Run TORQ Console evaluation suite.

    Executes deterministic evaluation sets to measure system performance,
    accuracy, and functionality across different task categories.

    Examples:
      torq-console eval --set v1.0
      torq-console eval --set v1.0 --seed 123 --output results.json
      torq-console eval --set v1.0 --no-baseline
    """
    try:
        from .core.evaluation.runner import EvaluationRunner

        # Determine evaluation set path
        eval_sets_dir = Path(__file__).parent / 'eval_sets'
        eval_set_path = eval_sets_dir / set_name

        if not eval_set_path.exists():
            console.print(f"[red]Evaluation set not found: {eval_set_path}[/red]")
            sys.exit(1)

        # Run evaluation
        runner = EvaluationRunner(str(eval_set_path), seed)
        results = runner.run_evaluation(
            output_file=output,
            compare_baseline=not no_baseline
        )

        # Exit with appropriate code (0 for pass, 1 for fail)
        sys.exit(0 if results.get('passed', True) else 1)

    except ImportError as e:
        console.print(f"[red]ERROR[/red] Evaluation system not available: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]ERROR[/red] {e}")
        sys.exit(1)


@main.command(name='agent')
@click.argument('subcommand', required=False)
@click.argument('args', nargs=-1)
@click.option('--model', '-m', default='anthropic/claude-3-5-sonnet-20241022',
              help='AI model to use for agents')
def agent_command(subcommand, args, model):
    """
    Marvin-powered AI agent system.

    Commands:
      query       - Intelligent query routing
      chat        - Chat with Prince Flowers agent
      code        - Generate code
      debug       - Debug assistance
      docs        - Generate documentation
      test        - Generate tests
      arch        - Design architecture
      orchestrate - Multi-agent coordination
      memory      - Manage agent memory
      metrics     - Show performance metrics
      status      - Show system status

    Example:
      torq-console agent query "How do I implement JWT auth?"
      torq-console agent code "Binary search tree" --language=python
    """
    try:
        from .agents import create_marvin_commands

        marvin_commands = create_marvin_commands(model=model)

        if not subcommand:
            result = asyncio.run(marvin_commands.handle_torq_agent_command('help', []))
        else:
            result = asyncio.run(marvin_commands.handle_torq_agent_command(subcommand, list(args)))

        console.print(result)
    except ImportError as e:
        console.print(f"[red]ERROR[/red] Marvin integration not available: {e}")
        console.print("Install marvin with: pip install marvin")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]ERROR[/red] Agent command failed: {e}")
        sys.exit(1)


@main.command()
@click.pass_context
def bench(ctx):
    """Performance benchmarking and SLO enforcement.

    Run performance benchmarks, monitor SLO compliance, and track performance over time.

    Examples:
      torq-console bench run                    # Run all benchmarks
      torq-console bench run simple_response    # Run specific test
      torq-console bench list                   # List recent results
      torq-console bench trends --category interactive  # Show performance trends
      torq-console bench regressions            # Check for regressions
    """
    try:
        from .benchmarking.cli import create_benchmark_commands
        bench_commands = create_benchmark_commands()

        # Get the parent context and forward args
        if ctx.parent:
            parent_params = ctx.parent.params
        else:
            parent_params = {}

        # Create a new context for benchmark commands
        bench_ctx = click.Context(bench_commands, info_name='bench', parent=ctx.parent)

        # Forward the command
        bench_commands.main(standalone_mode=False, parent=ctx.parent, obj=parent_params)

    except ImportError as e:
        console.print(f"[red]ERROR[/red] Benchmarking system not available: {e}")
        console.print("Ensure benchmarking dependencies are installed")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]ERROR[/red] Benchmark command failed: {e}")
        sys.exit(1)


async def launch_interactive_shell(console_instance: TorqConsole):
    """Launch interactive shell interface."""
    shell = InteractiveShell(console_instance)
    await shell.run()


async def launch_web_ui(console_instance: TorqConsole, host: str = "localhost", port: int = 8080):
    """Launch web UI interface."""
    web_ui = WebUI(console_instance)
    await web_ui.start_server(host=host, port=port)


if __name__ == '__main__':
    main()
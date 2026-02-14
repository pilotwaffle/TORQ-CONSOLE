#!/usr/bin/env python3
"""
TORQ Console - Main Entry Point
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Main entry point for TORQ Console"""

    # Load environment variables
    env_file = Path("E:/.env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

    # Import and run TORQ Console
    try:
        from torq_console.core.console import TorqConsole

        # Parse command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--help' or sys.argv[1] == '-h':
                print("""
TORQ Console - AI-Powered Development Environment

USAGE:
    python -m torq_console [COMMAND]

COMMANDS:
    (no args)        Start interactive TORQ Console
    --help, -h       Show this help message
    --version        Show version info
    --web            Start web UI server (Google Antigravity theme)
    --terminal, --tui Start beautiful terminal UI with Rich
    --test           Run self-test

FEATURES:
    • AI pair programming with Claude, DeepSeek, Ollama
    • Rich Terminal UI with Google Antigravity theme
    • Prince Flowers agent with advanced memory
    • Marvin 3.0 integration with intelligent agents
    • Spec Kit with RL-powered analysis
    • Web UI with Google Antigravity theme
    • MCP tool integration
    • Real-time collaboration

For more information, see: E:\\TORQ-TEST-REPORT.md
                """)
                return 0
            elif sys.argv[1] == '--version':
                from torq_console import __version__
                print(f"TORQ Console v{__version__}")
                return 0
            elif sys.argv[1] == '--web':
                # Start web UI
                print("Starting TORQ Console Web UI...")
                import asyncio

                from torq_console.ui.web import WebUI
                from torq_console.core.config import TorqConfig
                from torq_console.core.console import TorqConsole
                from torq_console.core.context_manager import ContextManager

                async def run_web():
                    config = TorqConfig()
                    console = TorqConsole(config)
                    console.context_manager = ContextManager(config=config)

                    # Skip async initialization for now - it's timing out
                    print("Skipping async initialization (timing out)")
                    print("Web server will start with limited functionality")

                    # Create and start web UI
                    web_ui = WebUI(console=console)
                    print("Starting web server on http://127.0.0.1:8088")
                    await web_ui.start_server(host="127.0.0.1", port=8088)

                asyncio.run(run_web())
                return 0
            elif sys.argv[1] == '--terminal' or sys.argv[1] == '--tui':
                # Start Rich Terminal UI
                import asyncio
                from torq_console.ui.terminal_ui import main as run_terminal_ui
                asyncio.run(run_terminal_ui())
                return 0
            elif sys.argv[1] == '--test':
                # Run self-test
                print("Running TORQ Console self-test...")
                import subprocess
                result = subprocess.run([sys.executable, "E:/test_torq_complete.py"], capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
                return result.returncode
            else:
                print(f"Unknown command: {sys.argv[1]}")
                print("Use --help for available commands")
                return 1
        else:
            # Start interactive console
            print("=" * 60)
            print("  TORQ Console - AI-Powered Development")
            print("=" * 60)
            print()

            # Initialize and start interactive session
            import asyncio

            async def run_console():
                try:
                    # Create console instance INSIDE async function
                    from torq_console.core.config import TorqConfig
                    config = TorqConfig()
                    console = TorqConsole(config)

                    # Initialize async components
                    await console.initialize_async()
                    print("\nTORQ Console ready!")
                    print("Type 'help' for commands or 'exit' to quit")
                    print()

                    while True:
                        try:
                            command = input("TORQ> ").strip()

                            if command.lower() in ['exit', 'quit']:
                                print("Goodbye!")
                                break
                            elif command.lower() == 'help':
                                print(console.get_help_text())
                            elif command:
                                result = await console.process_command(command)
                                print(result)
                        except EOFError:
                            print("\nGoodbye!")
                            break
                        except KeyboardInterrupt:
                            print("\nUse 'exit' to quit")
                            continue

                    await console.shutdown()
                except Exception as e:
                    print(f"Console error: {e}")
                    import traceback
                    traceback.print_exc()

            asyncio.run(run_console())

    except ImportError as e:
        print(f"Error importing TORQ Console: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\n\nTORQ Console stopped by user.")
        return 0
    except Exception as e:
        print(f"Error starting TORQ Console: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())